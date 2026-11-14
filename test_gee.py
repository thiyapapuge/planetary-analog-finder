
import ee

PROJECT = "identify-earth-locations"
LAT = -24.5
LON = -69.25

ee.Initialize(project=PROJECT)

point = ee.Geometry.Point([LON, LAT])
region = point.buffer(5000)

print("=== DIAGNOSTIC GOOGLE EARTH ENGINE ===")

# 1. Vérifier les coordonnées
print("Point :", point.coordinates().getInfo())

# 2. Tester NASADEM sans reprojection
dem = ee.Image("NASA/NASADEM_HGT/001").select("elevation")

print("Altitude NASADEM :",
      dem.reduceRegion(
          reducer=ee.Reducer.firstNonNull(),
          geometry=region,
          scale=30,
          maxPixels=1000000
      ).getInfo())

# 3. Calculer une pente simple
slope = ee.Terrain.slope(dem).rename("slope")

print("Pente NASADEM :",
      slope.reduceRegion(
          reducer=ee.Reducer.mean(),
          geometry=region,
          scale=90,
          maxPixels=1000000
      ).getInfo())

# 4. Vérifier le nombre de tuiles Copernicus
cop = (ee.ImageCollection("COPERNICUS/DEM/GLO30")
       .filterBounds(region))

print("Nombre de tuiles Copernicus :", cop.size().getInfo())

# 5. Vérifier la projection UTM
utm = point.transform("EPSG:32719", 1)
print("Coordonnées UTM :", utm.coordinates().getInfo())

print("=== FIN DU DIAGNOSTIC ===")
