from Processing.RepoProcessors import WaveformRepositoryProcessor
from Processing import DataProcessingPipeline
from Processing.TestDataProcessors import TitleSheetProcessor, NoProcessor, SequencingProcessor, PowerOnTimeProcessor, \
    WaveformCombinationProcessor


class OverviewDataProcessingPipeline(DataProcessingPipeline):

    def __init__(self):
        super(OverviewDataProcessingPipeline, self).__init__()
        self.processors = [
            WaveformRepositoryProcessor(),
            WaveformCombinationProcessor()

            # TitleSheetProcessor(),
            # NoProcessor(),
        ]
