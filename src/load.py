"""Chargement des données nettoyées dans PostgreSQL."""

import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import MetaData, Table, create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import URL, Engine


def get_engine() -> Engine:
    """Crée la connexion à PostgreSQL à partir des variables du fichier .env."""
    load_dotenv()
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.environ["POSTGRES_DB"],
    )
    return create_engine(url)


def _to_records(df: pd.DataFrame) -> list[dict]:
    """Convertit un DataFrame en liste de dicts, avec None à la place des NaN/NaT."""
    return df.astype(object).where(df.notna(), None).to_dict(orient="records")


def _insert(df: pd.DataFrame, table_name: str, engine: Engine,
            conflict_cols: list[str], update: bool) -> int:
    """Insère les lignes. En cas de conflit sur la clé : met à jour ou ignore."""
    if df.empty:
        return 0

    table = Table(table_name, MetaData(), autoload_with=engine)
    stmt = insert(table).values(_to_records(df))

    if update:
        update_cols = {
            col.name: stmt.excluded[col.name]
            for col in table.columns
            if col.name not in conflict_cols
        }
        stmt = stmt.on_conflict_do_update(index_elements=conflict_cols, set_=update_cols)
    else:
        stmt = stmt.on_conflict_do_nothing(index_elements=conflict_cols)

    with engine.begin() as conn:  # transaction : tout passe, ou rien
        result = conn.execute(stmt)
    return result.rowcount


def load_stations(df: pd.DataFrame, engine: Engine) -> int:
    """Upsert des stations : ajoute les nouvelles, met à jour les existantes."""
    return _insert(df, "stations", engine, conflict_cols=["station_id"], update=True)


def load_station_status(df: pd.DataFrame, engine: Engine) -> int:
    """Ajoute les relevés, en ignorant ceux déjà présents."""
    return _insert(df, "station_status", engine,
                   conflict_cols=["station_id", "collected_at"], update=False)