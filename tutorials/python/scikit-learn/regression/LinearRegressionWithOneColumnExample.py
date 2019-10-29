import pandas
from pyexasol import ExaConnection
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split


class LinearRegressionPredictionByOneColumn:
    def __init__(self, connection: ExaConnection):
        self.connection = connection

    def start_regression(self, schema_name: str, table_name: str, x_column_name: str, y_column_name: str):
        self.connection.open_schema(schema_name)
        pandas_result_set = self.connection.export_to_pandas(
            "SELECT {x_column_name}, {y_column_name} FROM {table_name} LIMIT 1000000".format(table_name=table_name,
                                                                                             x_column_name=x_column_name,
                                                                                             y_column_name=y_column_name))
        x = pandas_result_set[x_column_name].values.reshape(-1, 1)
        y = pandas_result_set[y_column_name].values.reshape(-1, 1)
        X_train, X_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=0)

        regression = LinearRegression()
        regression.fit(x, y)

        print(regression.intercept_)
        print(regression.coef_)

        y_pred = regression.predict(X_test)
        df = pandas.DataFrame({'Actual': y_test.flatten(), 'Predicted': y_pred.flatten()})
        print(df)
