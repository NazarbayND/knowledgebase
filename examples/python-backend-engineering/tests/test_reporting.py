import io
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from fulfillhub.inventory import Product
from fulfillhub.reporting import CsvInventoryError, open_products, summarize


def test_report_consumes_a_one_shot_stream_once(tmp_path: Path) -> None:
    path = tmp_path / "inventory.csv"
    path.write_text(
        "tenant,sku,stock\nacme,keyboard,3\n\nacme,monitor,2\nother,keyboard,7\n",
        encoding="utf-8",
    )
    at = datetime(2026, 10, 30, 12, tzinfo=timezone(timedelta(hours=3)))
    with open_products(path) as products:
        report = summarize(products, at=at)
        assert list(products) == []
    assert report == {
        "generated_at": "2026-10-30T09:00:00+00:00",
        "product_rows": 3,
        "total_units": 12,
        "units_by_tenant": {"acme": 5, "other": 7},
    }


@pytest.mark.parametrize(
    "contents",
    [
        "",
        "sku,tenant,stock\nkeyboard,acme,3\n",
        "tenant,sku,stock\nacme,keyboard,-1\n",
        "tenant,sku,stock\nacme,keyboard,True\n",
        "tenant,sku,stock\nacme,keyboard,1.5\n",
        "tenant,sku,stock\nacme,keyboard,03\n",
        "tenant,sku,stock\nacme,bad sku,3\n",
        "tenant,sku,stock\n ,keyboard,3\n",
        "tenant,sku,stock\nacme,keyboard\n",
        'tenant,sku,stock\nacme,"unterminated,3\n',
    ],
)
def test_invalid_csv_is_rejected(tmp_path: Path, contents: str) -> None:
    path = tmp_path / "invalid.csv"
    path.write_text(contents, encoding="utf-8")
    with pytest.raises(CsvInventoryError):
        with open_products(path) as products:
            list(products)


def test_row_error_preserves_line_and_cause(tmp_path: Path) -> None:
    path = tmp_path / "invalid.csv"
    path.write_text("tenant,sku,stock\nacme,keyboard,-1\n", encoding="utf-8")
    with pytest.raises(CsvInventoryError, match="line 2") as caught:
        with open_products(path) as products:
            list(products)
    assert isinstance(caught.value.__cause__, ValueError)


@pytest.mark.parametrize("fail_consumer", [False, True])
def test_partial_consumer_closes_owned_file(
    monkeypatch: pytest.MonkeyPatch, fail_consumer: bool
) -> None:
    stream = io.StringIO("tenant,sku,stock\nacme,keyboard,3\nacme,monitor,2\n")
    monkeypatch.setattr(Path, "open", lambda *args, **kwargs: stream)
    try:
        with open_products(Path("unused.csv")) as products:
            assert next(products) == Product("acme", "keyboard", 3)
            if fail_consumer:
                raise RuntimeError("consumer failed")
    except RuntimeError:
        assert fail_consumer
    assert stream.closed


def test_zero_stock_and_header_only_file_are_valid(tmp_path: Path) -> None:
    path = tmp_path / "empty.csv"
    path.write_text("tenant,sku,stock\n", encoding="utf-8")
    with open_products(path) as products:
        assert summarize(products, at=datetime(2026, 1, 1, tzinfo=UTC))["total_units"] == 0
    assert summarize([Product("acme", "keyboard", 0)], at=datetime.now(UTC))["product_rows"] == 1


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        summarize([], at=datetime(2026, 1, 1))
