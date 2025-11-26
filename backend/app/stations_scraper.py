import requests
from bs4 import BeautifulSoup
from app.models import Station
from app.database import SessionLocal, Base, engine

SIDSTATION_URL = "https://sidstation.loudet.org/stations-list-en.xhtml"

def fetch_stations():
    response = requests.get(SIDSTATION_URL)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    stations_list = []
    table = soup.find("table")
    if not table:
        print("No stations table found!")
        return []

    rows = table.find_all("tr")[1:]
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 6:
            continue
        name = cols[0].get_text(strip=True)
        # Get Frequency
        frequency_str = cols[1].get_text(strip=True)
        try:
            frequency = float(frequency_str)
        except ValueError:
            frequency = None
        # Get Country
        country = cols[2].get_text(strip=True)
        # Get Type (VLF/LF/ELF)
        type_ = cols[3].get_text(strip=True)
        # Get Latitude
        lat_str = cols[4].get_text(strip=True)
        try:
            latitude = float(lat_str)
        except ValueError:
            latitude = None
        # Get Longitude
        lon_str = cols[5].get_text(strip=True)
        try:
            longitude = float(lon_str)
        except ValueError:
            longitude = None

        stations_list.append({
            "name": name,
            "frequency": frequency,
            "country": country,
            "type": type_,
            "latitude": latitude,
            "longitude": longitude
        })

    return stations_list

def save_stations_to_db():
    Base.metadata.create_all(bind=engine)
    stations = fetch_stations()
    db = SessionLocal()
    for station in stations:
        exists = db.query(Station).filter_by(
            name=station["name"],
            frequency=station["frequency"]
        ).first()
        if not exists:
            db_station = Station(
                name=station["name"],
                frequency=station["frequency"],
                country=station["country"],
                type=station["type"],
                latitude=station["latitude"],
                longitude=station["longitude"]
            )
            db.add(db_station)
    db.commit()
    db.close()
    print(f"{len(stations)} stations processed and stored.")

if __name__ == "__main__":
    save_stations_to_db()