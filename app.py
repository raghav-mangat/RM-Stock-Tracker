from flask import Flask, render_template
import json

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
    with open("data/stock_data.json") as f:
        stock_data = json.load(f)

    if etf_id not in etf_data["info"]["etf_list"]:
        return "ETF Not Found", 404
    return render_template(
        "show_etf.html",
        etf_data=etf_data["etf_data"][etf_id],
        stock_data=stock_data["stock_data"],
        get_stock_color=get_stock_color
    )

def get_stock_color(perc_diff):
    """
    Function to determine stock color based on the percentage
    difference between last closing price and 200 DMA.
    :param perc_diff:
    :return: colour.
    """
    if perc_diff >= 10: # More than 10% above
        return "#66ff66" # Dark Green
    elif perc_diff <= -10: # More than 10% below
        return "#FF6666" # Dark Red
    elif perc_diff >= 2: # Between 2% and 10% above
        return "#99ff99" # Green
    elif perc_diff <= -2:  # Between 2% and 10% below
        return "#FF9999" # Red
    else: # Within ±2%
        return "#ffff66" # Yellow

if __name__ == "__main__":
    app.run(debug=True)