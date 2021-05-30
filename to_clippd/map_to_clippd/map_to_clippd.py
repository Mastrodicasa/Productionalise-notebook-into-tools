import os
import pandas as pd
import pytz

# get the location of this script so we can read in local files
# otherwise we have problems were we can't find the files
# as python will look in cwd instead of this directory
try:
    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__))
    )
except:
    __location__ = ''

class MapToClippd(object):
    def __init__(self):
        self.data_dictionary = pd.read_excel(os.path.join(__location__,'data_dictionary.xlsx'))

    def standardize_values(self, clippd_data):
        # Tidy datetime features and add round_date.
        datetime_features = ['round_time', 'shot_time']
        for i in datetime_features:
            clippd_data[i] = clippd_data[i].apply(lambda x: x.replace(tzinfo=pytz.UTC))

        clippd_data['round_date'] = pd.to_datetime(clippd_data['round_time']).dt.date

        # Convert data_source to categorical variable and order dataframe.
        clippd_data['data_source'] = pd.Categorical(clippd_data['data_source'],
                                                    categories=['arccos', 'gsl', 'whs'], ordered=True)
        clippd_data.sort_values(by=['data_source', 'player_id', 'round_time', 'round_id', 'hole_id'], inplace=True)

    def process(self, source, data):
        if source == "arccos":
            # Create empty Clippd dataframe.
            clippd_data = pd.DataFrame(columns=self.data_dictionary['Clippd'].values)

            # Add data to Clippd dataframe.

            ## Sort.
            data.sort_values(by=['player_id', 'round_time', 'round_id', 'hole_id', 'shot_id'], inplace=True)

            ## Concatenate data sources.
            clippd_data = pd.concat([clippd_data, data])
            clippd_data.reset_index(drop=True, inplace=True)

        self.standardize_values(clippd_data)