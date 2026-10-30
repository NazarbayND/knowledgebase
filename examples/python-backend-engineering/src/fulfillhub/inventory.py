"""A single-process inventory service with explicit ownership and typed boundaries."""

from collections.abc import Iterable
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Protocol


class InventoryError(Exception):
    """Base for business-level inventory failures."""


class UnknownSku(InventoryError):
    """The tenant does not own a product with this SKU."""


class InsufficientStock(InventoryError):
    """A reservation would make stock negative."""


class StockStatus(StrEnum):
    AVAILABLE = "available"
    EMPTY = "empty"


@dataclass(frozen=True, slots=True)
class Product:
    tenant: str
    sku: str
    stock: int

    def __post_init__(self) -> None:
        if not self.tenant.strip() or not self.sku.strip():
            raise ValueError("tenant and SKU must be non-empty")
        if isinstance(self.stock, bool) or not isinstance(self.stock, int) or self.stock < 0:
            raise ValueError("stock must be a non-negative integer")

    @property
    def status(self) -> StockStatus:
        return StockStatus.AVAILABLE if self.stock else StockStatus.EMPTY


class InventoryRepository(Protocol):
    def get(self, tenant: str, sku: str) -> Product: ...

    def save(self, product: Product) -> None: ...

    def all(self) -> tuple[Product, ...]: ...


class MemoryRepository:
    def __init__(self, products: Iterable[Product] = ()) -> None:
        self._products = {(p.tenant, p.sku): p for p in products}

    def get(self, tenant: str, sku: str) -> Product:
        try:
            return self._products[tenant, sku]
        except KeyError as exc:
            raise UnknownSku(f"unknown product: {tenant}/{sku}") from exc

    def save(self, product: Product) -> None:
        self._products[product.tenant, product.sku] = product

    def all(self) -> tuple[Product, ...]:
        return tuple(self._products.values())


class InventoryService:
    def __init__(self, repository: InventoryRepository) -> None:
        self.repository = repository

    def reserve(self, tenant: str, sku: str, *, quantity: int) -> Product:
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("quantity must be a positive integer")
        current = self.repository.get(tenant, sku)
        if quantity > current.stock:
            raise InsufficientStock(f"requested {quantity}; available {current.stock}")
        updated = replace(current, stock=current.stock - quantity)
        self.repository.save(updated)
        return updated
