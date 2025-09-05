import re
import requests

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

# steam app list
app_list = requests.get("https://api.steampowered.com/ISteamApps/GetAppList/v2/", headers=headers)
app_list_json = app_list.json()

def get_gamename():
    return str(input("Enter the game name you want to track: "))

def get_appid(game_name: str):
    for app in app_list_json["applist"]["apps"]:
        if app["name"].lower() == game_name.lower():
            return app["appid"]

def get_price(appid, country_code: str):
    app_data = requests.get(f"https://store.steampowered.com/api/appdetails?appids={appid}&cc={country_code}")
    app_data_json = app_data.json()

    final_formatted = app_data_json[str(appid)]["data"]["price_overview"]["final_formatted"]

    return final_formatted

# main code
gamename = get_gamename()
appid = get_appid(gamename)
price = get_price(appid, "UK")

print(price)