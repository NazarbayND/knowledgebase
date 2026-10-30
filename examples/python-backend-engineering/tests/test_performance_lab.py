import pytest

from fulfillhub.performance_lab import count_matches, indexed_count, measure


@pytest.mark.parametrize(
    "values,queries,expected",
    [([], [1], 0), ([1, 1, 2], [1, 1, 3], 2), ([0, 1, 2], [0, 2, 4], 2)],
)
def test_index_preserves_membership_count_semantics(
    values: list[int], queries: list[int], expected: int
) -> None:
    assert count_matches(values, queries) == expected
    assert indexed_count(values, queries) == expected


@pytest.mark.parametrize("size,repeats", [(0, 1), (10001, 1), (1, 0), (1, 21)])
def test_experiment_limits(size: int, repeats: int) -> None:
    with pytest.raises(ValueError):
        measure(size, repeats=repeats)
