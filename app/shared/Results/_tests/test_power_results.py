from pathlib import Path

from app.shared.Results.results import ScopePowerResult
from app.shared.Entities.entities import WaveformEntity

from basicTestCase.basic_test_case import BasicTestCase
from app.shared.Entities._tests._test_helper import dataframe_row

class ScopePowerResultTestCase(BasicTestCase):

    def test_init(self):
        sc = ScopePowerResult()

        self.assertTrue(sc.df.empty)
        self.assertEqual(sc.sheet_name, "Power")

    def test_from_row(self):
        sc = ScopePowerResult()

        wf =  WaveformEntity(testpoint="Test Power", runid=2, capture=2,
                             test_category="bob", units="W", location="fake",
                             scope_channel=1, steady_state_min=3.3,
                             steady_state_mean=3.4, steady_state_max=3.6,
                             steady_state_pk2pk=0.2, max=3.6, min=3.0,
                             user_reviewed=False, edge=True,
                             associated_rail="12V_Main")

        sc.add_result(power_entity=wf, picture_location="", df_row=dataframe_row)

        print(sc.df)
        expected_result = {'RunID': 2, 'Capture': 1, 'DUT': 'Mentor Harbor',
                        'PBA': 'K31123-001',
         'Rework': 0, 'DUT Serial': ' A6081C', 'Automation Status': 'Aborted',
         'Test Configuraton': 'Config 1', 'Technician': 'Tony Strojan',
         'Test Station': 'lno-test11', 'Test Setup Comment': 'Configuration #1',
         'ATS Version': '', 'Temperature (C)': 25, '12V_MAIN (V)': 10.8,
         '12V_MAIN Slewrate (V/S)': 200, '12V_MAIN Group': 'Main',
         'PCIE 3.3V Main (V)': 3.3, 'PCIE 3.3V Main Slewrate (V/S)': 1000,
         'PCIE 3.3V Main Group': 'Disabled', '3.3V_AUX (V)': 3.3,
         '3.3V_AUX Slewrate (V/S)': 200, '3.3V_AUX Group': 'Aux'}

        self.assertEqual(sc.df.shape, (1, len(expected_result)))

        for col, value in sc.df.items():
            self.assertEqual(value[0], expected_result[col])


    def test_add_multiple_rows(self):
        sc = ScopePowerResult()

        wf = WaveformEntity(testpoint="Test Power", runid=2, capture=2,
                            test_category="bob", units="W", location="fake",
                            scope_channel=1, steady_state_min=3.3,
                            steady_state_mean=3.4, steady_state_max=3.6,
                            steady_state_pk2pk=0.2, max=3.6, min=3.0,
                            user_reviewed=False, edge=True,
                            associated_rail="12V_Main")

        for _ in range(0,100):
            sc.add_result(power_entity=wf, picture_location="",
                      df_row=dataframe_row)

        self.logger.debug(f"Output Df shape is: {sc.df.shape}")
        self.assertEqual(sc.df.shape[0], 100)


    def test_plot_function(self):
        sc = ScopePowerResult()
        wfs = self._helper_load_waveforms()
        p = Path(r'C:\Users\ammonk\Desktop\Test_Folder\fake_uploads')

        outpath = sc.plot_entity(path=p,power_entity=wfs[0],
                       spec_max=25.0)

        expected_name = "12V_MAIN_25P0V.png"
        self.assertEqual(outpath.name, expected_name)
        self.assertEqual(outpath.resolve(), p.joinpath(expected_name).resolve())



