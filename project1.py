#Simple forum backend project
#Alexander Edgar
#CPSC476
import click
from flask import Flask, g, jsonify, request
from flask_basicauth import BasicAuth
import sqlite3

app = Flask(__name__)
app.config["DEBUG"] = True

#sqlite3 database setup code provided by official Flask documentation:
DATABASE = 'database.db'
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.cli.command()
def init_db():
    #Adds a custom command to Flask to initialize the db
    #Only run this once to populate the default database
    with app.app_context():
        db = get_db()
        with app.open_resource('init.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def select_dicts(query : str, params=None) -> list:
    '''Queries the database with the given SELECT statement and zips the column
        names together with the results, then returns a list
        of column_name:value rows'''
    try:
        db = get_db()
        cursor = db.cursor()
        rows = cursor.execute(query, params).fetchall() if params\
            else cursor.execute(query)
        return [dict(zip([colname[0] for colname in cursor.description], row)) \
            for row in rows]
    except sqlite3.Error as e:
        print(e)
        return []

class BasicDBAuth(BasicAuth):
    def check_credentials(username, password):
        # TODO: check with db to see if valid
        return False

basic_auth = BasicDBAuth(app)

@app.route("/forums", methods=['GET'])
def view_forums():
    #Returns a list of forums
    return jsonify(select_dicts("SELECT * FROM forums;"))

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

if __name__ == "__main__":
    app.run()
