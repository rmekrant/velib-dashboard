"""Pipeline ETL Vélib' : extraction -> nettoyage -> chargement dans PostgreSQL."""

import logging
import sys
from pathlib import Path

from extract import fetch_feed
from load import get_engine, load_station_status, load_stations
from transform import transform_station_information, transform_station_status

# Dossier logs/ à la racine du projet, quel que soit le dossier d'où on lance le script
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

handlers = [logging.FileHandler(LOG_DIR / "pipeline.log", encoding="utf-8")]
if sys.stderr:  # pas de console quand le script est lancé par le Planificateur
    handlers.append(logging.StreamHandler())

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=handlers,
)
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
    try:
        run()
    except Exception:
        logger.exception("Échec du pipeline")  # écrit l'erreur complète dans le log
        sys.exit(1)  # code de sortie non nul = le Planificateur sait que ça a échoué