import csv
import pyexasol


class CsvImporter:
    def __init__(self, dsn, user, password, schema_name, table_name):
        self.dsn = dsn
        self.user = user
        self.password = password
        self.schema_name = schema_name
        self.table_name = table_name

    def import_file(self, file_name_path, sql_create_table_file):
        connection = pyexasol.connect(dsn=self.dsn, user=self.user, password=self.password, compression=True)
        self.__handle_schema(connection, self.schema_name)
        query = open(sql_create_table_file, 'r')
        for line in query:
            connection.execute(query=line)

        self.__get_iterable_csv(file_name_path, connection)
        connection.close()

    def __handle_schema(self, connection, schema_name):
        connection.execute("CREATE SCHEMA IF NOT EXISTS " + schema_name + ";")
        connection.execute("OPEN SCHEMA " + schema_name + ";")

    def __get_iterable_csv(self, file_name_path, connection):
        with open(file_name_path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            next(csv_reader)
            connection.import_from_iterable(csv_reader, self.table_name)
