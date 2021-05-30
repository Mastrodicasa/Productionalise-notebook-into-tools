import numpy as np
import unittest
import pandas as pd
from aggregate_data import AggregateData


class MyTestCase(unittest.TestCase):
    def test_standardize_values(self):
        ad = AggregateData()
        # Create a dataframe with all the columns that are subject to change.
        columns_numeric = ad.numeric_features
        data = ["1" for column in columns_numeric]
        columns_time = ad.time_features
        data.extend(["2020-12-17T12:09:12.338000Z" for column in columns_time])
        columns_boolean = ad.boolean_features
        data.extend(["T" for column in columns_boolean])

        all_columns = columns_numeric + columns_time + columns_boolean

        df = pd.DataFrame([data], columns=all_columns)
        df = ad.standardize_values(df)
        for column in all_columns:
            if column in columns_numeric:
                self.assertEqual(type(df[column].values[0]),  np.int64)
            elif column in columns_time:
                self.assertEqual(type(df[column].values[0]), np.datetime64)
            else:
                self.assertEqual(type(df[column].values[0]), np.bool_)


if __name__ == '__main__':
    unittest.main()
