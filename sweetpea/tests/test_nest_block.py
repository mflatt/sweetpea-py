import operator as op
import pytest

from sweetpea import *
from sweetpea._internal.server import build_cnf
from acceptance import shuffled_design_sample, path_to_cnf_files, reset_expected_solutions

def has_run(vals, target, length):
    """
    Return True if `vals` contains a contiguous run of `target`
    of at least `length` occurrences.
    """
    run = 0
    for v in vals:
        name = v if isinstance(v, str) else getattr(v, "name", v)
        run = run + 1 if name == target else 0
        if run >= length:
            return True
    return False

def get_series(exp, key: str):
    """
    Return the values for factor `key` in a sampled experiment.
    Tries plain dict key first, then falls back to matching Factor.name.
    """
    if key in exp:
        return exp[key]
    for k in exp:
        if getattr(k, "name", None) == key or str(getattr(k, "name", "")) == key:
            return exp[k]
    raise KeyError(key)

# FIXME: remove skip
@pytest.mark.skip
@pytest.mark.parametrize('strategy', [IterateSATGen])
def test_nest_block_correct_solution2_count(strategy):
    A = Factor("A", ["a1", "a2"])
    B = Factor("B", ["b1", "b2"])

    outer = CrossBlock([A, B], [A, B], [])

    session = Factor("session", ["s1", "s2"])
    inner = CrossBlock([session], [session], [])

    nb = NestBlock(outer, inner, [])

    exps = synthesize_trials(nb, 2000, sampling_strategy=strategy)
    assert len(exps) == 24 * 16

def test_nest_block_pinned_local_block():
    A = Factor("A", ["a1", "a2"])
    B = Factor("B", ["b1", "b2"])

    outer = CrossBlock([A, B], [A, B], [Pin(1, (A, "a1"))])

    session = Factor("session", ["s1", "s2"])
    inner = CrossBlock([session], [session], [])

    nb1 = NestBlock(outer, inner, [])
    exps = synthesize_trials(nb1, 4, sampling_strategy=IterateSATGen)
    for exp in exps:
        assert exp["A"][2] == "a1"
        assert exp["A"][3] == "a1"

    nb2 = NestBlock(inner, outer, [])
    exps = synthesize_trials(nb2, 4, sampling_strategy=IterateSATGen)
    for exp in exps:
        assert exp["A"][1] == "a1"
        
def test_nest_block_pinned_spanning_block():
    A = Factor("A", ["a1", "a2"])
    B = Factor("B", ["b1", "b2"])

    outer = CrossBlock([A, B], [A, B], [])

    session = Factor("session", ["s1", "s2"])
    inner = CrossBlock([session], [session], [])

    nb1 = NestBlock(outer, inner, [Pin(1, (A, "a1"))])
    exps = synthesize_trials(nb1, 4, sampling_strategy=IterateSATGen)
    for exp in exps:
        assert exp["A"][1] == "a1"

    nb2 = NestBlock(inner, outer, [Pin(1, (A, "a1"))])
    exps = synthesize_trials(nb2, 4, sampling_strategy=IterateSATGen)
    for exp in exps:
        assert exp["A"][1] == "a1"

def test_double_nest_block_pinned_middle_block():
    A = Factor("A", ["a1", "a2"])
    B = Factor("B", ["b1", "b2"])

    outer = CrossBlock([A, B], [A, B], [])

    session = Factor("session", ["s1", "s2"])
    inner = CrossBlock([session], [session], [])

    nb1 = NestBlock(outer, inner, [Pin(1, (A, "a1"))])
    nb2 = NestBlock(inner, outer, [Pin(1, (A, "a1"))])

    epoch = Factor("epoch", ["e1", "e2"])
    outer_outer = CrossBlock([epoch], [epoch], [])

    dnb1 = NestBlock(outer_outer, nb1, [])
    exps = synthesize_trials(dnb1, 4, sampling_strategy=IterateSATGen)
    for exp in exps:
        assert exp["A"][1] == "a1"
        assert exp["A"][9] == "a1"

    dnb2 = NestBlock(outer_outer, nb2, [])
    exps2 = synthesize_trials(dnb2, 4, sampling_strategy=IterateSATGen)
    for exp in exps2:
        assert exp["A"][1] == "a1"
        assert exp["A"][9] == "a1"

def test_double_nest_block_pinned_inner_block():
    A = Factor("A", ["a1", "a2"])
    B = Factor("B", ["b1", "b2"])

    outer = CrossBlock([A, B], [A, B], [Pin(1, (A, "a1"))])

    session = Factor("session", ["s1", "s2"])
    inner = CrossBlock([session], [session], [])

    nb1 = NestBlock(outer, inner, [])
    nb2 = NestBlock(inner, outer, [])

    epoch = Factor("epoch", ["e1", "e2"])
    outer_outer = CrossBlock([epoch], [epoch], [])

    dnb1 = NestBlock(outer_outer, nb1, [])
    exps = synthesize_trials(dnb1, 4, sampling_strategy=IterateSATGen)
    for exp in exps:
        assert exp["A"][2] == "a1"
        assert exp["A"][10] == "a1"

    dnb2 = NestBlock(outer_outer, nb2, [])
    exps2 = synthesize_trials(dnb2, 4, sampling_strategy=IterateSATGen)
    for exp in exps2:
        assert exp["A"][1] == "a1"
        assert exp["A"][9] == "a1"

def test_nest_block_local_k_constaint():
    A = Factor("A", ["a1", "a2"])
    B = Factor("B", ["b1", "b2"])
    inner = CrossBlock([A, B], [A, B], [ExactlyKInARow(2, (A, "a1"))])

    session = Factor("session", [Level("s1"), Level("s2")])
    outer = CrossBlock([session], [session], [])
    nb = NestBlock(outer, inner, constraints=[])

    exps = synthesize_trials(nb, 1000, sampling_strategy=IterateGen)
    assert len(exps) == 288
    # At least one experiment should contain k 'a1's in a row across a boundary
    target_level = "a1"
    assert any(has_run(get_series(exp, "A"), "a1", 4) for exp in exps)

def test_nest_block_spanning_k_constaint():
    A = Factor("A", ["a1", "a2"])
    B = Factor("B", ["b1", "b2"])
    inner = CrossBlock([A, B], [A, B], [])

    session = Factor("session", [Level("s1"), Level("s2")])
    outer = CrossBlock([session], [session], [])
    nb = NestBlock(outer, inner, constraints=[ExactlyKInARow(2, (A, "a1"))])

    exps = synthesize_trials(nb, 1000, sampling_strategy=IterateGen)
    assert len(exps) == 256
    # At least one experiment should contain k 'a1's in a row across a boundary
    target_level = "a1"
    assert not any(has_run(get_series(exp, "A"), "a1", 4) for exp in exps)

def test_nest_block_dependent_factor():
    A = Factor("A", ["a1", "a2"])
    C = Factor("C", ["c1", "c2"])

    def same_a(a_levels):
        return a_levels[-1] == a_levels[0]

    D = Factor("D", [DerivedLevel("same", Transition(same_a, [A])),
                     ElseLevel("other")])

    outer = CrossBlock([A, D], [A, D], [])

    session = Factor("session", ["s1", "s2"])
    inner = CrossBlock([session], [session], [])

    nb = NestBlock(outer, inner, [], alignment=AlignmentMode.POST_PREAMBLE)

    exps = synthesize_trials(nb, 1000, sampling_strategy=IterateSATGen)
    assert len(exps) == 4

def test_nest_block_dependent_factor2():
    A = Factor("A", ["a1", "a2"])
    B = Factor("B", ["b1", "b2"])

    def consi(a, b):
        return (a == "a1" and b == "b1") or (a == "a2" and b == "b2") 

    E = Factor("E", [DerivedLevel("consi", WithinTrial(consi, [A, B])),
                     ElseLevel("incons")])

    outer = CrossBlock([A, B, E], [A, E], [])

    session = Factor("session", ["s1", "s2"])
    inner = CrossBlock([session], [session], [])
    
    nb = NestBlock(outer, inner, [], alignment=AlignmentMode.POST_PREAMBLE)

    exps = synthesize_trials(nb, 10, sampling_strategy=IterateSATGen)
    assert len(exps) == 10
