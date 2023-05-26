from unittest import TestCase
from pathlib import Path
import typing as t

from multiprocessing import Pool
import matplotlib.pyplot as plt
import numpy as np

from Processing.processing_usecase import ProcessingUseCase, TestpointQueryRequestObject, TestpointInfoRequestObject, \
    RunidInfoRequestObject

from Entities.WaveformFunctions.waveform_analysis import WaveformAnalysis

import scipy.signal as signal


def read_image(image_loc):
    p = Path(image_loc)
    wf_binary = WaveformAnalysis.read_binary_waveform(p, compressed=False)
    b, a = signal.butter(4, 20e6, fs=1.25e9, btype='low', analog=False)
    initial_values = wf_binary[:1000]
    extended_waveform = np.concatenate((initial_values, wf_binary))
    print(len(extended_waveform))
    filtered_wf = signal.lfilter(b, a, extended_waveform)[1000:]
    print(len(filtered_wf))
    downsample = WaveformAnalysis.min_max_downsample_1d(wf=filtered_wf, size=1000)
    return downsample


class TestProcessingUseCaseTestCase(TestCase):

    def test_query_testpoint(self):
        uc = ProcessingUseCase()
        request = TestpointQueryRequestObject(product="Clara Peak")
        query = uc.query_testpoints(testpoint_request=request)
        print(query)

    def test_query_runid(self):
        uc = ProcessingUseCase()
        request = RunidInfoRequestObject(product="Clara Peak", runid=6793, test_category="Main To Aux")
        df = uc.query_runid(runid_request=request)
        testpoints = df["waveforms.testpoint"].unique().tolist()
        testpoint_query_request = TestpointQueryRequestObject(product="Clara Peak",
                                                              testpoints=testpoints)
        testpoint_requirements_query = uc.query_testpoints(testpoint_request=testpoint_query_request)
        testpoint_requirement_names = [tp_req.testpoint for tp_req in testpoint_requirements_query]
        print(testpoint_requirement_names)

        def find_testpoint_requirement_by_name(tp_classes: t.List, target_name: str):
            for tp_class in tp_classes:
                if tp_class.testpoint == target_name:
                    return tp_class
            return None

        '''
        for group, grouped_df in df.groupby(by=["runid", "waveforms.capture"]):
            print(group, grouped_df.shape)
        # df.to_csv("test.csv")
        '''
        for group, grouped_df in df.groupby(by=["runid", "waveforms.testpoint"]):
            tp_req = find_testpoint_requirement_by_name(testpoint_requirements_query, target_name=group[1])
            if "CURRENT" in tp_req.testpoint:
                tp_req.current_rail = True
                continue
            with Pool() as pool:
                arrays = pool.map(read_image, grouped_df['waveforms.location'])

            b, a = signal.butter(4, 20e6, fs=1.25e9, btype='low', analog=False)
            fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(20, 20))
            og = axes[0]
            # Determine the filter delay (in samples)
            # filter_delay = int(0.5 * (len(b) - 1))
            filter_delay = 10000
            # print(filter_delay)
            filt = axes[1]
            for array in arrays:
                initial_value = array[0]
                print(initial_value)
                extended_waveform = np.concatenate(([initial_value] * filter_delay, array))
                filtered_wf = signal.lfilter(b, a, extended_waveform)[filter_delay:]
                print(len(filtered_wf))

                filt.plot(filtered_wf, color='red', alpha=0.25)
                og.plot(array, color='red', alpha=0.25)
            fig.suptitle(f"{group[1]}")
            plt.show()

            '''
            x_coords = []
            y_coords = []
            for i, array in enumerate(arrays):
                threshold = np.percentile(array, 99) * 0.1
                transition_indices = np.where(array < threshold)[0]
                print(transition_indices)
                x_coords.extend(transition_indices)
                y_coords.extend([i] * len(transition_indices))

            # plt.scatter(x_coords, y_coords, c='red', alpha=0.5, s=5)
            # plt.title(f"{title} ({threshold})")
            # plt.show()
            break
            '''
