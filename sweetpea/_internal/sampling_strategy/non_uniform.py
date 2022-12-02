from sweetpea._internal.sampling_strategy.base import Gen, SamplingResult
from sweetpea._internal.block import Block
from sweetpea._internal.sampling_strategy.iterate import IterateGen
from sweetpea._internal.sampling_strategy.random import RandomGen

class NonUniformGen(Gen):
    
    @staticmethod
    def class_name():
        return 'NonUniformGen'

    @staticmethod
    def sample(block: Block, sample_count: int) -> SamplingResult:
        if block.complex_factors_or_constraints:
            return IterateGen.sample(block, sample_count)
        else:
            return RandomGen.sample(block, sample_count)
