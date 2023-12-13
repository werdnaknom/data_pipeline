import unittest
import pandas as pd

from ..sequencing_pipeline import SequencingDataProcessingPipeline


class TestDataProcessingPipeline(unittest.TestCase):
    def test_pipeline_with_processors(self):
        pipeline = SequencingDataProcessingPipeline()
        response = pipeline.process_data()
        print(response)

    def test_pipeline_without_processors(self):
        pipeline = SequencingDataProcessingPipeline()

        # Create sample input data
        input_data = "test"

        # Process the data through the pipeline
        processed_data = pipeline.process_data(input_data)

        # Check if the processed data is None when no processors are added
        self.assertIsNone(processed_data)


if __name__ == '__main__':
    unittest.main()
