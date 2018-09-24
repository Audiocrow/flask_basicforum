import click
from flask import Flask, g, jsonify, request
from flask_basicauth import BasicAuth
import sqlite3

app = Flask(__name__)
app.config["DEBUG"] = True

#sqlite3 database setup from official Flask documentation:
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

#Add a custom command to Flask to initialize the db
#Only run this once to populate the default database
@app.cli.command()
def init_db():
    #Code provided by official Flask documentation:
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
    try:
        db = get_db()
        cur = db.cursor()
        forums = cur.execute("SELECT * FROM forums;").fetchall()
        print(forums)
        return jsonify(forums)
    except:
        return jsonify([])

@app.route("/forums", methods=['POST'])
@basic_auth.required
def create_forum():
    # TODO: request name, creator; return HTTP 201 Created or HTTP 409 Conflict
    # Set location header field to /forums/<forum_id> for new
    return

@app.route("/forums/<int:forum_id>")
def view_threads():
    # TODO
    return

if __name__ == "__main__":
    app.run()
