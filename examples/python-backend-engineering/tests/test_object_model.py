import pytest

from fulfillhub.object_model import Leaf, NonNegativeInt, Quantity, traced


def test_data_descriptor_precedes_instance_dictionary() -> None:
    quantity = Quantity(3)
    quantity.__dict__["amount"] = 999
    assert quantity.amount == 3
    assert isinstance(Quantity.amount, NonNegativeInt)
    quantity.amount = 4
    assert quantity.amount == 4


@pytest.mark.parametrize("invalid", [True, "3", 1.5, None])
def test_descriptor_rejects_non_integer_assignment(invalid: object) -> None:
    quantity = Quantity(3)
    with pytest.raises(TypeError):
        quantity.amount = invalid
    assert quantity.amount == 3


def test_negative_assignment_keeps_previous_value() -> None:
    quantity = Quantity(3)
    with pytest.raises(ValueError):
        quantity.amount = -1
    assert quantity.amount == 3


def test_method_binding_and_cooperative_mro() -> None:
    leaf = Leaf()
    method = leaf.trace
    assert method.__self__ is leaf
    assert method() == ["Left", "Right", "Root"]
    assert [cls.__name__ for cls in Leaf.__mro__] == ["Leaf", "Left", "Right", "Root", "object"]


def test_decorator_preserves_signature_metadata_and_return() -> None:
    events: list[str] = []

    @traced(events)
    def multiply(value: int, *, factor: int) -> int:
        """Multiply a value."""
        return value * factor

    assert multiply(3, factor=2) == 6
    assert multiply.__name__ == "multiply"
    assert multiply.__doc__ == "Multiply a value."
    assert events == ["enter:multiply", "exit:multiply"]


def test_decorator_propagates_original_exception_and_records_exit() -> None:
    events: list[str] = []
    failure = ValueError("original failure")

    @traced(events)
    def broken() -> None:
        raise failure

    with pytest.raises(ValueError) as caught:
        broken()
    assert caught.value is failure
    assert events == ["enter:broken", "exit:broken"]
