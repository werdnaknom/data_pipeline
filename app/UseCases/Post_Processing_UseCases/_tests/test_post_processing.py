from unittest import mock

import pandas as pd

from basicTestCase.basic_test_case import BasicTestCase

from app.shared.Responses.response import ResponseSuccess

from app.UseCases.Automation_Test_Post_Processing.post_processing_usecase import \
    AutomationTestUseCase
from app.UseCases.Automation_Test_Post_Processing.post_processing_usecase import \
    AnalyzeWaveformUseCase, AnalyzeWaveformRequestObject
from app.Repository.repository import Repository


class PostProcessingUseCaseTestCase(BasicTestCase):
    CLEANED_USER_DF = "cleaned_user_df.pkl"
    IDENTIFIED_EDGE_RAIL_DF = "edge_rail_df.pkl"
    TESTPOINTS_ADDED_DF = "testpoint_added_df.pkl"
    VALIDATED_DF = "validated_df.pkl"

    def _helper_load_cleaned_datafile(self):
        test_file = self._helper_get_file(self.CLEANED_USER_DF)
        df = self._helper_read_pickle(test_file)
        assert isinstance(df, pd.DataFrame), "something went wrong in " \
                                             "helper function, cleaned wasn't a dataframe"
        return df

    def _helper_load_identified_edge_rails(self):
        test_file = self._helper_get_file(self.IDENTIFIED_EDGE_RAIL_DF)
        df = self._helper_read_pickle(test_file)
        assert isinstance(df, pd.DataFrame), "something went wrong in " \
                                             "helper function, cleaned wasn't a dataframe"
        return df

    def _helper_load_test_point_added_df(self):
        test_file = self._helper_get_file(self.TESTPOINTS_ADDED_DF)
        df = self._helper_read_pickle(test_file)
        assert isinstance(df, pd.DataFrame), "something went wrong in " \
                                             "helper function, cleaned wasn't a dataframe"
        return df

    def _helper_load_validated_df(self):
        test_file = self._helper_get_file(self.VALIDATED_DF)
        df = self._helper_read_pickle(test_file)
        assert isinstance(df, pd.DataFrame), "something went wrong in " \
                                             "helper function, cleaned wasn't a dataframe"
        return df

    def _setUp(self):
        self.xlsx = self._helper_load_user_xlsx()
        self.datafile = self._helper_load_load_profile_csv()
        self.mock_repo = mock.MagicMock(Repository)
        self.uc = AutomationTestUseCase(repo=self.mock_repo)

    def test_load_dataframe_from_xlsx(self):
        xlsx_dict = self.uc.load_dataframe_from_xlsx(
            xlsx_path=self._helper_xlsx_path())

        self.logger.debug(f"load_dataframe from xlsx returned: {xlsx_dict}")

        self.assertIsInstance(xlsx_dict, dict)

        self.assertEqual(xlsx_dict.keys(), self._helper_load_user_xlsx().keys())

        for df in xlsx_dict.values():
            self.assertIsInstance(df, pd.DataFrame)

    def test_cleanup_rail_names(self):
        df = self.datafile
        num_testpoints = df.testpoint.nunique()
        cleanup = self.uc._cleanup_rail_names(user_file=self.xlsx,
                                              data_file=self.datafile)
        self.logger.debug(f"cleanup returned : {cleanup}")
        self.assertIsInstance(cleanup, pd.DataFrame)

        cleanup_testpoints = cleanup.testpoint.nunique()
        self.logger.debug(f"df had {num_testpoints} testpoints and now has "
                          f"{cleanup_testpoints} unique testpoints")
        self.assertLess(cleanup_testpoints, num_testpoints)

        ''' ONLY UNCOMMENT IF CLEANUP NEEDS TO BE UPDATED FOR TESTS
        
        p = self.TEST_FILE_FOLDER + "\\"+ self.CLEANED_USER_DF
        with open(p, 'wb') as f:
            pickle.dump(cleanup, f)
        print(p)
        '''

        self.logger.debug("Test passed!")

    def test_identify_edge_rails(self):
        datafile = self._helper_load_cleaned_datafile()

        edge_rails = self.uc._identify_edge_rails(user_file=self.xlsx,
                                                  data_file=datafile)
        self.assertIsInstance(edge_rails, pd.DataFrame)
        self.logger.debug(f"edge rails identified: {edge_rails}")

        current_rail = edge_rails[edge_rails.testpoint == "12V_MAIN_CURRENT"]
        voltage_rails = edge_rails[edge_rails.testpoint != "12V_MAIN_CURRENT"]
        self.assertTrue(current_rail[self.uc.CURRENT_RAIL].all(), True)
        self.assertFalse(voltage_rails[self.uc.CURRENT_RAIL].all(), False)
        self.assertEqual(edge_rails[edge_rails.testpoint == "12V_MAIN"][
                             self.uc.EXPECTED_NOMINAL].unique(), [12.0])

        self.assertEqual(current_rail[self.uc.SPEC_MAX].unique(), [2.1])

        self.assertTrue(current_rail[self.uc.EDGE_RAIL].all())
        self.assertTrue(edge_rails[edge_rails.testpoint == "12V_MAIN"][
                            self.uc.EDGE_RAIL].all())

        self.logger.debug(f"12V Main Current Associated Rail"
                          f":{current_rail[self.uc.ASSOCIATED_EDGE_RAIL].unique()}")
        self.assertEqual(current_rail[self.uc.ASSOCIATED_EDGE_RAIL].unique(),
                         ["12V_MAIN"])

        self.logger.debug(f"12V Main Associated Rail"
                          f":{edge_rails[edge_rails.testpoint == '12V_MAIN'][self.uc.ASSOCIATED_EDGE_RAIL].unique()}")

        self.assertEqual(edge_rails[edge_rails.testpoint == "12V_MAIN"][
                             self.uc.ASSOCIATED_EDGE_RAIL].unique(),
                         ["12V_MAIN_CURRENT"])

        edge_rail_names = ["12V_MAIN_CURRENT", "12V_MAIN"]
        not_edges = edge_rails[~edge_rails.testpoint.isin(
            edge_rail_names)]
        self.assertFalse(not_edges[self.uc.EDGE_RAIL].all())
        ''' ONLY UNCOMMENT IF IDENTIFIED EDGE RAILS NEEDS TO BE UPDATED FOR 
        TESTS

        p = self.TEST_FILE_FOLDER + "\\"+ self.IDENTIFIED_EDGE_RAILS_DF
        with open(p, 'wb') as f:
            pickle.dump(edge_rails, f)
        print(p)
        '''
        print(edge_rails.columns, sep="\n")
        self.logger.debug("Test passed!")

    def test_add_testpoint_criteria(self):
        df = self._helper_load_identified_edge_rails()
        onboard_rail_user = self.xlsx['On-Board Rails']

        testpoint_df = self.uc._add_testpoint_criteria(user_file=self.xlsx,
                                                       data_file=df)
        self.assertIsInstance(testpoint_df, pd.DataFrame)

        # self.logger.debug(f"Associated Rail values:"
        #                   f" {testpoint_df.associated_rail.unique()}")

        for i, row in onboard_rail_user.iterrows():
            self.logger.debug(row['Voltage Rail'])
            rail_df = testpoint_df[testpoint_df.testpoint ==
                                   row['Voltage Rail']]
            self.assertFalse(rail_df.empty)
            spec_max = rail_df[self.uc.SPEC_MAX].unique()
            self.logger.debug(f"Spec Max:"
                              f"{spec_max}, {row['Spec Max']}")
            self.assertEqual(spec_max, [row['Spec Max']])

            nominal = rail_df[self.uc.EXPECTED_NOMINAL].unique()
            self.logger.debug(f"Nominal:"
                              f"{nominal}, {row['Nominal Value']}")
            self.assertEqual(nominal, [row["Nominal Value"]])

            spec_min = rail_df[self.uc.SPEC_MIN].unique()
            self.logger.debug(f"Spec Min: {spec_min}, {row['Spec Min']}")
            self.assertEqual(spec_min, [row["Spec Min"]])
            self.assertFalse(rail_df[self.uc.EDGE_RAIL].all())
            self.assertFalse(rail_df[self.uc.CURRENT_RAIL].all())

        # ONLY UNCOMMENT IF TESTPOINTS NEED UPDATING
        '''
        p = self.TEST_FILE_FOLDER + "\\"+  self.TESTPOINTS_ADDED_DF
        with open(p, 'wb') as f:
            pickle.dump(testpoint_df, f)
        print(p)
        '''

        self.logger.debug("Test passed!")

    def test_find_or_upload_waveforms(self):
        df = self._helper_load_test_point_added_df()
        old_cols = set(df.columns)

        resp = self.uc._find_or_upload_waveforms(data_file=df)
        self.assertIsInstance(resp, ResponseSuccess)
        uploaded_df = resp.value

        uploaded_cols = set(uploaded_df.columns)

        diff = uploaded_cols - old_cols
        print(uploaded_df['WaveformEntity_id'][0])

        self.assertEqual(diff, {"WaveformEntity_id"})

        for value in uploaded_df['WaveformEntity_id'].values:
            self.assertIsInstance(value, mock.MagicMock)

    @mock.patch('app.UseCases.post_processing_tests.post_processing_usecase'
                '.PostProcessingWaveFormUseCase.load_dataframe_from_xlsx')
    @mock.patch('app.UseCases.post_processing_tests.post_processing_usecase'
                '.PostProcessingWaveFormUseCase.load_dataframe_from_csv')
    def test_process_request(self, mock_csv_df, mock_xlsx_df):
        mock_csv_df = self._helper_load_load_profile_csv()
        mock_xlsx_df = self._helper_load_capture_df()



    def test_get_waveform_entity(self):
        from app.Repository.repository import MongoRepository

        repo = MongoRepository()

        df = self._helper_load_validated_df()
        df = df[df.testpoint == df.iloc[0].testpoint][:16]
        uc = AnalyzeWaveformUseCase(repo=repo)
        for _ in range(2):
            for i, row in df.iterrows():
                req = AnalyzeWaveformRequestObject(df_row=row)
                id = uc.execute(req)
                if not id:
                    self.logger.debug(f"{id} \n Not loaded correctly!")
        document_count = repo.collection_waveform.count_documents({})
        self.logger.debug(f"Document count equals --> {document_count}, "
                          f"and should be should be {df.shape[0]}")
        self.assertEqual(repo.collection_waveform.count_documents({}),
                         df.shape[0])


    '''
    def test_find_or_upload_project(self):
        from app.Repository.repository import MongoRepository
        repo = MongoRepository()

        uc = PostProcessingWaveFormUseCase(repo)

        df = self._helper_load_test_point_added_df()
        starting_cols = set(df.columns)
        for x in range(5):
            result_df = uc._find_or_upload_projects(df)

        ending_cols = set(result_df.columns)

        print(ending_cols-starting_cols)
    '''


    def test_find_or_upload_project(self):
        project = self.create_fake_product_entities(1)[0]

        self.mock_repo.find_project_id.return_value = None
        self.mock_repo.insert_one.return_value = project._id

        df = self._helper_load_cleaned_datafile()
        original_cols = set(df.columns)

        #all df edits should be made inplace
        resp = self.uc._find_or_upload_projects(data_file=df)
        self.assertIsInstance(resp, ResponseSuccess)

        result_cols = set(df.columns)

        self.mock_repo.find_project_id.assert_called_once_with(
            project_name="Mentor Harbor")
        self.mock_repo.insert_one.assert_called_once()

        self.assertEqual(result_cols - original_cols, {"project_id"})
        self.assertEqual(df["project_id"].unique(), [project._id])

    def test_find_or_upload_pba(self):
        entities = self.create_fake_pba_entities(2)

        self.mock_repo.find_pba_id.return_value = None
        self.mock_repo.insert_one.side_effect = [e._id for e in entities]

        df = self._helper_load_cleaned_datafile()
        original_cols = set(df.columns)

        #all df edits should be made inplace
        resp = self.uc._find_or_upload_pbas(data_file=df)
        self.assertIsInstance(resp, ResponseSuccess)

        result_cols = set(df.columns)
        self.assertEqual(result_cols - original_cols, {"pba_id"})
        self.assertListEqual(list(df["pba_id"].unique()), [e._id for e in
                                                        entities])
        '''
        calls = [mock.call.find_pba_id(part_number='K31123-001',
                                      project='Mentor Harbor'),
                 mock.call.find_pba_id(part_number='K31123-003',
        project='Mentor Harbor')]
        self.mock_repo.assert_has_calls(calls, any_order=True)
        '''
        self.mock_repo.find_pba_id.assert_called()
        self.mock_repo.insert_one.assert_called()
        #self.mock_repo.insert_one.assert_called_with()

    def test_find_or_upload_reworks(self):
        entities = self.create_fake_rework_entities(2)


        self.mock_repo.find_rework_id.return_value = None
        self.mock_repo.insert_one.side_effect = [e._id for e in entities]

        df = self._helper_load_cleaned_datafile()
        original_cols = set(df.columns)


        #all df edits should be made inplace
        resp = self.uc._find_or_upload_reworks(data_file=df)
        self.assertIsInstance(resp, ResponseSuccess)

        result_cols = set(df.columns)
        self.assertEqual(result_cols - original_cols, {"rework_id"})
        self.assertListEqual(list(df["rework_id"].unique()), [e._id for e in
                                                        entities])

        self.mock_repo.find_rework_id.assert_called()
        self.mock_repo.insert_one.assert_called()
        #self.mock_repo.insert_one.assert_called_with()

    def test_find_or_upload_submissions(self):
        entities = self.create_fake_submission_entities(8)

        self.mock_repo.find_submission_id.return_value = None
        self.mock_repo.insert_one.side_effect = [e._id for e in entities]


        df = self._helper_load_cleaned_datafile()
        original_cols = set(df.columns)
        #print(df.serial_number.unique())

        # all df edits should be made inplace
        resp = self.uc._find_or_upload_submissions(data_file=df)
        self.assertIsInstance(resp, ResponseSuccess)

        result_cols = set(df.columns)
        self.assertEqual(result_cols - original_cols, {"submission_id"})
        self.assertListEqual(list(df["submission_id"].unique()), [e._id for e in
                                                              entities])

        self.mock_repo.find_submission_id.assert_called()
        self.mock_repo.insert_one.assert_called()
        # self.mock_repo.insert_one.assert_called_with()


    def test_find_or_upload_runids(self):
        entities = self.create_fake_runid_entities(15)

        self.mock_repo.find_run_id.return_value = None
        self.mock_repo.insert_one.side_effect = [e._id for e in entities]


        df = self._helper_load_cleaned_datafile()
        original_cols = set(df.columns)
        print(df.runid.nunique())

        # all df edits should be made inplace
        resp = self.uc._find_or_upload_runids(data_file=df)
        self.assertIsInstance(resp, ResponseSuccess)

        result_cols = set(df.columns)
        self.assertEqual(result_cols - original_cols, {"run_id"})
        self.assertListEqual(sorted(list(df["run_id"].unique())),
                             sorted([e._id for e in entities]))

        self.mock_repo.find_run_id.assert_called()
        self.mock_repo.insert_one.assert_called()
        # self.mock_repo.insert_one.assert_called_with()


    def test_find_or_upload_automation_tests(self):
        entities = self.create_fake_automation_test_entities(1)

        self.mock_repo.find_automation_test_id.return_value = None
        self.mock_repo.insert_one.side_effect = [e._id for e in entities]


        df = self._helper_load_cleaned_datafile()
        original_cols = set(df.columns)
        print(df.test_category.nunique())

        # all df edits should be made inplace
        _ = self.uc._find_or_upload_automation_test(data_file=df)

        result_cols = set(df.columns)
        self.assertEqual(result_cols - original_cols, {"automation_test_id"})
        self.assertListEqual(sorted(list(df["automation_test_id"].unique())),
                             sorted([e._id for e in entities]))

        self.mock_repo.find_automation_test_id.assert_called_once()
        self.mock_repo.insert_one.assert_called_once()
        # self.mock_repo.insert_one.assert_called_with()

    def test_find_or_upload_captures(self):
        entities = self.create_fake_waveform_capture_entities(94)

        self.mock_repo.find_waveform_capture_id.return_value = None
        self.mock_repo.insert_one.side_effect = [e._id for e in entities]


        df = self._helper_load_cleaned_datafile()
        original_cols = set(df.columns)

        # all df edits should be made inplace
        _ = self.uc._find_or_upload_captures(data_file=df)

        result_cols = set(df.columns)
        self.assertEqual(result_cols - original_cols, {"datacapture_id"})
        #print(sorted(df['datacapture_id'].unique()))

        self.assertListEqual(sorted(list(df["datacapture_id"].unique())),
                             sorted([e._id for e in entities]))

        self.mock_repo.find_waveform_capture_id.assert_called()
        self.mock_repo.insert_one.assert_called()
        # self.mock_repo.insert_one.assert_called_with()