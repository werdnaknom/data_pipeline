from Processing.RepoProcessors import SequencingRepositoryProcessor
from Processing import DataProcessingPipeline
from Processing.TestDataProcessors import TitleSheetProcessor, NoProcessor, SequencingProcessor, PowerOnTimeProcessor


class SequencingDataProcessingPipeline(DataProcessingPipeline):

    def __init__(self):
        super(SequencingDataProcessingPipeline, self).__init__()
        self.processors = [
            SequencingRepositoryProcessor(),
            TitleSheetProcessor(),
            NoProcessor(),
            SequencingProcessor(),
            PowerOnTimeProcessor()
        ]
