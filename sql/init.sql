-- Dimension : une ligne par station (données qui changent rarement)
CREATE TABLE IF NOT EXISTS stations (
    station_id    BIGINT PRIMARY KEY,
    station_code  TEXT NOT NULL,
    name          TEXT NOT NULL,
    lat           DOUBLE PRECISION NOT NULL,
    lon           DOUBLE PRECISION NOT NULL,
    capacity      INTEGER NOT NULL CHECK (capacity >= 0),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Faits : une ligne par station et par relevé
CREATE TABLE IF NOT EXISTS station_status (
    station_id        BIGINT NOT NULL REFERENCES stations (station_id),
    bikes_available   INTEGER NOT NULL CHECK (bikes_available >= 0),
    mechanical_bikes  INTEGER NOT NULL CHECK (mechanical_bikes >= 0),
    ebikes            INTEGER NOT NULL CHECK (ebikes >= 0),
    docks_available   INTEGER NOT NULL CHECK (docks_available >= 0),
    is_installed      BOOLEAN NOT NULL,
    is_renting        BOOLEAN NOT NULL,
    is_returning      BOOLEAN NOT NULL,
    last_reported     TIMESTAMPTZ,
    collected_at      TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (station_id, collected_at)
);

-- Accélère les requêtes filtrées par date (utile quand l'historique grossira)
CREATE INDEX IF NOT EXISTS idx_station_status_collected_at
    ON station_status (collected_at);