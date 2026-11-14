
import ee

# Remplacer par ton véritable ID de projet Google Cloud
PROJECT_ID = "identify-earth-locations"

# Initialiser la connexion
ee.Initialize(project=PROJECT_ID)

# Charger un jeu de données d'altitude
dem = ee.ImageCollection("COPERNICUS/DEM/GLO30")

# Vérifier que Google Earth Engine répond
print("Connexion Google Earth Engine réussie !")
print("Nombre de tuiles DEM :", dem.size().getInfo())
