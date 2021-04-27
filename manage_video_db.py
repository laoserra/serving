import sqlite3
from sqlite3 import Error
import time
import pandas as pd

# path to existent database
path = '/home/lserra/Work/Serving/output_folder/video/video.db'

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

def manage_database(command, connection_to_db=connection):
    cursor = connection_to_db.cursor()
    try:
        cursor.execute(command)
        connection_to_db.commit()
        print('Commmand executed successfully')
    except Error as e:
        print(f'The error "{e}" ocurred')

create_video_table = '''
CREATE TABLE IF NOT EXISTS video (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  unix_time_insertion INTEGER NOT NULL,
  name TEXT NOT NULL,
  frame_height INTEGER,
  frame_width INTEGER,
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
create_detections_table = '''
CREATE TABLE IF NOT EXISTS detections (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  unix_time_insertion INTEGER NOT NULL,
  video_id INTEGER NOT NULL,
  frame_sequence INTEGER NOT NULL,
  object TEXT,
  bbox_left REAL,
  bbox_right REAL,
  bbox_bottom REAL,
  bbox_top REAL,
  score REAL,
  FOREIGN KEY (video_id) REFERENCES video (id)
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
);
'''

# create database if it does not exist
# create table if not exists
manage_database(create_video_table)
manage_database(create_tracks_table)
manage_database(create_detections_table)

# to test foreign keys
#insert_video = '''
#INSERT INTO video (unix_time_insertion, name, size)
#VALUES (2,'test_1s.mp4','some_size');
#'''
#manage_database(insert_video)

# Execute a query to the database
def execute_query(query, condition=None, connection_to_db=connection):
    cursor = connection_to_db.cursor()
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

# querying the database for detections
#select_detections = 'SELECT * FROM detections'
#detections = execute_query(select_detections)
#print(detections)
#df = pd.DataFrame(detections, columns=['id','unix_time_insertion','video_id','image_sequence','object',
#                                        'bbox_left','bbox_right','bbox_bottom','bbox_top','score'])
#print(df.tail(20))

# querying the video table
#select_video = 'SELECT * FROM video'
#video_data = execute_query(select_video)
#print(video_data)
#df = pd.DataFrame(video_data, columns=['id','unix_time_insertion','name','frame_height',
#                                       'frame_width','counts_up','counts_down'])
#print(df.tail())

# querying the database for tracks
#select_tracks = 'SELECT * FROM tracks'
#tracks = execute_query(select_tracks)
#print(tracks)
#df = pd.DataFrame(tracks, columns=['id','object_id', 'coord_x', 'coord_y', 'video_id'])
#print(df)

def manage_multiple_records(insert_table,
                            list_of_insertions,
                            connection_to_db=connection):

    cursor = connection_to_db.cursor()

    try:
        cursor.executemany(insert_table, list_of_insertions)
        connection_to_db.commit()
        rc = cursor.rowcount
        print(f'A total of {rc} records inserted successfully into the table')
    except Error as e:
        print(f'The error "{e}" ocurred')


def insert_video_data(video_name, height, width, totalUp, totalDown):

    video_list = [(round(time.time()),
                   video_name,
                   height,
                   width,
                   totalUp,
                   totalDown)]
    
    insert_video = '''
    INSERT INTO
      video (unix_time_insertion, name, frame_height, frame_width, counts_up, counts_down)
    VALUES (?,?,?,?,?,?);
    '''
    manage_multiple_records(insert_video, video_list)


def insert_multiple_tracks(tracks, video_name): # tracks argument is a dictionary

    select_video_id = 'SELECT id FROM video WHERE name = ?;'
    video_id = execute_query(select_video_id, (video_name,))
    video_id = video_id[0][0] #access int inside tuple inside list
    tracks_list = []
    for track in tracks: # for each key in the dictionary
        for position in tracks[track]: # for each position in the value list
            tracks_list.append((int(track), #key, that is the object id
                                position[0], # coord_x
                                position[1], # coord_y
                                video_id))

    insert_tracks = '''
    INSERT INTO
      tracks (object_id, coord_x, coord_y, video_id)
    VALUES (?,?,?,?);
    '''
    manage_multiple_records(insert_tracks, tracks_list)


# return detections' foreign key value and frame sequence number
def get_video_id(video_name):
    select_video_id = 'SELECT id FROM video WHERE name = ?;'
    video_id = execute_query(select_video_id, (video_name,))
    video_id = video_id[0][0] #access int inside tuple inside list

    return video_id

#print(get_detection_attributes('test_1s_000011.jpg'))


def insert_multiple_detections(video_name, detections):
    video_id = get_video_id(video_name)
    detections_list = []
    item = None
    objects_of_interest = ['pedestrian']
    for detection in detections:
        if detection['object'] in objects_of_interest:
            item = (round(time.time()),
                    video_id,
                    detection['frame_sequence'],
                    detection['object'],
                    round(detection['coordinates']['left'], 3),
                    round(detection['coordinates']['right'], 3),
                    round(detection['coordinates']['bottom'], 3),
                    round(detection['coordinates']['top'], 3),
                    round(detection['score'], 3))
            detections_list.append(item)
            item = None

    insert_detections = '''
    INSERT INTO
      detections (unix_time_insertion, video_id, frame_sequence, object,
                  bbox_left, bbox_right, bbox_bottom, bbox_top, score)
    VALUES (?,?,?,?,?,?,?,?,?);
    '''
    manage_multiple_records(insert_detections, detections_list)
