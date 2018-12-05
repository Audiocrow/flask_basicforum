#Simple forum backend project
#Alexander Edgar
#CPSC476
import click
from flask import Flask, g, jsonify, request
from flask_basicauth import BasicAuth
import random
import sqlite3
import time

app = Flask(__name__)
app.config["DEBUG"] = True

DATABASE = 'database.db'

#make_dicts from http://flask.pocoo.org/docs/1.0/patterns/sqlite3/#initial-schemas
def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value) for idx, value in \
        enumerate(row))

#sqlite3 database setup code provided by official Flask documentation:
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = make_dicts
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

#query_db from http://flask.pocoo.org/docs/1.0/patterns/sqlite3/#initial-schemas
def query_db(query, args=(), one=False):
    try:
        res=get_db().execute(query, args).fetchall()
        return (res[0] if res else None) if one else res
    except sqlite3.Error as e:
        print('EXCEPTION AT query_db:%s' %(e))
        if one: return None
        else: return []

def insert_db(query, args=()):
    try:
        cursor = get_db().cursor()
        cursor.execute(query, args)
        get_db().commit()
    except sqlite3.Error as e:
        print('EXCEPTION AT insert_db:%s' %(e))

@app.cli.command()
def init_db():
    #Adds a custom command to Flask to initialize the db
    #Only run this once to populate the default database
    with app.app_context():
        db = get_db()
        with app.open_resource('init.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

class BasicDBAuth(BasicAuth):
    def check_credentials(self, username, password):
        check = query_db("SELECT username FROM users WHERE username=? AND password=?", [username, password])
        return (check != [])

basic_auth = BasicDBAuth(app)

@app.route("/forums", methods=['GET'])
def view_forums():
    #Returns a list of forums
    return jsonify(query_db("SELECT * FROM forums;"))

@app.route("/forums", methods=['POST'])
@basic_auth.required
def create_forum():
    input = request.get_json()
    name = input["name"]
    duplicate_check = query_db("SELECT name FROM forums WHERE name=?", [name])
    if duplicate_check:
        return jsonify("Forum already exists"), "409 CONFLICT"
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO forums (name, creator) VALUES (?,?)", [name, request.authorization["username"]])
    forum = cursor.lastrowid
    db.commit()
    response = jsonify()
    response.status_code = 201
    response.headers['location'] = '/forums/%d' %(forum)
    return response

@app.route("/forums/<int:forum_id>", methods=['GET'])
def view_threads(forum_id):
    #View the list of threads in a forum. Returns 200 OK or 404 NOT FOUND
    forum_check = query_db("SELECT * FROM forums;")
    if len(forum_check) < 1:
        return jsonify("No such forum"), "404 NOT FOUND"
    threads = query_db("SELECT id,title,creator,timestamp FROM threads WHERE forum=?", [forum_id])
    if len(threads) > 1:
        #Sort threads in reverse chronological order
        threads.sort(key=lambda k: time.strptime(k["timestamp"], \
        "%a, %d %b %Y %H:%M:%S %Z"), reverse=True)
    return jsonify(threads)

@app.route("/forums/<int:forum_id>", methods=['POST'])
@basic_auth.required
def create_thread(forum_id):
    #Posts a new thread to a forum
    #Returns the new location header and 201 CREATED, 404 NOT FOUND, or
    #400 BAD REQUEST if data was not provided
    forum = query_db("SELECT name FROM forums WHERE id=?", [forum_id], True)
    if not forum:
        return jsonify("HTTP 404 NOT FOUND"), "404 NOT FOUND"
    thread_id = query_db("SELECT COALESCE(MAX(id), 0) AS new_id FROM threads WHERE forum=?", [forum_id], True)['new_id']+1
    input = request.get_json()
    if not input or 'title' not in input or 'text' not in input:
        return jsonify("Must provide title and text"), "400 BAD REQUEST"
    db = get_db()
    cursor = db.cursor()
    #Note: does not check for duplicates
    timestamp = time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.gmtime())
    cursor.execute("INSERT INTO threads (id,forum,title,creator,timestamp) \
    VALUES(?,?,?,?,?)", [thread_id, forum_id, input['title'], request.authorization["username"], \
        timestamp])
    cursor.execute("INSERT INTO posts (thread,forum,author,text,timestamp) VALUES(?,?,?,?,?)", \
        [thread_id, forum_id, request.authorization["username"], input["text"], timestamp])
    db.commit()
    response = jsonify(input['text'])
    response.status_code = 201
    response.headers['location'] = '/forums/%d/%d' %(forum_id, thread_id)
    return response

@app.route("/forums/<int:forum_id>/<int:thread_id>", methods=['GET'])
def view_posts(forum_id, thread_id):
    #Views posts in a thread on the forum
    posts = query_db("SELECT author,text,timestamp FROM posts WHERE thread=? AND forum=?", [thread_id, forum_id])
    if len(posts) < 1:
        return jsonify("Thread or forum does not exist"), "404 NOT FOUND"
    elif len(posts) > 1:
        posts.sort(key=lambda k: k["timestamp"])
    return jsonify(posts)

@app.route("/forums/<int:forum_id>/<int:thread_id>", methods=['POST'])
@basic_auth.required
def create_post(forum_id, thread_id):
    #Post a new post in the specified thread
    thread = query_db("SELECT id FROM threads WHERE id=?", [thread_id])
    if len(thread) < 1:
        return jsonify("Thread does not exist"), "404 NOT FOUND"
    input = request.get_json()
    if not input or 'text' not in input:
        return jsonify("Must provide text to post"), "400 BAD REQUEST"
    timestamp = time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.gmtime())
    insert_db("INSERT INTO posts (thread,forum,author,text,timestamp) VALUES(?,?,?,?,?)", \
        [thread_id, forum_id, request.authorization["username"], input["text"], \
        timestamp])
    insert_db("UPDATE threads SET timestamp=? WHERE id=? AND forum=?", [timestamp, thread_id, forum_id])
    return jsonify(), "201 CREATED"

@app.route("/users", methods=['POST'])
def create_user():
    '''Creates a user in the database and returns either HTTP 201 Created,
        HTTP 400 if data was not provided, or HTTP 409 Conflict if the user
        already exists'''
    input = request.get_json()
    if not input or 'username' not in input or 'password' not in input:
        return jsonify("Must provide username and password"), "400 BAD REQUEST"
    user = input['username']
    pw = input['password']
    user_check = query_db("SELECT username FROM users WHERE username=?", [user])
    if user_check: return jsonify("User already exists"), "409 CONFLICT"
    insert_db("INSERT INTO users VALUES (?,?);", (user,pw))
    #TODO: fix returning HTTP 201 CREATED even on exception
    return jsonify("HTTP 201 CREATED"), "201 CREATED"

@app.route("/users/<username>", methods=['PUT'])
@basic_auth.required
def change_pw(username):
    '''Changes the password of a user Returns HTTP 404 if the provided username
        does not exist, HTTP 409 if the username does not match the current
        authenticated user, and HTTP 200 if OK.'''
    input = request.get_json()
    pw = input['password']
    user_check = query_db("SELECT username FROM users WHERE username=?", [username])
    if not user_check:
        return jsonify("User does not exist"), "404 NOT FOUND"
    if username != request.authorization["username"]:
        return jsonify("Username does not match current user"), "409 CONFLICT"
    insert_db("UPDATE users SET password=? WHERE username=?", [pw, username])
    return "", "200 OK"

if __name__ == "__main__":
    app.run()
