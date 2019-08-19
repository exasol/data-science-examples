import simplestopwatch


class CsvImporter:
    def __init__(self, connection):
        self.connection = connection

    def import_file(self, sql_create_table_file, schema_name, table_name, file_path, file_name, column_separator):
        self.__handle_schema(self.connection, schema_name)
        self.__execute_create_table(sql_create_table_file)
        self.__run_import_command(self.connection, table_name, file_path, file_name, column_separator)

    def __handle_schema(self, connection, schema_name):
        connection.execute("CREATE SCHEMA IF NOT EXISTS " + schema_name + ";")
        connection.execute("OPEN SCHEMA " + schema_name + ";")

    def __execute_create_table(self, sql_create_table_file):
        query = open(sql_create_table_file, 'r')
        for line in query:
            self.connection.execute(query=line)

    def __run_import_command(self, connection, table_name, file_path, file_name, column_separator):
        timer = simplestopwatch.Timer()
        connection.execute(
            "IMPORT INTO {table_name} FROM CSV AT '{file_path}' FILE '{file_name}' "
            "COLUMN SEPARATOR = '{column_separator}' SKIP = 1  "
            "ERRORS INTO error_table (CURRENT_TIMESTAMP) REJECT LIMIT UNLIMITED ERRORS".format(
                table_name=table_name, file_path=file_path, file_name=file_name, column_separator=column_separator))
        timer.stop()
        print("Imported in " + str(timer))
