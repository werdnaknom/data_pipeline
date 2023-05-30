import typing as t
import logging

import pandas as pd

from Processing.RepoProcessors import RepositoryProcessor
from Processing.dataprocessor_usecase import DataProcessor

logging.basicConfig(format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)s] : %(message)s',
                    level=logging.DEBUG)

LOG_LEVEL = logging.DEBUG


class DataProcessingPipeline:
    def __init__(self):
        self.processors = []
        self.formatters = []

    @classmethod
    def log(cls):
        logging_handler = logging.getLogger(cls.__name__)
        return logging_handler

    def add_processor(self, processor: DataProcessor):
        """
        Add a processor to the pipeline.
        A processor should be a callable that takes in data and returns processed data.
        """
        self.processors.append(processor)

    def process_data(self) -> t.Dict:
        """
        Process data through the pipeline by applying each processor sequentially.
        """
        sheets = {}
        if len(self.processors) < 1:
            print("No processors found in the pipeline.")
            return None

        processed_data = None
        for i, processor in enumerate(self.processors):
            if i == 0:  # Handle the first processor separately
                if isinstance(processor, RepositoryProcessor):
                    repository_response = processor.execute()
                else:
                    print("The first processor should be a RepositoryProcessor.")
                    return None
            else:
                if not repository_response:
                    print("No data available for processing.")
                    return None
                else:
                    processing_dataframe = repository_response.dataframe
                    processed_response = processor.execute(processing_dataframe)
                sheets[processed_response.title] = processed_response.dataframe
        return sheets
