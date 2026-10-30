from dataclasses import asdict

from fulfillhub.inventory import InventoryService, MemoryRepository, Product


def main() -> None:
    original = Product("acme", "keyboard", 3)
    service = InventoryService(MemoryRepository([original]))
    updated = service.reserve("acme", "keyboard", quantity=2)
    print({"before": asdict(original), "after": asdict(updated)})


if __name__ == "__main__":
    main()
