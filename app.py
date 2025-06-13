from flask import Flask, render_template
import json

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/stock")
def all_stocks():
    return render_template("all_stocks.html")

@app.route("/index")
def all_indexes():
    with open("data/index_holdings.json") as f:
        index_data = json.load(f)
    show_index_data = {}
    for index_name in index_data["info"]["index_list"]:
        show_index_data[index_name] = index_data["index_data"][index_name]["name"]

    return render_template("all_indexes.html", index_data=show_index_data)

@app.route("/index/<string:index_id>")
def show_index(index_id):
    with open("data/index_holdings.json") as f:
        index_data = json.load(f)
    with open("data/stock_data.json") as f:
        stock_data = json.load(f)

    if index_id not in index_data["info"]["index_list"]:
        return "Index Not Found", 404
    return render_template(
        "show_index.html",
        index_data=index_data["index_data"][index_id],
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
