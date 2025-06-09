from flask import Flask, render_template
from dotenv import load_dotenv
import os
import json

load_dotenv()

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

app = Flask(__name__)

@app.route("/")
def home():
    with open("data/etf_holdings.json") as f:
        etf_data = json.load(f)
    show_etf_data={}
    for etf_name in etf_data["info"]["etf_list"]:
        show_etf_data[etf_name] = etf_data["etf_data"][etf_name]["name"]

    return render_template("home.html", etf_data=show_etf_data)

@app.route("/etf/<string:etf_id>")
def show_etf(etf_id):
    with open("data/etf_holdings.json") as f:
        etf_data = json.load(f)
    if etf_id not in etf_data["info"]["etf_list"]:
        return "ETF Not Found", 404
    return render_template("show_etf.html", etf_data=etf_data["etf_data"][etf_id])
if __name__ == "__main__":
    app.run(debug=True)