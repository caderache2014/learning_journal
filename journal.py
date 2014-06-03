# -*- coding: utf-8 -*-
# add this at the top, just below the 'coding' line
import os
# add this up at the top
import psycopg2
# add this import at the top
from contextlib import closing
from flask import Flask


DB_SCHEMA = """
DROP TABLE IF EXISTS entries;
CREATE TABLE entries (
    id serial PRIMARY KEY,
    title VARCHAR (127) NOT NULL,
    text TEXT NOT NULL,
    created TIMESTAMP NOT NULL
)
"""


# add this just below the SQL table definition we just created
app = Flask(__name__)

# add this after app is defined
app.config['DATABASE'] = os.environ.get(
    'DATABASE_URL', 'dbname=learning_journal user=caderache2014'
)

# add the rest of this below the app.config statement
def connect_db():
    """Return a connection to the configured database"""
    return psycopg2.connect(app.config['DATABASE'])

# add this function after the connect_db function
def init_db():
    """Initialize the database using DB_SCHEMA

    WARNING: executing this function will drop existing tables.
    """
    with closing(connect_db()) as db:
        db.cursor().execute(DB_SCHEMA)
        db.commit()

@app.route('/')
def hello():
    return u'Hello world!'

# put this at the very bottom of the file.
if __name__ == '__main__':
    app.run(debug=True)