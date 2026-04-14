"""
Extract social facility data from OpenStreetMap for Australia.

1. Downloads Australia OSM extract from Geofabrik
2. Filters for relevant tags using osmium CLI
3. Converts filtered data to CSV
4. Cleans up the large PBF file

Requires: osmium-tool (apt install osmium-tool), requests
"""

import csv
import json
import os
import subprocess
import sys
import tempfile
import requests

GEOFABRIK_URL = "https://download.geofabrik.de/australia-oceania/australia-latest.osm.pbf"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "osm_social_facilities.csv")

# Tags to extract
FILTER_TAGS = [
    "n/amenity=social_facility",
    "n/amenity=community_centre",
    "n/office=ngo",
    "n/office=charity",
]

# Australian state bounding boxes for state assignment
STATE_BBOXES = [
    ("ACT", -35.95, 148.7, -35.1, 149.4),
    ("TAS", -43.7, 143.8, -39.5, 148.5),
    ("VIC", -39.2, 140.9, -33.9, 150.0),
    ("SA", -38.1, 129.0, -26.0, 141.0),
    ("NT", -26.0, 129.0, -10.9, 138.0),
    ("WA", -35.2, 112.9, -13.7, 129.0),
    ("QLD", -29.2, 137.9, -10.0, 154.0),
    ("NSW", -37.5, 140.9, -28.0, 154.0),
]

CSV_FIELDS = [
    "osm_id", "name", "lat", "lon", "state", "amenity", "office",
    "social_facility", "social_facility_for", "addr_street",
    "addr_suburb", "addr_postcode", "phone", "website", "email",
    "opening_hours", "wheelchair",
]


def lat_lon_to_state(lat, lon):
    """Assign an Australian state based on coordinates."""
    for state, s, w, n, e in STATE_BBOXES:
        if s <= lat <= n and w <= lon <= e:
            return state
    return ""


def download(dest_path):
    """Download the Geofabrik Australia extract."""
    print(f"Downloading Australia OSM extract...")
    print(f"  URL: {GEOFABRIK_URL}")

    response = requests.get(GEOFABRIK_URL, stream=True, timeout=30)
    response.raise_for_status()
    total = int(response.headers.get("content-length", 0))
    downloaded = 0

    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = downloaded * 100 // total
                mb = downloaded // (1024 * 1024)
                total_mb = total // (1024 * 1024)
                print(f"\r  {mb}/{total_mb} MB ({pct}%)", end="", flush=True)

    print(f"\n  Done.")


def filter_pbf(input_path, output_path):
    """Filter PBF using osmium CLI tool."""
    print(f"Filtering for social facilities...")
    cmd = ["osmium", "tags-filter", input_path] + FILTER_TAGS + ["-o", output_path, "--overwrite"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: osmium failed: {result.stderr}")
        sys.exit(1)
    size = os.path.getsize(output_path)
    print(f"  Filtered: {size // 1024} KB")


def convert_to_csv(filtered_pbf_path):
    """Convert filtered PBF to GeoJSON then to our CSV format."""
    print(f"Converting to CSV...")

    # Export as GeoJSON using osmium
    geojson_path = filtered_pbf_path.replace(".pbf", ".geojson")
    cmd = ["osmium", "export", filtered_pbf_path, "-o", geojson_path, "--overwrite", "-f", "geojson"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: osmium export failed: {result.stderr}")
        sys.exit(1)

    # Parse GeoJSON and write CSV
    with open(geojson_path) as f:
        data = json.load(f)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    records = []

    for feature in data.get("features", []):
        props = feature.get("properties", {})
        geom = feature.get("geometry", {})
        coords = geom.get("coordinates", [None, None])

        lon = coords[0] if coords[0] else ""
        lat = coords[1] if coords[1] else ""
        state = lat_lon_to_state(float(lat), float(lon)) if lat and lon else ""

        records.append({
            "osm_id": props.get("@id", ""),
            "name": props.get("name", ""),
            "lat": lat,
            "lon": lon,
            "state": state,
            "amenity": props.get("amenity", ""),
            "office": props.get("office", ""),
            "social_facility": props.get("social_facility", ""),
            "social_facility_for": props.get("social_facility:for", ""),
            "addr_street": props.get("addr:street", ""),
            "addr_suburb": props.get("addr:suburb", ""),
            "addr_postcode": props.get("addr:postcode", ""),
            "phone": props.get("phone", props.get("contact:phone", "")),
            "website": props.get("website", props.get("contact:website", "")),
            "email": props.get("email", props.get("contact:email", "")),
            "opening_hours": props.get("opening_hours", ""),
            "wheelchair": props.get("wheelchair", ""),
        })

    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(records)

    # Clean up geojson
    os.remove(geojson_path)

    print(f"  Written: {OUTPUT_CSV} ({len(records)} records)")
    return len(records)


def main():
    # Use temp files for the large downloads
    with tempfile.NamedTemporaryFile(suffix=".osm.pbf", delete=False) as tmp:
        full_pbf = tmp.name
    filtered_pbf = full_pbf.replace(".osm.pbf", "-filtered.osm.pbf")

    try:
        download(full_pbf)
        filter_pbf(full_pbf, filtered_pbf)
        count = convert_to_csv(filtered_pbf)
        print(f"\nDone. {count} social facilities extracted from OpenStreetMap.")
    finally:
        # Clean up large files
        for path in [full_pbf, filtered_pbf]:
            if os.path.exists(path):
                os.remove(path)
                print(f"  Cleaned up: {os.path.basename(path)}")


if __name__ == "__main__":
    main()
