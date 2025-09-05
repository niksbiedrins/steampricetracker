import re
import requests

# steam app list requests
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
app_list = requests.get("https://api.steampowered.com/ISteamApps/GetAppList/v2/", headers=headers)
app_list_json = app_list.json()

# helper funcions
def format_game_name(game_name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9\s]", "", game_name).lower().strip()

# main functions
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

# main code
gamename = get_gamename()
appid = get_appid(gamename)
price = get_price(appid, "UK")

print(price)