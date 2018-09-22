from flask import jsonify, request
app = Flask(__name__)
app.config["DEBUG"] = True

@app.route("/forums", methods=['GET'])
def view_forums:
    # TODO: return id, name, creator, HTTP 200 OK
    return

@app.route("/forums", methods=['POST'])
def create_forum:
    # TODO: request name, creator; return HTTP 201 Created or HTTP 409 Conflict
    # Set location header field to /forums/<forum_id> for new
    return

@app.route("/forums/<int:forum_id>")
def view_threads:
    # TODO
    return

if __name__ == "main":
    app.run()
