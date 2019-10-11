from pyexasol import ExaConnection

from regression.QueryGenerator import QueryGenerator


class LargeDataTransformer:
    def __init__(self, connection: ExaConnection):
        self.connection = connection

    def transform(self, schema_name: str, origin_table_name: str, final_table_name: str,
                  min_max_scaling_column_list: list,
                  categorical_columns_list: list):
        query_generator = QueryGenerator()
        min_max_scaling_query = self.__generate_min_max_scaling_query_column_list(categorical_columns_list,
                                                                                  min_max_scaling_column_list,
                                                                                  query_generator)
        categorical_views = self.__create_categorical_views(categorical_columns_list,
                                                            origin_table_name,
                                                            schema_name)
        final_query = query_generator.generate_final_query(categorical_views, final_table_name, origin_table_name,
                                                           min_max_scaling_query)
        print(final_query)
        self.connection.execute(final_query)

    def __create_categorical_views(self, categorical_columns_list, origin_table_name, schema_name):
        categorical_views = []
        self.connection.open_schema(schema_name)
        for column_name in categorical_columns_list:
            self.connection.execute(
                'CREATE OR REPLACE VIEW {column_name}_categories AS SELECT rownum - 1 AS id, {column_name} FROM (SELECT DISTINCT {column_name} FROM {origin_table_name})'
                    .format(column_name=column_name, origin_table_name=origin_table_name))
            new_table_name = column_name + '_CATEGORIES'
            categorical_views.append(new_table_name)
        return categorical_views

    def __generate_min_max_scaling_query_column_list(self, categorical_columns_list, min_max_scaling_column_list,
                                                     query_generator):
        min_max_scaling_query = ""
        for column in min_max_scaling_column_list:
            temp_query_part = query_generator.generate_min_max_scale_column_query(column)
            if column != min_max_scaling_column_list[-1] or len(categorical_columns_list) > 0:
                temp_query_part += ", "
            min_max_scaling_query += temp_query_part
        return min_max_scaling_query
