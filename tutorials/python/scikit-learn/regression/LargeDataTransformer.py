from pyexasol import ExaConnection


class LargeDataTransformer:
    def __init__(self, connection: ExaConnection):
        self.connection = connection

    def transform(self, schema_name: str, origin_table_name: str, new_table_name: str,
                  min_max_scaling_column_list: list,
                  categorical_columns_list: list):
        self.connection.open_schema(schema_name)
        select_subquery = self.__create_select_subquery(origin_table_name,
                                                        categorical_columns_list, min_max_scaling_column_list)
        query = "CREATE OR REPLACE TABLE {new_table_name} AS {select_subquery}".format(new_table_name=new_table_name,
                                                                                       select_subquery=select_subquery)
        print(query)
        self.connection.execute(query)

    def __create_select_subquery(self, origin_table_name: str,
                                 categorical_columns_list: list, min_max_scaling_column_list: list) -> str:
        select_subquery = "SELECT {max_min_scaling_columns_query}{comma}{categorical_columns_query} " \
                          "FROM {origin_table_name} {categorical_columns_postfix}"
        max_min_scaling_columns_query = self.__generate_query_for_min_max_scaling_columns(min_max_scaling_column_list)
        comma = ", " if len(max_min_scaling_columns_query) > 0 and len(categorical_columns_list) > 0 else ""
        categorical_columns_query = ""
        categorical_columns_postfix = ""
        if len(categorical_columns_list) > 0:
            categories_table_name_postfix = '_CATEGORIES'
            self.__create_categorical_tables(origin_table_name, categorical_columns_list, categories_table_name_postfix)
            categorical_columns_query = self.__generate_query_for_categorical_columns(categorical_columns_list,
                                                                                      categories_table_name_postfix)
            categorical_columns_postfix = self.___generate_categorical_columns_postfix(origin_table_name,
                                                                                       categorical_columns_list,
                                                                                       categories_table_name_postfix)
        return select_subquery.format(max_min_scaling_columns_query=max_min_scaling_columns_query,
                                      comma=comma,
                                      categorical_columns_query=categorical_columns_query,
                                      origin_table_name=origin_table_name,
                                      categorical_columns_postfix=categorical_columns_postfix)

    def __generate_query_for_min_max_scaling_columns(self, min_max_scaling_column_list):
        individual_columns_queries = []
        for column in min_max_scaling_column_list:
            individual_columns_queries.append(self.__generate_min_max_scale_column_query(column))
        return ', '.join(individual_columns_queries)

    def __generate_min_max_scale_column_query(self, column_name: str) -> str:
        return '1.00 * ("{column_name}" - MIN("{column_name}") OVER()) / (MAX("{column_name}") OVER () - MIN("{column_name}") OVER ()) AS "{column_name}"'.format(
            column_name=column_name)

    def __create_categorical_tables(self, origin_table_name: str,
                                    categorical_columns_list: list, categories_table_name_postfix: str):
        for column_name in categorical_columns_list:
            categories_table_name = column_name + categories_table_name_postfix
            self.connection.execute(
                'CREATE OR REPLACE TABLE {categories_table_name} AS SELECT rownum - 1 AS id, {column_name} FROM (SELECT DISTINCT {column_name} FROM {origin_table_name})'
                    .format(categories_table_name=categories_table_name, column_name=column_name,
                            origin_table_name=origin_table_name))

    def __generate_query_for_categorical_columns(self, categorical_columns_list: list,
                                                 categories_table_name_postfix: str) -> str:
        individual_columns_queries = []
        for column_name in categorical_columns_list:
            table_name = column_name + categories_table_name_postfix
            individual_columns_queries.append('{table_name}.id AS {column_name}'.format(table_name=table_name,
                                                                                        column_name=column_name))
        return ', '.join(individual_columns_queries)

    def ___generate_categorical_columns_postfix(self, origin_table_name: str,
                                                categorical_columns_list: list,
                                                categories_table_name_postfix: str) -> str:
        individual_columns_prefixes = []
        for column_name in categorical_columns_list:
            table_name = column_name + categories_table_name_postfix
            individual_columns_prefixes.append(
                "JOIN {table_name} ON {origin_table_name}.{column_name} = {table_name}.{column_name}".format(
                    column_name=column_name, table_name=table_name, origin_table_name=origin_table_name))
        return ' '.join(individual_columns_prefixes)
