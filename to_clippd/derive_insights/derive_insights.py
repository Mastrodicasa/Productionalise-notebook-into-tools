import numpy as np
import pandas as pd

from scipy.stats import zscore
from geopy import distance
import seaborn as sns
from scipy.interpolate import interp1d
import derive_insights.shot_misses as shot_misses
import os

# get the location of this script so we can read in local files
# otherwise we have problems were we can't find the files
# as python will look in cwd instead of this directory
try:
    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__))
    )
except:
    __location__ = ''


class DeriveInsights(object):

    def __init__(self):
        self.lie_dict = {'tee': 'Tee', 'fairway': 'Fairway', 'rough': 'Rough',
                         'sand': 'Sand', 'green': 'Green', 'Green': 'Green',
                         'In The Hole': 'In The Hole'}
        # Import PGA benchmark
        self.tee_app_arg = pd.read_csv(os.path.join(__location__, 'PGA Benchmark.csv'))
        self.put = pd.read_csv(os.path.join(__location__, 'PGA Putting Benchmark.csv'))

    def standardize_values(self, data):
        # Fill last shot with 'In The Hole'.
        data['shot_endTerrain'] = np.where(data['shot_shotId'] == data['hole_noOfShots'],
                                           'In The Hole',
                                           data['shot_endTerrain'])

        # Fill NaNs with 'Green'.
        data['shot_startTerrain'] = data['shot_startTerrain'].fillna('Green')
        data['shot_endTerrain'] = data['shot_endTerrain'].fillna('Green')

        # Convert to Clippd lie names.
        data['shot_startTerrain'] = data['shot_startTerrain'].map(self.lie_dict)
        data['shot_endTerrain'] = data['shot_endTerrain'].map(self.lie_dict)
        return data

    def calculate_distances(self, data):
        # Calculate starting distance for each shot.
        data['start_coordinates'] = list(zip(data['shot_startLat'],
                                             data['shot_startLong']))
        data['pin_coordinates'] = list(zip(data['hole_pinLat'],
                                           data['hole_pinLong']))
        data['shot_start_distance_yards'] = data.apply(
            lambda row: distance.distance(row['start_coordinates'], row['pin_coordinates']).ft / 3, axis=1)

        # Fill NaNs in end latitudes and longitudes and create end_coordinates column.
        data['shot_endLat'].fillna(data['hole_pinLat'], inplace=True)
        data['shot_endLong'].fillna(data['hole_pinLong'], inplace=True)
        data['end_coordinates'] = list(zip(data['shot_endLat'],
                                           data['shot_endLong']))

        # # Impute end_coordinates from next shot's start_coordinates.
        # data['end_coordinates'] = data.groupby(['round_userId',
        #                                                       'round_startTime',
        #                                                       'roundId',
        #                                                       'hole_holeId'])['start_coordinates'].shift(-1)
        # data['end_coordinates'].fillna(data['pin_coordinates'], inplace=True)

        # Calculate shot distance in yards using start and end coordinates.
        data['shot_distance_yards_calculated'] = data.apply(
            lambda row: distance.distance(row['start_coordinates'], row['end_coordinates']).ft / 3, axis=1)

        # Calculate end distance for each shot.
        data['shot_end_distance_yards'] = data.apply(
            lambda row: distance.distance(row['end_coordinates'], row['pin_coordinates']).ft / 3, axis=1)
        data['shot_end_distance_yards'].fillna(0, inplace=True)

        # Take hole length as the distance to CG for first shot.
        data['hole_yards'] = np.where(data['shot_shotId'] == 1,
                                      data['shot_startDistanceToCG'],
                                      np.nan)
        data['hole_yards'].ffill(inplace=True)
        data['hole_yards'] = pd.to_numeric(data['hole_yards'])
        return data

    def impute_shot_type(self, data):
        # Impute shot type.
        conditions = [(data['shot_startTerrain'] == 'Tee') & (data['hole_par'] != 3),
                      (data['shot_start_distance_yards'] <= 30) & (data['shot_startTerrain'] != 'Green'),
                      (data['shot_startTerrain'] == 'Green')]
        values = ['TeeShot', 'GreensideShot', 'Putt']
        data['shot_type'] = np.select(conditions, values, default='ApproachShot')

        # Calculate z-scores for shot distance and start distance and by club and shot type.
        data['shot_distance_yards_zscore'] = (data.groupby(['round_userId',
                                                            'shot_type',
                                                            'shot_clubType'])[
                                                  'shot_distance_yards_calculated'] \
                                              .transform(lambda x: zscore(x, ddof=1))).fillna(0)
        data['shot_start_distance_yards_zscore'] = (data.groupby(['round_userId',
                                                                  'shot_type',
                                                                  'shot_clubType'])[
                                                        'shot_start_distance_yards'] \
                                                    .transform(lambda x: zscore(x, ddof=1))).fillna(0)

        # Impute shot subtype.
        conditions = [data['shot_type'] == 'TeeShot',
                      (data['shot_type'] == 'ApproachShot') & \
                      (data['shot_distance_yards_zscore'] <= -1) & \
                      (data['shot_end_distance_yards'] > 30) & \
                      (data['shot_endTerrain'] != 'Fairway'),
                      (data['shot_type'] == 'ApproachShot') & \
                      (data['shot_distance_yards_zscore'] > -1) & \
                      (data['shot_start_distance_yards_zscore'] > 1) & \
                      (data['shot_end_distance_yards'] > 30),
                      data['shot_type'] == 'GreensideShot',
                      data['shot_type'] == 'Putt']
        values = ['TeeShot', 'Recovery', 'LayUp', 'GreensideShot', 'Putt']
        data['shot_subtype'] = np.select(conditions, values, default='GoingForGreen')
        return data

    def plot_shot_subtypes(self, data):
        ## TODO self.impute_shot_type(data)
        # Check shot subtype logic.
        ax1 = sns.jointplot(data=data[data['shot_type'] == 'ApproachShot'],
                            x='shot_start_distance_yards_zscore',
                            y='shot_distance_yards_zscore',
                            hue='shot_subtype',
                            height=6)
        ax2 = sns.jointplot(data=data[data['shot_type'] == 'ApproachShot'],
                            x='shot_start_distance_yards_zscore',
                            y='shot_end_distance_yards',
                            hue='shot_subtype',
                            height=6)

    def calculate_shot_miss_directions_and_distances(self, data):
        # Determine shot miss directions and distances using coordinates and indicators.

        ## Determine miss direction.
        data['start_to_end_bearing'] = shot_misses.get_bearing(data['start_coordinates'].str[0].values,
                                                               data['start_coordinates'].str[1].values,
                                                               data['end_coordinates'].str[0].values,
                                                               data['end_coordinates'].str[1].values)
        data['start_to_pin_bearing'] = shot_misses.get_bearing(data['start_coordinates'].str[0].values,
                                                               data['start_coordinates'].str[1].values,
                                                               data['pin_coordinates'].str[0].values,
                                                               data['pin_coordinates'].str[1].values)
        data['miss_bearing_left_right'] = data['start_to_end_bearing'] - data[
            'start_to_pin_bearing']
        data['miss_bearing_left_right'] = np.where(data['miss_bearing_left_right'] < 0,
                                                   data['miss_bearing_left_right'] + 360,
                                                   data['miss_bearing_left_right'])

        ## Determine miss distances.
        data['end_to_pin_bearing'] = shot_misses.get_bearing(data['end_coordinates'].str[0].values,
                                                             data['end_coordinates'].str[1].values,
                                                             data['pin_coordinates'].str[0].values,
                                                             data['pin_coordinates'].str[1].values)
        data['start_end_pin_angle'] = shot_misses.calculate_start_end_pin_angle(
            data['shot_distance_yards_calculated'],
            data['shot_start_distance_yards'],
            data['shot_end_distance_yards'])
        [data['shot_miss_distance_left_right'],
         data['shot_miss_distance_short_long']] = shot_misses.calculate_miss_distance(data['miss_bearing_left_right'],
                                                                                      data['start_end_pin_angle'],
                                                                                      data['shot_end_distance_yards'])

        ## Impute left/right and short_long miss directions for approach shots.
        conditions = [(data['shot_type'] == 'ApproachShot') & (data['hole_isGir'] == False) & \
                      (data['shot_miss_distance_left_right'] < 0),
                      (data['shot_type'] == 'ApproachShot') & (data['hole_isGir'] == False) & \
                      (data['shot_miss_distance_left_right'] > 0)]
        values = ['Left', 'Right']
        data['shot_miss_direction_left_right'] = np.select(conditions, values, default=np.nan)
        conditions = [(data['shot_type'] == 'ApproachShot') & (data['hole_isGir'] == False) & \
                      (data['shot_miss_distance_short_long'] < 0),
                      (data['shot_type'] == 'ApproachShot') & (data['hole_isGir'] == False) & \
                      (data['shot_miss_distance_short_long'] > 0)]
        values = ['Short', 'Long']
        data['shot_miss_direction_short_long'] = np.select(conditions, values, default=np.nan)

        ## Use miss distance information to impute miss_direction.
        conditions = [(data['shot_type'] == 'TeeShot') & (data['hole_isFairWayRight'] == True),
                      (data['shot_type'] == 'TeeShot') & (data['hole_isFairWayLeft'] == True),
                      (data['shot_type'] == 'ApproachShot') & (data['hole_isGir'] == False)]
        values = ['Right',
                  'Left',
                  (data['shot_miss_direction_short_long']
                   + ' '
                   + data['shot_miss_direction_left_right'])]
        data['shot_miss_direction_all_shots'] = np.select(conditions, values, default=np.nan)
        return data

    def process(self, data):

        data = self.standardize_values(data)
        data = self.calculate_distances(data)
        data = self.impute_shot_type(data)
        data = self.calculate_shot_miss_directions_and_distances(data)

        self.put['Distance'] = self.put['Distance (feet)'] / 3

        ## Set up interpolation functions.
        expected_shots_tee = interp1d(self.tee_app_arg[['Distance', 'Tee']].dropna()['Distance'],
                                      self.tee_app_arg[['Distance', 'Tee']].dropna()['Tee'],
                                      kind='linear',
                                      fill_value='extrapolation')
        expected_shots_fairway = interp1d(self.tee_app_arg[['Distance', 'Fairway']].dropna()['Distance'],
                                          self.tee_app_arg[['Distance', 'Fairway']].dropna()['Fairway'],
                                          kind='linear',
                                          fill_value='extrapolation')
        expected_shots_rough = interp1d(self.tee_app_arg[['Distance', 'Rough']].dropna()['Distance'],
                                        self.tee_app_arg[['Distance', 'Rough']].dropna()['Rough'],
                                        kind='linear',
                                        fill_value='extrapolation')
        expected_shots_sand = interp1d(self.tee_app_arg[['Distance', 'Sand']].dropna()['Distance'],
                                       self.tee_app_arg[['Distance', 'Sand']].dropna()['Sand'],
                                       kind='linear',
                                       fill_value='extrapolation')
        expected_shots_green = interp1d(self.put['Distance'], self.put['Expected putts'], kind='linear')

        ## Define functions.
        def expected_shots(x, lie):
            if lie == 'Tee':
                average_number_of_shots = expected_shots_tee(x)
            elif lie == 'Fairway':
                average_number_of_shots = expected_shots_fairway(x)
            elif lie == 'Rough':
                average_number_of_shots = expected_shots_rough(x)
            elif lie == 'Sand':
                average_number_of_shots = expected_shots_sand(x)
            elif lie == 'Green':
                average_number_of_shots = expected_shots_green(x)
            elif lie == 'In The Hole':
                average_number_of_shots = 0
            else:
                average_number_of_shots = np.nan
            return average_number_of_shots

        def strokes_gained_calculation(start_lie, start_distance, end_lie, end_distance, shot_number, next_shot_number):
            start_average_number_of_shots = expected_shots(start_distance, start_lie)
            end_average_number_of_shots = expected_shots(end_distance, end_lie)
            if next_shot_number:
                strokes_gained = start_average_number_of_shots - end_average_number_of_shots - 1
            else:
                strokes_gained = (start_average_number_of_shots - end_average_number_of_shots
                                  - (next_shot_number - shot_number))
            return strokes_gained

        # Strokes gained using PGA benchmark.

        ## Impute next shot number.
        data.sort_values(by=['round_userId', 'round_startTime', 'roundId', 'hole_holeId', 'shot_shotId'],
                         inplace=True)
        data['next_shot_shotId'] = data.groupby(['round_userId',
                                                 'round_startTime',
                                                 'roundId',
                                                 'hole_holeId'])['shot_shotId'].shift(-1)

        ## Calculate strokes gained.
        data['strokes_gained_calculated'] = data.apply(
            lambda row: strokes_gained_calculation(row['shot_startTerrain'],
                                                   row['shot_start_distance_yards'],
                                                   row['shot_endTerrain'],
                                                   row['shot_end_distance_yards'],
                                                   row['shot_shotId'],
                                                   row['next_shot_shotId']), axis=1)

        return data
