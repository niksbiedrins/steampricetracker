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
    return None

# main functions
def init_database(db_name: str, collection_name: str):
    try:
        client = MongoClient("mongodb://localhost:27017/")
        mydb = client[db_name]
        prices = mydb[collection_name]

        return mydb, prices
    except errors.ServerSelectionTimeoutError as e:
        print(f"Could not connect to MongoDB: {e}")
        return None, None

def get_appid(game_name: str) -> str:
    for app in app_list_json["applist"]["apps"]:
        if format_game_name(app["name"]) == format_game_name(game_name):
            return app["appid"]
    return None

def get_price(appid, country_code: str)  -> float:
    try:
        app_data = requests.get(f"https://store.steampowered.com/api/appdetails?appids={appid}&cc={country_code}", timeout=10)
        app_data.raise_for_status()
        app_data_json = app_data.json()

        price_string = app_data_json[str(appid)]["data"]["price_overview"]["final_formatted"]
        price_float = re.sub(r"[^\d.\s]", "", price_string)

        return price_float
    
    except requests.HTTPError as e:
        print(f"HTTP error fetching Steam data: {e}.")
    except requests.JSONDecodeError as e:
        print(f"JSON decode error: {e}.")
    except KeyError:
        print("Pirce data not found in response.")
    except ValueError:
        print("Price format error.")

def save_price(gamename: str, appid: str, price: float, prices_collection) -> str:
    if prices_collection is None:
        print("Cannot save price. No database connection!")
        return "no_connection"

    date = datetime.now().strftime("%d/%m/%y")
    time = datetime.now().strftime("%H:%M")

    existing = prices_collection.find_one({"appid": appid})
    if existing:
        print(f"{gamename} {appid} already exists in the database!")
        return "already_exists"

    try:
        prices_collection.insert_one({
            "gamename": get_gamename_from_appid(appid),
            "date": date,
            "time":  time,
            "appid": appid,
            "price": price,
        })
        print(f"Successfully stored {gamename} {appid} in the database!")
        return "success"
    except errors.PyMongoError as e:
        print(f"MongoDB error: {e}")
        return "error"

