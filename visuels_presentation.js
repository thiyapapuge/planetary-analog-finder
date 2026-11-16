// =============================================================================
// VISUELS POUR LA PRÉSENTATION — analogues terrestres de Jezero
// Nom à l'enregistrement dans Earth Engine : visuels_presentation
//
// Choisir une vue, cliquer sur Run, puis faire une capture d'écran de la carte.
//   'monde'     : le top 100 sur le globe, coloré selon l'accès + site recommandé
//   'site4'     : le site recommandé n° 4 (Puna argentine) en image satellite
//   'tibet'     : le Tibet occidental, meilleurs scores mondiaux, et l'Aksai Chin disputé
//   'altiplano' : l'Altiplano bolivien, sites accessibles et aires protégées
// Script léger : pas de calcul mondial (compatible avec le mode restreint).
// =============================================================================

var VUE = 'monde';

var top100 = ee.FeatureCollection([
  ee.Feature(ee.Geometry.Point([80.7541, 33.7901]), {rang: 1, statut: 0}),
  ee.Feature(ee.Geometry.Point([79.9456, 34.6166]), {rang: 2, statut: 0}),
  ee.Feature(ee.Geometry.Point([80.8529, 33.7362]), {rang: 3, statut: 0}),
  ee.Feature(ee.Geometry.Point([-68.1597, -25.1573]), {rang: 4, statut: 0}),
  ee.Feature(ee.Geometry.Point([79.1820, 35.1376]), {rang: 5, statut: 2}),
  ee.Feature(ee.Geometry.Point([81.0235, 33.6554]), {rang: 6, statut: 0}),
  ee.Feature(ee.Geometry.Point([-68.8873, -18.2133]), {rang: 7, statut: 1}),
  ee.Feature(ee.Geometry.Point([79.9546, 34.9669]), {rang: 8, statut: 2}),
  ee.Feature(ee.Geometry.Point([96.2769, 39.1082]), {rang: 9, statut: 0}),
  ee.Feature(ee.Geometry.Point([81.1673, 34.0866]), {rang: 10, statut: 0}),
  ee.Feature(ee.Geometry.Point([77.9603, 35.9012]), {rang: 11, statut: 0}),
  ee.Feature(ee.Geometry.Point([80.7091, 33.7452]), {rang: 12, statut: 0}),
  ee.Feature(ee.Geometry.Point([80.4935, 34.7693]), {rang: 13, statut: 0}),
  ee.Feature(ee.Geometry.Point([92.9622, 49.4567]), {rang: 14, statut: 0}),
  ee.Feature(ee.Geometry.Point([-71.2319, -16.3628]), {rang: 15, statut: 1}),
  ee.Feature(ee.Geometry.Point([96.7980, 39.5483]), {rang: 16, statut: 0}),
  ee.Feature(ee.Geometry.Point([80.0354, 34.6615]), {rang: 17, statut: 0}),
  ee.Feature(ee.Geometry.Point([81.3200, 34.2662]), {rang: 18, statut: 0}),
  ee.Feature(ee.Geometry.Point([-69.8216, -17.2971]), {rang: 19, statut: 1}),
  ee.Feature(ee.Geometry.Point([80.7541, 34.6166]), {rang: 20, statut: 0}),
  ee.Feature(ee.Geometry.Point([80.5025, 34.7154]), {rang: 21, statut: 0}),
  ee.Feature(ee.Geometry.Point([84.5270, 33.0266]), {rang: 22, statut: 0}),
  ee.Feature(ee.Geometry.Point([81.0146, 33.9608]), {rang: 23, statut: 0}),
  ee.Feature(ee.Geometry.Point([51.9361, 31.0682]), {rang: 24, statut: 0}),
  ee.Feature(ee.Geometry.Point([81.5625, 35.7934]), {rang: 25, statut: 0}),
  ee.Feature(ee.Geometry.Point([81.0954, 34.8681]), {rang: 26, statut: 0}),
  ee.Feature(ee.Geometry.Point([89.9348, 37.7158]), {rang: 27, statut: 0}),
  ee.Feature(ee.Geometry.Point([79.3886, 35.0208]), {rang: 28, statut: 2}),
  ee.Feature(ee.Geometry.Point([81.4997, 34.1584]), {rang: 29, statut: 0}),
  ee.Feature(ee.Geometry.Point([81.3829, 33.7722]), {rang: 30, statut: 0}),
  ee.Feature(ee.Geometry.Point([80.0085, 34.8322]), {rang: 31, statut: 2}),
  ee.Feature(ee.Geometry.Point([96.2500, 39.0632]), {rang: 32, statut: 0}),
  ee.Feature(ee.Geometry.Point([-68.4831, -19.0757]), {rang: 33, statut: 0}),
  ee.Feature(ee.Geometry.Point([-67.8902, -20.7646]), {rang: 34, statut: 0}),
  ee.Feature(ee.Geometry.Point([-67.8812, -20.7466]), {rang: 35, statut: 0}),
  ee.Feature(ee.Geometry.Point([81.5266, 33.8261]), {rang: 36, statut: 0}),
  ee.Feature(ee.Geometry.Point([80.0893, 33.5656]), {rang: 37, statut: 0}),
  ee.Feature(ee.Geometry.Point([52.9332, 30.4753]), {rang: 38, statut: 0}),
  ee.Feature(ee.Geometry.Point([84.8055, 32.8738]), {rang: 39, statut: 0}),
  ee.Feature(ee.Geometry.Point([80.8259, 34.8861]), {rang: 40, statut: 0}),
  ee.Feature(ee.Geometry.Point([52.1247, 31.1221]), {rang: 41, statut: 0}),
  ee.Feature(ee.Geometry.Point([80.0713, 35.0478]), {rang: 42, statut: 2}),
  ee.Feature(ee.Geometry.Point([95.8008, 39.5843]), {rang: 43, statut: 0}),
  ee.Feature(ee.Geometry.Point([95.7200, 39.6202]), {rang: 44, statut: 0}),
  ee.Feature(ee.Geometry.Point([-69.1299, -17.8810]), {rang: 45, statut: 0}),
  ee.Feature(ee.Geometry.Point([81.5176, 33.4937]), {rang: 46, statut: 0}),
  ee.Feature(ee.Geometry.Point([78.0591, 35.2544]), {rang: 47, statut: 2}),
  ee.Feature(ee.Geometry.Point([82.1285, 33.1164]), {rang: 48, statut: 0}),
  ee.Feature(ee.Geometry.Point([81.1403, 34.6076]), {rang: 49, statut: 0}),
  ee.Feature(ee.Geometry.Point([85.0211, 32.8379]), {rang: 50, statut: 0}),
  ee.Feature(ee.Geometry.Point([96.5644, 46.0791]), {rang: 51, statut: 0}),
  ee.Feature(ee.Geometry.Point([-67.9890, -24.9148]), {rang: 52, statut: 0}),
  ee.Feature(ee.Geometry.Point([92.4950, 47.9566]), {rang: 53, statut: 1}),
  ee.Feature(ee.Geometry.Point([-68.7885, -17.9618]), {rang: 54, statut: 0}),
  ee.Feature(ee.Geometry.Point([80.4935, 33.6464]), {rang: 55, statut: 0}),
  ee.Feature(ee.Geometry.Point([81.2751, 34.8412]), {rang: 56, statut: 0}),
  ee.Feature(ee.Geometry.Point([52.4571, 30.7808]), {rang: 57, statut: 0}),
  ee.Feature(ee.Geometry.Point([50.3910, 32.8828]), {rang: 58, statut: 0}),
  ee.Feature(ee.Geometry.Point([81.6164, 34.1944]), {rang: 59, statut: 0}),
  ee.Feature(ee.Geometry.Point([52.8434, 30.5562]), {rang: 60, statut: 0}),
  ee.Feature(ee.Geometry.Point([-69.8575, -17.2432]), {rang: 61, statut: 1}),
  ee.Feature(ee.Geometry.Point([51.9002, 30.9065]), {rang: 62, statut: 0}),
  ee.Feature(ee.Geometry.Point([80.6912, 33.3500]), {rang: 63, statut: 0}),
  ee.Feature(ee.Geometry.Point([52.0888, 30.9964]), {rang: 64, statut: 0}),
  ee.Feature(ee.Geometry.Point([52.3942, 31.0862]), {rang: 65, statut: 0}),
  ee.Feature(ee.Geometry.Point([51.6217, 31.5982]), {rang: 66, statut: 0}),
  ee.Feature(ee.Geometry.Point([81.2571, 34.5357]), {rang: 67, statut: 0}),
  ee.Feature(ee.Geometry.Point([101.7117, 38.5332]), {rang: 68, statut: 0}),
  ee.Feature(ee.Geometry.Point([59.5089, 35.6317]), {rang: 69, statut: 0}),
  ee.Feature(ee.Geometry.Point([81.1044, 33.3140]), {rang: 70, statut: 0}),
  ee.Feature(ee.Geometry.Point([81.8949, 33.4757]), {rang: 71, statut: 0}),
  ee.Feature(ee.Geometry.Point([84.6168, 32.9277]), {rang: 72, statut: 0}),
  ee.Feature(ee.Geometry.Point([-68.1237, -19.7674]), {rang: 73, statut: 0}),
  ee.Feature(ee.Geometry.Point([82.0297, 33.4578]), {rang: 74, statut: 0}),
  ee.Feature(ee.Geometry.Point([50.6874, 32.8020]), {rang: 75, statut: 0}),
  ee.Feature(ee.Geometry.Point([80.7451, 33.7811]), {rang: 76, statut: 0}),
  ee.Feature(ee.Geometry.Point([96.4117, 39.3866]), {rang: 77, statut: 0}),
  ee.Feature(ee.Geometry.Point([-106.1674, 38.1200]), {rang: 78, statut: 0}),
  ee.Feature(ee.Geometry.Point([79.2808, 35.6047]), {rang: 79, statut: 2}),
  ee.Feature(ee.Geometry.Point([81.4008, 33.4937]), {rang: 80, statut: 0}),
  ee.Feature(ee.Geometry.Point([78.8227, 35.0208]), {rang: 81, statut: 2}),
  ee.Feature(ee.Geometry.Point([-69.1568, -18.4649]), {rang: 82, statut: 1}),
  ee.Feature(ee.Geometry.Point([72.5704, 39.5214]), {rang: 83, statut: 0}),
  ee.Feature(ee.Geometry.Point([-68.3932, -18.9500]), {rang: 84, statut: 0}),
  ee.Feature(ee.Geometry.Point([52.7086, 30.6191]), {rang: 85, statut: 0}),
  ee.Feature(ee.Geometry.Point([78.1489, 35.6946]), {rang: 86, statut: 0}),
  ee.Feature(ee.Geometry.Point([52.5200, 30.9964]), {rang: 87, statut: 0}),
  ee.Feature(ee.Geometry.Point([-70.2797, -17.0635]), {rang: 88, statut: 0}),
  ee.Feature(ee.Geometry.Point([-68.6987, -25.9748]), {rang: 89, statut: 0}),
  ee.Feature(ee.Geometry.Point([84.2575, 33.0535]), {rang: 90, statut: 0}),
  ee.Feature(ee.Geometry.Point([53.0410, 30.4753]), {rang: 91, statut: 0}),
  ee.Feature(ee.Geometry.Point([78.3286, 35.2993]), {rang: 92, statut: 2}),
  ee.Feature(ee.Geometry.Point([59.3652, 35.6496]), {rang: 93, statut: 0}),
  ee.Feature(ee.Geometry.Point([90.2403, 38.7578]), {rang: 94, statut: 0}),
  ee.Feature(ee.Geometry.Point([78.8766, 34.8861]), {rang: 95, statut: 2}),
  ee.Feature(ee.Geometry.Point([-70.4144, -16.7760]), {rang: 96, statut: 0}),
  ee.Feature(ee.Geometry.Point([80.7002, 34.3740]), {rang: 97, statut: 0}),
  ee.Feature(ee.Geometry.Point([80.2600, 34.7064]), {rang: 98, statut: 0}),
  ee.Feature(ee.Geometry.Point([90.2403, 38.7488]), {rang: 99, statut: 0}),
  ee.Feature(ee.Geometry.Point([-67.7464, -20.5759]), {rang: 100, statut: 0})
]);
var site4 = top100.filter(ee.Filter.eq('rang', 4));

// Couleurs : 0 = accessible (vert), 1 = aire protégée (orange), 2 = zone disputée (rouge)
function couche(statut, couleur, nom) {
  Map.addLayer(top100.filter(ee.Filter.eq('statut', statut)), {color: couleur, pointSize: 6}, nom);
}
function points_top100() {
  couche(0, '2e8b57', 'Top 100 : accessible');
  couche(1, 'f08c00', 'Top 100 : aire protégée');
  couche(2, 'd62828', 'Top 100 : zone disputée');
  Map.addLayer(site4.map(function (f) { return f.buffer(15000); }).style({color: 'ffd700', width: 3, fillColor: 'ffd70055'}),
               {}, 'Site recommandé (n° 4)');
}

// Case de 25 km du site n° 4 (carré de 0,25°)
var case4 = ee.Geometry.Rectangle([-68.25, -25.25, -68.0, -25.0]);

if (VUE === 'monde') {
  Map.setOptions('SATELLITE');
  Map.setCenter(10, 15, 2);
  points_top100();
}

if (VUE === 'site4') {
  Map.setOptions('SATELLITE');
  Map.centerObject(case4, 11);
  // Image Sentinel-2 récente sans nuages, en couleurs naturelles puis en fausses couleurs géologie
  var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(case4).filterDate('2023-01-01', '2024-01-01')
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10)).median().clip(case4.buffer(5000));
  Map.addLayer(s2, {bands: ['B4', 'B3', 'B2'], min: 0, max: 3500}, 'Sentinel-2 couleurs naturelles');
  Map.addLayer(s2, {bands: ['B12', 'B11', 'B4'], min: 0, max: 4500}, 'Fausses couleurs géologie (SWIR)', false);
  Map.addLayer(s2.select('B11').divide(s2.select('B12')),
               {min: 1.0, max: 1.4, palette: ['black', 'yellow', 'white']}, 'Signal argileux B11/B12', false);
  Map.addLayer(ee.FeatureCollection([ee.Feature(case4)]).style({color: 'ffd700', width: 3, fillColor: '00000000'}),
               {}, 'Case de 25 km du site n° 4');
  Map.addLayer(site4, {color: 'ff0000', pointSize: 8}, 'Meilleure parcelle');
}

if (VUE === 'tibet') {
  Map.setOptions('SATELLITE');
  Map.setCenter(80.5, 34.5, 7);
  var aksai = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017').filter(ee.Filter.eq('country_na', 'Aksai Chin'));
  Map.addLayer(aksai.style({color: 'd62828', width: 2, fillColor: 'd6282833'}), {}, 'Aksai Chin (zone disputée)');
  points_top100();
}

if (VUE === 'altiplano') {
  Map.setOptions('SATELLITE');
  Map.setCenter(-68.6, -18.9, 8);
  var zone = ee.Geometry.Rectangle([-71, -21.5, -66.5, -16]);
  var aires = ee.FeatureCollection('WCMC/WDPA/current/polygons').filterBounds(zone);
  Map.addLayer(aires.style({color: 'f08c00', width: 2, fillColor: 'f08c0022'}), {}, 'Aires protégées (WDPA)');
  points_top100();
}
