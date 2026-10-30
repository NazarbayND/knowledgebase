"""JSON adapter. Single-writer snapshots are not database transactions."""

import json
from dataclasses import asdict
from pathlib import Path

from fulfillhub.inventory import MemoryRepository, Product


def decode_product(data: object) -> Product:
    if not isinstance(data, dict):
        raise ValueError("product must be an object")
    tenant: object = data.get("tenant")
    sku: object = data.get("sku")
    stock: object = data.get("stock")
    if not isinstance(tenant, str) or not isinstance(sku, str):
        raise ValueError("tenant and SKU must be strings")
    if isinstance(stock, bool) or not isinstance(stock, int):
        raise ValueError("stock must be an integer")
    return Product(tenant, sku, stock)


class JsonRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        records: object = []
        if path.exists():
            try:
                with path.open(encoding="utf-8") as stream:
                    records = json.load(stream)
            except json.JSONDecodeError as exc:
                raise ValueError("invalid inventory JSON") from exc
        if not isinstance(records, list):
            raise ValueError("inventory must be a JSON list")
        self._memory = MemoryRepository(decode_product(record) for record in records)

    def get(self, tenant: str, sku: str) -> Product:
        return self._memory.get(tenant, sku)

    def save(self, product: Product) -> None:
        # Prepare a new snapshot first; a write failure must not change memory.
        updated = MemoryRepository(self._memory.all())
        updated.save(product)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        try:
            with temporary.open("w", encoding="utf-8") as stream:
                json.dump([asdict(p) for p in updated.all()], stream, indent=2)
                stream.write("\n")
            temporary.replace(self.path)
        finally:
            temporary.unlink(missing_ok=True)
        self._memory = updated

    def all(self) -> tuple[Product, ...]:
        return self._memory.all()
