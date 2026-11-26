"""Deterministic request fingerprint utility for Orders idempotency.

Generates a SHA-256 fingerprint of a canonical cart representation.
The fingerprint is used to detect duplicate order creation requests
that reuse the same idempotency key with different cart contents.

Independent of database sessions and HTTP requests. All monetary values
are handled as Decimal and serialized as normalized decimal strings --
never as float.
"""

import hashlib
import json
from decimal import Decimal, InvalidOperation

from src.core.models.cart import Cart


TWO_PLACES = Decimal("0.01")


def _normalize_decimal(value: Decimal) -> str:
    """Normalize a Decimal monetary value to a fixed decimal string.

    Quantizes to two decimal places (matching Numeric(10, 2) used by
    price columns) and serializes without scientific notation or float
    conversion. Rejects values that cannot be represented exactly.

    Args:
        value: A Decimal monetary value.

    Returns:
        A normalized fixed-point decimal string (e.g. "29.99").

    Raises:
        ValueError: If value is not a Decimal or cannot be quantized
            to two decimal places.
    """
    if not isinstance(value, Decimal):
        raise ValueError(
            f"Monetary value must be a Decimal, got {type(value).__name__}"
        )

    try:
        quantized = value.quantize(TWO_PLACES)
    except InvalidOperation as exc:
        raise ValueError(
            f"Cannot normalize monetary value {value!r} to two decimal places"
        ) from exc

    return str(quantized)


def generate_cart_fingerprint(cart: Cart) -> str:
    """Generate a deterministic SHA-256 fingerprint for a cart request.

    The canonical representation contains:
      - cart_id
      - cart items sorted by product_id, each with product_id, quantity,
        and price_at_time (normalized Decimal string)

    Args:
        cart: A Cart model instance with cart_id and items loaded.

    Returns:
        A 64-character lowercase SHA-256 hexadecimal digest.

    Raises:
        ValueError: If any cart item's price_at_time is not a valid
            Decimal monetary value.
    """
    canonical = {
        "cart_id": str(cart.cart_id),
        "items": [
            {
                "product_id": str(item.product_id),
                "quantity": item.quantity,
                "price_at_time": _normalize_decimal(item.price_at_time),
            }
            for item in sorted(cart.items, key=lambda i: str(i.product_id))
        ],
    }

    json_str = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()
