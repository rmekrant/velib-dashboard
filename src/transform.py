"""Nettoyage des données Vélib' avec Pandas."""

import pandas as pd

from extract import fetch_feed


def transform_station_information(payload: dict) -> pd.DataFrame:
    """Nettoie le flux station_information (données statiques des stations)."""
    df = pd.DataFrame(payload["data"]["stations"])

    df = df[["station_id", "stationCode", "name", "lat", "lon", "capacity"]]
    df = df.rename(columns={"stationCode": "station_code"})

    df["station_code"] = df["station_code"].astype(str)
    df["name"] = df["name"].str.strip()
    df = df.drop_duplicates(subset="station_id")

    return df


def _count_bike_type(types: list, bike_type: str) -> int:
    """Extrait le nombre de vélos d'un type depuis [{"mechanical": 19}, {"ebike": 2}]."""
    for item in types or []:
        if bike_type in item:
            return int(item[bike_type])
    return 0


def transform_station_status(payload: dict) -> pd.DataFrame:
    """Nettoie le flux station_status (données temps réel des stations)."""
    df = pd.DataFrame(payload["data"]["stations"])

    # Aplatir la liste des types de vélos en deux colonnes
    df["mechanical_bikes"] = df["num_bikes_available_types"].apply(
        lambda types: _count_bike_type(types, "mechanical")
    )
    df["ebikes"] = df["num_bikes_available_types"].apply(
        lambda types: _count_bike_type(types, "ebike")
    )

    # Timestamp Unix -> date lisible en UTC
    df["last_reported"] = pd.to_datetime(df["last_reported"], unit="s", utc=True)

    # 0/1 -> booléens
    for col in ["is_installed", "is_renting", "is_returning"]:
        df[col] = df[col].astype(bool)

    df = df.rename(columns={
        "num_bikes_available": "bikes_available",
        "num_docks_available": "docks_available",
    })

    # Moment de la collecte : indispensable pour construire l'historique plus tard
    df["collected_at"] = pd.Timestamp.now(tz="UTC").floor("min")

    df = df[[
        "station_id", "bikes_available", "mechanical_bikes", "ebikes",
        "docks_available", "is_installed", "is_renting", "is_returning",
        "last_reported", "collected_at",
    ]]
    df = df.drop_duplicates(subset="station_id")

    return df


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 20)

    info = transform_station_information(fetch_feed("station_information"))
    status = transform_station_status(fetch_feed("station_status"))

    print("=== Stations (information) ===")
    print(info.head(), "\n")
    print(info.dtypes, "\n")

    print("=== Statut temps réel ===")
    print(status.head(), "\n")
    print(status.dtypes, "\n")

    # Premiers contrôles de cohérence
    installed = status[status["is_installed"]]
    print("Stations installées :", len(installed), "/", len(status))
    print("Stations vides  :", (installed["bikes_available"] == 0).sum())
    print("Stations pleines :", (installed["docks_available"] == 0).sum())
    print("Vélos mécaniques :", status["mechanical_bikes"].sum())
    print("Vélos électriques :", status["ebikes"].sum())

    incoherent = status[
        status["bikes_available"] != status["mechanical_bikes"] + status["ebikes"]
    ]
    print("Lignes où total ≠ méca + élec :", len(incoherent))

    missing = set(status["station_id"]) - set(info["station_id"])
    print("Stations dans status sans informations :", len(missing))