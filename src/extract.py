"""Récupération des données Vélib' depuis le flux open data GBFS."""

import json

import requests

BASE_URL = "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole"

FEEDS = {
    "station_information": f"{BASE_URL}/station_information.json",
    "station_status": f"{BASE_URL}/station_status.json",
}


def fetch_feed(feed_name: str) -> dict:
    """Télécharge un flux GBFS et renvoie le JSON sous forme de dictionnaire."""
    url = FEEDS[feed_name]
    response = requests.get(url, timeout=30)
    response.raise_for_status()  # lève une erreur si le serveur répond 404, 500...
    return response.json()


if __name__ == "__main__":
    for name in FEEDS:
        payload = fetch_feed(name)
        stations = payload["data"]["stations"]

        print(f"=== {name} ===")
        print("Clés de premier niveau :", list(payload.keys()))
        print("Nombre de stations :", len(stations))
        print("Exemple de station :")
        print(json.dumps(stations[0], indent=2, ensure_ascii=False))
        print()