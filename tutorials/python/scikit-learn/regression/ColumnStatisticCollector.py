import plotly.express as plotly
import pyexasol


class ColumnStatisticCollector:
    def get_categorical_stats(self, connection: pyexasol.connection, schema_name: str, table_name: str,
                              column_name: str):
        connection.execute("OPEN SCHEMA {schema_name};".format(schema_name=schema_name))

        sum_of_distinct_values = self.__get_query_result(connection,
                                                         'SELECT count (distinct "{column_name}") from {table_name};'
                                                         .format(column_name=column_name, table_name=table_name))
        sum_of_nulls = self.__get_query_result(connection,
                                               'SELECT COUNT(*) from  {table_name} WHERE "{column_name}" IS NULL;'
                                               .format(table_name=table_name, column_name=column_name))
        max_value = self.__get_query_result(connection, 'SELECT MAX("{column_name}") from {table_name};'
                                            .format(column_name=column_name, table_name=table_name))
        min_value = self.__get_query_result(connection, 'SELECT MIN("{column_name}") from {table_name};'
                                            .format(column_name=column_name, table_name=table_name))

        result_set = connection.export_to_pandas(
            'SELECT DISTINCT "{column_name}", COUNT("{column_name}") as sum_of_distinct_values from {table_name} '
            'GROUP BY "{column_name}" ORDER BY "{column_name}";'
                .format(column_name=column_name, table_name=table_name))

        bar = plotly.bar(result_set, x=(column_name), y="SUM_OF_DISTINCT_VALUES",
                         title="Column: " + column_name + ", sum of dist values=" + str(
                             sum_of_distinct_values) + ", nulls=" + str(sum_of_nulls) + ", max value=" + str(
                             max_value) + ", min value=" + str(min_value))
        bar.layout.xaxis.type = 'category'
        return bar

    def __get_query_result(self, connection: pyexasol.connection, query: str):
        iterable_query_result = connection.execute(query)
        counter = 0
        for row in iterable_query_result:
            counter = row[0]
        return counter
