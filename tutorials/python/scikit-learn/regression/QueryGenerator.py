from typing import List


class QueryGenerator():

    def generate_min_max_scale_column_query(self, column_name: str) -> str:
        return '1.00 * ("{column_name}" - MIN("{column_name}") OVER()) / (MAX("{column_name}") OVER () - MIN("{column_name}") OVER ()) AS "{column_name}"'.format(
            column_name=column_name)

    def generate_final_query(self, tables_list: List[str], final_table_name: str, origin_table_name: str,
                             min_max_scaling_query: str) -> str:
        query_part_1 = 'CREATE OR REPLACE TABLE {final_table_name} AS '.format(final_table_name=final_table_name)

        query_part_2 = 'SELECT ' + min_max_scaling_query
        for table in tables_list:
            column_name = table[:-11]
            query_part_2 += '{table_name}.id AS {column_name}'.format(table_name=table, column_name=column_name)
            if table != tables_list[-1]:
                query_part_2 += ", "
        query_part_2 += " FROM {origin_table_name}".format(origin_table_name=origin_table_name)

        query_part_3 = ""
        for table in tables_list:
            column_name = table[:-11]
            temp_query = " JOIN {table_name} ON {origin_table_name}.{column_name} = {table_name}.{column_name}".format(
                column_name=column_name, table_name=table, origin_table_name=origin_table_name)
            query_part_3 += temp_query

        query = query_part_1 + query_part_2 + query_part_3
        return query
