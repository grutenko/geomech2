from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@runtime_checkable
class Eq(Protocol):
    def __eq__(self, o: object) -> bool: ...


@dataclass
class Identity:
    o: Eq
    rel_data_o: Eq
    rel_data_target: Eq = None

    def __post_init__(self):
        if not isinstance(self.o, Eq) or not isinstance(self.rel_data_o, Eq) or not isinstance(self.rel_data_target, Eq):
            raise ValueError("Identity must be equable objects.")

    def __eq__(self, o):
        if not isinstance(o, Identity):
            return False
        if not isinstance(o.o, type(self.o)) or o.o.RID != self.o.RID:
            return False
        if not isinstance(o.rel_data_o, type(self.rel_data_o)):
            return False
        if hasattr(o.rel_data_o, "RID"):
            if o.rel_data_o.RID != self.o.RID:
                return False
        elif o.rel_data_o != self.rel_data_o:
            return False
        return o.rel_data_target == self.rel_data_target
