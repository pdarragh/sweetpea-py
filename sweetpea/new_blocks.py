"""This module provides the various kinds of blocks that can be used to create
a factorial experimental design.
"""


from __future__ import annotations


from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Set, Union

from sweetpea.new_constraints import Constraint, VariableTracker
from sweetpea.primitives import SimpleLevel, DerivedLevel, Factor, SimpleFactor, DerivedFactor


class ConversionMethod(Enum):
    NAIVE     = auto()
    SWITCHING = auto()
    TSEYTIN   = auto()

    DEFAULT   = TSEYTIN

    # TODO: Finish implementation.
    def convert(self, formula, next_variable):
        if self is ConversionMethod.NAIVE:
            ...
        if self is ConversionMethod.SWITCHING:
            ...
        if self is ConversionMethod.TSEYTIN:
            ...


@dataclass
class Block:

    design: List[Factor]

    crossing: List[Factor] = field(default_factory=list)

    constraints: List[Constraint] = field(default_factory=list)

    conversion_method: ConversionMethod = ConversionMethod.TSEYTIN

    variable_tracker: VariableTracker = field(init=False)

    _is_complex = None

    def __post_init__(self):
        # Ensure the design is non-empty.
        if not self.design:
            raise ValueError("Design must specify at least one factor.")

        # Any derived levels in the design's factors must derive simple factors
        # in the design.
        simple_factors: Set[SimpleFactor] = set()
        included_factors: Set[SimpleFactor] = set()

        def find_included_factors(level: DerivedLevel):
            for factor in level.window.factors:
                if isinstance(factor, DerivedFactor):
                    for sublevel in factor.levels:
                        find_included_factors(sublevel)
                elif isinstance(factor, SimpleFactor):
                    included_factors.add(factor)
                else:
                    raise RuntimeError(f"Expected SimpleFactor or DerivedFactor but found {type(level).__name__}.")

        for factor in self.design:
            for level in factor:
                if isinstance(level, SimpleLevel):
                    simple_factors.add(level.factor)
                elif isinstance(level, DerivedLevel):
                    find_included_factors(level)
                else:
                    raise RuntimeError(f"Expected SimpleLevel or DerivedLevel but found {type(level).__name__}.")

        undefined_factors = included_factors - simple_factors
        if undefined_factors:
            raise RuntimeError(f"Derived levels in design include factors that are not listed in the design: "
                               f"{', '.join(f.name for f in undefined_factors)}. "
                               f"Either these factors should be included in the design, or the derived levels should "
                               f"be adjusted.")

        # Generate the formula for this block.
        self.variable_tracker = VariableTracker(self.design)

    def __getitem__(self, factor_name: str) -> Factor:
        value = self.get_factor(factor_name)
        if value is None:
            raise KeyError(f"Factor '{factor_name}' not found in block.")
        return value

    def __contains__(self, factor: Union[str, Factor]) -> bool:
        def as_str(other: Factor) -> bool:
            return other.name == factor

        def as_fac(other: Factor) -> bool:
            return other == factor

        factor_matches = as_fac if isinstance(factor, Factor) else as_str

        for design_factor in self.design:
            if factor_matches(design_factor):
                return True
        return False

    def get_factor(self, factor_name: str) -> Optional[Factor]:
        for factor in self.design:
            if factor.name == factor_name:
                return factor
        return None

    @property
    def is_complex(self) -> bool:
        """A block is considered "complex" if any of the following conditions
        are met:

        * The block has :class:`Constraints <.Constraint>`.
        * Any of the :class:`Factors <.Factor>` in the ``design`` has a complex
          window.
        * Any of the :class:`Factors <.Factor>` in the ``crossing`` is a
          :class:`.DerivedFactor`.
        """
        if self._is_complex is None:
            self._is_complex = (
                len(self.constraints) > 0
                or any(factor.has_complex_window for factor in self.design)
                or any(isinstance(factor, DerivedFactor) for factor in self.crossing))
        return self._is_complex

    # TODO: REMOVE. (Backwards compatibility.)
    def has_factor(self, factor: Union[str, Factor]) -> bool:
        """Whether the given factor name or factor corresponds to a factor in
        this block's :attr:`~.Block.design`.

        .. deprecated:: 0.2.0

            This method will be removed in favor of straightforward membership
            checks, such as:

            .. code-block:: python

                block: Block = ...
                if "factor_name" in block:
                    ...
        """
        return factor in self
