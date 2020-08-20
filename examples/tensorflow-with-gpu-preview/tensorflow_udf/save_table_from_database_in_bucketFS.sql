/*
 saves the given table in the bucketFS specified by connection_name.
 You have to either adjust the input parameters to match your columns(and then also adjust the write to file),
 so it can be ordered by one of them.
 If the input was dynamic, it could not be ordered and the rows would ordered differently in the output file than in the DB.

 if you want dynamic input and sorted rows, you have to create the script dynamically.

 BUCKET_CONNECTION needs to be the name of a connection with the following specifcation:
    password = write pw
    address = address of the bucket in BucketFS
    user = name the saved table should have
 */


CREATE SCHEMA IF NOT EXISTS EXA_toolbox;
CREATE OR REPLACE PYTHON SET SCRIPT save_table_from_db_in_bucketFS(
    ID    DECIMAL ,
    "column"  VARCHAR(20000),
    "BUCKET_CONNECTION"       VARCHAR(20000) ORDER BY ID
    )
RETURNS VARCHAR(2000) AS

#from xmlrpclib import Server
import requests
import os

def create_bucket_path(connection_name):       # p = "http://w:wp@192.168.122.59:2580/bn/" + table_name
    bucket_connection_string = exa.get_connection(connection_name)

    uri = bucket_connection_string.address
    table_name = bucket_connection_string.user
    write_pw = bucket_connection_string.password

    if len(uri.split('https://', 1)) == 2:
        split_url = uri.split('https://', 1)
        uri = "{connection_first_part}w:{write_pw}@{url}{table_name}".format(
            connection_first_part='https://', write_pw=write_pw, url=split_url[1], table_name=table_name)
        path_in_bucketfs_dsn = split_url[1] + table_name
        path_in_bucketfs_dsn_split = path_in_bucketfs_dsn.split('/',1)
    elif len(uri.split('http://', 1)) == 2:
        split_url = uri.split('http://', 1)
        uri = "{connection_first_part}w:{write_pw}@{url}{table_name}".format(
            connection_first_part='http://', write_pw=write_pw, url=split_url[1], table_name=table_name)
        path_in_bucketfs_dsn = split_url[1] + table_name
        path_in_bucketfs_dsn_split = path_in_bucketfs_dsn.split('/',1)
    return uri, table_name, path_in_bucketfs_dsn_split[1]

def run(ctx):
    save_path = "tmp/"
    connection_name = ctx.BUCKET_CONNECTION                                   # pw = write pw, adress = adress of bucketfs, user = table_name
    bucket_path, table_name, path_in_bucketfs_dsn = create_bucket_path(connection_name)
    table_file = open((save_path + table_name), "w")

    while True:
        table_file.write( ctx.column + "\n")
        if not ctx.next():
            break
    table_file.close()

    files = open((save_path + table_name), 'r')
    requests.put(bucket_path, data=files)

    os.remove(save_path + table_name)
    return path_in_bucketfs_dsn         # return bucket_path if you need the whole path back
/
