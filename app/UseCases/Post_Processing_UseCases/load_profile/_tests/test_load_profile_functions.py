from unittest import TestCase, mock
import typing as t
import logging
import sys
import pickle

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

from basicTestCase.basic_test_case import BasicTestCase
from app.UseCases.Post_Processing_UseCases.load_profile.load_profile_use_case \
    import LoadProfileRequestObject, LoadProfileUseCase

from app.Repository.repository import Repository, MongoRepository
from app.shared.Entities.entities import WaveformEntity


class LoadProfileTestCase(BasicTestCase):
    logger_name = 'LoadProfileTestCase'

class LoadProfileFunctionsTestCase(LoadProfileTestCase):

    def setUp(self) -> None:
        super(LoadProfileFunctionsTestCase, self).setUp()
        self.test_df = self._helper_load_aux_to_main_csv()

    def test_groupout_capture(self):
        from app.UseCases.Post_Processing_UseCases.load_profile.load_profile_functions import \
            groupout_capture

        groupout_capture(df=self.test_df)


class LoadProfileCaptureUseCaseTestCase(LoadProfileTestCase):
    def _setUp(self) -> None:
        self.test_df = self._helper_load_load_profile_csv()
        self.df = self._helper_load_capture_df()
        self.wfs = self._helper_load_waveforms()
        self.mock_repo = mock.MagicMock(Repository)
        self.uc = LoadProfileUseCase(repo=self.mock_repo)

    def test_process_request(self):
        rq = LoadProfileRequestObject(df=self.test_df)
        uc = LoadProfileUseCase(repo=MongoRepository())
        resp = uc.execute(request_object=rq)
        print(resp)

    def test_pair_voltage_to_current(self):
        volt = self.wfs[0]
        curr = self.wfs[1]
        volt.associated_rail = curr.testpoint
        curr.associated_rail = volt.testpoint
        edges = [volt, curr]
        pairs = self.uc._pair_voltage_to_current(edges=edges)
        self.logger.debug(f"_pairs returned: {pairs}")

        self.assertIsInstance(pairs, list)
        self.assertIsInstance(pairs[0], tuple)

        self.assertEqual(pairs[0][0], edges[0])
        self.assertEqual(pairs[0][1], edges[1])

    def test_pair_empty_voltage_to_current(self):
        curr = self.wfs[1]
        curr.associated_rail = "12V_MAIN"
        currs = [curr]
        pairs = self.uc._pair_voltage_to_current(edges=currs)

        self.assertIsInstance(pairs, list)
        self.assertIsInstance(pairs[0], tuple)

        self.assertEqual(len(pairs[0]), 2)
        self.assertEqual(pairs[0][1], currs[0])

    def test_calculate_power(self):
        volt = self.wfs[0]
        curr = self.wfs[1]

        power_wf = self.uc._calculate_power(volt_wf=volt, curr_wf=curr)
        print(power_wf.max(), power_wf.mean(), power_wf.min(),
              volt.steady_state_max)

    def test_return_rails_by_id(self):
        self.mock_repo.find_many_waveforms.return_value = [wf.to_dict()
                                                           for wf in self.wfs]

        # uc = LoadProfileUseCase(repo=mock_repo)
        result = self.uc._return_rails(df=self.df)

        self.assertIsInstance(result, list)

        self.mock_repo.find_many_waveforms.assert_called_once_with(filters=
        [{
            "_id": wf._id}
            for wf in
            self.wfs])

        self.assertEqual(result, self.wfs)

    def test_return_edge_waveforms(self):
        wf_dicts = [wf.to_dict() for wf in self.wfs]

        mock_repo = mock.MagicMock(Repository)
        mock_repo.find_waveform_by_id.side_effect = wf_dicts

        uc = LoadProfileUseCase(repo=mock_repo)
        result = uc._return_edge_waveforms(df=self.df)

        self.assertIsInstance(result, list)

        wf_ids = self.df[self.df['edge_rail'] == True][
            'WaveformEntity_id'].to_list()
        self.assertEqual(len(result), len(wf_ids))

        repo_calls = [mock.call.find_waveform_by_id(waveform_id=wf_id) for wf_id in
                      wf_ids]
        mock_repo.assert_has_calls(repo_calls)

    def test_return_onboard_rails(self):
        wf_dicts = [wf.to_dict() for wf in self.wfs]

        mock_repo = mock.MagicMock(Repository)
        mock_repo.find_waveform_by_id.side_effect = wf_dicts[2:]

        uc = LoadProfileUseCase(repo=mock_repo)
        result = uc._return_onboard_rails(df=self.df)
        self.assertIsInstance(result, list)
        print(len(result))

        wf_ids = self.df[self.df['edge_rail'] == False][
            'WaveformEntity_id'].to_list()
        self.assertEqual(len(result), len(wf_ids))

        repo_calls = [mock.call.find_waveform_by_id(waveform_id=wf_id) for wf_id in
                      wf_ids]
        mock_repo.assert_has_calls(repo_calls)

    def test__create_power_entity(self):
        fake_x = np.arange(0, 1000)
        fake_y = np.ones(1000)
        min_ss = 0.9
        max_ss = 1.1
        min_p = 0.0
        max_p = 12
        fake_y[502] = min_ss
        fake_y[503] = max_ss
        fake_y[2] = max_p
        fake_y[3] = min_p
        downsample = [fake_x, fake_y]
        rail_name = "12V_MAIN"
        test_cate = "test"

        power = self.uc._create_power_entity(runid=1, capture=1,
                                             test_category=test_cate,
                                             associated_rail=rail_name,
                                             downsample=downsample,
                                             ss_index=101)
        self.logger.debug(f"Created Power Entity: {power}")
        self.assertIsInstance(power, WaveformEntity)
        self.assertEqual(power.testpoint, rail_name + "_Power")
        self.assertEqual(power.runid, 1)
        self.assertEqual(power.capture, 1)
        self.assertEqual(power.test_category, test_cate)
        self.assertEqual(power.units, "W")
        self.assertEqual(power.location, "N/A")
        self.assertEqual(power.scope_channel, 100)
        self.assertEqual(power.max, max_p)
        self.assertEqual(power.min, min_p)
        self.assertEqual(power.steady_state_mean, 1.0)
        self.assertEqual(power.steady_state_max, max_ss)
        self.assertEqual(power.steady_state_min, min_ss)
        self.assertAlmostEqual(power.steady_state_pk2pk, (max_ss - min_ss), 2)

    def test_create_power_entity(self):
        volts = self.wfs[0]
        currs = self.wfs[1]

        pe = self.uc.create_power_entity(volt_wf=volts, curr_wf=currs)

        self.logger.debug(f"Created Power Entity: {pe}")
        self.assertIsInstance(pe, WaveformEntity)

        self.assertEqual(pe.testpoint, volts.testpoint + "_Power")
        self.assertEqual(pe.runid, volts.runid)
        self.assertEqual(pe.capture, volts.capture)
        self.assertEqual(pe.test_category, volts.test_category)
        self.assertEqual(pe.units, "W")
        self.assertEqual(pe.location, "N/A")
        self.assertEqual(pe.scope_channel, 100)

        # plt.plot(pe.x_axis(), pe.y_axis())
        # plt.show()

    def test_return_edge_rail_pairs(self):
        volt = self.wfs[0]
        curr = self.wfs[1]
        volt.associated_rail = curr.testpoint
        curr.associated_rail = volt.testpoint
        volt.edge = True
        curr.edge = True
        result = self.uc.return_edge_rail_pairs(waveform_list=[volt, curr] +
                                                              self.wfs[2:])
        self.logger.debug(msg=f"edge pairs returned: {result}")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        for pair in result:
            self.assertIsInstance(pair, tuple)
            for wf, expected in zip(pair, [volt, curr]):
                self.assertIsInstance(wf, WaveformEntity)
                self.assertEqual(wf, expected)

    def test_validate_current(self):
        # print(*self.df, sep="\n")
        volt = self.wfs[0]
        curr = self.wfs[1]
        volt.associated_rail = curr.testpoint
        curr.associated_rail = volt.testpoint
        volt.edge = True
        curr.edge = True
        result = self.uc.validate_current(df=self.df,
                                          waveforms=[volt, curr] + self.wfs[
                                                                       2:])
        self.logger.debug(f"validate current returned: {result}")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        for rdict in result:
            self.assertIsInstance(rdict, dict)
            for key in ['Result', 'Reason', "max_current_ss", "max_current",
                        "mean_current_ss", "min_current_ss"]:
                self.logger.debug(f"Result[{key}] = {rdict[key]}")

        df = pd.DataFrame(result)
        print(df)

    def test_load_waveforms(self):
        self.mock_repo.find_many_waveforms.return_value = [wf.to_dict() for
                                                           wf in self.wfs]
        wfs = self.uc.load_waveforms(df=self.df)

        self.assertIsInstance(wfs, list)
        for wf_r, wf_e in zip(wfs, self.wfs):
            self.logger.debug(f"Loaded in {wf_r}")
            self.assertIsInstance(wf_r, WaveformEntity)
            self.assertEqual(wf_r, wf_e)

        self.mock_repo.find_many_waveforms.assert_called_once()

    def test_find_minimum_steady_state_index(self):

        result = self.uc.find_minimum_steady_state_index(waveform_list=self.wfs)
        self.logger.debug(f"{result}")
        self.assertEqual(result, 101)

        mock_wf = mock.MagicMock(WaveformEntity)
        mock_wf.steady_state_index.return_value = 45
        mock_wf.units = "V"
        waveform_list = self.wfs + [mock_wf]
        result = self.uc.find_minimum_steady_state_index(
            waveform_list=waveform_list)

        self.logger.debug(f"{result}")
        self.assertEqual(result, 45)
        mock_wf.steady_state_index.assert_called_once()

    def test_validate_power(self):
        volt = self.wfs[0]
        curr = self.wfs[1]
        volt.associated_rail = curr.testpoint
        curr.associated_rail = volt.testpoint
        volt.edge = True
        curr.edge = True
        result = self.uc.validate_power(waveforms=self.wfs[2:] + [volt, curr],
                               df=self.df)
        self.logger.debug(f"validate power returned: f{result}")

        self.assertIsInstance(result, list)

        df = pd.DataFrame(result)
        print(df)

    def test_validate_waveforms(self):
        result = self.uc.validate_waveforms(waveforms=self.wfs, df=self.df)
        self.logger.debug(f"validate waveforms returned: f{result}")

        for r in result:
            print(r)

        df = pd.DataFrame(result)
        print(df)
