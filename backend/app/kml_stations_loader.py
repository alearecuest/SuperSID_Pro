import xml.etree.ElementTree as ET
from app.models import Station
from app.database import SessionLocal, Base, engine
import re

KML_FILES = [
    ("vlf.kml", "VLF"),
    ("time.kml", "TIME"),
]

ns = {'kml': 'http://earth.google.com/kml/2.2'}

def parse_frequency(desc):
    match = re.search(r'(\d+(?:\.\d+)?)\s*kHz', desc)
    if match:
        return float(match.group(1))
    return None

def parse_status(style_url):
    if style_url is not None and 'disabled' in style_url:
        return "historic"
    return "active"

def parse_type(folder_name, desc, default_type):
    folder = folder_name.lower() if folder_name else ""
    if 'vlf' in folder:
        return 'VLF'
    if 'lf' in folder:
        return 'LF'
    if 'hf' in folder:
        return 'HF'
    freq = parse_frequency(desc)
    if freq:
        if freq < 30:
            return 'VLF'
        elif 30 <= freq < 300:
            return 'LF'
        else:
            return 'HF'
    return default_type

def parse_kml_file(filepath, default_type):
    tree = ET.parse(filepath)
    root = tree.getroot()
    stations = []

    for folder in root.findall('.//kml:Folder', ns):
        folder_name = folder.find('kml:name', ns)
        folder_name = folder_name.text if folder_name is not None else ""
        for placemark in folder.findall('.//kml:Placemark', ns):
            name = placemark.find('kml:name', ns)
            name = name.text if name is not None else None
            desc = placemark.find('kml:description', ns)
            desc = desc.text if desc is not None else ""
            coords_elem = placemark.find('.//kml:coordinates', ns)
            coords = coords_elem.text.strip() if coords_elem is not None else ""
            style_url = placemark.find('kml:styleUrl', ns)
            style_url = style_url.text if style_url is not None else ""

            lon, lat = None, None
            if coords:
                parts = coords.split(',')
                if len(parts) >= 2:
                    lon, lat = parts[0], parts[1]

            frequency = parse_frequency(desc)
            type_ = parse_type(folder_name, desc, default_type)
            status = parse_status(style_url)

            desc_lines = re.sub(r'<br\s*/?>', '\n', desc).split('\n')
            country = desc_lines[-1].strip() if len(desc_lines) > 1 else folder_name

            if name and lat and lon:
                stations.append({
                    "name": name,
                    "frequency": frequency,
                    "country": country,
                    "type": type_,
                    "latitude": float(lat),
                    "longitude": float(lon),
                    "status": status
                })
    return stations

def save_stations_to_db(stations):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    for s in stations:
        exists = db.query(Station).filter_by(
            name=s["name"], frequency=s["frequency"]).first()
        if not exists:
            db_station = Station(
                name=s["name"],
                frequency=s["frequency"],
                country=s["country"],
                type=s["type"],
                latitude=s["latitude"],
                longitude=s["longitude"],
            )
            db.add(db_station)
    db.commit()
    db.close()
    print(f"{len(stations)} stations processed and stored.")

if __name__ == "__main__":
    all_stations = []
    for file, default_type in KML_FILES:
        print(f"Procesando {file} ...")
        stations = parse_kml_file(file, default_type)
        print(f"{len(stations)} estaciones encontradas.")
        all_stations.extend(stations)
    save_stations_to_db(all_stations)