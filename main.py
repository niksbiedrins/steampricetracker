import re
import requests
from bs4 import BeautifulSoup

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
get_app_data_response = requests.get("https://api.steampowered.com/ISteamApps/GetAppList/v2/", headers=headers)
data = get_app_data_response.json()

def get_gamename():
    return str(input("Enter the game name you want to track: "))

def get_appid(game_name: str):
    for app in data["applist"]["apps"]:
        if app["name"].lower() == game_name.lower():
            return app["appid"]

def get_app_html(appid: int):
    steam_app_response = requests.get(f"https://store.steampowered.com/app/{appid}")
    return BeautifulSoup(steam_app_response.text, "html.parser")

def parse_app_price(app_html):
    price_container = app_html.find_all("div", class_="game_purchase_action")
    
    for element in price_container:
        price_div =  element.find("div", class_="game_purchase_price price")
        price_text = price_div.get_text(strip=True)
        formatted_price = float(re.sub(r"[^\d.]", "", price_text)) # remove currency symbol and cast to a float.
        return formatted_price

# main code
gamename = get_gamename()
appid = get_appid(gamename)
app_html = get_app_html(appid)
price = parse_app_price(app_html)

print(price)