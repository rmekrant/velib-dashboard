"""Pipeline ETL Vélib' : extraction -> nettoyage -> chargement dans PostgreSQL."""

import logging

from extract import fetch_feed
from load import get_engine, load_station_status, load_stations
from transform import transform_station_information, transform_station_status

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def run() -> None:
    logger.info("Extraction des flux GBFS...")
    info = transform_station_information(fetch_feed("station_information"))
    status = transform_station_status(fetch_feed("station_status"))
    logger.info("%d stations, %d statuts récupérés", len(info), len(status))

    # Garde-fou : la clé étrangère refuserait un statut sans station connue
    known = status["station_id"].isin(info["station_id"])
    if (~known).any():
        logger.warning("%d statuts ignorés : station absente de station_information",
                       (~known).sum())
    status = status[known]

    engine = get_engine()
    n_stations = load_stations(info, engine)
    n_status = load_station_status(status, engine)
    logger.info("Stations insérées ou mises à jour : %d", n_stations)
    logger.info("Nouveaux relevés enregistrés : %d", n_status)


if __name__ == "__main__":
    run()