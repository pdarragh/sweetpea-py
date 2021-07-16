__all__ = [
    "Formula",
    "SimpleFormula",
    "Var", "And", "Or", "Not",
    "ComplexFormula",
    "If", "IfAndOnlyIf", "Iff",
]


from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Formula:
    def __new__(cls, *_, **__):
        annotations = cls.__dict__.get("__annotations__", {})
        if not annotations:
            raise ValueError(f"Cannot directly instantiate {cls.__name__}.")
        return super().__new__(cls)

    def __str__(self) -> str:
        class_name = type(self).__name__
        annotations = type(self).__dict__.get("__annotations__", {})
        field_strs = []
        for field in annotations:
            value = getattr(self, field)
            field_str: str
            if isinstance(value, (list, tuple)):
                field_str = "(" + ", ".join(map(str, value)) + ")"
            else:
                field_str = str(value)
            field_strs.append(field_str)
        fields_str = ", ".join(field_strs)
        return f"{class_name}({fields_str})"


@dataclass(frozen=True)
class SimpleFormula(Formula):
    pass


@dataclass(frozen=True)
class Var(SimpleFormula):
    value: int
    label: str

    def __str__(self) -> str:
        return f"v{self.value}"


@dataclass(frozen=True)
class And(SimpleFormula):
    conjuncts: Tuple[Formula]

    def __init__(self, *conjuncts):
        if not conjuncts:
            raise ValueError("Cannot instantiate Or without conjuncts!")
        if len(conjuncts) == 1:
            conjuncts = conjuncts[0]
        # Fix the type of the conjuncts.
        if isinstance(conjuncts, tuple):
            pass
        elif isinstance(conjuncts, list):
            conjuncts = tuple(conjuncts)
        else:
            try:
                iterator = iter(conjuncts)
                conjuncts = tuple(iterator)
            except TypeError:
                conjuncts = (conjuncts, )
        # Set the field!
        object.__setattr__(self, "conjuncts", conjuncts)

    def __getitem__(self, index: int) -> Formula:
        return self.conjuncts[index]

    def __len__(self) -> int:
        return len(self.conjuncts)


@dataclass(frozen=True)
class Or(SimpleFormula):
    disjuncts: Tuple[Formula]

    def __init__(self, *disjuncts):
        if not disjuncts:
            raise ValueError("Cannot instantiate Or without disjuncts!")
        if len(disjuncts) == 1:
            disjuncts = disjuncts[0]
        # Fix the type of the disjuncts.
        if isinstance(disjuncts, tuple):
            pass
        elif isinstance(disjuncts, list):
            disjuncts = tuple(disjuncts)
        else:
            try:
                iterator = iter(disjuncts)
                disjuncts = tuple(iterator)
            except TypeError:
                disjuncts = (disjuncts, )
        # Set the field!
        object.__setattr__(self, "disjuncts", disjuncts)

    def __getitem__(self, index: int) -> Formula:
        return self.disjuncts[index]

    def __len__(self) -> int:
        return len(self.disjuncts)


@dataclass(frozen=True)
class Not(SimpleFormula):
    argument: Formula

    @property
    def c(self) -> Formula:
        return self.argument


@dataclass(frozen=True)
class ComplexFormula(Formula):
    pass


@dataclass(frozen=True)
class If(ComplexFormula):
    antecedent: Formula
    consequent: Formula

    @property
    def p(self) -> Formula:
        return self.antecedent

    @property
    def q(self) -> Formula:
        return self.consequent


@dataclass(frozen=True)
class IfAndOnlyIf(ComplexFormula):
    antecedent: Formula
    consequent: Formula

    @property
    def p(self) -> Formula:
        return self.antecedent

    @property
    def q(self) -> Formula:
        return self.consequent


Iff = IfAndOnlyIf
