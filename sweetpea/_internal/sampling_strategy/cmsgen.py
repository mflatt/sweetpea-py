from typing import List, cast

from sweetpea._internal.sampling_strategy.base import Gen, SamplingResult
from sweetpea._internal.sampling_strategy.unigen import UniGen
from sweetpea._internal.block import Block


"""
This strategy relies fully on CMSGen to produce the desired number of samples.
"""
class CMSGen(Gen):
    # The CMSGen API is similar to Unigen, so we piggy-back on that implementation.

    @staticmethod
    def class_name():
        return 'CMSGen'

    @staticmethod
    def sample(block: Block, sample_count: int, min_search: bool=False) -> SamplingResult:
        return UniGen.sample(block, sample_count, min_search, use_cmsgen=True)
