import unittest

import numpy as np
import pandas as pd
from derive_insights import DeriveInsights

PATH_DATA_PICKLE = "test/unit/test_derive_insights/arccos_data.pkl"


class MyTestCase(unittest.TestCase):
    def test_deduct_shot_values(self):
        # Create toy dataframe
        columns = 'shot_shotId', 'hole_noOfShots', 'shot_endTerrain', 'shot_startTerrain'
        toy = [[3, 3, "fairway", "fairway"],
               [1, 2, "rough", np.nan]]
        toy_df = pd.DataFrame(toy, columns=columns)
        di = DeriveInsights()
        output = di._DeriveInsights__deduct_shot_values(toy_df)
        # Check if t
        self.assertEqual(output.iloc[0]["shot_endTerrain"], "In The Hole", "shot_endTerrain should change when " \
                                                                           "shot_shotId and hole_noOfShots are equal")
        self.assertEqual(output.iloc[0]["shot_startTerrain"], "Fairway", "fairway should change to Fairway")
        self.assertEqual(output.iloc[1]["shot_startTerrain"], "Green", "NaN should be replaced by Green")

    def test_calculate_shot_distance(self):
        df = pd.read_pickle(PATH_DATA_PICKLE)
        di = DeriveInsights()
        output = di._DeriveInsights__calculate_shot_distance(df)
        self.assertEqual(output.iloc[0]['shot_start_distance_yards'], 478.16731911812394, "Expected results with "
                                                                                          "those 2 "
                                                                                          "points (52.166022757016, "
                                                                                          "0.166272406133), "
                                                                                          "(52.165891736696, "
                                                                                          "0.172658975318)")

    def test_impute_shot_type(self):
        df = pd.read_pickle(PATH_DATA_PICKLE)
        di = DeriveInsights()
        df = di._DeriveInsights__calculate_shot_distance(df)
        output = di._DeriveInsights__impute_shot_type(df)
        self.assertEqual(output.iloc[0]["shot_type"], "ApproachShot")
        self.assertEqual(output.iloc[0]["shot_subtype"], "LayUp")


if __name__ == '__main__':
    unittest.main()
