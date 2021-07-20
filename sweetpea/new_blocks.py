"""This module provides the various kinds of blocks that can be used to create
a factorial experimental design.
"""


from __future__ import annotations


from dataclasses import dataclass, field
from enum import Enum, auto
from functools import reduce
from itertools import product
from typing import List, Optional, Set, Tuple, Union

from sweetpea.new_constraints import Constraint, Exclusion, VariableTracker
from sweetpea.formulas import Var
from sweetpea.primitives import Level, SimpleLevel, DerivedLevel, Factor, SimpleFactor, DerivedFactor


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

    ########
    ## Init Fields
    ##
    ## The @dataclass-generated `__init__` method will provide parameters for
    ## all of the following fields.

    design: List[Factor]

    crossings: List[List[Factor]] = field(default_factory=list)

    constraints: List[Constraint] = field(default_factory=list)

    conversion_method: ConversionMethod = ConversionMethod.TSEYTIN

    require_complete_crossing: bool = True

    ########
    ## Non-Init Fields
    ##
    ## The following fields will not appear in the @dataclass-generated
    ## `__init__` method. This is accomplished by using
    ## `dataclasses.field(init=False)` (for public fields) or using an
    ## underscore-prefixed name (for "private" fields).

    variable_tracker: VariableTracker = field(init=False)

    exclusions: int = field(init=False)

    _is_complex: Optional[bool] = None

    _crossing_size: Optional[int] = None

    def __post_init__(self):
        # Ensure the design is satisfactory.
        self._check_design()

        # Initialize the variable tracker for this block with the design.
        self.variable_tracker = VariableTracker(self.design)

        # Count the exclusions.
        self.exclusions = self._count_exclusions()

    def _check_design(self):
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

    def _count_exclusions(self) -> int:
        # If there are no crossings listed, we have nothing to exclude.
        if not self.crossings:
            return 0

        # Generate a full crossing as a list of tuples from the first list of
        # crossed factors.
        # TODO: Is it right to only use the first crossing? What does it mean
        #       if there are multiple crossings but only one is checked for
        #       exclusions?
        full_crossing = list(product(factor.levels for factor in self.crossings[0]))

        # Initialize a set of tuples.
        excluded_crossings: Set[Tuple[Level, Level]] = set()

        for exclusion in (constraint for constraint in self.constraints if isinstance(constraint, Exclusion)):
            ...

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
            self._is_complex = not (len(self.constraints) > 0
                                    or any(factor.has_complex_window for factor in self.design)
                                    or any(any(isinstance(factor, DerivedFactor)
                                               for factor in crossing)
                                           for crossing in self.crossings))
        return self._is_complex

    @property
    def crossing_size(self) -> int:
        if self._crossing_size is None:
            raise RuntimeError("Block's crossing size is undefined! Was this block properly initialized?")
        return self._crossing_size

    def get_factor(self, factor_name: str) -> Optional[Factor]:
        for factor in self.design:
            if factor.name == factor_name:
                return factor
        return None

    def first_variable_for_level(self, level: Level) -> Var:
        return self.variable_tracker[level][0]

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
                factor: Factor = ...
                if factor in block:
                    ...
        """
        return factor in self


@dataclass
class FullyCrossedBlock(Block):
    def __post_init__(self):
        super().__post_init__()

        # Initialize crossing size.
        size = reduce(lambda acc, factor: acc * len(factor.levels), self.crossings[0])


@dataclass
class PartiallyCrossedBlock(Block):
    def __post_init__(self):
        super().__post_init__()
