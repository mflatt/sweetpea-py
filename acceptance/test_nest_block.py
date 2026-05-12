import operator as op
import pytest

from sweetpea import *
from sweetpea._internal.server import build_cnf
from acceptance import shuffled_design_sample, path_to_cnf_files, reset_expected_solutions

@pytest.mark.slow
@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
def test_correct_solution_count(strategy):
    A = Factor("A", ["a1", "a2"])
    B = Factor("B", ["b1", "b2"])

    inner = CrossBlock([A, B], [A, B], [])

    session = Factor("session", ["s1", "s2"])
    outer = CrossBlock([session], [session], [])

    nb = NestBlock(outer, inner, [])

    exps = synthesize_trials(nb, 2000, sampling_strategy=strategy)
    assert len(exps) == 24 * 24 *2

@pytest.mark.parametrize('strategy', [IterateSATGen])
def test_correct_solution2_count(strategy):
    A = Factor("A", ["a1", "a2"])
    B = Factor("B", ["b1", "b2"])

    outer = CrossBlock([A, B], [A, B], [])

    session = Factor("session", ["s1", "s2"])
    inner = CrossBlock([session], [session], [])

    nb = NestBlock(outer, inner, [])

    exps = synthesize_trials(nb, 2000, sampling_strategy=strategy)
    assert len(exps) == 24 * 16

def test_pinned_within_cross():
    A = Factor("A", ["a1", "a2"])
    B = Factor("B", ["b1", "b2"])

    outer = CrossBlock([A, B], [A, B], [Pin(1, (A, "a1"))])

    session = Factor("session", ["s1", "s2"])
    inner = CrossBlock([session], [session], [])

    nb1 = NestBlock(outer, inner, [])
    exps = synthesize_trials(nb1, 4, sampling_strategy=IterateSATGen)
    # relying on `SWEETPEA_CHECK_SYNTHESIZED` to check pinning constraint

    nb2 = NestBlock(inner, outer, [])
    exps = synthesize_trials(nb2, 4, sampling_strategy=IterateSATGen)
    # relying on `SWEETPEA_CHECK_SYNTHESIZED` to check pinning constraint
