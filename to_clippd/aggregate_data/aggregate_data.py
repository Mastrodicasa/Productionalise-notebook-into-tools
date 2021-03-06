import pandas as pd


class AggregateData(object):
    """
    Takes 3 data (rounds_data, terrain_data, course_info) and aggregates the data into one dataframe.

    Attributes:
        numeric_features (array): All the columns that should have numerical values
        time_features (array): All the columns that should have datetime values
        boolean_map (dict): Dict mapping string representation of booleans and pythonic booleans
        boolean_map (array): All the columns that should have boolean values
    """

    def __init__(self):
        self.numeric_features = ["shot_shotId", "shot_clubType", "shot_clubId", "shot_startLat", "shot_startLong",
                                 "shot_endLat", "shot_endLong", "shot_distance", "shot_startAltitude",
                                 "shot_endAltitude", "shot_noOfPenalties", "hole_noOfShots", "hole_pinLat",
                                 "hole_pinLong", "hole_putts", "hole_holeId", "hole_approachShotId", "roundId"]
        self.time_features = ["shot_shotTime", "hole_startTime", "hole_endTime", "round_startTime", "round_endTime"]
        self.boolean_map = {"T": True, "F": False, 1: True, 0: False, "None": None}
        self.boolean_features = ["shot_isHalfSwing", "shot_shouldIgnore", "shot_isSandUser",
                                 "shot_isNonSandUser", "shot_shouldConsiderPuttAsChip", "hole_isFairWayRight",
                                 "hole_isFairWayLeft", "hole_scoreOverride", "hole_isSandSave",
                                 "hole_isUpDown", "hole_isFairWayRightUser", "hole_isFairWayUser",
                                 "hole_isFairWayLeftUser", "hole_isGir", "hole_isFairWay",
                                 "hole_isSandSaveChance"]

    def __standardize_values(self, hole_info):
        """
        Makes sure the values in the dataframe are either numeric, datetime or boolean.

        Args:
            hole_info (dataframe): Dataframe that has all the columns from self.numeric_features, self.time_features and
                       self.boolean_features combined.
        Returns:
            hole_info (dataframe): All the columns cited above are now either numbers, datetime or booleans.
        """
        # Convert numeric features to float/int.
        for i in self.numeric_features:
            hole_info[i] = pd.to_numeric(hole_info[i])

        # Convert time features to datetime.
        for i in self.time_features:
            hole_info[i] = pd.to_datetime(hole_info[i])

        # Convert boolean features.
        hole_info[self.boolean_features] = hole_info[self.boolean_features].replace(self.boolean_map)
        return hole_info

    def __create_hole_info(self, rounds_data):
        """
        Converts rounds_data into a dataframe.

        Args:
            rounds_data (array): Array containing the data from rounds

        Returns:
            (dataframe) The json structure is flatten out. Values are standardized.
        """
        ## Convert hole_info to dataframe.
        appended_data = []
        for item in rounds_data:
            key_list = list(item["holes"][0].keys())
            key_list = list(set(key_list) - set(["shots"]))
            shot_data = pd.json_normalize(item["holes"],
                                          "shots",
                                          key_list,
                                          record_prefix="shot_",
                                          meta_prefix="hole_")
            shot_data["roundId"] = item["roundId"]
            appended_data.append(shot_data)

        hole_info = pd.concat(appended_data)

        # Convert round info to dataframe.
        round_info = pd.DataFrame(rounds_data)
        round_info.columns = ["round_" + column for column in round_info.columns]

        # Merge hole and round info and drop round_holes column.
        hole_info = hole_info.merge(round_info,
                                    left_on=["roundId"],
                                    right_on=["round_roundId"])
        hole_info.drop(columns=["round_holes"], inplace=True)

        return self.__standardize_values(hole_info)

    @staticmethod
    def __create_hole_info_terrain(terrain_data):
        """
        Converts terrain_data into a dataframe.

        Args:
            terrain_data (array): Array containing the data from terrain

        Returns:
            (dataframe) The json structure is flatten out.
        """
        # Convert hole_info to dataframe.
        appended_data = []
        for item in terrain_data:
            key_list = list(item["holes"][0].keys())
            key_list = list(set(key_list) - set(["drive", "approach", "chip", "sand"]))
            drive_data = pd.json_normalize(item["holes"],
                                           "drive",
                                           key_list,
                                           record_prefix="shot_",
                                           meta_prefix="hole_")
            approach_data = pd.json_normalize(item["holes"],
                                              "approach",
                                              key_list,
                                              record_prefix="shot_",
                                              meta_prefix="hole_")
            chip_data = pd.json_normalize(item["holes"],
                                          "chip",
                                          key_list,
                                          record_prefix="shot_",
                                          meta_prefix="hole_")
            sand_data = pd.json_normalize(item["holes"],
                                          "sand",
                                          key_list,
                                          record_prefix="shot_",
                                          meta_prefix="hole_")
            shot_data = pd.concat([drive_data, approach_data, chip_data, sand_data], axis=0)
            shot_data["roundId"] = item["roundId"]
            appended_data.append(shot_data)
        return pd.concat(appended_data)

    def process(self, rounds_data, terrain_data, course_info):
        """
        Takes 3 inputs, creates dataframe for each of them and returns a dataframe that is a combination of the three.

        Args:
            rounds_data
            terrain_data
            course_info

        Returns:
            None if one of the args is None
            (dataframe) One dataframe that has merged all the relevant columns
        """
        if None in [rounds_data, terrain_data, course_info]:
            return None

        # Create courses dataframe.
        course_info = pd.json_normalize(course_info, "courses")

        # Create shot dataframe.
        hole_info = self.__create_hole_info(rounds_data)

        # Add course name.
        course_name = course_info[["name", "courseId"]].drop_duplicates()
        hole_info = hole_info.merge(course_name,
                                    how="left",
                                    left_on=["round_courseId"],
                                    right_on=["courseId"])

        # Create shot dataframe with terrain data.
        hole_info_terrain = self.__create_hole_info_terrain(terrain_data)

        # Merge terrain data with shot data.
        hole_info = hole_info.merge(
            hole_info_terrain[["roundId", "hole_holeId", "shot_shotId",
                               "hole_par", "shot_startDistanceToCG",
                               "shot_startTerrain", "shot_endTerrain"]],
            how="left",
            left_on=["roundId", "hole_holeId", "shot_shotId"],
            right_on=["roundId", "hole_holeId", "shot_shotId"])

        # Sort data by player, date, round Id, hole Id and shot number.
        hole_info.sort_values(by=["round_userId", "round_startTime", "roundId", "hole_holeId", "shot_shotId"],
                              inplace=True)

        return hole_info
