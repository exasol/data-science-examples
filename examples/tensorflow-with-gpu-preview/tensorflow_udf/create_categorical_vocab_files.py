import yaml
import pyexasol

# example credentials.yaml

# credentials:
#     user: "user"
#     password: "password"
#     dsn: "192.168.122.59:port"
# bucket_con:
#     bucket_address: "http://192.168.122.59:port/bucket_path/"
#     write_password: "write password"

def create_bucket_connection(bucket_con, table_name, con):
    bucket_address = bucket_con["bucket_address"]
    write_pw = bucket_con["write_password"]
    con.execute("CREATE OR REPLACE CONNECTION BUCKET_CONNECTION TO '{bucket}' USER '{table_name}' IDENTIFIED BY '{write_pw}'"
                                    .format(bucket=bucket_address, table_name=table_name, write_pw=write_pw))


def save_to_bucket(con, categorical_table_names, schema_name, credentials):
    con.open_schema("exa_toolbox")                                                                     # replace withe the schema your script is in
    bucket_paths = {}
    for table in categorical_table_names:
        table_name = categorical_table_names[table]
        create_bucket_connection(credentials["bucket_con"], table_name, con)
        res = con.execute("SELECT save_table_from_db_in_bucketFS(id, {column}, 'BUCKET_CONNECTION') FROM {schema}.{table}".
                    format(column=table, schema=schema_name, table=table_name))
        for row in res:
            bucket_paths[table] = row[0]
    con.execute("DROP CONNECTION IF EXISTS BUCKET_CONNECTION")
    return bucket_paths


def vocab_files_for_categorical_columns(categorical_input_columns, origin_table_name,
                                        schema_name, con):
    categorical_table_names = {}
    con.open_schema(schema_name)
    for column_name in categorical_input_columns:
        new_table_name = column_name + '_CATEGORIES'
        # "ExaStatement may fetch result set rows as tuples (default) or as dict (set fetch_dict=True in connection options).
        con.execute(
            'CREATE OR REPLACE TABLE {table_name} AS SELECT rownum-1 AS id, {column_name} FROM(SELECT DISTINCT {column_name} FROM {origin_table_name})'
                    .format(table_name=new_table_name, column_name=column_name, origin_table_name=origin_table_name))
        categorical_table_names[column_name] = new_table_name
    return categorical_table_names


def drop_vocab_tables(categorical_table_names, con, schema_name):
    for table in categorical_table_names:
        table_name = categorical_table_names[table]
        con.execute(
            'DROP TABLE {schema}.{table_name}'
                .format(table_name=table_name, schema=schema_name))


def create_categorical_vocab_files_in_bucketfs(categorical_input_columns, original_table, schema):

    with open("credentials.yaml") as file:
        credentials = yaml.load(file, yaml.Loader)
    file.close()
    user = credentials["credentials"]["user"]
    password = credentials["credentials"]["password"]
    dsn = credentials["credentials"]["dsn"]
    con = pyexasol.connect(dsn=dsn, user=user, password=password, autocommit=True, schema=schema)

    categorical_table_names = vocab_files_for_categorical_columns(categorical_input_columns, original_table, schema, con)
    bucket_paths = save_to_bucket(con, categorical_table_names, schema, credentials)
    drop_vocab_tables(categorical_table_names, con, schema)
    print("paths of vocab files in bucketFS : ", bucket_paths)

    return bucket_paths

# usage: create_categorical_vocab_files_in_bucketfs(["f_int_0", "f_int_1", "f_float_0"], "data_test_column_encoder_categories", "test")



