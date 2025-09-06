from flask import Flask, render_template, request, jsonify
from steam_tracker import get_appid, get_price, init_database, save_price

app = Flask(__name__)
mydb, prices_collection = init_database("pricehistory", "prices")

tracked_games = []

@app.route("/", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        gamename = request.form.get("gamename")
        appid = get_appid(gamename)
        price = get_price(appid, "UK")
        saved = save_price(gamename, appid, price, prices_collection)

        tracked_games.append({
            "gamename": gamename,
            "appid": appid,
            "price": price,
        })

    return render_template("index.html", tracked_games=tracked_games)
        

if __name__ == "__main__":
    app.run(debug=True)