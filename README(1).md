# Google Earth Engine scripts

These scripts compute the model on the whole planet. They run in the [Earth Engine Code Editor](https://code.earthengine.google.com/) (JavaScript).
Their CSV and GeoTIFF exports (to Google Drive) are the data files the Streamlit app reads.

| Order | Script | What it does | Output |
|---|---|---|---|
| 1 | `modele_final_v1.js` | **Main model.** Climate × terrain × rock filters on every pixel, grouping into 0.25° cells, scores and profiles | `final_sites_<zone>.csv`, `final_surfaces_<zone>.csv` (top sites and funnel areas) |
| 2 | `composition_top20.js` | Clay and iron-oxide ratios from Sentinel-2 (B11/B12, B4/B2) in a 2 km disc around each top site | `composition_top20.csv` |
| 3 | `acces_top100.js` | Field check for the top 100: travel time to a city, disputed territory, protected areas, plus an "accessible rank" | `acces_top100.csv` |
| 4 | `etapes_monde_export.js` | The same model as script 1, exported as a 4-band image (land, step 1, steps 1+2, steps 1+2+3) for the before/after slider of the app | `etapes_masques_<zone>.tif` (GeoTIFF, 0.05°) |
| – | `visuels_presentation.js` | Ready-made map views for screenshots (world top 100, site #4, Tibet, Altiplano) | none (maps only) |

## How to run

1. Open the Code Editor, paste a script and save it under the name given in its header.
2. Set `ZONE_CHOISIE = 'andes'` for a quick test, then `'monde'` for the global run.
3. Click **Run**, then start the export in the **Tasks** tab. Files land in your Google Drive.
4. Rename or copy the CSV files next to `app.py` (see the main repository).

If the global export hits "User memory limit exceeded", lower the resolution in `etapes_monde_export.js` (`PAS = 0.1`) or the tile size (`shardSize: 16`).

## Datasets (Earth Engine IDs)

| Use | ID |
|---|---|
| Surface temperature (day / night) | `MODIS/061/MOD11A2` |
| Vegetation (NDVI) | `MODIS/061/MOD13A2` |
| Aridity (precipitation / PET) | `IDAHO_EPSCOR/TERRACLIMATE` |
| Surface water | `JRC/GSW1_4/GlobalSurfaceWater` |
| Elevation 90 m | `MERIT/DEM/v1_0_3` |
| Rock (thermal emissivity) | `NASA/ASTER_GED/AG100_003` |
| Clays, visual check | `COPERNICUS/S2_SR_HARMONIZED` |
| Travel time to cities | `Oxford/MAP/accessibility_to_cities_2015_v1_0` |
| Borders, disputed areas | `USDOS/LSIB_SIMPLE/2017` |
| Protected areas | `WCMC/WDPA/current/polygons` |

Time window for MODIS and TerraClimate: **2023** (`DEBUT = '2023-01-01'`, `FIN = '2024-01-01'`).
