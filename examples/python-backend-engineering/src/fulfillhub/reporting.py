"""Stream validated CSV products while keeping file ownership explicit."""

import argparse
import csv
import json
import re
from collections import Counter
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO, TypedDict

from fulfillhub.inventory import Product


class CsvInventoryError(ValueError):
    """The CSV structure or a product row is invalid."""


class Report(TypedDict):
    generated_at: str
    product_rows: int
    total_units: int
    units_by_tenant: dict[str, int]


def _products(stream: TextIO) -> Iterator[Product]:
    reader = csv.reader(stream, strict=True)
    try:
        if next(reader, None) != ["tenant", "sku", "stock"]:
            raise CsvInventoryError("expected header: tenant,sku,stock")
        for row in reader:
            if not row or all(not field.strip() for field in row):
                continue
            try:
                if len(row) != 3:
                    raise ValueError("expected exactly three columns")
                tenant, sku, raw_stock = (field.strip() for field in row)
                if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,31}", sku) is None:
                    raise ValueError("invalid SKU")
                if re.fullmatch(r"0|[1-9][0-9]*", raw_stock) is None:
                    raise ValueError("stock must be a non-negative decimal integer")
                yield Product(tenant, sku, int(raw_stock))
            except ValueError as exc:
                raise CsvInventoryError(f"line {reader.line_num}: {exc}") from exc
    except csv.Error as exc:
        raise CsvInventoryError(f"line {reader.line_num}: malformed CSV") from exc


@contextmanager
def open_products(path: Path) -> Iterator[Iterator[Product]]:
    """The iterator may only be consumed inside this context's lifetime."""
    with path.open(encoding="utf-8", newline="") as stream:
        yield _products(stream)


def summarize(products: Iterable[Product], *, at: datetime) -> Report:
    if at.utcoffset() is None:
        raise ValueError("report timestamp must be timezone-aware")
    units: Counter[str] = Counter()
    rows = 0
    for product in products:
        units[product.tenant] += product.stock
        rows += 1
    return {
        "generated_at": at.astimezone(UTC).isoformat(),
        "product_rows": rows,
        "total_units": sum(units.values()),
        "units_by_tenant": dict(sorted(units.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    with open_products(args.path) as products:
        report = summarize(products, at=datetime.now(UTC))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
