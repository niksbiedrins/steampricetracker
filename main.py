import re
from datetime import datetime
from pymongo import MongoClient, errors
import requests

# steam app list requests
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
app_list = requests.get("https://api.steampowered.com/ISteamApps/GetAppList/v2/", headers=headers)
app_list_json = app_list.json()

# helper funcions
def format_game_name(game_name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9\s]", "", game_name).lower().strip()

def get_gamename_from_appid(appid: str):
    for app in app_list_json["applist"]["apps"]:
        if app["appid"] == appid:
            return app["name"]

# main functions
def init_database(db_name: str, collection_name: str):
    client = MongoClient("mongodb://localhost:27017/")
    mydb = client[db_name]
    prices = mydb[collection_name]

    return mydb, prices

def get_gamename() -> str:
    return str(input("Enter the game name you want to track: "))

def get_appid(game_name: str) -> str:
    for app in app_list_json["applist"]["apps"]:
        if format_game_name(app["name"]) == format_game_name(game_name):
            return app["appid"]

def get_price(appid, country_code: str)  -> float:
    app_data = requests.get(f"https://store.steampowered.com/api/appdetails?appids={appid}&cc={country_code}")
    app_data_json = app_data.json()

    price_string = app_data_json[str(appid)]["data"]["price_overview"]["final_formatted"]
    price_float = re.sub(r"[^\d.\s]", "", price_string)

    return price_float

def save_price(gamename: str, appid: str, price: float, prices_collection):
    date = datetime.now().strftime("%d/%m/%y")
    time = datetime.now().strftime("%H:%M")

    try:
        prices_collection.insert_one({
            "gamename": get_gamename_from_appid(appid),
            "date": date,
            "time":  time,
            "appid": appid,
            "price": price,
        })
        print(f"Successfully stored {gamename} {appid} in the database!")
    except errors.DuplicateKeyError:
        print(f"{gamename} {appid} already exists in the database!")

# main code
mydb, prices_collection = init_database("pricehistory", "prices")
gamename = get_gamename()
appid = get_appid(gamename)
price = get_price(appid, "UK")

save_price(gamename, appid, price, prices_collection)
