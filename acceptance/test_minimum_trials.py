import operator as op
import pytest

from sweetpea.primitives import Factor, DerivedLevel, WithinTrial, Transition
from sweetpea import fully_cross_block, NonUniformSamplingStrategy, UniformCombinatoricSamplingStrategy, synthesize_trials, minimum_trials
from sweetpea.tests.test_utils import get_level_from_name
from acceptance import shuffled_design_sample, path_to_cnf_files, reset_expected_solutions

correct_response = Factor(name="correct_response", initial_levels=["H", "S"])
congruency = Factor(name="congruency", initial_levels=["congruent", "incongruent"])
design     = [correct_response, congruency]
crossing   = [correct_response, congruency]

@pytest.mark.parametrize('strategy', [NonUniformSamplingStrategy, UniformCombinatoricSamplingStrategy])
@pytest.mark.parametrize('trial_count', [4, 5, 6, 7, 8])
def test_stays_balanced(strategy, trial_count):
    crossing_size = 1
    for f in crossing:
        crossing_size *= len(f.levels)
    block  = fully_cross_block(design=design, crossing=crossing, constraints=[minimum_trials(trials=trial_count)])
    experiments = synthesize_trials(block=block, samples=3, sampling_strategy = strategy)

    for exp in experiments:
        conds = list(zip(*exp.values()))
        for cond in conds:
            assert len(conds) == trial_count

        to_go =  trial_count
        while to_go > 0:
            tabulation: Dict[List[str], bool] = dict()
            for cond in conds[:crossing_size]:
                assert not (cond in tabulation)
                tabulation[cond] = True
            to_go -= crossing_size
            cond = cond[crossing_size:]