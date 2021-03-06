import operator as op
import pytest

from itertools import permutations

from sweetpea import fully_cross_block
from sweetpea.blocks import Block
from sweetpea.primitives import Factor, DerivedLevel, WithinTrial, Transition, Window, SimpleLevel
from sweetpea.constraints import Constraint, Consistency, FullyCross, Derivation, AtMostKInARow, ExactlyKInARow, Exclude
from sweetpea.backend import LowLevelRequest, BackendRequest
from sweetpea.logic import And, Or, If, Iff, Not, to_cnf_tseitin
from sweetpea.tests.test_utils import get_level_from_name

color = Factor("color", ["red", "blue"])
text  = Factor("text",  ["red", "blue"])

con_level  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
inc_level  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
con_factor = Factor("congruent?", [con_level, inc_level])

color_repeats_factor = Factor("color repeats?", [
    DerivedLevel("yes", Transition(lambda colors: colors[0] == colors[1], [color])),
    DerivedLevel("no",  Transition(lambda colors: colors[0] != colors[1], [color]))
])

text_repeats_factor = Factor("text repeats?", [
    DerivedLevel("yes", Transition(lambda texts: texts[0] == texts[1], [text])),
    DerivedLevel("no",  Transition(lambda texts: texts[0] != texts[1], [text]))
])

congruent_bookend = Factor("congruent bookend?", [
    DerivedLevel("yes", Window(lambda color, text: color == text, [color, text], 1, 3)),
    DerivedLevel("no",  Window(lambda color, text: color != text, [color, text], 1, 3))
])

design = [color, text, con_factor]
crossing = [color, text]
block = fully_cross_block(design, crossing, [])


def test_consistency():
    # From standard example
    # [ LowLevelRequest("EQ", 1, [1, 2]), LowLevelRequest("EQ", 1, [3, 4]), ...]
    backend_request = BackendRequest(0)

    Consistency.apply(block, backend_request)
    assert backend_request.ll_requests == \
        list(map(lambda x: LowLevelRequest("EQ", 1, [x, x+1]), range(1, 24, 2)))

    # Different case
    backend_request = BackendRequest(0)
    f = Factor("a", ["b", "c", "d", "e"])
    f_block = fully_cross_block([f], [f], [])

    Consistency.apply(f_block, backend_request)
    assert backend_request.ll_requests == \
        list(map(lambda x: LowLevelRequest("EQ", 1, [x, x+1, x+2, x+3]), range(1, 16, 4)))

    # Varied level lengths
    backend_request = BackendRequest(0)
    f1 = Factor("a", ["b", "c", "d"])
    f2 = Factor("e", ["f"])
    f_block = fully_cross_block([f1, f2], [f1, f2], [])

    Consistency.apply(f_block, backend_request)
    assert backend_request.ll_requests == [
        LowLevelRequest("EQ", 1, [1, 2, 3]), LowLevelRequest("EQ", 1, [4]),
        LowLevelRequest("EQ", 1, [5, 6, 7]), LowLevelRequest("EQ", 1, [8]),
        LowLevelRequest("EQ", 1, [9, 10, 11]), LowLevelRequest("EQ", 1, [12])]


@pytest.mark.parametrize('design', permutations([color, text, color_repeats_factor]))
def test_consistency_with_transition(design):
    block = fully_cross_block(design, [color, text], [])

    backend_request = BackendRequest(0)
    Consistency.apply(block, backend_request)

    # Because the color_repeats_factor doesn't apply to the first trial, (there isn't a previous trial
    # to compare to) the variables only go up to 22.
    assert backend_request.ll_requests == \
        list(map(lambda x: LowLevelRequest("EQ", 1, [x, x+1]), range(1, 22, 2)))


@pytest.mark.parametrize('design', permutations([color, text, color_repeats_factor, text_repeats_factor]))
def test_consistency_with_multiple_transitions(design):
    block = fully_cross_block(design, [color, text], [])

    backend_request = BackendRequest(0)
    Consistency.apply(block, backend_request)

    assert backend_request.ll_requests == \
        list(map(lambda x: LowLevelRequest("EQ", 1, [x, x+1]), range(1, 28, 2)))


def test_consistency_with_transition_first_and_uneven_level_lengths():
    color3 = Factor("color3", ["red", "blue", "green"])

    yes_fn = lambda colors: colors[0] == colors[1] == colors[2]
    no_fn = lambda colors: not yes_fn(colors)
    color3_repeats_factor = Factor("color3 repeats?", [
        DerivedLevel("yes", Window(yes_fn, [color3], 3, 1)),
        DerivedLevel("no",  Window(no_fn, [color3], 3, 1))
    ])

    block = fully_cross_block([color3_repeats_factor, color3, text], [color3, text], [])

    backend_request = BackendRequest(0)
    Consistency.apply(block, backend_request)

    assert backend_request.ll_requests == [
        LowLevelRequest("EQ", 1, [1,  2,  3 ]), LowLevelRequest("EQ", 1, [4,  5 ]),
        LowLevelRequest("EQ", 1, [6,  7,  8 ]), LowLevelRequest("EQ", 1, [9,  10]),
        LowLevelRequest("EQ", 1, [11, 12, 13]), LowLevelRequest("EQ", 1, [14, 15]),
        LowLevelRequest("EQ", 1, [16, 17, 18]), LowLevelRequest("EQ", 1, [19, 20]),
        LowLevelRequest("EQ", 1, [21, 22, 23]), LowLevelRequest("EQ", 1, [24, 25]),
        LowLevelRequest("EQ", 1, [26, 27, 28]), LowLevelRequest("EQ", 1, [29, 30]),

        LowLevelRequest("EQ", 1, [31, 32]),
        LowLevelRequest("EQ", 1, [33, 34]),
        LowLevelRequest("EQ", 1, [35, 36]),
        LowLevelRequest("EQ", 1, [37, 38])
    ]


def test_consistency_with_general_window():
    design = [color, text, congruent_bookend]
    crossing = [color, text]
    block = fully_cross_block(design, crossing, [])

    backend_request = BackendRequest(0)
    Consistency.apply(block, backend_request)

    assert backend_request.ll_requests == [
        LowLevelRequest("EQ", 1, [1,  2 ]), LowLevelRequest("EQ", 1, [3,  4 ]),
        LowLevelRequest("EQ", 1, [5,  6 ]), LowLevelRequest("EQ", 1, [7,  8 ]),
        LowLevelRequest("EQ", 1, [9,  10]), LowLevelRequest("EQ", 1, [11, 12]),
        LowLevelRequest("EQ", 1, [13, 14]), LowLevelRequest("EQ", 1, [15, 16]),

        LowLevelRequest("EQ", 1, [17, 18]),
        LowLevelRequest("EQ", 1, [19, 20])
    ]


def test_fully_cross_simple():
    block = fully_cross_block([color, text],
                              [color, text],
                              [])

    (expected_cnf, _) = to_cnf_tseitin(And([
        Iff(17, And([1,  3 ])), Iff(18, And([1,  4 ])), Iff(19, And([2,  3 ])), Iff(20, And([2,  4 ])),
        Iff(21, And([5,  7 ])), Iff(22, And([5,  8 ])), Iff(23, And([6,  7 ])), Iff(24, And([6,  8 ])),
        Iff(25, And([9,  11])), Iff(26, And([9,  12])), Iff(27, And([10, 11])), Iff(28, And([10, 12])),
        Iff(29, And([13, 15])), Iff(30, And([13, 16])), Iff(31, And([14, 15])), Iff(32, And([14, 16]))
    ]), 33)

    backend_request = BackendRequest(17)
    FullyCross.apply(block, backend_request)

    assert backend_request.fresh == 66
    assert backend_request.cnfs == [expected_cnf]
    assert backend_request.ll_requests == [
        LowLevelRequest("GT", 0, [17, 21, 25, 29]),
        LowLevelRequest("GT", 0, [18, 22, 26, 30]),
        LowLevelRequest("GT", 0, [19, 23, 27, 31]),
        LowLevelRequest("GT", 0, [20, 24, 28, 32])
    ]


def test_fully_cross_with_constraint():
    (expected_cnf, _) = to_cnf_tseitin(And([
        Iff(25, And([1,  3 ])), Iff(26, And([1,  4 ])), Iff(27, And([2,  3 ])), Iff(28, And([2,  4 ])),
        Iff(29, And([7,  9 ])), Iff(30, And([7,  10])), Iff(31, And([8,  9 ])), Iff(32, And([8,  10])),
        Iff(33, And([13, 15])), Iff(34, And([13, 16])), Iff(35, And([14, 15])), Iff(36, And([14, 16])),
        Iff(37, And([19, 21])), Iff(38, And([19, 22])), Iff(39, And([20, 21])), Iff(40, And([20, 22]))
    ]), 41)

    backend_request = BackendRequest(25)
    FullyCross.apply(block, backend_request)

    assert backend_request.fresh == 74
    assert backend_request.cnfs == [expected_cnf]
    assert backend_request.ll_requests == [
        LowLevelRequest("GT", 0, [25, 29, 33, 37]),
        LowLevelRequest("GT", 0, [26, 30, 34, 38]),
        LowLevelRequest("GT", 0, [27, 31, 35, 39]),
        LowLevelRequest("GT", 0, [28, 32, 36, 40])
    ]


@pytest.mark.parametrize('design',
    [[color, text, color_repeats_factor],
     [color_repeats_factor, color, text]])
def test_fully_cross_with_transition_in_design(design):
    block = fully_cross_block(design,
                              [color, text],
                              [])

    backend_request = BackendRequest(23)
    FullyCross.apply(block, backend_request)

    (expected_cnf, _) = to_cnf_tseitin(And([
        Iff(23, And([1,  3 ])), Iff(24, And([1,  4 ])), Iff(25, And([2,  3 ])), Iff(26, And([2,  4 ])),
        Iff(27, And([5,  7 ])), Iff(28, And([5,  8 ])), Iff(29, And([6,  7 ])), Iff(30, And([6,  8 ])),
        Iff(31, And([9,  11])), Iff(32, And([9,  12])), Iff(33, And([10, 11])), Iff(34, And([10, 12])),
        Iff(35, And([13, 15])), Iff(36, And([13, 16])), Iff(37, And([14, 15])), Iff(38, And([14, 16]))
    ]), 39)

    assert backend_request.fresh == 72
    assert backend_request.cnfs == [expected_cnf]
    assert backend_request.ll_requests == [
        LowLevelRequest("GT", 0, [23, 27, 31, 35]),
        LowLevelRequest("GT", 0, [24, 28, 32, 36]),
        LowLevelRequest("GT", 0, [25, 29, 33, 37]),
        LowLevelRequest("GT", 0, [26, 30, 34, 38])
    ]


def test_fully_cross_with_uncrossed_simple_factors():
    other = Factor('other', ['l1', 'l2'])
    block = fully_cross_block([color, text, other],
                              [color, text],
                              [])

    backend_request = BackendRequest(25)
    FullyCross.apply(block, backend_request)

    (expected_cnf, _) = to_cnf_tseitin(And([
        Iff(25, And([1,  3 ])), Iff(26, And([1,  4 ])), Iff(27, And([2,  3 ])), Iff(28, And([2,  4 ])),
        Iff(29, And([7,  9 ])), Iff(30, And([7,  10])), Iff(31, And([8,  9 ])), Iff(32, And([8,  10])),
        Iff(33, And([13, 15])), Iff(34, And([13, 16])), Iff(35, And([14, 15])), Iff(36, And([14, 16])),
        Iff(37, And([19, 21])), Iff(38, And([19, 22])), Iff(39, And([20, 21])), Iff(40, And([20, 22]))
    ]), 41)

    assert backend_request.fresh == 74
    assert backend_request.cnfs == [expected_cnf]
    assert backend_request.ll_requests == [
        LowLevelRequest("GT", 0, [25, 29, 33, 37]),
        LowLevelRequest("GT", 0, [26, 30, 34, 38]),
        LowLevelRequest("GT", 0, [27, 31, 35, 39]),
        LowLevelRequest("GT", 0, [28, 32, 36, 40])
    ]


def test_fully_cross_with_transition_in_crossing():
    direction = Factor("direction", ["up", "down"])

    block = fully_cross_block([direction, color, color_repeats_factor],
                              [direction, color_repeats_factor],
                              [])

    backend_request = BackendRequest(29)
    FullyCross.apply(block, backend_request)

    (expected_cnf, _) = to_cnf_tseitin(And([
        Iff(29, And([ 5, 21])), Iff(30, And([ 5, 22])), Iff(31, And([ 6, 21])), Iff(32, And([ 6, 22])),
        Iff(33, And([ 9, 23])), Iff(34, And([ 9, 24])), Iff(35, And([10, 23])), Iff(36, And([10, 24])),
        Iff(37, And([13, 25])), Iff(38, And([13, 26])), Iff(39, And([14, 25])), Iff(40, And([14, 26])),
        Iff(41, And([17, 27])), Iff(42, And([17, 28])), Iff(43, And([18, 27])), Iff(44, And([18, 28])),
    ]), 45)

    assert backend_request.fresh == 78
    assert backend_request.cnfs == [expected_cnf]
    assert backend_request.ll_requests == [
        LowLevelRequest("GT", 0, [29, 33, 37, 41]),
        LowLevelRequest("GT", 0, [30, 34, 38, 42]),
        LowLevelRequest("GT", 0, [31, 35, 39, 43]),
        LowLevelRequest("GT", 0, [32, 36, 40, 44])
    ]


# def test_fully_cross_with_exclude():
#     color = Factor("color", ["red", "blue", "green"])
#     text =  Factor("text",  ["red", "blue"])

#     def illegal_stimulus(color, text):
#         return color == "green" and text == "blue"

#     def legal_stimulus(color, text):
#         return not illegal_stimulus(color, text)

#     stimulus_configuration = Factor("stimulus configuration", [
#         DerivedLevel("legal",   WithinTrial(legal_stimulus, [color, text])),
#         DerivedLevel("illegal", WithinTrial(illegal_stimulus, [color, text]))
#     ])

#     block = fully_cross_block([color, text, stimulus_configuration],
#                               [color, text],
#                               [Exclude(stimulus_configuration, get_level_from_name(stimulus_configuration, "illegal"))],
#                               require_complete_crossing=False)

#     backend_request = BackendRequest(36)
#     FullyCross.apply(block, backend_request)

#     (expected_cnf, _) = to_cnf_tseitin(And([
#         Iff(36, And([ 1, 4 ])), Iff(37, And([ 1, 5 ])), Iff(38, And([ 2, 4 ])), Iff(39, And([ 2, 5 ])), Iff(40, And([ 3, 4 ])), Iff(41, And([ 3, 5 ])),
#         Iff(42, And([ 8, 11])), Iff(43, And([ 8, 12])), Iff(44, And([ 9, 11])), Iff(45, And([ 9, 12])), Iff(46, And([10, 11])), Iff(47, And([10, 12])),
#         Iff(48, And([15, 18])), Iff(49, And([15, 19])), Iff(50, And([16, 18])), Iff(51, And([16, 19])), Iff(52, And([17, 18])), Iff(53, And([17, 19])),
#         Iff(54, And([22, 25])), Iff(55, And([22, 26])), Iff(56, And([23, 25])), Iff(57, And([23, 26])), Iff(58, And([24, 25])), Iff(59, And([24, 26])),
#         Iff(60, And([29, 32])), Iff(61, And([29, 33])), Iff(62, And([30, 32])), Iff(63, And([30, 33])), Iff(64, And([31, 32])), Iff(65, And([31, 33]))
#     ]), 66)

#     assert backend_request.fresh == 127
#     assert backend_request.cnfs == [expected_cnf]
#     assert backend_request.ll_requests == [
#         LowLevelRequest("GT", 0, [36, 42, 48, 54, 60]),
#         LowLevelRequest("GT", 0, [37, 43, 49, 55, 61]),
#         LowLevelRequest("GT", 0, [38, 44, 50, 56, 62]),
#         LowLevelRequest("GT", 0, [39, 45, 51, 57, 63]),
#         LowLevelRequest("GT", 0, [40, 46, 52, 58, 64]),
#         LowLevelRequest("GT", 0, [41, 47, 53, 59, 65])
#     ]


def test_derivation():
    # Congruent derivation
    d = Derivation(4, [[0, 2], [1, 3]], con_factor)
    backend_request = BackendRequest(24)
    d.apply(block, backend_request)

    (expected_cnf, expected_fresh) = to_cnf_tseitin(And([
        Iff(5,  Or([And([1,  3 ]), And([2,  4 ])])),
        Iff(11, Or([And([7,  9 ]), And([8,  10])])),
        Iff(17, Or([And([13, 15]), And([14, 16])])),
        Iff(23, Or([And([19, 21]), And([20, 22])]))
    ]), 24)

    assert backend_request.fresh == expected_fresh
    assert backend_request.cnfs == [expected_cnf]

    # Incongruent derivation
    d = Derivation(5, [[0, 3], [1, 2]], con_factor)
    backend_request = BackendRequest(24)
    d.apply(block, backend_request)

    (expected_cnf, expected_fresh) = to_cnf_tseitin(And([
        Iff(6,  Or([And([1,  4 ]), And([2,  3 ])])),
        Iff(12, Or([And([7,  10]), And([8,  9 ])])),
        Iff(18, Or([And([13, 16]), And([14, 15])])),
        Iff(24, Or([And([19, 22]), And([20, 21])]))
    ]), 24)

    assert backend_request.fresh == expected_fresh
    assert backend_request.cnfs == [expected_cnf]


def test_derivation_with_transition():
    block = fully_cross_block([color, text, color_repeats_factor],
                              [color, text],
                              [])

    # Color repeats derivation
    d = Derivation(16, [[0, 4], [1, 5]], color_repeats_factor)
    backend_request = BackendRequest(23)
    d.apply(block, backend_request)

    (expected_cnf, expected_fresh) = to_cnf_tseitin(And([
        Iff(17, Or([And([1, 5 ]), And([2,  6 ])])),
        Iff(19, Or([And([5, 9 ]), And([6,  10])])),
        Iff(21, Or([And([9, 13]), And([10, 14])]))
    ]), 23)

    assert backend_request.fresh == expected_fresh
    assert backend_request.cnfs == [expected_cnf]

    # Color does not repeat derivation
    d = Derivation(17, [[0, 5], [1, 4]], color_repeats_factor)
    backend_request = BackendRequest(23)
    d.apply(block, backend_request)

    (expected_cnf, expected_fresh) = to_cnf_tseitin(And([
        Iff(18, Or([And([1, 6 ]), And([2,  5 ])])),
        Iff(20, Or([And([5, 10]), And([6,  9 ])])),
        Iff(22, Or([And([9, 14]), And([10, 13])]))
    ]), 23)

    assert backend_request.fresh == expected_fresh
    assert backend_request.cnfs == [expected_cnf]


def test_derivation_with_multiple_transitions():
    block = fully_cross_block([color, text, color_repeats_factor, text_repeats_factor],
                              [color, text],
                              [])

    # Text repeats derivation
    d = Derivation(22, [[2, 6], [3, 7]], text_repeats_factor)
    backend_request = BackendRequest(29)
    d.apply(block, backend_request)

    (expected_cnf, expected_fresh) = to_cnf_tseitin(And([
        Iff(23, Or([And([3,  7 ]), And([4,  8 ])])),
        Iff(25, Or([And([7,  11]), And([8,  12])])),
        Iff(27, Or([And([11, 15]), And([12, 16])]))
    ]), 29)

    assert backend_request.fresh == expected_fresh
    assert backend_request.cnfs == [expected_cnf]

    # Text does not repeat derivation
    d = Derivation(23, [[2, 7], [3, 6]], text_repeats_factor)
    backend_request = BackendRequest(29)
    d.apply(block, backend_request)

    (expected_cnf, expected_fresh) = to_cnf_tseitin(And([
        Iff(24, Or([And([3,  8 ]), And([4,  7 ])])),
        Iff(26, Or([And([7,  12]), And([8,  11])])),
        Iff(28, Or([And([11, 16]), And([12, 15])]))
    ]), 29)

    assert backend_request.fresh == expected_fresh
    assert backend_request.cnfs == [expected_cnf]


def test_derivation_with_three_level_transition():
    f = Factor("f", ["a", "b", "c"])
    f_transition = Factor("transition", [
        DerivedLevel("aa", Transition(lambda c: c[0] == "a" and c[1] == "a", [f])),
        DerivedLevel("ab", Transition(lambda c: c[0] == "a" and c[1] == "b", [f])),
        DerivedLevel("ac", Transition(lambda c: c[0] == "a" and c[1] == "c", [f])),
        DerivedLevel("ba", Transition(lambda c: c[0] == "b" and c[1] == "a", [f])),
        DerivedLevel("bb", Transition(lambda c: c[0] == "b" and c[1] == "b", [f])),
        DerivedLevel("bc", Transition(lambda c: c[0] == "b" and c[1] == "c", [f])),
        DerivedLevel("ca", Transition(lambda c: c[0] == "c" and c[1] == "a", [f])),
        DerivedLevel("cb", Transition(lambda c: c[0] == "c" and c[1] == "b", [f])),
        DerivedLevel("cc", Transition(lambda c: c[0] == "c" and c[1] == "c", [f])),
    ])

    block = fully_cross_block([f, f_transition], [f], [])

    # a-a derivation
    d = Derivation(9, [[0, 3]], f_transition)
    backend_request = BackendRequest(28)
    d.apply(block, backend_request)

    (expected_cnf, expected_fresh) = to_cnf_tseitin(And([
        Iff(10, Or([And([1, 4])])),
        Iff(19, Or([And([4, 7])]))
    ]), 28)

    assert backend_request.fresh == expected_fresh
    assert backend_request.cnfs == [expected_cnf]


def test_derivation_with_general_window():
    block = fully_cross_block([color, text, congruent_bookend],
                              [color, text],
                              [])
    # congruent bookend - yes
    d = Derivation(16, [[0, 2], [1, 3]], congruent_bookend)
    backend_request = BackendRequest(19)
    d.apply(block, backend_request)

    (expected_cnf, expected_fresh) = to_cnf_tseitin(And([
        Iff(17, Or([And([ 1, 3 ]), And([ 2, 4 ])])),
        Iff(19, Or([And([13, 15]), And([14, 16])]))
    ]), 19)

    assert backend_request.fresh == expected_fresh
    assert backend_request.cnfs == [expected_cnf]

    # congruent bookend - no
    d = Derivation(17, [[0, 3], [1, 2]], congruent_bookend)
    backend_request = BackendRequest(19)
    d.apply(block, backend_request)

    (expected_cnf, expected_fresh) = to_cnf_tseitin(And([
        Iff(18, Or([And([ 1, 4 ]), And([ 2, 3 ])])),
        Iff(20, Or([And([13, 16]), And([14, 15])]))
    ]), 19)

    assert backend_request.fresh == expected_fresh
    assert backend_request.cnfs == [expected_cnf]


def test_atmostkinarow_validate():
    color = Factor("color", ["red", "blue"])
    with pytest.raises(ValueError):
        AtMostKInARow(SimpleLevel("yo"), color)

    # Levels must either be a factor/level tuple, or a Factor.
    AtMostKInARow(1, (color, get_level_from_name(color, "red")))
    AtMostKInARow(1, color)

    with pytest.raises(ValueError):
        AtMostKInARow(1, 42)

    with pytest.raises(ValueError):
        AtMostKInARow(1, (color, get_level_from_name(color, "red"), "oops"))


def __run_kinarow(c: Constraint, block: Block = block) -> BackendRequest:
    backend_request = BackendRequest(block.variables_per_sample() + 1)
    for dc in c.desugar():
        dc.apply(block, backend_request)
    return backend_request


def test_atmostkinarow():
    backend_request = __run_kinarow(AtMostKInARow(3, color))
    assert backend_request.ll_requests == [
        LowLevelRequest("LT", 4, [1,  7, 13, 19]),
        LowLevelRequest("LT", 4, [2,  8, 14, 20])
    ]

    backend_request = __run_kinarow(AtMostKInARow(1, (color, get_level_from_name(color, "red"))))
    assert backend_request.ll_requests == [
        LowLevelRequest("LT", 2, [1,  7 ]),
        LowLevelRequest("LT", 2, [7,  13]),
        LowLevelRequest("LT", 2, [13, 19])
    ]

    backend_request = __run_kinarow(AtMostKInARow(2, (color, get_level_from_name(color, "red"))))
    assert backend_request.ll_requests == [
        LowLevelRequest("LT", 3, [1, 7,  13]),
        LowLevelRequest("LT", 3, [7, 13, 19])
    ]

    backend_request = __run_kinarow(AtMostKInARow(1, (color, get_level_from_name(color, "blue"))))
    assert backend_request.ll_requests == [
        LowLevelRequest("LT", 2, [2,  8 ]),
        LowLevelRequest("LT", 2, [8,  14]),
        LowLevelRequest("LT", 2, [14, 20])
    ]

    backend_request = __run_kinarow(AtMostKInARow(2, (color, get_level_from_name(color, "blue"))))
    assert backend_request.ll_requests == [
        LowLevelRequest("LT", 3, [2, 8,  14]),
        LowLevelRequest("LT", 3, [8, 14, 20])
    ]

    backend_request = __run_kinarow(AtMostKInARow(3, (con_factor, get_level_from_name(con_factor, "con"))))
    assert backend_request.ll_requests == [
        LowLevelRequest("LT", 4, [5, 11, 17, 23])
    ]


def test_atmostkinarow_disallows_k_of_zero():
    with pytest.raises(ValueError):
        AtMostKInARow(0, (con_factor, get_level_from_name(con_factor, "con")))


def test_nomorethankinarow_sugar():
    backend_request = __run_kinarow(AtMostKInARow(1, (color, get_level_from_name(color, "red"))))
    assert backend_request.ll_requests == [
        LowLevelRequest("LT", 2, [1,  7 ]),
        LowLevelRequest("LT", 2, [7,  13]),
        LowLevelRequest("LT", 2, [13, 19])
    ]


@pytest.mark.parametrize('design', permutations([color, text, color_repeats_factor]))
def test_atmostkinarow_with_transition(design):
    block = fully_cross_block(design, [color, text], [])

    backend_request = __run_kinarow(AtMostKInARow(1, (color_repeats_factor, get_level_from_name(color_repeats_factor, "yes"))), block)
    assert backend_request.ll_requests == [
        LowLevelRequest("LT", 2, [17, 19]),
        LowLevelRequest("LT", 2, [19, 21])
    ]

    backend_request = __run_kinarow(AtMostKInARow(1, (color_repeats_factor, get_level_from_name(color_repeats_factor, "no"))), block)
    assert backend_request.ll_requests == [
        LowLevelRequest("LT", 2, [18, 20]),
        LowLevelRequest("LT", 2, [20, 22])
    ]


def test_atmostkinarow_with_multiple_transitions():
    block = fully_cross_block([color, text, color_repeats_factor, text_repeats_factor],
                              [color, text],
                              [])

    backend_request = __run_kinarow(AtMostKInARow(1, (text_repeats_factor, get_level_from_name(text_repeats_factor, "yes"))), block)
    assert backend_request.ll_requests == [
        LowLevelRequest("LT", 2, [23, 25]),
        LowLevelRequest("LT", 2, [25, 27])
    ]

    backend_request = __run_kinarow(AtMostKInARow(1, (text_repeats_factor, get_level_from_name(text_repeats_factor, "no"))), block)
    assert backend_request.ll_requests == [
        LowLevelRequest("LT", 2, [24, 26]),
        LowLevelRequest("LT", 2, [26, 28])
    ]


def test_exactlykinarow():
    backend_request = __run_kinarow(ExactlyKInARow(1, (color, get_level_from_name(color, "red"))))
    (expected_cnf, expected_fresh) = to_cnf_tseitin(And([
        If(1, Not(7)),
        If(And([Not(1), 7]), Not(13)),
        If(And([Not(7), 13]), Not(19))
    ]), 25)

    assert backend_request.fresh == expected_fresh
    assert backend_request.cnfs == [expected_cnf]

    backend_request = __run_kinarow(ExactlyKInARow(2, (color, get_level_from_name(color, "red"))))
    (expected_cnf, expected_fresh) = to_cnf_tseitin(And([
        If(1, And([7, Not(13)])),
        If(And([Not(1), 7]), And([13, Not(19)])),
        If(And([Not(7), 13]), 19),
        If(19, 13)
    ]), 25)

    assert backend_request.fresh == expected_fresh
    assert backend_request.cnfs == [expected_cnf]

    backend_request = __run_kinarow(ExactlyKInARow(3, (color, get_level_from_name(color, "red"))))
    (expected_cnf, expected_fresh) = to_cnf_tseitin(And([
        If(1, And([7, 13, Not(19)])),
        If(And([Not(1), 7]), And([13, 19])),
        If(19, 13),
        If(13, 7)
    ]), 25)

    assert backend_request.fresh == expected_fresh
    assert backend_request.cnfs == [expected_cnf]


def test_exactlykinarow_disallows_k_of_zero():
    with pytest.raises(ValueError):
        ExactlyKInARow(0, (color, get_level_from_name(color, "red")))


def test_kinarow_with_bad_factor():
    bogus_factor = Factor("f", ["a", "b", "c"])
    with pytest.raises(ValueError):
        fully_cross_block(design, crossing, [ExactlyKInARow(2, (bogus_factor, get_level_from_name(bogus_factor, "a")))])


def test_exclude():
    f = Exclude(color, get_level_from_name(color, "red"))
    backend_request = BackendRequest(0)
    f.apply(block, backend_request)
    assert backend_request.cnfs == [And([-1, -7, -13, -19])]

    f = Exclude(con_factor, get_level_from_name(con_factor, "con"))
    backend_request = BackendRequest(0)
    f.apply(block, backend_request)
    assert backend_request.cnfs == [And([-5, -11, -17, -23])]


def test_exclude_with_transition():
    block = fully_cross_block([color, text, color_repeats_factor],
                              [color, text],
                              [])

    c = Exclude(color_repeats_factor, get_level_from_name(color_repeats_factor, "yes"))
    backend_request = BackendRequest(0)
    c.apply(block, backend_request)
    assert backend_request.cnfs == [And([-17, -19, -21])]


def test_exclude_with_general_window():
    block = fully_cross_block([color, text, congruent_bookend],
                              [color, text],
                              [])

    c = Exclude(congruent_bookend, get_level_from_name(congruent_bookend, "yes"))
    backend_request = BackendRequest(0)
    c.apply(block, backend_request)
    assert backend_request.cnfs == [And([-17, -19])]


def test_exclude_with_reduced_crossing():
    color = Factor("color", ["red", "blue", "green"])
    text =  Factor("text",  ["red", "blue"])

    def illegal_stimulus(color, text):
        return color == "green" and text == "blue"

    def legal_stimulus(color, text):
        return not illegal_stimulus(color, text)

    stimulus_configuration = Factor("stimulus configuration", [
        DerivedLevel("legal",   WithinTrial(legal_stimulus, [color, text])),
        DerivedLevel("illegal", WithinTrial(illegal_stimulus, [color, text]))
    ])

    c = Exclude(stimulus_configuration, get_level_from_name(stimulus_configuration, "illegal"))
    block = fully_cross_block([color, text, stimulus_configuration],
                              [color, text],
                              [c],
                              require_complete_crossing=False)

    backend_request = BackendRequest(0)
    c.apply(block, backend_request)
    assert backend_request.cnfs == [And([-7, -14, -21, -28, -35])]


def test_exclude_with_three_derived_levels():
    color_list = ["red", "green", "blue"]
    color = Factor("color", color_list)
    text  = Factor("text",  color_list)

    def count_diff(colors, texts):
        changes = 0
        if (colors[0] != colors[1]): changes += 1
        if (texts[0] != texts[1]): changes += 1
        return changes

    def make_k_diff_level(k):
        def k_diff(colors, texts):
            return count_diff(colors, texts) == k
        return DerivedLevel(str(k), Transition(k_diff, [color, text]))

    changed = Factor("changed", [make_k_diff_level(0),
                                 make_k_diff_level(1),
                                 make_k_diff_level(2)]);

    exclude_constraint = Exclude(changed, get_level_from_name(changed, "2"))

    design       = [color, text, changed]
    crossing     = [color, text]
    block        = fully_cross_block(design, crossing, [exclude_constraint])

    backend_request = BackendRequest(0)
    exclude_constraint.apply(block, backend_request)
    assert backend_request.cnfs == [And([-57, -60, -63, -66, -69, -72, -75, -78])]
