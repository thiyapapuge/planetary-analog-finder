"""Mesures satellites Earth Engine pour Planetary Analog Finder.

Les indicateurs sont descriptifs, non directement comparables à des mesures
lunaires/martiennes sans harmonisation des résolutions et périodes.
"""
from datetime import date
import ee

LANDCOVER = {10:'Arbres',20:'Arbustes',30:'Prairies',40:'Cultures',50:'Zones bâties',
             60:'Sol nu / végétation clairsemée',70:'Neige / glace',80:'Eau',
             90:'Zones humides herbacées',95:'Mangroves',100:'Mousses / lichens'}


def initialize(project_id: str):
    if not project_id or not project_id.strip():
        raise ValueError('Renseigner un identifiant de projet Google Cloud valide.')
    ee.Initialize(project=project_id.strip())


def analyze(latitude: float, longitude: float, radius_m: int = 5000,
            start_date: str = '2024-01-01', end_date: str = '2025-01-01') -> dict:
    """Calcule les 6 métriques autour d'un point. end_date est exclusive."""
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError('Coordonnées invalides.')
    if not 500 <= radius_m <= 20000:
        raise ValueError('Rayon autorisé : 500 à 20 000 m.')
    if date.fromisoformat(start_date) >= date.fromisoformat(end_date):
        raise ValueError('La date de fin doit être postérieure à la date de début.')
    zone = ee.Geometry.Point([longitude, latitude]).buffer(radius_m)

    # DEM : mosaïque sur la zone, en projection métrique locale pour les dérivées.
    dem_collection = ee.ImageCollection('COPERNICUS/DEM/GLO30').filterBounds(zone).select('DEM')
    if dem_collection.size().getInfo() == 0:
        raise ValueError('Aucune donnée Copernicus DEM pour cette zone.')
    dem = dem_collection.mosaic().rename('altitude')
    # Projection métrique adaptée à la latitude (UTM hors régions polaires).
    if -80 <= latitude <= 84:
        utm_zone = min(60, int((longitude + 180) // 6) + 1)
        epsg = (32600 if latitude >= 0 else 32700) + utm_zone
        metric_crs = f'EPSG:{epsg}'
    else:
        metric_crs = 'EPSG:3413' if latitude > 0 else 'EPSG:3031'
    dem30 = dem.resample('bilinear').reproject(crs=metric_crs, scale=30)
    slope = ee.Terrain.slope(dem30).rename('pente')
    # TRI de Riley : racine de la somme des carrés des écarts avec les 8 voisins.
    kernel = ee.Kernel.square(radius=1, units='pixels', normalize=False)
    # Calcul par voisinage (neighborhoodToBands retourne les 9 valeurs).
    neighbors = dem30.neighborhoodToBands(kernel)
    diff_sq = neighbors.subtract(dem30).pow(2)
    tri = diff_sq.reduce(ee.Reducer.sum()).sqrt().rename('tri')
    terrain = dem30.addBands(slope).addBands(tri)
    terrain_stats = terrain.reduceRegion(ee.Reducer.mean(), zone, 30, maxPixels=1e8, tileScale=4).getInfo()

    # Sentinel-2 SR Harmonized, masque SCL (nuages, ombres, neige et pixels défectueux).
    s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
          .filterBounds(zone).filterDate(start_date, end_date)
          .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 70)))
    s2_count = s2.size().getInfo()
    ndvi_value = None
    if s2_count:
        def masked_ndvi(img):
            scl = img.select('SCL')
            valid = (scl.neq(0).And(scl.neq(1)).And(scl.neq(3))
                     .And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
                     .And(scl.neq(11)))
            return img.normalizedDifference(['B8','B4']).rename('ndvi').updateMask(valid)
        ndvi_image = s2.map(masked_ndvi).median()
        ndvi_value = ndvi_image.reduceRegion(ee.Reducer.mean(), zone, 20,
                                             maxPixels=1e8, tileScale=4).get('ndvi').getInfo()

    # MOD11A2 : LST de jour, composites 8 jours, facteur 0.02 K.
    modis = (ee.ImageCollection('MODIS/061/MOD11A2')
             .filterBounds(zone).filterDate(start_date, end_date))
    modis_count = modis.size().getInfo()
    temp_value = None
    if modis_count:
        def temp_celsius(img):
            valid = img.select('QC_Day').bitwiseAnd(3).lte(1)
            return img.select('LST_Day_1km').multiply(0.02).subtract(273.15).rename('temp_c').updateMask(valid)
        temp_value = (modis.map(temp_celsius).mean()
                      .reduceRegion(ee.Reducer.mean(), zone, 1000,
                                    maxPixels=1e8, tileScale=4).get('temp_c').getInfo())

    # ESA WorldCover v200 (2021) : classe modale, différente des années Sentinel/MODIS.
    worldcover = ee.ImageCollection('ESA/WorldCover/v200').first().select('Map')
    cover_code = worldcover.reduceRegion(ee.Reducer.mode(), zone, 10,
                                         maxPixels=1e8, tileScale=4).get('Map').getInfo()
    cover_code = int(cover_code) if cover_code is not None else None
    return {
        'altitude_m': terrain_stats.get('altitude'),
        'pente_deg': terrain_stats.get('pente'),
        'tri_m': terrain_stats.get('tri'),
        'ndvi': ndvi_value,
        'temperature_c': temp_value,
        'occupation_code': cover_code,
        'occupation': LANDCOVER.get(cover_code, 'Non disponible'),
        'images_sentinel': s2_count,
        'composites_modis': modis_count,
        'periode': f'{start_date} au {end_date} (fin exclue)',
        'worldcover_annee': 2021,
        'rayon_m': radius_m,
        'latitude': latitude,
        'longitude': longitude,
    }
