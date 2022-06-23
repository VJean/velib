"""
This simple server acts a datasource for Grafana
"""

from flask import Flask, jsonify, request
from dateutil import parser as date_parser
from datetime import timedelta

app = Flask(__name__)
metrics = ["freedocks", "bikes", "docks"]
tags = [
    {"type": "string", "text": "bike_type"},
    {"type": "string", "text": "station_name"},
]


@app.route("/")
def test_connection():
    return "Let's roll!", 200


@app.route("/search", methods=["POST"])
def search():
    return jsonify(metrics)


@app.route("/query", methods=["POST"])
def query():
    q = request.json
    date_start = date_parser.isoparse(q["range"]["from"])
    date_end = date_parser.isoparse(q["range"]["to"])
    # load corresponding files
    # TODO watch out for that timezone...
    day_start_str = date_start.date().strftime('%Y%m%d')
    day_end_str = date_end.date().strftime('%Y%m%d')
    file_start = day_start_str + "-velib-records.csv"
    file_end = day_end_str + "-velib-records.csv"
    filenames = [file_start]
    day = date_start.date()
    while filenames[-1] != file_end:
        day = day + timedelta(days=1)
        filenames.append(day.strftime('%Y%m%d') + "-velib-records.csv") 

    targets = [t["target"] for t in q["targets"] if t["type"] == "timeseries"]

    response = []
    for t in targets:
        response.append({"target": t, "datapoints": []})
    return jsonify(response)


@app.route("/annotations", methods=["POST"])
def annotations():
    pass


@app.route("/tag-keys", methods=["POST"])
def get_tag_keys():
    return jsonify(tags)


@app.route("/tag-values", methods=["POST"])
def get_tag_values():
    tag = request.json["key"]
    if tag == "bike_type":
        return jsonify([{"text": "mechanical"}, {"text": "electric"}])
    elif tag == "station_name":
        pass
