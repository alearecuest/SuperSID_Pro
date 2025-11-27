import React, { useEffect, useState } from "react";
import axios from "axios";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// Íconos para marcador según estado
function stationIcon(color) {
  return new L.Icon({
    iconUrl:
      color === "active"
        ? "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png"
        : "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png",
    shadowUrl:
      "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });
}

function StationsExplorer() {
  const [stations, setStations] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [filterType, setFilterType] = useState("VLF");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterCountry, setFilterCountry] = useState("");
  const [filterFreq, setFilterFreq] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    axios.get("http://localhost:8000/stations/")
      .then(res => {
        setStations(res.data);
        console.log("Datos de estaciones:", res.data); // Debug: Verifica datos recibidos
      });
  }, []);

  // Filtro avanzado por tipo, estado, país, frecuencia y búsqueda
  const filtered = stations
    .filter(s => !filterType || s.type === filterType)
    .filter(s => !filterStatus || s.status === filterStatus)
    .filter(s => !filterCountry || (s.country && s.country.toLowerCase().includes(filterCountry.toLowerCase())))
    .filter(s => !filterFreq || (s.frequency && s.frequency.toString().includes(filterFreq)))
    .filter(
      s =>
        !search ||
        s.name.toLowerCase().includes(search.toLowerCase()) ||
        (s.country && s.country.toLowerCase().includes(search.toLowerCase()))
    );

  // Selección de estación individual
  const toggleSelect = id => {
    setSelectedIds(ids =>
      ids.includes(id) ? ids.filter(x => x !== id) : [...ids, id]
    );
  };

  // Selección y deselección masiva
  const selectAll = () => setSelectedIds(filtered.map(s => s.id));
  const deselectAll = () => setSelectedIds([]);

  // Centro del mapa para mostrar la región de la primera estación filtrada
  const mapCenter =
    filtered.length && filtered[0].latitude && filtered[0].longitude
      ? [parseFloat(filtered[0].latitude), parseFloat(filtered[0].longitude)]
      : [20, 0];

  return (
    <div>
      <h2>Explorador de Estaciones</h2>
      {/* Filtros avanzados */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "1em", marginBottom: "1em" }}>
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
        <label>
          Estado:&nbsp;
          <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
            <option value="">Todos</option>
            <option value="active">Activo</option>
            <option value="historic">Histórico</option>
          </select>
        </label>
        <label>
          País:&nbsp;
          <input value={filterCountry} onChange={e => setFilterCountry(e.target.value)} placeholder="Filtrar país" />
        </label>
        <label>
          Frecuencia:&nbsp;
          <input value={filterFreq} onChange={e => setFilterFreq(e.target.value)} placeholder="Ej: 16.3" />
        </label>
        <input
          type="text"
          placeholder="Buscar por nombre o país"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <button onClick={selectAll}>Seleccionar todas (filtradas)</button>
        <button onClick={deselectAll}>Deseleccionar todas</button>
      </div>

      {/* Vista lista/tabla de estaciones filtradas */}
      <div style={{ display: "flex", gap: "2em" }}>
        <div style={{ flex: 1, minWidth: "320px", maxHeight: "650px", overflowY: "auto" }}>
          <ul>
            {filtered.map(s => (
              <li
                key={s.id}
                onClick={() => toggleSelect(s.id)}
                style={{
                  cursor: "pointer",
                  backgroundColor: selectedIds.includes(s.id) ? "#e0f7fa" : "#fff",
                  border: "1px solid #ccc",
                  borderRadius: "6px",
                  margin: "0.5em 0",
                  padding: "0.5em"
                }}
              >
                <strong>{s.name}</strong>{" "}
                {s.status === "active"
                  ? <span style={{ color: "green" }}>[activo]</span>
                  : <span style={{ color: "red" }}>[historic]</span>}
                <br />
                Tipo: {s.type} | Frecuencia: {s.frequency ? s.frequency + " kHz" : "—"}
                <br />
                País: {s.country}
                <br />
                Lat: {s.latitude}, Lon: {s.longitude}
                <br />
                <span>
                  {selectedIds.includes(s.id)
                    ? "✅ Seleccionada"
                    : "Haz click para seleccionar"}
                </span>
              </li>
            ))}
          </ul>
        </div>
        {/* Mapa con marcadores */}
        <div style={{ flex: 2, minWidth: "400px" }}>
          <MapContainer center={mapCenter} zoom={2.5} style={{ height: "600px", width: "100%" }}>
            <TileLayer
              attribution="Map data &copy; OpenStreetMap contributors"
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {filtered
              .filter(s => s.latitude && s.longitude && !isNaN(s.latitude) && !isNaN(s.longitude))
              .map(s => (
                <Marker
                  key={s.id}
                  position={[parseFloat(s.latitude), parseFloat(s.longitude)]}
                  icon={stationIcon(s.status)}
                  eventHandlers={{
                    click: () => toggleSelect(s.id)
                  }}
                >
                  <Popup>
                    <strong>{s.name}</strong><br />
                    {s.status === "active"
                      ? <span style={{ color: "green" }}>[activo]</span>
                      : <span style={{ color: "red" }}>[historic]</span>}
                    <br />
                    Tipo: {s.type}
                    <br />
                    Frecuencia: {s.frequency ? s.frequency + " kHz" : "—"}
                    <br />
                    País: {s.country}
                    <br />
                    Lat: {s.latitude}, Lon: {s.longitude}
                  </Popup>
                </Marker>
              ))}
          </MapContainer>
        </div>
      </div>

      {/* Muestra resumen selecciones */}
      <div style={{ marginTop: "2em" }}>
        <h3>Estaciones seleccionadas ({selectedIds.length}):</h3>
        <ul>
          {filtered.filter(s => selectedIds.includes(s.id)).map(s => (
            <li key={s.id}>
              <strong>{s.name}</strong> ({s.frequency ? s.frequency + " kHz" : "—"}, {s.country})
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default StationsExplorer;