from flask import Flask, render_template, request, jsonify, redirect
from steam_tracker import get_appid, get_price, get_icon_link, get_gamename_from_appid
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tracking.db"
db = SQLAlchemy(app)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appid = db.Column(db.String(20), unique=True, nullable=False)
    gamename = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    gameicon = db.Column(db.String(500), nullable=True)
    date = db.Column(db.String(10), nullable=False)  # "dd/mm/yy"
    time = db.Column(db.String(5), nullable=False)   # "HH:MM"
    date_added = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<Game {self.gamename} ({self.appid})>"

@app.route("/", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        gamename = request.form.get("gamename")
        appid = get_appid(gamename)
        price = get_price(appid, "UK")
        gameicon = get_icon_link(appid, "UK")
        now = datetime.now()

        print(gameicon)

        existing_game = Game.query.filter_by(appid=appid).first()
        if existing_game:
            return "This game is already being tracked!"

        new_game = Game(
            appid=appid,
            gamename=get_gamename_from_appid(appid),
            price=price,
            gameicon=gameicon,
            date=now.strftime("%d/%m/%y"),
            time=now.strftime("%H:%M"),
            date_added=now
        )

        try:
            db.session.add(new_game)
            db.session.commit()
            return redirect('/')
        except:
            return "error adding game"
    else:
        games = Game.query.order_by(Game.date_added).all()
        return render_template("index.html", games=games)

if __name__ == "__main__":
    app.run(debug=True)