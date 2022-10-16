from unittest import TestCase, mock
import logging
import sys
from pathlib import Path

import numpy as np


class WaveformFunctionsTestCase(TestCase):
    logger = logging.getLogger('WaveformTestLogger')
    logger.setLevel(level=logging.DEBUG)

    def setUp(self) -> None:
        self.hdlr = logging.StreamHandler(sys.stderr)
        self.logger.addHandler(hdlr=self.hdlr)
        self.location = r'\\npo\coos\LNO_Validation\Validation_Data\_data\ATS ' \
                        r'2.0\Mentor Harbor\K31123-003\RW00\BB063A\906\Tests\Aux ' \
                        r'To Main\2\CH1.bin'

    def tearDown(self) -> None:
        self.logger.removeHandler(self.hdlr)

    def test_read_waveform_binary_compressed(self):
        from app.shared.Helpers.waveform_functions import read_waveform_binary

        with self.assertRaises(NotImplementedError):
            read_waveform_binary(location=Path(""), compressed=True)

    def test_read_waveform_binary_uncompressed(self):
        from app.shared.Helpers.waveform_functions import read_waveform_binary

        wf = read_waveform_binary(location=Path(self.location),
                                  compressed=False)

        self.logger.debug(msg=f"Read waveform should be ~3.3: {wf}")
        self.assertIsInstance(wf, np.ndarray)
        self.assertEqual(wf.shape, (1250000,))
        self.assertAlmostEqual(wf[-1], 3.36, places=2)

    def test_create_waveform_x_coords(self):
        from app.shared.Helpers.waveform_functions import \
            create_waveform_x_coords

        x_inc = 0.00000008
        length = 1250000

        x_wf = create_waveform_x_coords(x_increment=x_inc, length=length)
        self.logger.debug(msg=f"X_COORD WF is:{x_wf}")

        self.assertEqual(x_wf[-1], 1.00000000e-01)  # last point should equal
        # 100ms
        self.assertEqual(x_wf[0], 0)
        self.assertEqual(x_wf.shape, (length,))

    def test_min_max_downsample_2d(self):
        from app.shared.Helpers.waveform_functions import min_max_downsample_2d
        from app.shared.Helpers.waveform_functions import \
            create_waveform_x_coords
        from app.shared.Helpers.waveform_functions import read_waveform_binary
        x_inc = 0.00000008
        length = 1250000
        size = 500

        wf_y = read_waveform_binary(location=Path(self.location),
                                    compressed=False)
        self.logger.debug(msg=f"WF read as shape: {wf_y.shape}")

        x_wf = create_waveform_x_coords(x_increment=x_inc, length=length)
        wf_x_downsampled, wf_y_downsampled = min_max_downsample_2d(wf_x=x_wf,
                                                                   wf_y=wf_y,
                                                                   size=size)

        self.logger.debug(msg=f"WF_X size: {wf_x_downsampled.size}")
        self.logger.debug(msg=f"WF_Y size: {wf_y_downsampled.size}")
        self.assertEqual(wf_x_downsampled.size, size * 2)
        self.assertEqual(wf_y_downsampled.size, size * 2)

        self.assertEqual(wf_x_downsampled.size, wf_y_downsampled.size)

        self.assertEqual(wf_y_downsampled.max(), wf_y.max())
        self.assertEqual(wf_y_downsampled.min(), wf_y.min())

        self.assertIsInstance(wf_x_downsampled, np.ndarray)
        self.assertIsInstance(wf_y_downsampled, np.ndarray)

    def test_min_max_downsample_1d(self):
        from app.shared.Helpers.waveform_functions import min_max_downsample_1d
        from app.shared.Helpers.waveform_functions import read_waveform_binary
        size = 500

        wf_y = read_waveform_binary(location=Path(self.location),
                                    compressed=False)
        self.logger.debug(msg=f"WF read as shape: {wf_y.shape}")

        downsampled_wf = min_max_downsample_1d(wf=wf_y,
                                               size=size)

        self.logger.debug(msg=f"WF_X size: {downsampled_wf.size}")
        self.assertEqual(downsampled_wf.size, size * 2)

        self.assertEqual(downsampled_wf.max(), wf_y.max())
        self.assertEqual(downsampled_wf.min(), wf_y.min())

        self.assertIsInstance(downsampled_wf, np.ndarray)

    def test_find_cutoff_target_by_percentile(self):
        from app.shared.Helpers.waveform_functions import \
            find_cutoff_target_by_percentile
        from app.shared.Helpers.waveform_functions import read_waveform_binary

        dir_path = Path(
            r'\\npo\coos\LNO_Validation\Validation_Data\_data\ATS 2.0\Mentor Harbor\K31123-003\RW00\BB0624\922\Tests\Aux To Main\1')
        bin_files = [f for f in dir_path.iterdir() if f.suffix == ".bin"]

        for file in bin_files:
            self.logger.debug("---" * 6)
            self.logger.debug(file.name)
            wf = read_waveform_binary(file, compressed=False)
            self.logger.debug(msg=f"WF read as shape: {wf.shape}")

            for perc in range(10, 100, 10):
                target = find_cutoff_target_by_percentile(wf=wf,
                                                          percentile=perc)
                self.assertIsInstance(target, float)
                self.logger.debug(f"{perc} == {target}")
            for perc in range(91, 100, 1):
                target = find_cutoff_target_by_percentile(wf=wf,
                                                          percentile=perc)
                self.assertIsInstance(target, float)
                self.logger.debug(f"{perc} == {target}")

    def test_find_steady_state_wf(self):
        from app.shared.Helpers.waveform_functions import \
            find_steady_state_wf
        from app.shared.Helpers.waveform_functions import read_waveform_binary

        target_voltage = 3.3 * 0.9

        wf = read_waveform_binary(Path(self.location), compressed=False)
        self.logger.debug(msg=f"WF read as shape: {wf.shape}")

        ss_wf = find_steady_state_wf(wf=wf, value=target_voltage)

        self.logger.debug(f"Returned WF is of time length: "
                          f"{(ss_wf.size * 0.00000008) * 1000}")
        self.logger.debug(f"Returned wf is of size: {ss_wf.size}")

        self.assertLess(ss_wf.size, wf.size)

        self.logger.debug(f"not ss max: {wf[:wf.size - ss_wf.size].max()} < "
                          f"{target_voltage}")
        self.assertLess(wf[:wf.size - ss_wf.size].max(), target_voltage)
        self.logger.debug(f"ss first: {ss_wf[0]} > "
                          f"{target_voltage}")
        self.assertGreater(ss_wf[0], target_voltage)

    def test_steady_state_waveform_by_percentile(self):
        from app.shared.Helpers.waveform_functions import \
            find_steady_state_waveform_by_percentile
        from app.shared.Helpers.waveform_functions import read_waveform_binary

        wf = read_waveform_binary(Path(self.location), compressed=False)
        self.logger.debug(msg=f"WF read as shape: {wf.shape}")

        for accuracy in [0.8, 0.85, 0.9, 0.95, 0.97]:
            self.logger.debug("---" * 10)
            self.logger.debug(f"Accuracy: {accuracy}")
            ss_wf = find_steady_state_waveform_by_percentile(wf=wf,
                                                             accuracy=accuracy)
            self.logger.debug(ss_wf.size)
            self.logger.debug(ss_wf[0])
            self.logger.debug(ss_wf)
            self.assertLess(ss_wf.size, wf.size)
            self.assertEqual(ss_wf[:1000].all(), wf[:1000].all())

    def test_steady_state_waveform_by_percetile_with_bad_accuracy(self):
        from app.shared.Helpers.waveform_functions import \
            find_steady_state_waveform_by_percentile

        with self.assertRaises(AssertionError):
            _ = find_steady_state_waveform_by_percentile(
                wf=np.ndarray([1, 2, 3, 4, 5]),
                percentile=100)
            self.fail("Should never reach this line")
