"""Diagnostic ciblé des géométries et des pentes NASADEM dans Earth Engine."""
import ee

PROJECT = 'identify-earth-locations'
LAT, LON = -24.5, -69.25
CRS = 'EPSG:32719'
CELL_M = 10000
COLS, ROWS = 3, 2

ee.Initialize(project=PROJECT)
point = ee.Geometry.Point([LON, LAT])
center = point.transform(CRS, 1)
cx, cy = map(float, center.coordinates().getInfo())
print('Centre UTM :', cx, cy)
print('Point géographique :', point.coordinates().getInfo())

dem = ee.Image('NASA/NASADEM_HGT/001').select('elevation')
slope = ee.Terrain.slope(dem).rename('pente_grossiere_deg')

print('Pente point/buffer 5 km :', slope.reduceRegion(
    ee.Reducer.mean(), point.buffer(5000), 90, maxPixels=1000000
).getInfo())

x0 = cx - COLS * CELL_M / 2
z0 = cy - ROWS * CELL_M / 2
features = []
for row in range(ROWS):
    for col in range(COLS):
        x = x0 + col * CELL_M
        y = z0 + row * CELL_M
        geom = ee.Geometry.Rectangle([x, y, x + CELL_M, y + CELL_M], proj=CRS, geodesic=False)
        ident = f'R{row+1:02d}-{col+1:02d}'
        features.append(ee.Feature(geom, {'id': ident}))

fc = ee.FeatureCollection(features)
print('Nombre de cellules :', fc.size().getInfo())
print('Première cellule, centre WGS84 :',
      features[0].geometry().centroid(1).transform('EPSG:4326', 1).coordinates().getInfo())
print('Première cellule, emprise WGS84 :',
      features[0].geometry().transform('EPSG:4326', 1).bounds(1).coordinates().getInfo())

print('Altitude cellule 1 :', dem.reduceRegion(
    ee.Reducer.mean(), features[0].geometry(), 90, maxPixels=10000000
).getInfo())
print('Pente cellule 1 (reduceRegion) :', slope.reduceRegion(
    ee.Reducer.mean(), features[0].geometry(), 90, maxPixels=10000000
).getInfo())

reduced = slope.reduceRegions(collection=fc, reducer=ee.Reducer.mean(), scale=90, tileScale=8)
for feature in reduced.getInfo()['features']:
    p = feature['properties']
    print(p['id'], 'pente :', p.get('pente_grossiere_deg'))
