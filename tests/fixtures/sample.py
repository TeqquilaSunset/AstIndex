class BaseClass:
    """Base class."""

    def base_method(self):
        pass


class DerivedClass(BaseClass):
    """Derived class."""

    def __init__(self, value: int):
        self.value = value

    def get_value(self) -> int:
        return self.value


def standalone_function(name: str) -> str:
    """A standalone function."""
    return f"Hello, {name}"
