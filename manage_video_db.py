import sqlite3
from sqlite3 import Error
import time
import pandas as pd

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

create_video_table = '''
CREATE TABLE IF NOT EXISTS video (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  unix_time_insertion INTEGER NOT NULL,
  name TEXT NOT NULL,
  size TEXT NOT NULL,
  counts_up INTEGER DEFAULT 0,
  counts_down INTEGER DEFAULT 0
);
'''

create_tracks_table = '''
CREATE TABLE IF NOT EXISTS tracks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  object_id INTEGER,
  coord_x INTEGER,
  coord_y INTEGER,
  video_id INTEGER NOT NULL,
  FOREIGN KEY (video_id) REFERENCES video (id)
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
);
'''
#need to update this table to reference the video table
create_detections_table = '''
CREATE TABLE IF NOT EXISTS detections (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  unix_time_insertion INTEGER NOT NULL,
  video_id INTEGER NOT NULL,
  image_sequence INTEGER NOT NULL,
  object TEXT,
  coordinates TEXT,
  score REAL,
  FOREIGN KEY (video_id) REFERENCES video (id)
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
);
'''

# create database if it does not exist
# create table if not exists
manage_database(connection, create_video_table)
manage_database(connection, create_tracks_table)
manage_database(connection, create_detections_table)
#insert_video = '''
#INSERT INTO video (unix_time_insertion, name, size)
#VALUES (2,'test_1s.jpg','some_size');
#'''
#manage_database(connection, insert_video)

# Execute a query to the database
def execute_query(connection, query, condition=None):
    cursor = connection.cursor()
    result = None
    try:
        if condition:
            cursor.execute(query, condition)
        else:
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

# this function needs to be called from backbone.py
def insert_video_data(video, connection_to_db=connection):
    cursor = connection_to_db.cursor()
    #do something

    video_list = [()] # to complete
    
    insert_video = '''
    INSERT INTO
      video (unix_time_insertion, name, size, counts_up, counts_down)
    VALUES (?,?,?,?,?);
    '''

    try:
        cursor.executemany(insert_video, video_list)
        connection.commit()
        rc = cursor.rowcount
        print('One record inserted successfully into the video table')
    except Error as e:
        print(f'The error "{e}" ocurred')


# I'm assuming the video name is within the tracks....
# this function needs to be called from backbone.py
def insert_multiple_tracks(tracks, connection_to_db=connection):
    cursor = connection_to_db.cursor()

    video_id = get_video_id() #to develop this function
    tracks_list = []
    for track in tracks:
        for position in tracks[track]:
            tracks_list.append((int(track),
                                position[0],
                                position[1],
                                video_id))

    insert_tracks = '''
    INSERT INTO
      tracks (object_id, coord_x, coord_y, video_id)
    VALUES (?,?,?,?);
    '''

    try:
        cursor.executemany(insert_tracks, tracks_list)
        connection.commit()
        rc = cursor.rowcount
        print(f'A total of {rc} records inserted successfully into tracks table')
    except Error as e:
        print(f'The error "{e}" ocurred')


# return detections' foreign key value and frame sequence number
def get_detection_attributes(image_name):
    video_name = image_name[:-11] + image_name[-4:]
    select_video_id = 'SELECT id FROM video WHERE name = ?;'
    video_id = execute_query(connection, select_video_id, (video_name,))
    video_id = video_id[0][0] #access int inside tuple inside list

    image_sequence = int(image_name[-10:-4])

    return video_id, image_sequence

#print(get_detection_attributes('test_1s_000011.jpg'))

def insert_multiple_detections(detections, connection_to_db=connection):
    cursor = connection_to_db.cursor()

    video_id = get_detection_attributes(detections[0]['image'])[0]
    image_sequence = get_detection_attributes(detections[0]['image'])[1]
    detections_list = []
    item = None
    objects_of_interest = ['pedestrian']
    for detection in detections:
        if detection['object'] in objects_of_interest:
            item = (round(time.time()),
                    video_id,
                    image_sequence,
                    #detection['image'],
                    #str(detection['image_size']),
                    detection['object'],
                    str(detection['coordinates']),
                    round(detection['score'], 3))
            detections_list.append(item)
            item = None

    insert_detections = '''
    INSERT INTO
      detections (unix_time_insertion, video_id, image_sequence, 
                  object, coordinates, score)
    VALUES (?,?,?,?,?,?);
    '''

    try:
        cursor.executemany(insert_detections, detections_list)
        connection.commit()
        rc = cursor.rowcount
        print(f'A total of {rc} records inserted successfully into detections table')
    except Error as e:
        print(f'The error "{e}" ocurred')
