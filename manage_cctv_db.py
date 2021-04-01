import sqlite3
from sqlite3 import Error
import time
import pandas as pd
print(sqlite3.sqlite_version)

# path to existent database
path = '/home/lserra/Work/Serving/output_folder/video/video.sqlite'

def create_connection(path):
    connection = None
    try:
        connection = sqlite3.connect(path)
        print('Connection to SQLite DB successful')
    except Error as e:
        print(f'The error "{e}" ocurred')

    return connection

# Establish a connection to existent database
connection = create_connection(path)

def manage_database(connection, command):
    cursor = connection.cursor()
    try:
        cursor.execute(command)
        connection.commit()
        print('Commmand executed successfully')
    except Error as e:
        print(f'The error "{e}" ocurred')

create_detections_table = '''
CREATE TABLE IF NOT EXISTS detections (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  unix_time_insertion INTEGER NOT NULL,
  image TEXT NOT NULL,
  image_size TEXT NOT NULL,
  object TEXT,
  coordinates TEXT,
  score REAL
);
'''

# create database if it does not exist
# create table if not exists
manage_database(connection, create_detections_table)

# Execute a query to the database
def execute_query(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        print('Query executed successfully')
        return result #returns list of tuples
    except Error as e:
        print(f'The error "{e}" ocurred')

# example if querying the database
#select_detections = 'SELECT * FROM detections'
#detections = execute_query(connection, select_detections)
#print(detections)
#df = pd.DataFrame(detections, columns=['id','unix_time_insertion','image','image_size',
#                                       'object','coordinates','score'])
#print(df)

def insert_multiple_detections(detections, connection_to_db=connection):
    cursor = connection_to_db.cursor()

    detections_list = []
    item = None
    objects_of_interest = ['bicycle', 'car', 'person', 
                           'motorcycle', 'bus', 'truck']
    for detection in detections:
        if detection['object'] in objects_of_interest:
            item = (round(time.time()),
                    detection['image'],
                    str(detection['image_size']),
                    detection['object'],
                    str(detection['coordinates']),
                    round(detection['score'], 3))
            detections_list.append(item)
            item = None

    insert_detections = '''
    INSERT INTO
      detections (unix_time_insertion, image, image_size, object, coordinates, score)
    VALUES (?,?,?,?,?,?);
    '''

    try:
        cursor.executemany(insert_detections, detections_list)
        connection.commit()
        rc = cursor.rowcount
        print(f'A total of {rc} records inserted successfully into detections table')
    except Error as e:
        print(f'The error "{e}" ocurred')
