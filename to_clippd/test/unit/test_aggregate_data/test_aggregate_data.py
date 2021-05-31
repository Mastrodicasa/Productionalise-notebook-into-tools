import json
import unittest

import numpy as np
import pandas as pd
from aggregate_data import AggregateData

PATH_ROUNDS_JSON = "test/unit/test_aggregate_data/round.json"
PATH_TERRAIN_JSON = "test/unit/test_aggregate_data/terrain.json"
PATH_COURSE_JSON = "test/unit/test_aggregate_data/2020-12-03T12_20_14.080Z.json"


class MyTestCase(unittest.TestCase):

    def test_standardize_values(self):
        ad = AggregateData()
        # Create a dataframe with all the columns that are subject to change.
        # Create the columns
        columns_numeric = ad.numeric_features
        columns_time = ad.time_features
        columns_boolean = ad.boolean_features
        all_columns = columns_numeric + columns_time + columns_boolean

        # Create the data
        data = ["1.0" for column in columns_numeric]
        data.extend(["2020-12-17T12:09:12.338000Z" for column in columns_time])
        data.extend(["T" for column in columns_boolean])

        # Create the dataframe
        df = pd.DataFrame([data], columns=all_columns)
        # Standardize the values and check the results
        df = ad._AggregateData__standardize_values(df)
        for column in all_columns:
            if column in columns_numeric:
                self.assertIn(type(df[column].values[0]), [np.int64, np.float64], column + " should be a numeric")
            elif column in columns_time:
                self.assertEqual(type(df[column].values[0]), np.datetime64, column + " should be a datetime")
            else:
                self.assertEqual(type(df[column].values[0]), np.bool_, column + " should be a boolean")

    def test_create_hole_info(self):
        # Read a round json file and run create_hole_info
        with open(PATH_ROUNDS_JSON) as f:
            rounds_data = [json.load(f)]
        ad = AggregateData()
        hole_info = ad._AggregateData__create_hole_info(rounds_data)

        # Check if the output is a dataframe and its values are standardized
        # Get all the columns to check
        columns_numeric = ad.numeric_features
        columns_time = ad.time_features
        columns_boolean = ad.boolean_features
        all_columns = columns_numeric + columns_time + columns_boolean
        for column in all_columns:
            # Some fields are None
            if hole_info[column].values[0] is not None:
                if column in columns_numeric:
                    self.assertIn(type(hole_info[column].values[0]), [np.int64, np.float64],
                                  column + "should be a numeric")
                elif column in columns_time:
                    self.assertEqual(type(hole_info[column].values[0]), np.datetime64, column + " should be a datetime")
                else:
                    self.assertEqual(type(hole_info[column].values[0]), np.bool_, column + " should be a boolean")

    def test_create_hole_info_terrain(self):
        # Those should be the columns of a hole_info_terrain_columns dataframe
        hole_info_terrain_columns = ['shot_holeId', 'shot_shotId', 'shot_clubType', 'shot_noOfPenalties',
                                     'shot_isFairWay', 'shot_isFairWayRight', 'shot_isFairWayLeft',
                                     'shot_isRecoveryShot', 'shot_strokesGained', 'shot_startDistanceToCG',
                                     'shot_endDistanceToCG', 'shot_startTerrain', 'shot_endTerrain',
                                     'shot_distance', 'shot_distanceFromFairWayBounds', 'shot_clubId',
                                     'shot_shouldIgnore', 'shot_needsRecovery', 'shot_isFpOrMissedShot',
                                     'shot_surrogateKey', 'shot_isLeft', 'shot_isRight',
                                     'shot_distanceFromCenterLine', 'hole_noOfShots',
                                     'hole_noOfDrivePlusOnePenalties', 'hole_isUpDownChance',
                                     'hole_approachStrokesGained', 'hole_noOfSandShots', 'hole_isGir',
                                     'hole_noOfPuttPlusOnePenalties', 'hole_chipStrokesGained',
                                     'hole_noOfPutts', 'hole_isUpDown', 'hole_noOfApproachPlusTwoPenalties',
                                     'hole_noOfChipErrors', 'hole_noOfApproachPlusOnePenalties',
                                     'hole_isSandSave', 'hole_puttStrokesGained', 'hole_isFairWay',
                                     'hole_sandStrokesGained', 'hole_noOfChipPlusOnePenalties',
                                     'hole_noOfChipPlusTwoPenalties', 'hole_endTime', 'hole_noOfDrives',
                                     'hole_isSandSaveChance', 'hole_startTime', 'hole_isFairWayLeft',
                                     'hole_noOfSandPlusOnePenalties', 'hole_holeId',
                                     'hole_noOfRecoveryShots', 'hole_adjustedScore',
                                     'hole_driveStrokesGained', 'hole_noOfPuttPlusTwoPenalties',
                                     'hole_isFairWayRight', 'hole_noOfApproachShots', 'hole_par',
                                     'hole_noOfSandPlusTwoPenalties', 'hole_noOfDrivePlusTwoPenalties',
                                     'hole_noOfSandErrors', 'hole_noOfChips', 'shot_noOfPutts',
                                     'shot_strokesToGetDown', 'shot_angle', 'shot_isApproach',
                                     'shot_isLayUp', 'shot_isUpDownChance', 'shot_isUpDown',
                                     'shot_isSandSaveChance', 'shot_isSandSave', 'roundId']
        # Read a round json file and run create_hole_info
        with open(PATH_TERRAIN_JSON) as f:
            terrain_data = [json.load(f)]
        ad = AggregateData()
        df_terrain = ad._AggregateData__create_hole_info_terrain(terrain_data)
        # Check if all the columns exist in the new dataframe
        for column in hole_info_terrain_columns:
            self.assertIn(column, df_terrain.columns, column + " should exist in the dataframe")

    def test_process_if_None_input(self):
        ad = AggregateData()
        df_hole = ad.process(None, None, None)
        self.assertEqual(df_hole, None, "When one input is None, AggregateData().process() should return None")

    def test_process_check_output(self):
        # Those should be the columns of a hole_info dataframe
        hole_info_columns = ['shot_shotId', 'shot_clubType', 'shot_clubId', 'shot_startLat',
                             'shot_startLong', 'shot_endLat', 'shot_endLong', 'shot_distance',
                             'shot_isHalfSwing', 'shot_startAltitude', 'shot_endAltitude',
                             'shot_shotTime', 'shot_shouldIgnore', 'shot_noOfPenalties',
                             'shot_isSandUser', 'shot_isNonSandUser',
                             'shot_shouldConsiderPuttAsChip', 'shot_userStartTerrainOverride',
                             'hole_noOfShots', 'hole_isSandSaveChance', 'hole_approachShotId',
                             'hole_isUpDownChance', 'hole_startTime', 'hole_putts',
                             'hole_isFairWayLeft', 'hole_holeId', 'hole_pinLong',
                             'hole_isFairWayUser', 'hole_shouldIgnore', 'hole_isUpDown',
                             'hole_isFairWayRight', 'hole_isFairWayRightUser',
                             'hole_isFairWayLeftUser', 'hole_isSandSave', 'hole_pinLat',
                             'hole_scoreOverride', 'hole_isFairWay', 'hole_endTime', 'hole_isGir',
                             'roundId', 'round_roundId', 'round_roundVersion', 'round_courseId',
                             'round_userId', 'round_startTime', 'round_endTime', 'round_noOfHoles',
                             'round_noOfShots', 'round_shouldIgnore', 'round_teeId',
                             'round_isPrivate', 'round_isVerified', 'round_isEnded',
                             'round_isDriverRound', 'round_courseVersion', 'round_lastModifiedTime',
                             'round_noOfHolesOverride', 'round_scoreOverride', 'name', 'courseId',
                             'hole_par', 'shot_startDistanceToCG', 'shot_startTerrain', 'shot_endTerrain']
        # Read in json files as dictionaries.
        with open(PATH_ROUNDS_JSON) as f:
            rounds_data = [json.load(f)]
        with open(PATH_TERRAIN_JSON) as f:
            terrain_data = [json.load(f)]
        with open(PATH_COURSE_JSON) as f:
            course_info = json.load(f)
        ad = AggregateData()
        df_hole = ad.process(rounds_data, terrain_data, course_info)
        # Check if all the columns exist in the new dataframe
        for column in hole_info_columns:
            self.assertIn(column, df_hole.columns, column + " should exist in the dataframe")


if __name__ == '__main__':
    unittest.main()
