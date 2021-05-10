import sqlite3
from sqlite3 import Error
import time
import config_file as config
#import pandas as pd

category_index = config.CATEGORY_INDEX

def create_connection(path_to_db):
    connection = None
    try:
        connection = sqlite3.connect(path_to_db)
        print('Connection to SQLite DB successful')
    except Error as e:
        print(f'The error "{e}" ocurred when trying to connect to db')

    return connection

# Establish a connection to existent database
connection = create_connection(config.PATH_DB)

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
  fps INTEGER,
  file_format TEXT,
  frame_height INTEGER,
  frame_width INTEGER,
  counts_up INTEGER DEFAULT 0,
  counts_down INTEGER DEFAULT 0
);
'''

create_classes_table = '''
CREATE TABLE classes (
  id INTEGER NOT NULL,
  name TEXT NOT NULL
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
  class_id INTEGER,
  bbox_left REAL,
  bbox_right REAL,
  bbox_bottom REAL,
  bbox_top REAL,
  score REAL,
  FOREIGN KEY (video_id) REFERENCES video (id)
    ON UPDATE NO ACTION
    ON DELETE NO ACTION,
  FOREIGN KEY (class_id) REFERENCES classes (id)
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
);
'''

# create database if it does not exist
# create table if not exists
manage_database(create_video_table)
manage_database(create_tracks_table)
manage_database(create_detections_table)

# if table classes not created create it and insert classes
def check_create_classes_table(classes_table, connection_to_db=connection):
    cursor = connection_to_db.cursor()
    #get the count of tables with the name 'classes'
    query = ''' SELECT count(name) FROM sqlite_master 
                WHERE type='table' AND name LIKE 'classes' '''
    cursor.execute(query)
    if not cursor.fetchone()[0]:
        try:
            cursor.execute(classes_table)
            classes_list = []
            for key in category_index.keys():
                classes_list.append((key, category_index[key]['name']))
            classes_list.append((max(category_index.keys()) + 1, 'N/A'))
            insert_classes = '''
            INSERT INTO classes (id,name) VALUES (?,?);
            '''
            cursor.executemany(insert_classes, classes_list)
            connection_to_db.commit()
            rc = cursor.rowcount
            print(f'A total of {rc} records inserted successfully into classes table')
        except Error as e:
            print(f'The error "{e}" ocurred when trying to create/insert classes table')

check_create_classes_table(create_classes_table)


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
#df = pd.DataFrame(detections, columns=['id','unix_time_insertion','video_id','image_sequence','class_id',
#                                        'bbox_left','bbox_right','bbox_bottom','bbox_top','score'])
#df = df.tail(2000)
#df.to_csv('/home/lserra/Work/Serving/select_detections.csv', index=False)

# querying the video table
#select_video = 'SELECT * FROM video'
#video_data = execute_query(select_video)
#print(video_data)
#df = pd.DataFrame(video_data, columns=['id','unix_time_insertion','name','frame_height',
#                                       'frame_width','counts_up','counts_down'])

# querying the database for tracks
#select_tracks = 'SELECT * FROM tracks'
#tracks = execute_query(select_tracks)
#df = pd.DataFrame(tracks, columns=['id','object_id', 'coord_x', 'coord_y', 'video_id'])
#print(df)

# querying the database for classes
#select_classes = 'SELECT * FROM classes'
#classes = execute_query(select_classes)
#df = pd.DataFrame(classes, columns=['id','object_id', 'coord_x', 'coord_y', 'video_id'])
#print(df)

def manage_multiple_records(insert_table,
                            list_of_insertions,
                            table,
                            connection_to_db=connection):

    cursor = connection_to_db.cursor()

    try:
        cursor.executemany(insert_table, list_of_insertions)
        connection_to_db.commit()
        rc = cursor.rowcount
        print(f'A total of {rc} records inserted successfully into the {table} table')
    except Error as e:
        print(f'The error "{e}" ocurred when trying to insert data to the {table} table')


def insert_video_data(video_name, fps, file_format, height, width, totalUp, totalDown):

    video_list = [(round(time.time()),
                   video_name,
                   fps,
                   file_format,
                   height,
                   width,
                   totalUp,
                   totalDown)]
    
    insert_video = '''
    INSERT INTO
      video (unix_time_insertion, name, fps, file_format, frame_height, frame_width, counts_up, counts_down)
    VALUES (?,?,?,?,?,?,?,?);
    '''
    manage_multiple_records(insert_video, video_list, 'video')


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
    manage_multiple_records(insert_tracks, tracks_list, 'tracks')


# return detections' foreign key value and frame sequence number
def get_video_id(video_name):
    select_video_id = 'SELECT id FROM video WHERE name = ?;'
    video_id = execute_query(select_video_id, (video_name,))
    video_id = video_id[0][0] #access int inside tuple inside list

    return video_id


def get_class_id(class_name):
    select_class_id = 'SELECT id FROM classes WHERE name = ?;'
    class_id = execute_query(select_class_id, (class_name,))
    class_id = class_id[0][0] #access int inside tuple inside list

    return class_id


def insert_multiple_detections(video_name, detections):
    video_id = get_video_id(video_name)
    detections_list = []
    item = None
    for detection in detections:
        if detection['class'] in category_index.keys():
            class_id = detection['class']
        else:
            class_id = get_class_id('N/A')
        item = (round(time.time()),
                video_id,
                detection['frame_sequence'],
                class_id,
                round(detection['coordinates']['left'], 3),
                round(detection['coordinates']['right'], 3),
                round(detection['coordinates']['bottom'], 3),
                round(detection['coordinates']['top'], 3),
                round(detection['score'], 3))
        detections_list.append(item)
        item = None

    insert_detections = '''
    INSERT INTO
      detections (unix_time_insertion, video_id, frame_sequence, class_id,
                  bbox_left, bbox_right, bbox_bottom, bbox_top, score)
    VALUES (?,?,?,?,?,?,?,?,?);
    '''
    manage_multiple_records(insert_detections, detections_list, 'detections')


# update counts on the video table after video processed
def update_counts(totalUp, totalDown, video_name):
    update_counts = f"""
    UPDATE video
    SET counts_up = {totalUp},
        counts_down = {totalDown}
    WHERE name = '{video_name}';
    """
    manage_database(update_counts)
