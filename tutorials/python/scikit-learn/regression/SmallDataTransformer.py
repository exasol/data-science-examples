from typing import Any

import pandas
from pandas import DataFrame
from pyexasol import ExaConnection
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import MinMaxScaler


class SmallDataTransformer:
    """
    Use this class when a table contains less than 10.000.000 rows.
    """

    def __init__(self, connection: ExaConnection):
        self.connection = connection

    def transform(self, schema_name: str, origin_table_name: str, final_table_name: str,
                  min_max_scaling_columns_list: list,
                  categorical_columns_list: list, all_columns_with_types_list: str) -> None:
        self.connection.open_schema(schema_name)
        pandas_result_set = self.connection.export_to_pandas(
            "SELECT * FROM {table_name}".format(table_name=origin_table_name))
        encoded_categorical_columns_data_frame = self.__encode_as_labels(categorical_columns_list, pandas_result_set)
        encoded_numerical_columns_data_frame = pandas.DataFrame.from_records(
            self.__encode_as_max_min(min_max_scaling_columns_list,
                                     pandas_result_set))
        all_columns_data_frame = pandas.concat(
            [encoded_categorical_columns_data_frame, encoded_numerical_columns_data_frame],
            axis=1)
        self.connection.execute(
            'CREATE OR REPLACE TABLE {final_table_name} ({all_columns_with_types_list});'
                .format(final_table_name=final_table_name, all_columns_with_types_list=all_columns_with_types_list))
        self.connection.import_from_pandas(all_columns_data_frame, final_table_name)

    def __encode_as_labels(self, categorical_columns_list: list, columns_data_frame: DataFrame) -> Any:
        if len(categorical_columns_list) != 0:
            categorical_columns_data_frame = columns_data_frame[categorical_columns_list]
            if not categorical_columns_data_frame.empty:
                return categorical_columns_data_frame.apply(LabelEncoder().fit_transform)
        else:
            return None

    def __encode_as_max_min(self, min_max_scaling_columns_list: list, columns_data_frame: DataFrame):
        if len(min_max_scaling_columns_list) != 0:
            min_max_columns_data_frame = columns_data_frame[min_max_scaling_columns_list]
            if not min_max_columns_data_frame.empty:
                return MinMaxScaler().fit_transform(min_max_columns_data_frame)
        else:
            return None
