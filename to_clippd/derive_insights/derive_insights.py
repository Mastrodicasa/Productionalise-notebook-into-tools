import os

import derive_insights.shot_misses as shot_misses
import derive_insights.stroke_gained as stroke_gained
import numpy as np
import pandas as pd
import seaborn as sns
from geopy import distance
from scipy.interpolate import interp1d
from scipy.stats import zscore

# get the location of this script so we can read in local files
# otherwise we have problems were we can"t find the files
# as python will look in cwd instead of this directory
try:
    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__))
    )
except Exception:
    __location__ = ""


class DeriveInsights(object):
    """
    Derives additional insights from existing values of a dataframe.

    Attributes:
        lie_dict: Used to convert to Clippd lie names
        tee_app_arg: This is PGA Benchmark
        put: This PGA putting benchmark
        expected_shots_functions: Dict of all the interpolation functions
    """

    def __init__(self):
        self.lie_dict = {"tee": "Tee", "fairway": "Fairway", "rough": "Rough",
                         "sand": "Sand", "green": "Green", "Green": "Green",
                         "In The Hole": "In The Hole"}
        # Import PGA benchmark
        self.tee_app_arg = pd.read_csv(os.path.join(__location__, "PGA Benchmark.csv"))
        self.put = pd.read_csv(os.path.join(__location__, "PGA Putting Benchmark.csv"))
        self.put["Distance"] = self.put["Distance (feet)"] / 3

        # Set up interpolation functions.
        expected_shots_tee = interp1d(self.tee_app_arg[["Distance", "Tee"]].dropna()["Distance"],
                                      self.tee_app_arg[["Distance", "Tee"]].dropna()["Tee"],
                                      kind="linear",
                                      fill_value="extrapolation")
        expected_shots_fairway = interp1d(self.tee_app_arg[["Distance", "Fairway"]].dropna()["Distance"],
                                          self.tee_app_arg[["Distance", "Fairway"]].dropna()["Fairway"],
                                          kind="linear",
                                          fill_value="extrapolation")
        expected_shots_rough = interp1d(self.tee_app_arg[["Distance", "Rough"]].dropna()["Distance"],
                                        self.tee_app_arg[["Distance", "Rough"]].dropna()["Rough"],
                                        kind="linear",
                                        fill_value="extrapolation")
        expected_shots_sand = interp1d(self.tee_app_arg[["Distance", "Sand"]].dropna()["Distance"],
                                       self.tee_app_arg[["Distance", "Sand"]].dropna()["Sand"],
                                       kind="linear",
                                       fill_value="extrapolation")
        expected_shots_green = interp1d(self.put["Distance"], self.put["Expected putts"], kind="linear")

        self.expected_shots_functions = {
            "expected_shots_tee": expected_shots_tee,
            "expected_shots_fairway": expected_shots_fairway,
            "expected_shots_rough": expected_shots_rough,
            "expected_shots_sand": expected_shots_sand,
            "expected_shots_green": expected_shots_green
        }

    def __deduct_shot_values(self, data):
        """
        Deducts the values of the shots: In the Hole, Green. Convert to Clippd Lie names

        Args:
            data: Dataframe containing shots data
        Returns:
            (dataframe) with "shot_endTerrain" and "shot_endTerrain" updated
        """
        # Fill last shot with "In The Hole".
        data["shot_endTerrain"] = np.where(data["shot_shotId"] == data["hole_noOfShots"],
                                           "In The Hole",
                                           data["shot_endTerrain"])

        # Fill NaNs with "Green".
        data["shot_startTerrain"] = data["shot_startTerrain"].fillna("Green")
        data["shot_endTerrain"] = data["shot_endTerrain"].fillna("Green")

        # Convert to Clippd lie names.
        data["shot_startTerrain"] = data["shot_startTerrain"].map(self.lie_dict)
        data["shot_endTerrain"] = data["shot_endTerrain"].map(self.lie_dict)
        return data

    @staticmethod
    def __calculate_shot_distance(data):
        """
        Calculates the distance using the using start and end coordinates.
        Args:
            data: Dataframe containing shots data
        Returns:
            (dataframe) returned with the distances calculated
        """
        # Calculate starting distance for each shot.
        data["start_coordinates"] = list(zip(data["shot_startLat"],
                                             data["shot_startLong"]))
        data["pin_coordinates"] = list(zip(data["hole_pinLat"],
                                           data["hole_pinLong"]))

        # I wanted to changed it with a function that can take numpy arrays directly,
        # but because the results were slightly different I only vectorized the function.
        vect_distance = np.vectorize(distance.distance)
        result = vect_distance(data["start_coordinates"], data["pin_coordinates"])
        data["shot_start_distance_yards"] = [obj.ft / 3 for obj in result]

        # Fill NaNs in end latitudes and longitudes and create end_coordinates column.
        data["shot_endLat"].fillna(data["hole_pinLat"], inplace=True)
        data["shot_endLong"].fillna(data["hole_pinLong"], inplace=True)
        data["end_coordinates"] = list(zip(data["shot_endLat"],
                                           data["shot_endLong"]))

        # Calculate shot distance in yards using start and end coordinates.
        result = vect_distance(data["start_coordinates"], data["end_coordinates"])
        data["shot_distance_yards_calculated"] = [obj.ft / 3 for obj in result]

        # Calculate end distance for each shot.
        result = vect_distance(data["end_coordinates"], data["pin_coordinates"])
        data["shot_end_distance_yards"] = [obj.ft / 3 for obj in result]
        data["shot_end_distance_yards"].fillna(0, inplace=True)

        # Take hole length as the distance to CG for first shot.
        data["hole_yards"] = np.where(data["shot_shotId"] == 1,
                                      data["shot_startDistanceToCG"],
                                      np.nan)
        data["hole_yards"].ffill(inplace=True)
        data["hole_yards"] = pd.to_numeric(data["hole_yards"])
        return data

    @staticmethod
    def __impute_shot_type(data):
        """
        Impute shot type and shot sub_type.

        Args:
            data: Dataframe containing shots data
        Returns:
            (dataframe) returned with the imputed shot type and sub_type
        """
        conditions = [(data["shot_startTerrain"] == "Tee") & (data["hole_par"] != 3),
                      (data["shot_start_distance_yards"] <= 30) & (data["shot_startTerrain"] != "Green"),
                      (data["shot_startTerrain"] == "Green")]
        values = ["TeeShot", "GreensideShot", "Putt"]
        data["shot_type"] = np.select(conditions, values, default="ApproachShot")

        # Calculate z-scores for shot distance and start distance and by club and shot type.

        data["shot_distance_yards_zscore"] = (data.groupby(["round_userId", "shot_type", "shot_clubType"])
                                              ["shot_distance_yards_calculated"].transform(zscore, ddof=1)).fillna(0)
        data["shot_start_distance_yards_zscore"] = (data.groupby(["round_userId", "shot_type", "shot_clubType"])
                                                    ["shot_start_distance_yards"].transform(zscore, ddof=1)).fillna(0)

        # Impute shot subtype.
        conditions = [data["shot_type"] == "TeeShot",
                      (data["shot_type"] == "ApproachShot") & (data["shot_distance_yards_zscore"] <= -1) & (data["shot_end_distance_yards"] > 30) & (data["shot_endTerrain"] != "Fairway"),
                      (data["shot_type"] == "ApproachShot") & (data["shot_distance_yards_zscore"] > -1) & (data["shot_start_distance_yards_zscore"] > 1) & (data["shot_end_distance_yards"] > 30),
                      data["shot_type"] == "GreensideShot",
                      data["shot_type"] == "Putt"]
        values = ["TeeShot", "Recovery", "LayUp", "GreensideShot", "Putt"]
        data["shot_subtype"] = np.select(conditions, values, default="GoingForGreen")
        return data

    def plot_shot_subtypes(self, data):
        """Plot the subtypes plot to check the shot subtype logic"""
        self.__impute_shot_type(data)
        # Check shot subtype logic.
        sns.jointplot(data=data[data["shot_type"] == "ApproachShot"],
                      x="shot_start_distance_yards_zscore",
                      y="shot_distance_yards_zscore",
                      hue="shot_subtype",
                      height=6)
        sns.jointplot(data=data[data["shot_type"] == "ApproachShot"],
                      x="shot_start_distance_yards_zscore",
                      y="shot_end_distance_yards",
                      hue="shot_subtype",
                      height=6)

    @staticmethod
    def __calculate_shot_miss_directions_and_distances(data):
        """
        Determine shot miss directions and distances using coordinates and indicators.

        Args:
            data: Dataframe containing shots data
        Returns:
            (dataframe) returned with the miss direction and the miss distance
        """
        # Determine miss direction.
        data["start_to_end_bearing"] = shot_misses.get_bearing(data["start_coordinates"].str[0].values,
                                                               data["start_coordinates"].str[1].values,
                                                               data["end_coordinates"].str[0].values,
                                                               data["end_coordinates"].str[1].values)
        data["start_to_pin_bearing"] = shot_misses.get_bearing(data["start_coordinates"].str[0].values,
                                                               data["start_coordinates"].str[1].values,
                                                               data["pin_coordinates"].str[0].values,
                                                               data["pin_coordinates"].str[1].values)
        data["miss_bearing_left_right"] = data["start_to_end_bearing"] - data[
            "start_to_pin_bearing"]
        data["miss_bearing_left_right"] = np.where(data["miss_bearing_left_right"] < 0,
                                                   data["miss_bearing_left_right"] + 360,
                                                   data["miss_bearing_left_right"])

        # Determine miss distances.
        data["end_to_pin_bearing"] = shot_misses.get_bearing(data["end_coordinates"].str[0].values,
                                                             data["end_coordinates"].str[1].values,
                                                             data["pin_coordinates"].str[0].values,
                                                             data["pin_coordinates"].str[1].values)
        data["start_end_pin_angle"] = shot_misses.calculate_start_end_pin_angle(
            data["shot_distance_yards_calculated"],
            data["shot_start_distance_yards"],
            data["shot_end_distance_yards"])
        [data["shot_miss_distance_left_right"],
         data["shot_miss_distance_short_long"]] = shot_misses.calculate_miss_distance(data["miss_bearing_left_right"],
                                                                                      data["start_end_pin_angle"],
                                                                                      data["shot_end_distance_yards"])

        # Impute left/right and short_long miss directions for approach shots.
        conditions = [(data["shot_type"] == "ApproachShot") & (data["hole_isGir"] is False) & (data["shot_miss_distance_left_right"] < 0),
                      (data["shot_type"] == "ApproachShot") & (data["hole_isGir"] is False) & (data["shot_miss_distance_left_right"] > 0)]
        values = ["Left", "Right"]
        data["shot_miss_direction_left_right"] = np.select(conditions, values, default=np.nan)
        conditions = [(data["shot_type"] == "ApproachShot") & (data["hole_isGir"] is False) & (data["shot_miss_distance_short_long"] < 0),
                      (data["shot_type"] == "ApproachShot") & (data["hole_isGir"] is False) & (data["shot_miss_distance_short_long"] > 0)]
        values = ["Short", "Long"]
        data["shot_miss_direction_short_long"] = np.select(conditions, values, default=np.nan)

        # Use miss distance information to impute miss_direction.
        conditions = [(data["shot_type"] == "TeeShot") & (data["hole_isFairWayRight"] is True),
                      (data["shot_type"] == "TeeShot") & (data["hole_isFairWayLeft"] is True),
                      (data["shot_type"] == "ApproachShot") & (data["hole_isGir"] is False)]
        values = ["Right",
                  "Left",
                  (data["shot_miss_direction_short_long"]
                   + " "
                   + data["shot_miss_direction_left_right"])]
        data["shot_miss_direction_all_shots"] = np.select(conditions, values, default=np.nan)
        return data

    def process(self, data):
        """
        Takes a dataframe with all the basic information, and derive insights from them.

        The insights are:
        - Shot values
        - Shot distance
        - Shot type
        - Shot miss directions and distances

        Args:
            data: Dataframe containing shots data

        Returns:
            None if data is None
            (dataframe) With all the derived insights
        """
        if data is None:
            return None

        data = self.__deduct_shot_values(data)
        data = self.__calculate_shot_distance(data)
        data = self.__impute_shot_type(data)
        data = self.__calculate_shot_miss_directions_and_distances(data)

        # Strokes gained using PGA benchmark.

        # Impute next shot number.
        data.sort_values(by=["round_userId", "round_startTime", "roundId", "hole_holeId", "shot_shotId"],
                         inplace=True)
        data["next_shot_shotId"] = data.groupby(["round_userId",
                                                 "round_startTime",
                                                 "roundId",
                                                 "hole_holeId"])["shot_shotId"].shift(-1)

        # Calculate strokes gained.
        vect_func = np.vectorize(stroke_gained.strokes_gained_calculation)
        data["strokes_gained_calculated"] = vect_func(data["shot_startTerrain"],
                                                      data["shot_start_distance_yards"],
                                                      data["shot_endTerrain"],
                                                      data["shot_end_distance_yards"],
                                                      data["shot_shotId"],
                                                      data["next_shot_shotId"],
                                                      stroke_gained.expected_shots,
                                                      self.expected_shots_functions)

        return data
