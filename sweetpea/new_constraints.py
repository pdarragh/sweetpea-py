"""This module provides constraints for CNF generation."""


from dataclasses import InitVar, dataclass, field
from typing import List

from sweetpea.formulas import Formula, Var
from sweetpea.primitives import Factor


@dataclass
class VariableTracker:

    design: InitVar[List[Factor]]

    next_value: int = field(init=False, default=1)

    level_variables: List[Var] = field(init=False, default_factory=list)

    def __post_init__(self, design: List[Factor]):
        # Generate variables for each level in the design.
        for factor in design:
            for level in factor:
                if level.weight > 1:
                    for weight_label in range(level.weight):
                        self.level_variables.append(Var(self.next_value,
                                                        f"{factor.name}.{level.name}.w{weight_label}"))
                        self.next_value += 1
                else:
                    self.level_variables.append(Var(self.next_value, f"{factor.name}.{level.name}"))
                    self.next_value += 1


@dataclass
class Constraint:
    def generate_formula(self, tracker: VariableTracker) -> Formula:
        pass


@dataclass
class Consistency(Constraint):
    def generate_formula(self, tracker: VariableTracker) -> Formula:
        ...
