import React from "react";
import logo from "./assets/radioastronomylogo.png";
import StationsExplorer from "./components/StationsExplorer";
import StationsList from "./components/StationsList";

function App() {
  return (
    <div className="App" style={{ textAlign: "center", marginTop: "2rem" }}>
      <img src={logo} alt="SuperSID Pro Logo" style={{ height: "120px", marginBottom: "24px" }} />
      <h1>SuperSID Pro</h1>
      <h3>Radio Astronomy VLF/LF Monitoring Dashboard</h3>
      <div style={{ marginTop: "2rem", textAlign: "left", maxWidth: "1200px", margin: "2rem auto" }}>
        <StationsExplorer />
        <StationsList />
      </div>
    </div>
  );
}

export default App;