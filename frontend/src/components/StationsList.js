import React, { useEffect, useState } from "react";
import axios from "axios";

function StationsList() {
  const [stations, setStations] = useState([]);
  const [filterType, setFilterType] = useState("VLF");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    let url = "http://localhost:8000/stations?";
    const params = [];
    if (filterType) params.push(`type=${filterType}`);
    if (search) params.push(`name=${encodeURIComponent(search)}`);
    url += params.join("&");
    axios.get(url)
      .then((response) => {
        setStations(response.data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [filterType, search]);

  return (
    <div>
      <h2>Estaciones {filterType ? filterType : "todas"} disponibles</h2>
      <div style={{ marginBottom: "1em" }}>
        <label>
          Tipo:&nbsp;
          <select value={filterType} onChange={e => setFilterType(e.target.value)}>
            <option value="">Todas</option>
            <option value="VLF">VLF</option>
            <option value="LF">LF</option>
            <option value="HF">HF</option>
            <option value="TIME">TIME</option>
          </select>
        </label>
        &nbsp;&nbsp;
        <input
          type="text"
          placeholder="Buscar nombre"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>
      {loading && <p>Cargando estaciones...</p>}
      <ul>
        {stations.map((station) => (
          <li key={station.id} style={{marginBottom:"1em"}}>
            <strong>{station.name}</strong>{" "}
            {station.status === "active"
              ? <span style={{color:"green"}}>[activo]</span>
              : <span style={{color:"red"}}>[historic]</span>}<br/>
            Tipo: {station.type} | Frecuencia: {station.frequency ? station.frequency + " kHz" : "—"}<br/>
            Ubicación: {station.country}<br/>
            Lat: {station.latitude ?? "—"}, Lon: {station.longitude ?? "—"}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default StationsList;