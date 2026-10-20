-- Tous les relevés, enrichis des infos station et des indicateurs calculés
CREATE OR REPLACE VIEW v_status_history AS
SELECT
    st.station_id,
    s.station_code,
    s.name,
    s.lat,
    s.lon,
    s.capacity,
    st.collected_at,
    st.bikes_available,
    st.mechanical_bikes,
    st.ebikes,
    st.docks_available,
    -- Taux de remplissage sur les bornettes réellement utilisables
    ROUND(
        st.bikes_available::numeric
        / NULLIF(st.bikes_available + st.docks_available, 0),
        4
    ) AS fill_rate,
    CASE
        WHEN st.bikes_available + st.docks_available = 0 THEN 'Hors service'
        WHEN st.bikes_available = 0 THEN 'Vide'
        WHEN st.docks_available = 0 THEN 'Pleine'
        ELSE 'Disponible'
    END AS station_state
FROM station_status AS st
JOIN stations AS s USING (station_id)
WHERE st.is_installed;

-- Le dernier relevé de chaque station : c'est ce que montre le tableau de bord
CREATE OR REPLACE VIEW v_latest_status AS
SELECT DISTINCT ON (station_id) *
FROM v_status_history
ORDER BY station_id, collected_at DESC;