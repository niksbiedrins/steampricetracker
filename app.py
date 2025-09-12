import requests
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, render_template, request, jsonify, redirect
from steam_tracker import get_appid, get_price, get_icon_link, get_gamename_from_appid

# flask init
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tracking.db"
db = SQLAlchemy(app)

# Webhook database - stores webhook url
class Webhook(db.Model):
    __tablename__ = "notification"

    id = db.Column(db.Integer, primary_key=True)
    webhook_url = db.Column(db.String(500), unique=True, nullable=False)

# Game database - stores tracked game data
class Game(db.Model):
    __tablename__ = "games"

    id = db.Column(db.Integer, primary_key=True)
    appid = db.Column(db.String(20), unique=True, nullable=False)
    gamename = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    gameicon = db.Column(db.String(500), nullable=True)
    date = db.Column(db.String(10), nullable=False)  # "dd/mm/yy"
    time = db.Column(db.String(5), nullable=False)   # "HH:MM"
    date_added = db.Column(db.DateTime, default=datetime.now)

    price_history = db.relationship("PriceHistory", backref="game", lazy=True)

# PriceHistory database - stores price history of tracked game
class PriceHistory(db.Model):
    __tablename__ = "price_history"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(10), nullable=False)  # "dd/mm/yy"
    time = db.Column(db.String(5), nullable=False)   # "HH:MM"
    created_at = db.Column(db.DateTime, default=datetime.now)

def add_new_game(gamename):
    appid = get_appid(gamename)
    price = get_price(appid, "UK")
    icon = get_icon_link(appid, "UK")
    now = datetime.now()
    
    new_game = Game(
        appid=appid,
        gamename=get_gamename_from_appid(appid),
        price=price,
        gameicon=icon,
        date=now.strftime("%d/%m/%y"),
        time=now.strftime("%H:%M"),
        date_added=now
    )

    db.session.add(new_game)
    db.session.flush()
    
    history = PriceHistory(
        game_id=new_game.id,
        price=price,
        date=now.strftime("%d/%m/%y"),
        time=now.strftime("%H:%M")
    )
    db.session.add(history)
    db.session.commit()
    return new_game

def add_webhook_url(webhook_url):
    existing = Webhook.query.first()
    if existing:
        existing.webhook_url = webhook_url
    else:
        existing = Webhook(webhook_url=webhook_url)
        db.session.add(existing)

    db.session.commit()
    return existing

def send_webhook(title, content, description, color, icon):
    embed = {
        "title": title,
        "description": description,
        "color": color,
        "image" : {
            "url": icon
        }
    }

    data = {
        "content": content,
        "embeds": [embed]
    }

    existing = Webhook.query.first()
    webhook_url = existing.webhook_url

    requests.post(webhook_url, json=data)

def check_prices():
    with app.app_context():
        tracked_games = Game.query.all()
        if not tracked_games:
            print("No games to check")
            return
        
        for game in tracked_games:
            latest_price = get_price(game.appid, "UK")
            if latest_price != game.price:
                print("Price has changed!")

                game.price = latest_price
                db.session.add(game)

                now = datetime.now()
                history = PriceHistory(
                    game_id=game.id,
                    price=latest_price,
                    date=now.strftime("%d/%m/%y"),
                    time=now.strftime("%H:%M")
                )
                db.session.add(history)

                send_webhook(
                    game.gamename,
                    "Price Updated 💰",
                    f"**AppID:** {game.appid}\n**Old Price:** £{game.price}\n**New Price:** £{latest_price}",
                    0x0099ff,
                    game.gameicon
                )

        db.session.commit()

@app.route("/", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        try:
            saved_game = add_new_game(request.form.get("gamename"))
            gamename = saved_game.gamename
            appid = saved_game.appid
            icon = saved_game.gameicon
            date = saved_game.date
            price = saved_game.price

            send_webhook(
                gamename, 
                "Added to tracking✅", 
                f"**AppID:** {appid} \n **Price:** {price} **Date:** {date}",
                0x00e074,
                icon
            )
        
            return redirect('/')
        except Exception as e:
            db.session.rollback()
            return f"Error {e}"
    else:
        games = Game.query.order_by(Game.date_added).all()
        return render_template("track.html", games=games)

@app.route("/settings", methods=["POST", "GET"])
def settings():
    if request.method == "POST":
        try:
            saved_notification = add_webhook_url(request.form.get("webhook_url"))
            webhook_url = saved_notification.webhook_url
            
            data = {"content": "Webhook has been saved!"}
            requests.post(webhook_url, json=data)

            return redirect("/")
        except Exception as e:
            db.session.rollback()
            return f"Error {e}"

    existing = Webhook.query.first()
    webhook_url = existing.webhook_url if existing else ""
    return render_template("settings.html", webhook_url=webhook_url)

@app.route("/untrack", methods=["POST"])
def untrack_game():
    data = request.get_json()
    appid = data.get("appid")
    gamename = data.get("gamename")
    price = data.get("price")
    icon = data.get("icon")

    game = Game.query.filter_by(appid=appid).first()

    try:
        PriceHistory.query.filter_by(game_id=game.id).delete()

        send_webhook(
            gamename, 
            "Removed from tracking❌", 
            f"**AppID:** {appid} \n **Price:** {price}",
            0xff5555,
            icon
        )

        db.session.delete(game)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    scheduler  = BackgroundScheduler()
    scheduler.add_job(func=check_prices, trigger="interval", seconds=10)
    scheduler.start()

    try:
        with app.app_context():
            print(f"Currently tracking {Game.query.count()} games.")
        app.run(debug=True)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()