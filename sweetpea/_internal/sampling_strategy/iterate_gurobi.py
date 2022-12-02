from sweetpea._internal.sampling_strategy.base import Gen, SamplingResult
from sweetpea._internal.block import Block
from sweetpea._internal.core import CNF
from sweetpea._internal.core.generate.sample_ilp import sample_ilp_iterate

class IterateGurobiGen(Gen):

    @staticmethod
    def class_name():
        return 'IterateGurobiGen'

    @staticmethod
    def sample(block: Block, sample_count: int) -> SamplingResult:
        backend_request = block.build_backend_request()
        if block.show_errors():
            return SamplingResult([], {})

        solutions = sample_ilp_iterate(
            sample_count,
            CNF(backend_request.get_cnfs_as_json()),
            block.variables_per_sample(),
            backend_request.get_requests_as_generation_requests())

        # TODO: see minimum_trials edge case from unigen.py if that problem occurs

        result = list(map(lambda s: Gen.decode(block, s.assignment), solutions))
        return SamplingResult(result, {})
