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
                  min_max_scaling_column_list: list,
                  categorical_columns_list: list, all_columns_with_types_list: str):
        self.connection.open_schema(schema_name)
        pandas_result_set = self.connection.export_to_pandas(
            "SELECT * FROM {table_name}".format(table_name=origin_table_name))
        # Encoding categorical columns with label encoder.
        encoded_result_set = self.__encode_as_labels(categorical_columns_list, pandas_result_set)
        # Encoding nominal column with MinMaxScaler.
        encoded_result_set[min_max_scaling_column_list] = MinMaxScaler().fit_transform(
            encoded_result_set[min_max_scaling_column_list])
        # Write the results to a new table. The table should be created before the script runs.
        self.connection.execute(
            'CREATE OR REPLACE TABLE {final_table_name} ({all_columns_with_types_list});'
                .format(final_table_name=final_table_name, all_columns_with_types_list=all_columns_with_types_list))
        self.connection.import_from_pandas(encoded_result_set, final_table_name)

    def __encode_as_labels(self, categorical_columns_list: list, pandas_result_set):
        output = pandas_result_set.copy()

        if categorical_columns_list is not None:
            for column in categorical_columns_list:
                output[column] = LabelEncoder().fit_transform(output[column])
        else:
            for column_name, column in output.iteritems():
                output[column_name] = LabelEncoder().fit_transform(column)
        return output
