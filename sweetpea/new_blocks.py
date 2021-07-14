"""This module provides the various kinds of blocks that can be used to create
a factorial experimental design.
"""


from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Union

from sweetpea.new_constraints import Constraint
from sweetpea.primitives import DerivedFactor, Factor


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
class BlockVar:
    """A formula variable for use in :class:`Blocks <.Block>`. Variables used
    in formulas were traditionally implemented as simple :class:`ints <int>`,
    but they are not truly integers since the typical integer operations
    (addition, multiplication, etc.) have no meaning for formula variables.

    In addition to an integer :attr:`~.BlockVar.value`, formula variables also
    have a :attr:`~.BlockVar.label`. This is used to mark the manner in which a
    variable was generated, which helps with debugging problematic formulas.
    """
    value: int
    label: str

    def __int__(self) -> int:
        return self.value


@dataclass
class Block:
    design: List[Factor]
    crossing: List[Factor] = field(default_factory=list)
    constraints: List[Constraint] = field(default_factory=list)
    conversion_method: ConversionMethod = ConversionMethod.TSEYTIN

    _is_complex = None

    def __post_init__(self):
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
