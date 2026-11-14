
import ee

from test_earth_engine import PROJECT_ID

# 1. Connexion à ton projet Google Cloud
ee.Initialize(project=PROJECT_ID)

# 2. Zone d'étude : désert d'Atacama
latitude = -24.50
longitude = -69.25

point = ee.Geometry.Point([longitude, latitude])
zone = point.buffer(5000)

# 3. Charger le modèle numérique de terrain
collection = ee.ImageCollection(
    "COPERNICUS/DEM/GLO30"
).filterBounds(zone)

dem = (
    collection.select("DEM")
    .mosaic()
    .setDefaultProjection(collection.first().projection())
)

# 4. Calculer la pente
pente = ee.Terrain.slope(dem)

# 5. Extraire les statistiques
resultats = dem.rename("altitude").addBands(
    pente.rename("pente")
).reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=zone,
    scale=30,
    maxPixels=1e8
).getInfo()

print("=== ANALYSE ATACAMA ===")
print("Altitude moyenne :", resultats["altitude"], "m")
print("Pente moyenne :", resultats["pente"], "degrés")
