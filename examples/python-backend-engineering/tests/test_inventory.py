from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from fulfillhub.inventory import (
    InsufficientStock,
    InventoryRepository,
    InventoryService,
    MemoryRepository,
    Product,
    StockStatus,
    UnknownSku,
)
from fulfillhub.storage import JsonRepository, decode_product


@pytest.fixture(params=["memory", "json"])
def repository(request: pytest.FixtureRequest, tmp_path: Path) -> InventoryRepository:
    repo: InventoryRepository
    if request.param == "memory":
        repo = MemoryRepository()
    else:
        repo = JsonRepository(tmp_path / "inventory.json")
    repo.save(Product("acme", "keyboard", 3))
    repo.save(Product("other", "keyboard", 7))
    return repo


def test_reservation_preserves_original_and_other_tenant(repository: InventoryRepository) -> None:
    original = repository.get("acme", "keyboard")
    updated = InventoryService(repository).reserve("acme", "keyboard", quantity=2)
    assert original.stock == 3
    assert updated.stock == 1
    assert updated.status is StockStatus.AVAILABLE
    assert repository.get("acme", "keyboard") == updated
    assert repository.get("other", "keyboard").stock == 7


def test_insufficient_stock_does_not_mutate(repository: InventoryRepository) -> None:
    before = repository.all()
    with pytest.raises(InsufficientStock):
        InventoryService(repository).reserve("acme", "keyboard", quantity=4)
    assert repository.all() == before


@pytest.mark.parametrize("quantity", [0, -1, True])
def test_invalid_quantity_does_not_mutate(repository: InventoryRepository, quantity: int) -> None:
    before = repository.all()
    with pytest.raises(ValueError, match="positive integer"):
        InventoryService(repository).reserve("acme", "keyboard", quantity=quantity)
    assert repository.all() == before


def test_unknown_tenant_cannot_reserve(repository: InventoryRepository) -> None:
    with pytest.raises(UnknownSku) as caught:
        InventoryService(repository).reserve("missing", "keyboard", quantity=1)
    assert isinstance(caught.value.__cause__, KeyError)


def test_zero_stock_is_valid_but_unavailable(repository: InventoryRepository) -> None:
    result = InventoryService(repository).reserve("acme", "keyboard", quantity=3)
    assert result.status is StockStatus.EMPTY
    with pytest.raises(InsufficientStock):
        InventoryService(repository).reserve("acme", "keyboard", quantity=1)


def test_product_is_immutable() -> None:
    product = Product("acme", "keyboard", 3)
    with pytest.raises(FrozenInstanceError):
        product.stock = 0


@pytest.mark.parametrize(
    "data",
    [
        None,
        [],
        {},
        {"tenant": "a", "sku": "b", "stock": True},
        {"tenant": "a", "sku": "b", "stock": -1},
        {"tenant": "a", "sku": "b", "stock": "3"},
    ],
)
def test_external_data_requires_runtime_validation(data: object) -> None:
    with pytest.raises(ValueError):
        decode_product(data)


def test_json_snapshot_survives_reopening(tmp_path: Path) -> None:
    path = tmp_path / "inventory.json"
    repo = JsonRepository(path)
    repo.save(Product("acme", "keyboard", 3))
    InventoryService(repo).reserve("acme", "keyboard", quantity=2)
    assert JsonRepository(path).get("acme", "keyboard").stock == 1
    assert not path.with_suffix(".json.tmp").exists()


def test_json_decode_error_preserves_cause(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("not-json", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid inventory JSON") as caught:
        JsonRepository(path)
    assert caught.value.__cause__ is not None


def test_failed_write_preserves_memory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = JsonRepository(tmp_path / "inventory.json")
    repo.save(Product("acme", "keyboard", 3))

    def fail_replace(self: Path, target: Path) -> Path:
        raise OSError("simulated replacement failure")

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError, match="simulated"):
        InventoryService(repo).reserve("acme", "keyboard", quantity=1)
    assert repo.get("acme", "keyboard").stock == 3
    assert JsonRepository(repo.path).get("acme", "keyboard").stock == 3
    assert not repo.path.with_suffix(".json.tmp").exists()
