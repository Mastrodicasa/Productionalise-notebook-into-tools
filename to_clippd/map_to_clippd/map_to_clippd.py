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
    """
    Takes a dataframe from an external source and map it to a clippd Dataframe

    Attributes:
        data_dictionary: Mapping between the name of the columns in Clippd and arccos
    """
    def __init__(self):
        self.data_dictionary = pd.read_excel(os.path.join(__location__, 'data_dictionary.xlsx'))

    @staticmethod
    def __standardize_values(clippd_data):
        """
        Standardizes values and sort a clippd dataframe.

        Args:
            clippd_data: Dataframe with all the keys needed in CLippd
        Returns:
            (dataframe) with standardized time and converted data_source to categorical variable
        """
        # Tidy datetime features and add round_date.
        datetime_features = ['round_time', 'shot_time']
        for i in datetime_features:
            clippd_data[i] = [x.replace(tzinfo=pytz.UTC) for x in clippd_data[i]]

        clippd_data['round_date'] = pd.to_datetime(clippd_data['round_time']).dt.date

        # Convert data_source to categorical variable and order dataframe.
        clippd_data['data_source'] = pd.Categorical(clippd_data['data_source'],
                                                    categories=['arccos', 'gsl', 'whs'], ordered=True)
        clippd_data.sort_values(by=['data_source', 'player_id', 'round_time', 'round_id', 'hole_id'], inplace=True)
        return clippd_data

    def process(self, source, data):
        """
        Takes a dataframe from an external source and map it to a Clippd Dataframe.

        Can only read from the source: "arccos" at the moment

        Args:
             source: source of the external data
             data: Dataframe containing the data from an external source
        Returns:
            None if data is None or if source is not "arccos"
            (dataframe) Clippd Dataframe
        """
        if data is None:
            return None
        if source == "arccos":
            arccos_data_dictionary = self.data_dictionary[['Clippd', 'Arccos']]
            arccos_data_dictionary = arccos_data_dictionary.dropna().set_index('Arccos').to_dict()['Clippd']

            # Filter relevant columns, apply data dictionary and add data_source field.
            filtered_columns = list(arccos_data_dictionary.keys())
            filtered_columns.remove("'arccos'")
            data = data[filtered_columns].copy()
            data.columns = data.columns.to_series().map(arccos_data_dictionary)
            data['data_source'] = 'arccos'

            # Create empty Clippd dataframe.
            clippd_data = pd.DataFrame(columns=self.data_dictionary['Clippd'].values)

            # Add data to Clippd dataframe.
            # Sort.
            data.sort_values(by=['player_id', 'round_time', 'round_id', 'hole_id', 'shot_id'], inplace=True)

            # Concatenate data sources.
            clippd_data = pd.concat([clippd_data, data])
            clippd_data.reset_index(drop=True, inplace=True)

            return self.__standardize_values(clippd_data)
        else:
            return None
