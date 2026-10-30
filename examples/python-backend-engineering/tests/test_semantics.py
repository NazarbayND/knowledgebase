"""Executable answer key for Module 1's twelve prediction questions."""

import pytest

CASES = [
    ("a = [1]; b = a; b.append(2); result = a", [1, 2]),
    ("a = [[1]]; b = a.copy(); b[0].append(2); result = a", [[1, 2]]),
    ("import copy; a = [[1]]; b = copy.deepcopy(a); b[0].append(2); result = a", [[1]]),
    ("a = [1]; b = [1]; result = (a == b, a is b)", (True, False)),
    ("result = (isinstance(True, int), True == 1)", (True, True)),
    ("result = (bool([]), bool('0'), None is None)", (False, True, True)),
    (
        "def add(x, items=[]):\n    items.append(x)\n    return items\n"
        "a = add(1); b = add(2); result = (a, a is b)",
        ([1, 2], True),
    ),
    ("functions = [lambda: i for i in range(3)]; result = [f() for f in functions]", [2, 2, 2]),
    ("functions = [lambda i=i: i for i in range(3)]; result = [f() for f in functions]", [0, 1, 2]),
    ("values = iter([1, 2]); first = list(values); result = (first, list(values))", ([1, 2], [])),
    (
        "events = []\ntry:\n    events.append('try')\nfinally:\n    events.append('finally')\n"
        "result = events",
        ["try", "finally"],
    ),
    ("data = {'a': 1, 'b': 2}; data['a'] = 3; result = list(data.items())", [("a", 3), ("b", 2)]),
]


@pytest.mark.parametrize("source,expected", CASES, ids=[f"snippet-{i}" for i in range(1, 13)])
def test_prediction(source: str, expected: object) -> None:
    namespace: dict[str, object] = {}
    exec(source, namespace)  # Only the trusted literal snippets above are executed.
    assert namespace["result"] == expected
