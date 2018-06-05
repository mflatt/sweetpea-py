from functools import reduce
from collections import namedtuple
from itertools import product
import json
from itertools import islice
from typing import Any, Dict, List, Union, Tuple, Iterator, Iterable


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#         Example program (simple stroop)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
import operator as op

color = Factor("color", ["red", "blue"])
text  = Factor("text",  ["red", "blue"])

conLevel  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
incLevel  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
conFactor = Factor("congruent?", [conLevel, incLevel])

design       = [color, text, conFactor]

# k = 1
# constraints = [LimitRepeats(k, conLevel)]

crossing     = [color, text]
experiment   = fully_cross_block(design, crossing, []) # constraints)
(nVars, cnf) = synthesize_trials(experiment)
"""
   


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#         Named Tuples
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# TODO field validation, ie
# 1. levels should be non-empty
# 2. length of window args should match the number of args that func wants
# 3. length of window args for transition must be 2, and for withinTrial must be 1
# 4. types for the boolean functions (ie the args to And is a list of boolean functions)

# Everything the user interacts with
Factor       = namedtuple('Factor', 'name levels')
Window       = namedtuple('Window', 'func args stride')
Window.__new__.__defaults__ = (None, None, 1)

WithinTrial  = namedtuple('WithinTrial', 'func args')
Transition   = namedtuple('Transition', 'func args')
DerivedLevel = namedtuple('DerivedLevel', 'name window')

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Everything from the frontend

HLBlock = namedtuple('HLBlock', 'design xing hlconstraints')
ILBlock = namedtuple('ILBlock', 'startAddr endAddr design xing constraints')

# constraints
FullyCross = namedtuple('FullyCross', '')
Consistency = namedtuple('Consistency', '')
Derivation = namedtuple('Derivation', 'derivedIdx dependentIdxs')

NoMoreThanKInARow = namedtuple('NoMoreThanKInARow', 'k levels')

# output
Request = namedtuple('Request', 'equalityType k booleanValues')


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Some nice boolean functions
"""
input_list is a list of the things being "anded" together
    for instance, `a && b` becomes And([a, b])
for Iff the args are `a` and `b`, as in, `a iff b`
"""
And = namedtuple('And', 'input_list')
Or  = namedtuple('Or' , 'input_list')
Iff = namedtuple('Iff', 'a b')
Not = namedtuple('Not', 'input')


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#         "Front End" transformations
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# ~~~~~~~~~~ Helper functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
Helper function which grabs names from derived levels; 
    if the level is non-derived the level *is* the name
"""
def get_level_name(level: Any) -> Any:
    if isinstance(level, DerivedLevel):
        return level.name
    return level


""" 
Usage::
    >>> color = Factor("color", ["red", "blue"])
    >>> text  = Factor("text",  ["red", "blue", "green"])
    >>> get_all_level_names([color, text])
    [('color', 'red'), ('color', 'blue'), ('text', 'red'), ('text', 'blue')]

"""
def get_all_level_names(design: List[Factor]) -> List[Tuple[Any, Any]]:
    return [(factor.name, get_level_name(level)) for factor in design for level in factor.levels]


"""
This is a helper function which takes boolean equations formatted with the namedTuples: Iff, And, Or, Not and converts them into CNF, ie, And([Or(...), Or(...) ...])
General approach here: https://www.cs.jhu.edu/~jason/tutorials/convert-to-CNF.html
TODO: is there a python implementation available?
Note: toCNF may or maynot need access to fresh variables depending on implementation
"""
def toCNF(boolean_func: Union[And, Or, Not, Iff]) -> And:
    pass


"""
Need to pretty-print results of the toCNF call in the DIMACS format
ie, And([Or(1, 4), Or(5, -4, 2), Or(-1, -5)]) needs to print as:
    1 4 0
    5 -4 2 0
    -1 -5 0
"""
def cnfToStr(expr: And) -> str:
    pass


"""
A full crossing is the product of the number of levels 
in all the factors in the xing.

Usage::
    >>> color = Factor("color", ["red", "blue"])
    >>> text  = Factor("text",  ["red", "blue", "green"])
    >>> fully_cross_size([color, text])
    6

:param xing: A list of Factor namedpairs ``Factor(name, levels)``.
:rtype: Int
"""
def fully_cross_size(xing: List[Factor]) -> int:
    acc = 1
    for fact in xing:
        acc *= len(fact.levels)
    return acc

"""
Analogous to fully_cross_size:
>>> design_size([color, text])
4
"""
def design_size(design: List[Factor]) -> int:
    return sum([len(f.levels) for f in design])
    
"""
Usage::
    >>> get_dep_xProduct(conLevel)
[(('color', 'red'), ('text', 'red')), 
 (('color', 'red'), ('text', 'blue')), 
 (('color', 'blue'), ('text', 'red')), 
 (('color', 'blue'), ('text', 'blue'))]
:param level: A derived level which we want to get the crossing of
:rtype: list of tuples of tuples of strings which represent the crossing 
** Careful! The length of the (outer) tuple depends on how many terms are part of the derivation! That's why there isn't a mypy annotation on the return type!
"""
def get_dep_xProduct(level: DerivedLevel) -> List[Tuple[Any, ...]]:
    return list(product(*[[(depFact.name, x) for x in depFact.levels] for depFact in level.window.args]))
    
    
"""
handy-dandy chunker from SO: https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
"""
# TODO: add a canary print statement in case the resulting lists are not all the same length-- that is not the expected behavior (at least how it's used in desugar_fullycrossed)
def chunk(it: Iterable[Any], size: int) -> Iterator[Tuple[Any, ...]]:
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())
 
"""
This is a helper for getting how many directly encoded variables there are in the experiment.
For instance, if we have the simple stoop experiment (at the bottom of this page) then
    we have 4 trials, each of which encode state for 6 levels 
    (this is because not all the factors are part of the full crossing)
    so there are 24 encoding variables
"""
def encoding_variable_size(design: List[Factor], xing: List[Factor]) -> int:
    return design_size(design) * fully_cross_size(xing)    
    
""" Simple helper to make process_derivations a tiny bit more legible
"""
def get_derived_factors(design: List[Factor]) -> List[Factor]:
    is_derived = lambda x : isinstance(x.levels[0], DerivedLevel)
    return list(filter(is_derived, design))   
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~ Functions that have to do with derivations (called from fully_cross_block) ~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# TODO make sure this works for derivations over 2+ levels
"""
Useage::
    >>> import operator as op
    >>> color = Factor("color", ["red", "blue"])
    >>> text  = Factor("text",  ["red", "blue"])
    >>> conLevel  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
    >>> incLevel  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
    >>> conFactor = Factor("congruent?", [conLevel, incLevel])
    >>> design = [color, text, conFactor]
    >>> xing = [color, text]
    >>> process_derivations(design, xing)
    [Derivation(derivedIdx=4, dependentIdxs=[[0, 2], [1, 3]]), Derivation(derivedIdx=5, dependentIdxs=[[0, 3], [1, 2]])]
rtype: returns a list of tuples. Each tuple is structured as:
        (index of the derived level, list of dependent levels)
In the example above, the indicies of the design are:
    idx: level:
    0    color:red
    1    color:blue
    2    text:red
    3    text:blue
    4    conFactor:con
    5    conFactor:inc
So the tuple (4, [[0,2], [1,3]]) represents the information that 
    the derivedLevel con is true iff
        (color:red && text:red) ||
        (color:blue && text:blue)
    by pairing the relevant indicies together.
"""
def process_derivations(design: List[Factor], xing: List[Factor]) -> List[Derivation]:
    derived_factors = get_derived_factors(design)
    all_levels = get_all_level_names(design)
    accum = []
    for fact in derived_factors:
        for level in fact.levels:
            level_index = all_levels.index((fact.name, level.name))                 
            x_product = get_dep_xProduct(level)
            # filter to valid pairs, and get their idxs
            valid_pairs = [pair for pair in x_product if level.window.func(pair[0][1], pair[1][1])]
            valid_idxs = [[all_levels.index(level) for level in pair] for pair in valid_pairs]
            shifted_idxs = shift_window(valid_idxs, level.window, design_size(design))
            accum.append(Derivation(level_index, shifted_idxs))
    return accum


"""
This is a helper function that shifts the idxs of process_derivations.
ie, if its a Transition(op.eq, [color, color]) (ie "repeat" color transition) 
    then the indexes for the levels of color would be like (0, 0), (1, 1)
    but actually, the window size for a transition is 2, so what we really want is the indicies
    (0, 5), (1, 6) (assuming there are 4 levels in the design)
So this helper function shifts over indices that were meant to be intepretted as being in a subsequent trial.
TODO: general window case later
"""
def shift_window(idxs: List[List[int]], window: Union[WithinTrial, Transition, Window], 
                                        trial_size:int) -> List[List[int]]:
    if isinstance(window, WithinTrial):
        return idxs
    elif isinstance(window, Transition):
        # update the idxs in slot 2 to be +trialsize
        return [[pair[0], pair[1]+trial_size] for pair in idxs]
    #TODO: general constraint case 
    elif isinstance(window, Window):
        window_width = len(window.args)
        print("WARNING THIS CASE IS NOT YET IMPLEMENTED")
        return idxs
    else: 
        raise ValueError("Wierd window encountered while processing derivations!")
    

    
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~ Functions that have to do with desugaring (called from synthesize) ~~~~~~~~~~~~~~~~~~~~~~~~~ 
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
The derivations come in looking like
    Derivation(4, [[0, 2], [1, 3]])
    (derivedLevel index; list of indicies that are dependent)
This represents:
    4 iff (0 and 2) or (1 and 3)
These indicies are used the get the corresponding trial variables. Continuing from the example in of processDerivations, the first trial is represented by variables [1-6] (notice this feels like an off-by-one: the indicies start from 0, but the boolean variables start from 1). So we would use the idxs to map onto the vars as:
    5 iff (1 and 3) or (2 and 4)
Then we convert to CNF directly, ie
    toCNF(Iff(5, Or(And(1,3), And(2,4))))
This is then done for all window-sizes, taking into account strides (which are specified only in DerivedLevels specified with a general Window rather than Transition or WithinTrial). We grab window-sized chunks of the variables that represent the trials, map the variables using the indices, and then convert to CNF. These chunks look like:
    window1: 1  2  3  4  5  6
    window2: 7  8  9  10 11 12
So, for the second trial (since the window size in this example is 1) it would be:
    11 iff (7 and 9) or (8 and 10)
90% sure this is the correct way to generalize to derivations involving 2+ levels & various windowsizes
one test is the experiment: color = ["r", "b", "g"]; text = ["r", "b"]; conFactor; fullycross(color, text) + noMoreThanKInARow 1 conLevel

returns a list of CNF clauses (& mutates the fresh variable)
"""
def desugar_derivation(fresh:int, derivation:Derivation, hl_block:HLBlock) -> And:
    print("WARNING THIS IS NOT YET IMPLEMENTED")
    return And([])


"""
The "consistency" constraints ensure that only one level of each factor is 'on' at a time.
So for instance in the experiment
    color = Factor("color", ["red", "blue"])
    text  = Factor("text",  ["red", "blue"])
    design = crossing = [color, text, conFactor]
    experiment   = fully_cross_block(design, crossing, []) 
The first trial is represented by the boolean vars [1, 2, 3, 4]
    0 is true iff the trial is color:red
    1 is true iff the trial is color:blue
    2 is true iff the trial is text:red
    3 is true iff the trial is text:blue
The second trial is represented by the boolean vars [5-8], the third by [9-12], the fourth by [13-16]
So this desugaring applies the following constraints:
    sum(1, 2) EQ 1
    sum(3, 4) EQ 1
    sum(5, 6) EQ 1
    ...
    sum(15, 16) EQ 1
It is an optimization to go directly to CNF instead of calling the backend, but it'll be cleaner to let the backend deal with that optimization rather than hacking it in here.
"""
def desugar_consistency(fresh:int, hl_block:HLBlock) -> List[Request]:
    # TODO:
    # construct the level pairs by computing size_fully_crossed_block & getting the levels out of hl_block
    print("WARNING THIS IS NOT YET IMPLEMENTED")
    return []




"""
We represent the fully crossed constraint by allocating additional boolean variables to represent each unique state. Only factors in xing will contribute to the number of states (there may be factors in the design that aren't in the xing). 
Continuing with example from desugar_consistency we will represent the states:
    (color:red, text:red)
    (color:red, text:blue)
    (color:blue, text:red)
    (color:blue, text:blue)
-- 1. Generate Intermediate Vars
Using the fresh var counter, allocate numTrials * numStates new vars
-- 2. Entangle them w/ block vars
Add to the CNF queue: toCNF(Iff(newVar, And(levels)))
    ie, if the variable 1 indicates color:red, the var 3 indicates text:red, and the var 25 represents (color:red, text:red):
        toCNF(Iff(25, And([1, 3])))
-- 3. 1 hot the *states* ie, 1 red circle, etc
same as desugar_consistency above, collect all the state vars that represent each state & enforce that only one of those states is true, ie
    sum(25, 29, 33, 37) EQ 1
    (and 3 more of these for each of the other states).
This function returns BOTH some cnf clauses and some reqs.
"""
def desugar_full_crossing(fresh:int, hl_block:HLBlock) -> Tuple[And, List[Request]]:
    numStates = fully_cross_size(hl_block.xing) # same as number of trials in fully crossing
    numEncodingVars = encoding_variable_size(hl_block.design, hl_block.xing)
    # Step 1:
    numStateVars = numStates * numStates
    stateVars = list(range(fresh, fresh+numStateVars))
    fresh += numStateVars
    # Step 2:
    states = list(chunk(stateVars, numStates))
    transposed = list(map(list, zip(*states)))
    chunked_trials = list(chunk(list(range(1, numEncodingVars)), design_size(hl_block.design)))
    # TODO: resume here!
    # 1. group chunked_trials into factor shaped subchunks
        # ie, [[1, 2], [3, 4], [5, 6]], [[7, 8], ...
    # 2. grab the subchunks which correspond to levels in the xing
        # ie, [[1, 2], [3, 4]], [[7, 8], [9, 10]], [[...
    # 3. for each trial, take the itertools product of all the subchunks
        # ie, [[1, 3], [1, 4], [2, 3], [2, 4]], ...
    # 4. get those into an Iff w/ the state variables; ie Iff(25, And([1,3])) & then toCNF that & stash it on the queue.
    # Step 3:
    # 5. make Requests for each transposed list that add up to k=1.
    print("WARNING THIS IS NOT YET IMPLEMENTED")
    return None # todo!


"""
This desugars pretty directly into the llrequests.
The only thing to do here is to collect all the boolean vars that match the same level & pair them up according to k.
Continuing with the example from desugar_consistency:
    say we want NoMoreThanKInARow 1 ("color", "red")
    then we need to grab all the vars which indicate color-red : [1, 5, 9, 13] 
    and then wrap them up so that we're making requests like:
        sum(1, 5)  LT 1
        sum(5, 9)  LT 1
        sum(9, 13) LT 1
    if it had been NoMoreThanKInARow 2 ("color", "red") the reqs would have been:
        sum(1, 5, 9)  LT 2
        sum(5, 9, 13) LT 2
TODO: off-by-one errors?
"""
def desugar_nomorethankinarow(fresh:int, k:int, level:Any, hl_block:HLBlock) -> List[Request]:
    print("WARNING THIS IS NOT YET IMPLEMENTED")
    return []


"""
TODO: not sure how 'balance' needs to be expressed given the current derivations. Ask Sebastian for a motivating example experiment.
"""
def desugar_balance(fresh:int, factor_to_balance:Any, hl_block:HLBlock):
    print("WARNING THIS IS NOT YET IMPLEMENTED")
    return []
  
    
"""
Goal is to produce a json structure like:
    { "fresh" : 18,
         "requests" : [{
           "equalityType" : "EQ",
           "k" : 2,
           "booleanValues" : [1, 3, 5]
         },
         {
           "equalityType" : "LT",
           "k" : 1,
           "booleanValues" : [2, 4, 6]
         }
         ]
       }
Passing along the "fresh" variable counter & a list of reqs to the backend
Important! The backend is expecting json with these exact key names; if the names are change the backend Parser.hs file needs to be updated.
"""
def jsonify(fresh:int, ll_calls: List[Request]) -> str:
    # wrap all the calls in a dictionary:
    return json.dumps({ "fresh" : fresh,
                        "requests" : ll_calls })
 

    
"""
We desugar constraints in 2 ways; directly to CNF and by
    creating Requests to the backend. The requests are
    namedTuples that represent lowlevel requests:
A request is: namedtuple('Request', 'equalityType k booleanValues')
    options for equality-type are "EQ", "LT" & "GT"
We start keeping track of a "fresh" variable counter here; it starts at numTrials*numLevels+1. The convention is you use the fresh variable, and then update it. So fresh is like an always available new boolean variable. 
Recall an HLBlock is: namedtuple('HLBlock', 'design xing hlconstraints')
#TODO
"""
def desugar(hl_block: HLBlock) -> Tuple[int, And, List[Request]]:
    fresh = 1 + encoding_variable_size(hl_block.design, hl_block.xing)
    cnfs_created = []
    reqs_created = [] 
    # -----------------------------------------------------------
    # These go directly to CNF
    # filter the constraints to route to the correct processesors
    derivations = list(filter(lambda x: isinstance(x, Derivation), hl_block.hlconstraints))
    desugared_ders = [desugar_derivation(fresh, x, hl_block) for x in derivations] # <- todo, not implemented
    cnfs_created.extended(desugared_ders) 

    # -----------------------------------------------------------
    # These create lowlevel requests
    #reqs_created.append(desugar_consistency(hl_block))
    # filter for any NoMoreThanKInARow constraints in hl_block.hlconstraints
    #reqs_created.append(desugar_nomorethankinarow(k, level))
    
    # -----------------------------------------------------------
    # This one does both...
    (cnf, reqs) = desugar_full_crossing(fresh, hl_block)
    cnfs_created.extend(cnf)
    reqs_created.extend(reqs)
    
    return (fresh, cnfs_created, reqs_created)




# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~ Top-Level functions ~~~~~~~~~~~~~~~~~~~~~     
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
Returns a fully crossed block that we'll process with synthesize!
"""
def fully_cross_block(design: List[Factor], xing: List[Factor], constraints: Any) -> HLBlock:
    derivation_constraints : List[Any] = process_derivations(design, xing)
    all_constraints = [FullyCross, Consistency] + derivation_constraints + constraints
    return HLBlock(design, xing, all_constraints)

"""
TODO: also psyNeuLink readable
"""
def decode(design : List[Factor], result : str) -> str:
    print("WARNING THIS IS NOT YET IMPLEMENTED")
    return "human readable string"

"""
This is where the magic happens. Desugars the constraints from fully_cross_block (which results in some direct cnfs being produced and some requests to the backend being produced). Then calls unigen on the full cnf file. Then decodes that cnf file into (1) something human readable & (2) psyNeuLink readable.
"""
def synthesize_trials(hl_block: HLBlock, output: str) -> str:
    (fresh, cnfs, reqs) = desugar(hl_block)
    result = jsonify(fresh, reqs)
    with open('ll_constraints.json') as f:  # important: the backend is looking for a file with this name
        f.write(result)
    # TODO: start subprocess call w/ backend on ll_constraints.json
        # this should call the process "stack exec generate-popcount > ex.cnf"
    # append to the file "ex.cnf" of the successful subprocess call w/ cnfs generated from desugaring
        # note: this will involve updating the DIMACS header which can either be done by
        # 1) parsing the header, incrementing the numVars & numClauses & writing new header
        # 2) passing the backend the CNF and offloading the update to the backend
    # start subprocess call that calls unigen
    # decode the results
    return ""
  

