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
                         x_columns_categorical_list: list, y_column_name: str, batch_size: int) -> DataFrame:
        self.connection.open_schema(schema_name)
        regressor = SGDRegressor()
        x_columns_categorical_dict = self.__get_x_columns_categorical_with_max_value(table_name,
                                                                                     x_columns_categorical_list)
        categories = [numpy.arange(value + 1) for value in x_columns_categorical_dict.values()]
        print('Numerical columns to analyze: ' + str(x_columns_numerical_list))
        print('Categorical columns to analyze: ' + str(x_columns_categorical_list))
        one_hot_encoder = OneHotEncoder(categories=categories, sparse=False)
        self.__train(regressor, table_name, list(x_columns_categorical_dict.keys()), x_columns_numerical_list,
                     y_column_name, one_hot_encoder, batch_size)
        prediction = self.__predict(regressor, table_name, list(x_columns_categorical_dict.keys()),
                                    x_columns_numerical_list, y_column_name, one_hot_encoder, batch_size)
        return prediction

    def __get_x_columns_categorical_with_max_value(self, table_name: str, x_columns_categorical_list: list) -> dict:
        x_columns_categorical_dict = {}
        for column in x_columns_categorical_list:
            max_value_list = self.connection.export_to_list(
                "SELECT MAX({column_name}) FROM {table_name}".format(column_name=column, table_name=table_name))
            x_columns_categorical_dict[column] = int((max_value_list[0])[0])
        return x_columns_categorical_dict

    def __train(self, regressor: SGDRegressor, table_name: str, x_columns_categorical_list: list,
                x_columns_numerical_list: list, y_column_name: str, one_hot_encoder: OneHotEncoder,
                batch_size: int) -> None:
        split = 'train'
        start_index = 0
        finish_index = batch_size
        while True:
            all_columns_train_data_frame = self.__get_data_frame_with_all_columns(x_columns_categorical_list,
                                                                                  x_columns_numerical_list,
                                                                                  y_column_name, table_name,
                                                                                  split, start_index, finish_index)
            if all_columns_train_data_frame.empty:
                break
            print("Training for batch " + str(start_index) + "-" + str(finish_index))
            start_index = finish_index
            finish_index += batch_size
            x_columns_data_frame = self.__get_x_columns_data_frame(all_columns_train_data_frame,
                                                                   x_columns_categorical_list,
                                                                   x_columns_numerical_list, split, one_hot_encoder)
            y_column_ndarray = self.__get_y_column_ndarray(all_columns_train_data_frame, y_column_name, split)
            self.__run_training_cycle(x_columns_data_frame, y_column_ndarray, regressor)

    def __get_data_frame_with_all_columns(self, x_columns_categorical_list: list, x_columns_numerical_list: list,
                                          y_column_name: str, table_name: str, split: str, start_index: int,
                                          finish_index: int) -> DataFrame:
        all_columns_list = x_columns_categorical_list + x_columns_numerical_list
        all_columns_list.append(y_column_name)
        query_all_columns_train = self.__create_query(table_name, all_columns_list, split, start_index, finish_index)
        print("Importing result set for {split}...".format(split=split))
        all_columns_train_data_frame = self.connection.export_to_pandas(query_all_columns_train)
        print("Result set for {split} was obtained:\n".format(split=split) + str(all_columns_train_data_frame.head()))
        return all_columns_train_data_frame

    def __create_query(self, table_name: str, columns_list: list, split: str, start_index: int,
                       finish_index: int) -> str:
        x_columns_string = ', '.join(columns_list)
        query = "SELECT {x_columns_string} FROM {table_name} WHERE split = '{split}' AND id >{start_index} AND id <={finish_index}".format(
            table_name=table_name,
            x_columns_string=x_columns_string,
            split=split, start_index=start_index, finish_index=finish_index)
        print("Query generated: " + query)
        return query

    def __get_x_columns_data_frame(self, all_columns_train_data_frame: DataFrame, x_columns_categorical_list: list,
                                   x_columns_numerical_list: list, split: str,
                                   one_hot_encoder: OneHotEncoder) -> DataFrame:
        categorical_columns_date_frame = all_columns_train_data_frame[x_columns_categorical_list]
        encoded_categorical_columns_data_frame = self.__encode_categorical_columns(categorical_columns_date_frame,
                                                                                   one_hot_encoder)
        numerical_columns_data_frame = all_columns_train_data_frame[x_columns_numerical_list]
        x_columns_data_frame = pandas.concat([encoded_categorical_columns_data_frame, numerical_columns_data_frame],
                                             axis=1)
        print(
            "Prepared data frame for {split}:\n".format(split=split) + str(x_columns_data_frame.head()))
        return x_columns_data_frame

    def __get_y_column_ndarray(self, all_columns_train_data_frame: DataFrame, y_column_name: str,
                               split: str) -> numpy.ndarray:
        y_column_ndarray = all_columns_train_data_frame[y_column_name].values.reshape(-1)
        return y_column_ndarray

    def __encode_categorical_columns(self, categorical_columns_date_frame: DataFrame,
                                     one_hot_encoder: OneHotEncoder) -> DataFrame:
        one_hot_encoder.fit(categorical_columns_date_frame.values[0:1, :])
        transformed_column = DataFrame(one_hot_encoder.transform(categorical_columns_date_frame.values))
        return transformed_column

    def __run_training_cycle(self, x_columns: DataFrame, y_column: numpy.ndarray, regressor: SGDRegressor) -> None:
        regressor.partial_fit(x_columns, y_column)
        print('Intercept: ' + str(regressor.intercept_)
              + '. Score: ' + str(regressor.score(x_columns, y_column)))

    def __predict(self, regressor: SGDRegressor, table_name: str, x_columns_categorical_list: list,
                  x_columns_numerical_list: list, y_column_name: str, one_hot_encoder: OneHotEncoder,
                  batch_size: int) -> DataFrame:
        split = 'test'
        start_index = 0
        finish_index = batch_size
        prediction_result_data_frame = DataFrame()
        while True:
            print("Prediction for batch " + str(start_index) + "-" + str(finish_index))
            all_columns_test_data_frame = self.__get_data_frame_with_all_columns(x_columns_categorical_list,
                                                                                 x_columns_numerical_list,
                                                                                 y_column_name, table_name,
                                                                                 split, start_index, finish_index)
            if all_columns_test_data_frame.empty:
                break
            start_index = finish_index
            finish_index += batch_size
            x_columns_data_frame = self.__get_x_columns_data_frame(all_columns_test_data_frame,
                                                                   x_columns_categorical_list, x_columns_numerical_list,
                                                                   split, one_hot_encoder)
            y_column_ndarray = self.__get_y_column_ndarray(all_columns_test_data_frame, y_column_name, split)
            part_of_predicted_data = self.__run_predict(regressor, x_columns_data_frame, y_column_ndarray)
            prediction_result_data_frame = prediction_result_data_frame.append(part_of_predicted_data,
                                                                               ignore_index=True)
        return prediction_result_data_frame

    def __run_predict(self, regressor: SGDRegressor, x_columns: DataFrame, y_column_actual: numpy.ndarray):
        y_column_predicted = regressor.predict(x_columns)
        df = pandas.DataFrame({'Actual': y_column_actual.flatten(), 'Predicted': y_column_predicted.flatten()})
        return df
