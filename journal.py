# -*- coding: utf-8 -*-
# add this at the top, just below the 'coding' line
import os
import psycopg2
import markdown
from contextlib import closing
from datetime import datetime
from dateutil import tz
from flask import Flask
from flask import g
from flask import render_template
from flask import abort
from flask import request
from flask import url_for
from flask import redirect
from flask import session
from passlib.hash import pbkdf2_sha256
from pyshorteners.shorteners import Shortener

shortener = Shortener('GoogleShortener')


DB_SCHEMA = """
DROP TABLE IF EXISTS entries;
CREATE TABLE entries (
    id serial PRIMARY KEY,
    title VARCHAR (127) NOT NULL,
    text TEXT NOT NULL,
    created TIMESTAMP NOT NULL
)
"""
DB_ENTRY_INSERT = """
INSERT INTO entries (title, text, created) VALUES (%s, %s, %s)
"""

DB_SPECIFIC_ENTRY = """
SELECT id, title, text, created FROM entries WHERE id = %s
"""
DB_ENTRIES_LIST = """
SELECT id, title, text, created FROM entries ORDER BY created DESC
"""
DB_ENTRY_UPDATE = """
UPDATE ONLY entries AS en
SET (title, text, created) = (%s, %s, %s)
WHERE entry_id = %s
"""

DB_ENTRY_LIST=  """
SELECT id, title, text, created FROM entries AS en
WHERE text = %s AND title = %s
"""



# add this just below the SQL table definition we just created
app = Flask(__name__)

#0
def _markdown(text):
    return markdown.markdown(text, extensions=['codehilite'])

#1
def get_local_datetime(utc_time):
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()
    utc_time = utc_time.replace(tzinfo=from_zone)
    return utc_time.astimezone(to_zone)

#2
def get_entry(entry_id):
    conn = get_database_connection()
    cur = conn.cursor()
    cur.execute(DB_ENTRY_LIST, [entry_id])
    keys = ('id', 'title', 'text', 'created')
    try:
        fetched = cur.fetchall()[0]
    except IndexError:
        return None
    entry = {keys[i]: fetched[i] for i in xrange(len(keys))}
    entry['html'] = _markdown(entry['text'])
    return entry

#3
def get_all_entries():
    conn = get_database_connection()
    cur = conn.cursor()
    cur.execute(DB_ENTRIES_LIST)
    entries = cur.fetchall()
    keys = ('id', 'title', 'text', 'created')
    return [dict(zip(keys, e)) for e in entries]

#4
def get_specific_entry(entry_no):
    conn = get_database_connection()
    cur = conn.cursor()
    cur.execute(DB_SPECIFIC_ENTRY, [entry_no])
    keys = ('id', 'title', 'text', 'created')
    return [dict(zip(keys, e)) for e in cur.fetchall()][0]

#5
def write_entry(title, text):
    if not title or not text:
        raise ValueError("Need title and text required for writing an entry")
    con = get_database_connection()
    cur = con.cursor()
    now = datetime.utcnow()
    cur.execute(DB_ENTRY_INSERT, [title, text, now])

#6
def update_entry(entry_id, new_title, new_text):
    if not new_title or not new_text:
        raise ValueError("Text or title required for updating an entry")
    conn = get_database_connection()
    curr = conn.cursor()
    now = datetime.datetime.utcnow()
    cur.execute(DB_ENTRY_UPDATE, (new_title, new_text, now, entry_Id))

def get_one_entry_ajax():
    con = get_database_connection()
    cur = con.cursor()
    cur.execute(DB_ENTRIES_LIST)
    return cur.fetchone()
    
#7
@app.route('/')
def show_entries():
    entries = get_all_entries()
    for entry in entries:
        entry['text'] = markdown.markdown(entry['text'], extensions=['codehilite'])
        entry['created'] = get_local_datetime(entry['created'])
    return render_template('list_entries.html', entries=entries)

#8
@app.route('/entry/<int:entry_id>/')
def show_entry(entry_id):
        e = get_entry(entry_id)
        e['text'] = markdown.markdown(e['text'], extensions=['codehilite']) 
        return render_template('list_entry.html', entry=entry)

#8
@app.route('/add', methods=['POST'])
def add_entry():
        if 'logged_in' in session:
            try:
                write_entry(request.form['title'], request.form['text'])
            except psycopg2.Error:
                abort(500)
            return redirect(url_for('show_new_entry_ajax'))
        else:
            return redirect(url_for('login'))

@app.route('/show_new_entry_ajax')
def show_new_entry_ajax():
    entry = get_one_entry_ajax()
    return render_template('show_with_ajax.html', entry=entry)

#COPY
@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if not post_id or 'logged_in' not in session or \
        session['logged_in'] is False:
            return redirect(url_for('show_entries'))
    entry = get_entry(post_id)
    if request.method == 'POST' and entry is not None:
        try:
            edit_entry(post_id, request.form['title'], request.form['text'])
            return redirect(url_for('show_entries'))
        except psycopg2.Error:
            abort(500)
    return render_template('edit_entry.html', entry=entry)


@app.route('/entry/<int:entry_id>/edit/', methods=['GET', 'POST'])
def edit_entry(entry_id):
    if 'logged_in' in session:
        if request.method ==  'GET':
            e = get_entry(entry_id)
            return render_template('edit.html', entry=entry)
        elif request.method == 'POST':
            try:
                update_entry(entry_id, request.form['title'], request.form['text'])
            except psycopg2.Error:
                abort(500)
            return redirect(url_for, 'show_entry', entry_id=entry_id)
    else:
        return redirect(url_for('login'))

#COPY
def edit_entry(post_id, title, text):
    if not title or not text:
        raise ValueError("Title and text required for writing an entry")
    con = get_database_connection()
    cur = con.cursor()
    now = datetime.datetime.utcnow()
    cur.execute(DB_ENTRY_EDIT, (title, text, now, post_id))
#10
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        try:
            do_login(request.form['username'].encode('utf-8'), request.form['password'].encode('utf-8'))
            return redirect(url_for('show_entries'))
        except ValueError:
            error = "Failed to Log In"
        
    return render_template('login.html', error=error)

#11
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('show_entries'))

#13
@app.route('/edit/<entry_number>', methods=['GET', 'POST'])
def edit(entry_no):
    if request.method == 'GET':
        e = get_specific_entry(entry_no)
        return render_template('edit.html', entry=entry)
    elif request.method == 'POST':
        update_entry(request.form['title'], request.form['text'], entry_no )
        return redirection(url_for('show_entries'))

# add this after app is defined
app.config['DATABASE'] = os.environ.get(
    'DATABASE_URL', 'dbname=learning_journal'
)

# this configuratin setting is already there
app.config['DATABASE'] = os.environ.get(
    'DATABASE_URL', 'dbname=learning_journal'
)
# add the following two new settings just below
app.config['ADMIN_USERNAME'] = os.environ.get(
    'ADMIN_USERNAME', 'admin'
)
# then update the ADMIN_PASSWORD config setting:
app.config['ADMIN_PASSWORD'] = os.environ.get(
    'ADMIN_PASSWORD', pbkdf2_sha256.encrypt('admin')
)

app.config['SECRET_KEY'] = os.environ.get(
    'FLASK_SECRET_KEY', 'sooperseekritvaluenooneshouldknow'
)

#14
def connect_db():
    """Return a connection to the configured database"""
    return psycopg2.connect(app.config['DATABASE'])

#15
def init_db():
    """Initialize the database using DB_SCHEMA

    WARNING: executing this function will drop existing tables.
    """
    with closing(connect_db()) as db:
        db.cursor().execute(DB_SCHEMA)
        db.commit()

#16
def get_database_connection():
    db = getattr(g, 'db', None)
    if db is None:
        g.db = db = connect_db()
    return db

#17
def do_login(username='', passwd=''):
    if username != app.config['ADMIN_USERNAME']:
        raise ValueError
    if not pbkdf2_sha256.verify(passwd, app.config['ADMIN_PASSWORD']):
        raise ValueError
    session['logged_in'] = True

#18
@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        if exception and isinstance(exception, psycopg2.Error):
            # if there was a problem with the database, rollback any
            # existing transaction
            db.rollback()
        else:
            # otherwise, commit
            db.commit()
        db.close()   

# put this at the very bottom of the file.
if __name__ == '__main__':
    app.run(debug=True)
