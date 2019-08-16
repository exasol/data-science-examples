import pyexasol
import simplestopwatch


class CsvImporter:
    def __init__(self, dsn, user, password):
        self.dsn = dsn
        self.user = user
        self.password = password

    def import_file(self, sql_create_table_file, schema_name, table_name, file_path, file_name):
        connection = pyexasol.connect(dsn=self.dsn, user=self.user, password=self.password, compression=True)
        self.__handle_schema(connection, schema_name)
        query = open(sql_create_table_file, 'r')
        for line in query:
            connection.execute(query=line)

        self.__get_iterable_csv(connection, table_name, file_path, file_name)
        connection.close()

    def __handle_schema(self, connection, schema_name):
        connection.execute("CREATE SCHEMA IF NOT EXISTS " + schema_name + ";")
        connection.execute("OPEN SCHEMA " + schema_name + ";")

    def __get_iterable_csv(self, connection, table_name, file_path, file_name):
        timer = simplestopwatch.Timer()
        connection.execute(
            "IMPORT INTO " + table_name + " FROM CSV AT '" + file_path + "' FILE '" + file_name
            + "' COLUMN SEPARATOR = ',' SKIP = 1  ERRORS INTO error_table (CURRENT_TIMESTAMP) REJECT LIMIT UNLIMITED ERRORS")
        timer.stop()
        print("Imported in " + str(timer))
