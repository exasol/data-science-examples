import itertools

import numpy
import pandas
from pandas import DataFrame
from pyexasol import ExaConnection
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import OneHotEncoder


class LinearRegressionPrediction:
    def __init__(self, connection: ExaConnection):
        self.connection = connection

    def start_regression(self, schema_name: str, table_name: str, x_columns_numerical_list: list,
                         x_columns_categorical_dict: dict, y_column_name: str) -> None:
        self.connection.open_schema(schema_name)
        regressor = SGDRegressor()
        self.__train(regressor, table_name, x_columns_categorical_dict, x_columns_numerical_list, y_column_name)
        prediction = self.__predict(regressor, table_name, x_columns_categorical_dict, x_columns_numerical_list,
                                    y_column_name)
        print("Prediction data:\n" + str(prediction))

    def __train(self, regressor: SGDRegressor, table_name: str, x_columns_categorical_dict: dict,
                x_columns_numerical_list: list, y_column_name: str) -> None:
        x_columns_categorical_list = list(x_columns_categorical_dict.keys())
        split = 'train'
        all_columns_train_data_frame = self.__get_data_frame_with_all_columns(x_columns_categorical_list,
                                                                              x_columns_numerical_list,
                                                                              y_column_name, table_name,
                                                                              split)
        x_columns_data_frame = self.__get_x_columns_data_frame(all_columns_train_data_frame, x_columns_categorical_dict,
                                                               x_columns_categorical_list, x_columns_numerical_list,
                                                               split)
        y_column_ndarray = self.__get_y_column_ndarray(all_columns_train_data_frame, y_column_name, split)
        for _ in itertools.repeat(None, 100):
            self.__run_training_cycle(x_columns_data_frame, y_column_ndarray, regressor)

    def __get_data_frame_with_all_columns(self, x_columns_categorical_list: list, x_columns_numerical_list: list,
                                          y_column_name: str, table_name: str, split: str) -> DataFrame:
        print('Numerical columns to analyze: ' + str(x_columns_numerical_list))
        print('Categorical columns to analyze: ' + str(x_columns_categorical_list))
        all_columns_list = x_columns_categorical_list + x_columns_numerical_list
        all_columns_list.append(y_column_name)
        query_all_columns_train = self.__create_query(table_name, all_columns_list, split)
        print("Importing result set for {split}...".format(split=split))
        all_columns_train_data_frame = self.connection.export_to_pandas(query_all_columns_train)
        print("Result set for {split} was obtained:\n".format(split=split) + str(all_columns_train_data_frame.head()))
        return all_columns_train_data_frame

    def __create_query(self, table_name: str, columns_list: list, split: str) -> str:
        x_columns_string = ', '.join(columns_list)
        query = "SELECT {x_columns_string} FROM {table_name} WHERE split = '{split}'".format(
            table_name=table_name,
            x_columns_string=x_columns_string,
            split=split)
        print("Query generated: " + query)
        return query

    def __get_x_columns_data_frame(self, all_columns_train_data_frame: DataFrame, x_columns_categorical_dict: dict,
                                   x_columns_categorical_list: list, x_columns_numerical_list: list,
                                   split: str) -> DataFrame:
        categorical_columns_date_frame = all_columns_train_data_frame.filter(x_columns_categorical_list, axis=1)
        encoded_categorical_columns_data_frame = self.__encode_categorical_columns(categorical_columns_date_frame,
                                                                                   x_columns_categorical_dict)
        numerical_columns_data_frame = all_columns_train_data_frame.filter(x_columns_numerical_list, axis=1)
        x_columns_data_frame = pandas.concat([encoded_categorical_columns_data_frame, numerical_columns_data_frame],
                                             axis=1)
        print(
            "Prepared data frame with x columns for {split}:\n".format(split=split) + str(x_columns_data_frame.head()))
        return x_columns_data_frame

    def __get_y_column_ndarray(self, all_columns_train_data_frame: DataFrame, y_column_name: str,
                               split: str) -> numpy.ndarray:
        y_column_ndarray = all_columns_train_data_frame[y_column_name].values.reshape(-1)
        print("Prepared data frame with y column for {split}:\n".format(split=split) + str(y_column_ndarray))
        return y_column_ndarray

    def __encode_categorical_columns(self, pandas_result_set_for_training: DataFrame,
                                     x_columns_categorical: dict) -> DataFrame:
        categories = []
        for value in x_columns_categorical.values():
            categories.append(numpy.arange(value + 1))
        one_hot_encoder = OneHotEncoder(categories=categories, sparse=False)
        one_hot_encoder.fit(pandas_result_set_for_training.values[0:1, :])
        transformed_column = DataFrame(one_hot_encoder.transform(pandas_result_set_for_training.values))
        print("OneHotEncoder transformed column:\n " + str(transformed_column))
        return transformed_column

    def __run_training_cycle(self, x_columns: DataFrame, y_column: numpy.ndarray, regressor: SGDRegressor) -> None:
        regressor.partial_fit(x_columns, y_column)
        print('Intercept: ' + str(regressor.intercept_)
              + '. Score: ' + str(regressor.score(x_columns, y_column)))

    def __predict(self, regressor, table_name, x_columns_categorical_dict,
                  x_columns_numerical_list, y_column_name) -> DataFrame:
        x_columns_categorical_list = list(x_columns_categorical_dict.keys())
        split = 'test'
        all_columns_test_data_frame = self.__get_data_frame_with_all_columns(x_columns_categorical_list,
                                                                             x_columns_numerical_list,
                                                                             y_column_name, table_name,
                                                                             split)
        x_columns_data_frame = self.__get_x_columns_data_frame(all_columns_test_data_frame, x_columns_categorical_dict,
                                                               x_columns_categorical_list, x_columns_numerical_list,
                                                               split)
        y_column_ndarray = self.__get_y_column_ndarray(all_columns_test_data_frame, y_column_name, split)
        return self.__run_predict(regressor, x_columns_data_frame, y_column_ndarray)

    def __run_predict(self, regressor: SGDRegressor, x_columns: DataFrame, y_column_actual: numpy.ndarray):
        y_column_predicted = regressor.predict(x_columns)
        df = pandas.DataFrame({'Actual': y_column_actual.flatten(), 'Predicted': y_column_predicted.flatten()})
        return df
