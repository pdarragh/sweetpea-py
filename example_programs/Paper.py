# Make SweetPea visible regardless of whether it's been installed.
import sys
sys.path.append("..")

import operator
from sweetpea.primitives import Factor, DerivedLevel, WithinTrial, Transition
from sweetpea import fully_cross_block, synthesize_trials_non_uniform, print_experiments, at_most_k_in_a_row, exclude

color_list = ["red", "green", "blue"]

color = Factor("color", color_list)
word  = Factor("word",  color_list)

congruent   = DerivedLevel("con", WithinTrial(operator.eq, [color, word]))
incongruent = DerivedLevel("inc", WithinTrial(operator.ne, [color, word]))

congruence  = Factor("congruence", [congruent, incongruent])

one_con_at_a_time = at_most_k_in_a_row(1, (congruence, congruent))


def one_diff(colors, words):
    if (colors[0] == colors[1]):
        return words[0] != words[1]
    else:
        return words[0] == words[1]

def both_diff(colors, words):
    return not one_diff(colors, words)

one = DerivedLevel("one", Transition(one_diff, [color, word]))
both = DerivedLevel("both", Transition(both_diff, [color, word]))
changed = Factor("changed", [one, both])

block        = fully_cross_block([color,word,congruence,changed], [color,word,changed], [])

experiments  = synthesize_trials_non_uniform(block, 1)

print_experiments(block, experiments)
