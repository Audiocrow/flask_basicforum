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
        cur = get_db().execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv
    except:
        if one: return None
        else: return []

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
    def check_credentials(username, password):
        # TODO: check with db to see if valid
        return False

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
    '''Creates a user in the database and returns either HTTP 201 Created
        or HTTP 409 Conflict if the user already exists'''
    return

if __name__ == "__main__":
    app.run()
