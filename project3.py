#Simple forum backend project - version 3 with ScyllaDB
#Alexander Edgar
#CPSC476
from cassandra.cluster import Cluster
from cassandra.query import dict_factory
import click
from flask import Flask, g, jsonify, request
from flask_basicauth import BasicAuth
import time
import uuid

app = Flask(__name__)
app.config["DEBUG"] = True

KEYSPACE = 'bbs'
CLUSTER_IP = '172.17.0.2'

class post(dict):
    def __init__(self, author, text, timestamp):
        dict.__init__(self, author=author, text=text, timestamp=timestamp)

def get_db(UseKeyspace=True):
    db = getattr(g, '_database', None)
    if db is None:
        cluster = getattr(g, '_cluster', None)
        if cluster is None:
            cluster = g._cluster = Cluster([CLUSTER_IP])
            cluster.register_user_type(KEYSPACE, 'post', post)
        db = g._database = cluster.connect(KEYSPACE) if UseKeyspace else \
            cluster.connect()
        db.row_factory = dict_factory
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.shutdown()

#query_db from http://flask.pocoo.org/docs/1.0/patterns/sqlite3/#initial-schemas
def query_db(query, args=[], one=False):
    try:
        res=get_db().execute(query, args)
        return (res[0] if res else None) if one else res
    except Exception as e:
        print('EXCEPTION AT query_db:%s' %(e))
        if one: return None
        else: return []

@app.cli.command()
def init_db():
    #Adds a custom command to Flask to initialize the db
    #Only run this once to populate the default database
    with app.app_context():
        db = get_db(False)
        db.execute("DROP KEYSPACE IF EXISTS %s" %KEYSPACE)
        db.execute("CREATE KEYSPACE %s WITH replication = {'class':'SimpleStrategy', 'replication_factor' : '1' }" %KEYSPACE)
        db.execute("USE %s" %KEYSPACE)
        with open('init.cql', mode='r') as f:
            for command in f.read().split(';'):
                if len(command)>1:
                    db.execute(command)
        redis_forum = uuid.uuid4()
        mongodb_forum = uuid.uuid4()
        db.execute("INSERT INTO forums (id,name,creator) VALUES (%s,'redis', 'alice');", [redis_forum])
        db.execute("INSERT INTO forums (id,name,creator) VALUES (%s,'mongodb', 'bob');", [mongodb_forum])
        db.execute("""INSERT INTO threads (id,forum,title,creator,timestamp,posts) VALUES (%s, %s, 'Does anyone know how to start Redis?', 'bob',
            'Wed, 05 Sep 2018 16:34:46 GMT', [{author:'bob', text:'bob placeholder text', timestamp:'Wed, 05 Sep 2018 16:22:29 GMT'},
            {author:'alice', text:'snarky alice response', timestamp:'Wed, 05 Sep 2018 16:34:46 GMT'}]);""", [uuid.uuid4(), redis_forum])
        db.execute("""INSERT INTO threads (id,forum,title,creator,timestamp,posts) VALUES (%s, %s, 'Has anyone heard of Edis?', 'charlie', 'Tue, 04 Sep 2018 13:18:43 GMT',
            [{author:'charlie', text:'charlie placeholder text', timestamp:'Tue, 04 Sep 2018 13:18:43 GMT'}]);""", [uuid.uuid4(), mongodb_forum])


class BasicDBAuth(BasicAuth):
    def check_credentials(self, username, password):
        check = query_db("SELECT username FROM users WHERE username=%s AND password=%s", [username, password])
        return (check != [])

basic_auth = BasicDBAuth(app)

@app.route("/forums", methods=['GET'])
def view_forums():
    #Returns a list of forums
    return jsonify(list(query_db("SELECT * FROM forums;")))

@app.route("/forums", methods=['POST'])
@basic_auth.required
def create_forum():
    #Create a forum - does not check for name duplicates
    input = request.get_json()
    name = input["name"]
    forum_id = uuid.uuid4()
    get_db().execute("INSERT INTO forums (id, name, creator) VALUES (%s,%s,%s)", [forum_id,name, request.authorization["username"]])
    response = jsonify()
    response.status_code = 201
    response.headers['location'] = '/forums/%s' %(forum_id)
    return response

@app.route("/forums/<uuid:forum_id>", methods=['GET'])
def view_threads(forum_id):
    #View the list of threads in a forum. Returns 200 OK and the resulting threads
    threads = list(query_db("SELECT id,title,creator,timestamp FROM threads WHERE forum=%s", [forum_id]))
    if len(threads) > 1:
        #Sort threads in reverse chronological order
        threads.sort(key=lambda k: time.strptime(k["timestamp"], \
        "%a, %d %b %Y %H:%M:%S %Z"), reverse=True)
    elif len(threads) <= 0:
        return jsonify("No threads found.")
    return jsonify(threads)

@app.route("/forums/<uuid:forum_id>", methods=['POST'])
@basic_auth.required
def create_thread(forum_id):
    #Posts a new thread to a forum and returns HTTP 201 Created, or HTTP 400 bad request
    #Warning: does not ensure the forum exists
    input = request.get_json()
    if not input or 'title' not in input or 'text' not in input:
        return jsonify("Must provide title and text"), "400 BAD REQUEST"
    db = get_db()
    timestamp = time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.gmtime())
    thread_id = uuid.uuid4()
    post_data = [post(request.authorization['username'], input['text'], timestamp)]
    statement=db.prepare("INSERT INTO threads (id,forum,title,creator,timestamp,posts) \
        VALUES (?,?,?,?,?,?)")
    db.execute(statement, [thread_id, forum_id, input['title'], request.authorization['username'], \
        timestamp, post_data])
    response = jsonify(input['text'])
    response.status_code = 201
    response.headers['location'] = '/forums/%s/%s' %(forum_id, thread_id)
    return response

@app.route("/forums/<uuid:forum_id>/<uuid:thread_id>", methods=['GET'])
def view_posts(forum_id, thread_id):
    #Views posts in a thread on the forum
    posts = query_db("SELECT posts FROM threads WHERE id=%s AND forum=%s", [thread_id, forum_id], True)
    if not posts:
        return jsonify("Thread or forum does not exist"), "404 NOT FOUND"
    posts = posts["posts"]
    if len(posts) > 1:
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
