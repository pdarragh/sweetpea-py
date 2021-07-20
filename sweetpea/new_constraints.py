"""This module provides constraints for CNF generation."""


from __future__ import annotations


from collections import defaultdict
from dataclasses import InitVar, dataclass, field
from typing import Dict, List, Optional

from sweetpea.formulas import Formula, Var
from sweetpea.primitives import Factor, Level


@dataclass
class VariableTracker:

    design: InitVar[List[Factor]]

    next_value: int = field(init=False, default=1)

    variables: List[Var] = field(init=False, default_factory=list)

    variable_dict: Dict[int, Var] = field(init=False, default_factory=dict)

    factor_variables: Dict[Factor, List[Var]] = field(init=False, default_factory=lambda: defaultdict(list))

    level_variables: Dict[Level, List[Var]] = field(init=False, default_factory=lambda: defaultdict(list))

    constraint_variables: Dict[Constraint, List[Var]] = field(init=False, default_factory=lambda: defaultdict(list))

    def __post_init__(self, design: List[Factor]):
        # Generate variables for each level in the design.
        for factor in design:
            for level in factor:
                if level.weight > 1:
                    for weight_index in range(level.weight):
                        self.generate_level_var(level, weight_index)

                else:
                    self.generate_level_var(level)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.variables[key]
        if isinstance(key, Level):
            variables = self.level_variables.get(key)
            if variables is None:
                raise KeyError(f"No such level in tracker: {key.name}.")
            return variables
        if isinstance(key, Factor):
            variables = self.factor_variables.get(key)
            if variables is None:
                raise KeyError(f"No such factor in tracker: {key.name}.")
        if isinstance(key, Constraint):
            variables = self.constraint_variables.get(key)
            if variables is None:
                raise KeyError(f"No such constraint in tracker: {key}.")
        raise KeyError(f"Invalid key: {key}.")

    def generate_var(self, label: Optional[str] = None) -> Var:
        value = self.next_value
        self.next_value += 1
        if label is None:
            label = f"v{value}"
        var = Var(value, label)
        self.variables.append(var)
        self.variable_dict[value] = var
        return var

    def generate_level_var(self, level: Level, weight: Optional[int] = None, extra_label: Optional[str] = None):
        if weight is None:
            label = f"{level.factor.name}.{level.name}"
        else:
            label = f"{level.factor.name}.{level.name}.w{weight}"
        if extra_label is not None:
            label += f".{extra_label}"
        var = self.generate_var(label)
        self.factor_variables[level.factor].append(var)
        self.level_variables[level].append(var)


@dataclass
class Constraint:
    def generate_formula(self, tracker: VariableTracker) -> Formula:
        pass


# TODO: Do we actually need this?
@dataclass
class Consistency(Constraint):
    def generate_formula(self, tracker: VariableTracker) -> Formula:
        pass


@dataclass
class FullyCross(Constraint):
    def generate_formula(self, tracker: VariableTracker) -> Formula:
        ...


@dataclass
class Exclusion(Constraint):
    ...
