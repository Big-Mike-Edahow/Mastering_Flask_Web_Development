# init_db.py
# Initialize database and create table

import sqlite3
import datetime

conn = sqlite3.connect('database.db')
curs = conn.cursor()

with open('schema.sql') as f:
    conn.executescript(f.read())

conn.commit()

title = "Big Mike's Trucking Adventures"
text = "Big Mike drives Truck spring, summer and fall across America, from sea to shining sea."
publish_date = datetime.datetime.now()
user_id = 1

data_tuple = (title, text, publish_date, user_id)
sql_query = '''INSERT INTO post (title, text, publish_date, user_id) VALUES (?, ?, ?, ?);'''

curs.execute(sql_query, data_tuple)
conn.commit()

title = "Keep It Simple, Stupid"
text = "Big Mike has to start out small and simple and build from there. Give Big Mike enough time, and he'll get there."
publish_date = datetime.datetime.now()
user_id = 1

data_tuple = (title, text, publish_date, user_id)
sql_query = '''INSERT INTO post (title, text, publish_date, user_id) VALUES (?, ?, ?, ?);'''

curs.execute(sql_query, data_tuple)
conn.commit()

conn.close()

