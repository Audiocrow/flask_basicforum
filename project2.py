#Simple forum backend project
#Alexander Edgar
#CPSC476
import click
from flask import Flask, g, jsonify, request
from flask_basicauth import BasicAuth
import random
import sqlite3
import time
import uuid

app = Flask(__name__)
app.config["DEBUG"] = True

DATABASE = 'database'
sqlite3.register_converter('GUID', lambda b: uuid.UUID(bytes_le=b))
sqlite3.register_adapter(uuid.UUID, lambda u: u.bytes_le)

#make_dicts from http://flask.pocoo.org/docs/1.0/patterns/sqlite3/#initial-schemas
def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value) for idx, value in \
        enumerate(row))

#sqlite3 database setup code provided by official Flask documentation:
def get_db(shard=None):
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE + (str(shard) if shard is not None else "") + '.db', detect_types=sqlite3.PARSE_DECLTYPES)
        db.row_factory = make_dicts
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
        setattr(g, '_database', None)

#query_db from http://flask.pocoo.org/docs/1.0/patterns/sqlite3/#initial-schemas
def query_db(query, args=(), shard=None, one=False):
    try:
        res=get_db(shard).execute(query, args).fetchall()
        return (res[0] if res else None) if one else res
    except sqlite3.Error as e:
        print('EXCEPTION AT query_db:%s' %(e))
        if one: return None
        else: return []

def insert_db(query, args=(), shard=None):
    try:
        db = get_db(shard)
        cursor = db.cursor()
        cursor.execute(query, args)
        db.commit()
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
        close_connection(None)
        threads = []
        threads.append((uuid.uuid4(), 2, 'MongoDB test thread', 'adam', 'Fri, 25 Oct 2018 17:00:15 GMT'))
        threads.append((uuid.uuid4(), 1, 'Does anyone know how to start Redis?', 'bob', 'Wed, 05 Sep 2018 16:22:29 GMT'))
        threads.append((uuid.uuid4(), 1, 'Has anyone heard of Edis?', 'charlie', 'Tue, 04 Sep 2018 13:18:43 GMT'))

        for shard in range(0,3):
            db = get_db(shard)
            db.cursor().execute('''CREATE TABLE if NOT EXISTS threads (
                guid GUID PRIMARY KEY,
                forum INTEGER,
                title TEXT,
                creator TEXT,
                timestamp TEXT
            );''')
            db.cursor().execute('CREATE INDEX idx_threads ON threads(forum, creator);')
            with app.open_resource('init'+str(shard)+'.sql', mode='r') as f:
                db.cursor().executescript(f.read())
            for thread in threads:
                if thread[0].int%3 is shard:
                    db.cursor().execute('INSERT INTO threads VALUES(?,?,?,?,?);', thread)
                    if thread[2] == 'MongoDB test thread':
                        db.cursor().execute('INSERT INTO posts VALUES(?,?,?,?);', [2, 'adam', 'adam text in mongodb test thread', 'Fri, 25 Oct 2018 17:00:15 GMT'])
                    elif thread[2] == 'Does anyone know how to start Redis?':
                        db.cursor().execute('INSERT INTO posts VALUES(?,?,?,?);', [1, 'bob', 'bob text in Redis thread', 'Wed, 05 Sep 2018 16:22:29 GMT'])
                        db.cursor().execute('INSERT INTO posts VALUES(?,?,?,?);', [1, 'alice', 'snarky alice response in Redis thread', 'Wed, 05 Sep 2018 16:34:46'])
                    elif thread[2] == 'Has anyone heard of Edis?':
                        db.cursor().execute('INSERT INTO posts VALUES(?,?,?,?);', [1, 'charlie', 'charlie text in Edis thread', 'Tue, 04 Sep 2018 13:18:43 GMT'])
            db.commit()
            close_connection(None)

class BasicDBAuth(BasicAuth):
    #NOTE: USER AUTH ALWAYS ENDS UP HITTING THE USER DATABASE, NOT ONE OF THE SHARDED ones
    #I REALIZE TO FIX THIS I WOULD HAVE TO POST REDUNDANT USER DATA TO EVERY SHARD DURING CREATION OF A NEW USER
    def check_credentials(self, username, password):
        check = query_db("SELECT username FROM users WHERE username=? AND password=?", [username, password])
        result = (check != [])
        close_connection(None)
        return result

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
    #Note: has to hit all database shards
    forum_check = query_db("SELECT * FROM forums WHERE id=?", [forum_id])
    if len(forum_check) < 1:
        return jsonify("No such forum"), "404 NOT FOUND"
    close_connection(None)
    #get threads from shard 0
    threads = query_db("SELECT guid,creator,title,timestamp FROM threads WHERE forum=?", [forum_id], 0)
    close_connection(None)
    #get threads from shard 1
    threads.extend(query_db("SELECT guid,creator,title,timestamp FROM threads WHERE forum=?", [forum_id], 1))
    close_connection(None)
    #get threads from shard 2
    threads.extend(query_db("SELECT guid,creator,title,timestamp FROM threads WHERE forum=?", [forum_id], 2))
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
    #Note: does not check if the forum exists (do this elsewhere such as on the front-end?)
    input = request.get_json()
    if not input or 'title' not in input or 'text' not in input:
        return jsonify("Must provide title and text"), "400 BAD REQUEST"
    thread_id = uuid.uuid4()
    db = get_db(thread_id.int%3)
    cursor = db.cursor()
    #Note: does not check for duplicate threads (title/creator combo)
    timestamp = time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.gmtime())
    cursor.execute("INSERT INTO threads (guid,forum,title,creator,timestamp) \
    VALUES(?,?,?,?,?)", [thread_id,forum_id,input['title'], request.authorization["username"], \
        timestamp])
    cursor.execute("INSERT INTO posts (forum,author,text,timestamp) VALUES(?,?,?,?)", \
        [forum_id, request.authorization["username"], input["text"], timestamp])
    db.commit()
    response = jsonify(input['text'])
    response.status_code = 201
    response.headers['location'] = '/forums/%d/%d' %(forum_id, thread_id)
    return response

@app.route("/forums/<int:forum_id>/<int:thread_id>", methods=['GET'])
def view_posts(forum_id, thread_id):
    #Views posts in a thread on the forum
    posts = query_db("SELECT author,text,timestamp FROM posts WHERE forum=?", [forum_id], thread_id%3)
    if len(posts) < 1:
        return jsonify("Thread does not exist"), "404 NOT FOUND"
    elif len(posts) > 1:
        posts.sort(key=lambda k: k["timestamp"])
    return jsonify(posts)

@app.route("/forums/<int:forum_id>/<int:thread_id>", methods=['POST'])
@basic_auth.required
def create_post(forum_id, thread_id):
    #Post a new post in the specified thread
    shard = thread_id%3
    thread = query_db("SELECT guid FROM threads WHERE guid=?", [uuid.UUID(int=thread_id)], shard)
    if len(thread) < 1:
        return jsonify("Thread does not exist"), "404 NOT FOUND"
    input = request.get_json()
    if not input or 'text' not in input:
        return jsonify("Must provide text to post"), "400 BAD REQUEST"
    insert_db("INSERT INTO posts (forum,author,text,timestamp) VALUES(?,?,?,?)", \
        [forum_id, request.authorization["username"], input["text"], \
        time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.gmtime())], shard)
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
