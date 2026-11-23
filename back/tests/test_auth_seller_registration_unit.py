"""Unit tests for seller registration endpoint.

Tests use mocked database sessions - no live database required.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from src.core.sellers.router import register_seller
from src.core.models.seller import Seller
from src.core.models.user import User
from src.core.security.schemas import UserResponse
from src.core.sellers.schemas import SellerRegisterRequest, SellerResponse


class TestRegisterSellerEndpoint:
    """Tests for the seller registration endpoint."""

    def setup_method(self):
        self.mock_db = MagicMock()

    def test_successful_registration(self):
        """Successful registration should create seller and return response."""
        request = SellerRegisterRequest(
            store_name="Test Store",
            business_name="Test Business",
            tax_id="TAX123",
            payment_info_json="{}",
            bank_account="BANK123",
        )

        # Mock no existing seller profile
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        current_user = UserResponse(
            user_id="user-123",
            username="johndoe",
            email="john@example.com",
            is_seller=False,
            is_verified=False,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        self.mock_db.add.return_value = None
        self.mock_db.commit.return_value = None

        def mock_refresh(obj):
            obj.user_id = current_user.user_id
            obj.created_at = current_user.created_at

        self.mock_db.refresh.side_effect = mock_refresh

        result = register_seller(request, self.mock_db, current_user)

        assert result.seller_id == "user-123"
        assert result.store_name == "Test Store"
        assert result.business_name == "Test Business"
        assert result.tax_id == "TAX123"
        assert result.payment_info_json == "{}"
        assert result.bank_account == "BANK123"
        assert result.is_verified is False

        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()

        added_seller = self.mock_db.add.call_args[0][0]
        assert added_seller.seller_id == "user-123"
        assert added_seller.store_name == "Test Store"
        assert added_seller.business_name == "Test Business"
        assert added_seller.tax_id == "TAX123"
        assert added_seller.payment_info_json == "{}"
        assert added_seller.bank_account == "BANK123"

    def test_duplicate_seller_raises_conflict(self):
        """Duplicate seller profile should raise 409 Conflict."""
        request = SellerRegisterRequest(
            store_name="Existing Store",
            business_name="Existing Business",
            tax_id="EXISTING123",
            payment_info_json="{}",
            bank_account="EXISTING_BANK",
        )

        mock_existing_seller = MagicMock()
        mock_existing_seller.seller_id = "user-123"

        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_existing_seller
        )

        current_user = UserResponse(
            user_id="user-123",
            username="johndoe",
            email="john@example.com",
            is_seller=False,
            is_verified=False,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        with pytest.raises(HTTPException) as exc_info:
            register_seller(request, self.mock_db, current_user=current_user)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "already has a seller profile" in exc_info.value.detail
        self.mock_db.commit.assert_not_called()

    def test_database_error_rolls_back(self):
        """Database error during commit should trigger rollback and 409."""
        request = SellerRegisterRequest(
            store_name="Test Store",
            business_name="Test Business",
            tax_id="TAX123",
            payment_info_json="{}",
            bank_account="BANK123",
        )

        current_user = UserResponse(
            user_id="user-123",
            username="johndoe",
            email="john@example.com",
            is_seller=False,
            is_verified=False,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        self.mock_db.commit.side_effect = IntegrityError("statement", {}, Exception("db error"))

        with pytest.raises(HTTPException) as exc_info:
            register_seller(request, self.mock_db, current_user)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        self.mock_db.rollback.assert_called_once()