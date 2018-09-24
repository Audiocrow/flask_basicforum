#Simple forum backend project
#Alexander Edgar
#CPSC476
import click
from flask import Flask, g, jsonify, request
from flask_basicauth import BasicAuth
import sqlite3

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
    # TODO: request name, creator; return HTTP 201 Created or HTTP 409 Conflict
    # Set location header field to /forums/<forum_id> for new
    print("Hello %s" % basic_auth.username())
    return

@app.route("/forums/<int:forum_id>")
def view_threads():
    # TODO
    return

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
