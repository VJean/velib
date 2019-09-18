from flask import Flask, jsonify, request

app = Flask(__name__)
metrics = ["freedocks", "bikes", "docks"]
tags = [{"type":"string","text":"bike_type"},{"type":"string","text":"station_name"}]


@app.route("/")
def test_connection():
    return "Let's roll!", 200


@app.route("/search", methods=["POST"])
def search():
    return jsonify(metrics)


@app.route("/query", methods=["POST"])
def query():
    pass


@app.route("/annotations", methods=["POST"])
def annotations():
    pass


@app.route("/tag-keys", methods=["POST"])
def get_tag_keys():
    return jsonify(tags)


@app.route("/tag-values", methods=["POST"])
def get_tag_values():
    tag = request.json['key']
    if tag == "bike_type":
        return jsonify([{"text":"mechanical"},{"text":"electric"}])
    elif tag == "station_name":
        pass
