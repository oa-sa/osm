# commons-au/osm

Extracts social facility data from OpenStreetMap for Australia and publishes it to [commons-au/data](https://github.com/commons-au/data).

## How It Works

1. Downloads the full Australia OSM extract from [Geofabrik](https://download.geofabrik.de/australia-oceania.html) (~889 MB)
2. Filters for social facilities, community centres, NGOs, and charities using `osmium-tool`
3. Converts the filtered data to CSV
4. Pushes to `commons-au/data/osm/`

## What It Extracts

| OSM Tag | What |
|---------|------|
| `amenity=social_facility` | Food banks, shelters, counselling, outreach, clothing banks |
| `amenity=community_centre` | Community centres |
| `office=ngo` | Non-government organisations |
| `office=charity` | Charities |

## Running Locally

```bash
pip install -r requirements.txt

# Download, filter, convert
python run.py
```

Output will be in `output/osm_social_facilities.csv`.

## Automation

Runs via GitHub Actions (manual trigger). See `.github/workflows/osm.yml`.

## Data License

OpenStreetMap data is licensed under the [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/).

Attribution: © OpenStreetMap contributors

## License

This code is released under [CC0 1.0](LICENSE) — public domain.
