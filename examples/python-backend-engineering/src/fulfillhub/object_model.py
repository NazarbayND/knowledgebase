"""Typed descriptor, method resolution and decorator investigations."""

from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, Self, TypeVar, overload


class NonNegativeInt:
    def __set_name__(self, owner: type, name: str) -> None:
        self.storage = "_" + name

    @overload
    def __get__(self, instance: None, owner: type | None = None) -> Self: ...

    @overload
    def __get__(self, instance: object, owner: type | None = None) -> int: ...

    def __get__(self, instance: object | None, owner: type | None = None) -> Self | int:
        if instance is None:
            return self
        value: object = getattr(instance, self.storage)
        if not isinstance(value, int):
            raise TypeError("corrupt descriptor storage")
        return value

    def __set__(self, instance: object, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("quantity must be an integer")
        if value < 0:
            raise ValueError("quantity must be non-negative")
        setattr(instance, self.storage, value)


class Quantity:
    amount = NonNegativeInt()

    def __init__(self, amount: int) -> None:
        self.amount = amount


class Root:
    def trace(self) -> list[str]:
        return ["Root"]


class Left(Root):
    def trace(self) -> list[str]:
        return ["Left", *super().trace()]


class Right(Root):
    def trace(self) -> list[str]:
        return ["Right", *super().trace()]


class Leaf(Left, Right):
    pass


P = ParamSpec("P")
R = TypeVar("R")


def traced(events: list[str]) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorate(function: Callable[P, R]) -> Callable[P, R]:
        @wraps(function)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            events.append("enter:" + function.__name__)
            try:
                return function(*args, **kwargs)
            finally:
                events.append("exit:" + function.__name__)

        return wrapper

    return decorate


def main() -> None:
    quantity = Quantity(3)
    quantity.__dict__["amount"] = 999  # The data descriptor still wins lookup.
    print("descriptor value:", quantity.amount)
    print("method order:", Leaf().trace())
    print("MRO:", [cls.__name__ for cls in Leaf.__mro__])
    events: list[str] = []

    @traced(events)
    def multiply(value: int, *, factor: int) -> int:
        return value * factor

    print("decorated result:", multiply(3, factor=2), "events:", events)


if __name__ == "__main__":
    main()
