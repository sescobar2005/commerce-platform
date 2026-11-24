"""Unit tests for seller endpoints.

Tests use mocked database sessions - no live database required.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from src.core.sellers.router import register_seller
from src.core.models.seller import Seller
from src.core.models.store import Store
from src.core.models.user import User
from src.core.security.schemas import UserResponse
from src.core.sellers.router import create_store, get_seller
from src.core.sellers.schemas import (
    SellerRegisterRequest,
    SellerResponse,
    StoreCreateRequest,
    StoreResponse,
)


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
        self.mock_db.refresh.return_value = None

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

        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        self.mock_db.commit.side_effect = IntegrityError("statement", {}, Exception("db error"))

        current_user = UserResponse(
            user_id="user-123",
            username="johndoe",
            email="john@example.com",
            is_seller=False,
            is_verified=False,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        with pytest.raises(HTTPException) as exc_info:
            register_seller(request, self.mock_db, current_user)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        self.mock_db.rollback.assert_called_once()


class TestCreateStoreEndpoint:
    """Tests for the store creation endpoint."""

    def setup_method(self):
        self.mock_db = MagicMock()

    def test_successful_store_creation(self):
        """Successful store creation should create store and return response."""
        request = StoreCreateRequest(
            name="Test Store",
            description="A test store",
            slug="test-store",
            logo_url="https://example.com/logo.png",
            cover_image_url="https://example.com/cover.png",
        )

        # Mock existing seller
        mock_seller = MagicMock()
        mock_seller.seller_id = "seller-123"

        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_seller,  # seller lookup succeeds
            None,  # no existing store with this slug
        ]

        current_user = UserResponse(
            user_id="seller-123",
            username="johndoe",
            email="john@example.com",
            is_seller=True,
            is_verified=True,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        self.mock_db.add.return_value = None
        self.mock_db.commit.return_value = None
        self.mock_db.refresh.return_value = None

        def mock_refresh(obj):
            obj.store_id = "store-123"
            obj.created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            obj.updated_at = obj.created_at

        self.mock_db.refresh.side_effect = mock_refresh

        result = create_store("seller-123", request, self.mock_db, current_user)

        assert result.store_id == "store-123"
        assert result.seller_id == "seller-123"
        assert result.name == "Test Store"
        assert result.description == "A test store"
        assert result.slug == "test-store"
        assert result.logo_url == "https://example.com/logo.png"
        assert result.cover_image_url == "https://example.com/cover.png"
        assert result.is_active is True

        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()

        added_store = self.mock_db.add.call_args[0][0]
        assert added_store.seller_id == "seller-123"
        assert added_store.name == "Test Store"
        assert added_store.description == "A test store"
        assert added_store.slug == "test-store"

    def test_duplicate_store_slug_raises_conflict(self):
        """Duplicate store slug should raise 409 Conflict."""
        request = StoreCreateRequest(
            name="Test Store",
            description="A test store",
            slug="existing-store",
        )

        mock_seller = MagicMock()
        mock_seller.seller_id = "seller-123"

        existing_store = MagicMock()
        existing_store.slug = "existing-store"

        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_seller,  # seller lookup succeeds
            existing_store,  # store slug lookup finds existing store
        ]

        current_user = UserResponse(
            user_id="seller-123",
            username="johndoe",
            email="john@example.com",
            is_seller=True,
            is_verified=True,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        with pytest.raises(HTTPException) as exc_info:
            create_store("seller-123", request, self.mock_db, current_user)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in exc_info.value.detail
        self.mock_db.commit.assert_not_called()

    def test_seller_not_found_raises_404(self):
        """Non-existent seller should raise 404."""
        request = StoreCreateRequest(
            name="Test Store",
            slug="test-store",
        )

        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        current_user = UserResponse(
            user_id="seller-123",
            username="johndoe",
            email="john@example.com",
            is_seller=True,
            is_verified=True,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        with pytest.raises(HTTPException) as exc_info:
            create_store("seller-123", request, self.mock_db, current_user)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Seller not found" in exc_info.value.detail

    def test_wrong_seller_raises_403(self):
        """Store belonging to another seller should raise 403."""
        request = StoreCreateRequest(
            name="Test Store",
            slug="test-store",
        )

        mock_seller = MagicMock()
        mock_seller.seller_id = "seller-456"  # Different seller

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_seller

        current_user = UserResponse(
            user_id="user-123",
            username="johndoe",
            email="john@example.com",
            is_seller=False,
            is_verified=False,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        with pytest.raises(HTTPException) as exc_info:
            create_store("seller-456", request, self.mock_db, current_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "does not belong to the authenticated seller" in exc_info.value.detail


class TestGetSellerEndpoint:
    """Tests for the seller profile retrieval endpoint."""

    def setup_method(self):
        self.mock_db = MagicMock()

    def test_successful_get_seller(self):
        """Successful retrieval should return seller profile."""
        request = None  # GET has no request body

        mock_seller = MagicMock()
        mock_seller.seller_id = "seller-123"
        mock_seller.store_name = "Test Store"
        mock_seller.business_name = "Test Business"
        mock_seller.tax_id = "TAX123"
        mock_seller.payment_info_json = "{}"
        mock_seller.bank_account = "BANK123"
        mock_seller.is_verified = False
        mock_seller.created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_seller

        current_user = UserResponse(
            user_id="seller-123",
            username="johndoe",
            email="john@example.com",
            is_seller=True,
            is_verified=True,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        result = get_seller("seller-123", self.mock_db, current_user)

        assert result.seller_id == "seller-123"
        assert result.store_name == "Test Store"
        assert result.business_name == "Test Business"
        assert result.tax_id == "TAX123"
        assert result.payment_info_json == "{}"
        assert result.bank_account == "BANK123"
        assert result.is_verified is False

    def test_seller_not_found_raises_404(self):
        """Non-existent seller should raise 404."""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        current_user = UserResponse(
            user_id="seller-123",
            username="johndoe",
            email="john@example.com",
            is_seller=True,
            is_verified=True,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        with pytest.raises(HTTPException) as exc_info:
            get_seller("nonexistent-seller", self.mock_db, current_user)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Seller not found" in exc_info.value.detail

    def test_seller_belongs_to_another_user_raises_403(self):
        """Seller belonging to another user should raise 403."""
        mock_seller = MagicMock()
        mock_seller.seller_id = "seller-456"  # Different seller

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_seller

        current_user = UserResponse(
            user_id="user-123",
            username="johndoe",
            email="john@example.com",
            is_seller=False,
            is_verified=False,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        with pytest.raises(HTTPException) as exc_info:
            get_seller("seller-456", self.mock_db, current_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Seller does not belong to the authenticated user" in exc_info.value.detail