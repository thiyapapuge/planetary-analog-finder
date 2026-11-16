// =============================================================================
// COMPOSITION TOP 20 — argiles Sentinel-2 sur le top 20 mondial du modèle final
// Nom à l'enregistrement dans Earth Engine : composition_top20
//
// Jezero = ancien delta riche en ARGILES (Fe/Mg) et roches à OXYDES DE FER.
// On mesure avec Sentinel-2 (10-20 m), uniquement sur les sites candidats :
//   - ratio argiles     B11/B12 (SWIR) : élevé = minéraux argileux / hydroxylés
//   - ratio oxydes fer  B4/B2  (rouge/bleu) : élevé = sol rougeâtre (Fe3+)
//   - NDVI de contrôle (la végétation fausse les ratios)
// Calcul léger : un disque de 2 km autour de chaque site (pas de calcul mondial).
// =============================================================================

// -----------------------------------------------------------------------------
// 1. SITES À ANALYSER (ajouter / modifier des lignes ici)
// -----------------------------------------------------------------------------
var sites = ee.FeatureCollection([
  ee.Feature(ee.Geometry.Point([80.754, 33.790]), {nom: 'Monde #1', role: 'candidat'}),
  ee.Feature(ee.Geometry.Point([79.946, 34.617]), {nom: 'Monde #2', role: 'candidat'}),
  ee.Feature(ee.Geometry.Point([80.853, 33.736]), {nom: 'Monde #3', role: 'candidat'}),
  ee.Feature(ee.Geometry.Point([-68.160, -25.157]), {nom: 'Monde #4', role: 'candidat'}),
  ee.Feature(ee.Geometry.Point([79.182, 35.138]), {nom: 'Monde #5', role: 'candidat'}),
  ee.Feature(ee.Geometry.Point([81.024, 33.655]), {nom: 'Monde #6', role: 'candidat'}),
  ee.Feature(ee.Geometry.Point([-68.887, -18.213]), {nom: 'Monde #7', role: 'candidat'}),
  ee.Feature(ee.Geometry.Point([79.955, 34.967]), {nom: 'Monde #8', role: 'candidat'}),
  ee.Feature(ee.Geometry.Point([96.277, 39.108]), {nom: 'Monde #9', role: 'candidat'}),
  ee.Feature(ee.Geometry.Point([81.167, 34.087]), {nom: 'Monde #10', role: 'candidat'}),
  ee.Feature(ee.Geometry.Point([77.960, 35.901]), {nom: 'Monde #11', role: 'candidat'}),
  ee.Feature(ee.Geometry.Point([80.709, 33.745]), {nom: 'Monde #12', role: 'candidat'}),
  ee.Feature(ee.Geometry.Point([80.494, 34.769]), {nom: 'Monde #13', role: 'candidat'}),
  ee.Feature(ee.Geometry.Point([92.962, 49.457]), {nom: 'Monde #14', role: 'candidat'}),
  ee.Feature(ee.Geometry.Point([-71.232, -16.363]), {nom: 'Monde #15', role: 'candidat'}),
  ee.Feature(ee.Geometry.Point([96.798, 39.548]), {nom: 'Monde #16', role: 'candidat'}),
  ee.Feature(ee.Geometry.Point([80.035, 34.661]), {nom: 'Monde #17', role: 'candidat'}),
  ee.Feature(ee.Geometry.Point([81.320, 34.266]), {nom: 'Monde #18', role: 'candidat'}),
  ee.Feature(ee.Geometry.Point([-69.822, -17.297]), {nom: 'Monde #19', role: 'candidat'}),
  ee.Feature(ee.Geometry.Point([80.754, 34.617]), {nom: 'Monde #20', role: 'candidat'}),
  ee.Feature(ee.Geometry.Point([58.50, 22.90]),   {nom: 'Oman, ophiolite', role: 'témoin positif'}),
  ee.Feature(ee.Geometry.Point([51.00, 20.00]),   {nom: "Rub' al Khali", role: 'témoin négatif'})
]);

var RAYON_M = 2000;      // taille de la zone analysée autour de chaque point
var FOCUS = 0;           // numéro du site affiché sur la carte (0 = premier de la liste)

// -----------------------------------------------------------------------------
// 2. IMAGE SENTINEL-2 SANS NUAGES (médiane 2023, masque SCL)
// -----------------------------------------------------------------------------
var zones = sites.map(function (f) { return f.buffer(RAYON_M); });

function masquer(img) {
  var scl = img.select('SCL');
  // garde : 4 végétation, 5 sol nu, 6 eau, 7 non classé ; retire nuages, ombres, neige
  var ok = scl.eq(4).or(scl.eq(5)).or(scl.eq(6)).or(scl.eq(7));
  return img.updateMask(ok).select(['B2', 'B3', 'B4', 'B8', 'B11', 'B12']);
}

var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(zones)
  .filterDate('2023-01-01', '2024-01-01')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
  .map(masquer)
  .median();

// -----------------------------------------------------------------------------
// 3. INDICES ET SCORE COMPOSITION
// -----------------------------------------------------------------------------
var argiles = s2.select('B11').divide(s2.select('B12')).rename('ratio_argiles');
var fer     = s2.select('B4').divide(s2.select('B2')).rename('ratio_fer');
var ndvi    = s2.normalizedDifference(['B8', 'B4']).rename('ndvi');

function borner(img, v0, v1) { return img.subtract(v0).divide(v1 - v0).clamp(0.01, 1); }

// Bornes indicatives (à ajuster après les premiers résultats) :
// argiles : rampe 1.15 -> 1.40 (fiche de Lilian) ; fer : 1.0 = neutre, 1.8 = sol très rouge
var s_argiles = borner(argiles, 1.15, 1.40);   // rampe CLAY de Lilian (à calibrer)
var s_fer     = borner(fer, 1.0, 1.8);
var s_nu      = borner(ndvi, 0.4, 0.1);    // sol nu requis pour que les ratios soient fiables

// Moyenne géométrique : argiles 45 %, fer 35 %, sol nu 20 %
var score_compo = s_argiles.log().multiply(0.45)
  .add(s_fer.log().multiply(0.35))
  .add(s_nu.log().multiply(0.20))
  .exp().rename('score_compo');

// -----------------------------------------------------------------------------
// 4. RÉSULTATS PAR SITE (moyenne dans le disque de 2 km)
// -----------------------------------------------------------------------------
var resultats = score_compo.addBands([argiles, fer, ndvi]).reduceRegions({
  collection: zones, reducer: ee.Reducer.mean(), scale: 20, tileScale: 4
});

print('COMPOSITION [nom, rôle, score compo, ratio argiles, ratio fer, NDVI] :',
  resultats.map(function (f) {
    return f.set('ligne', [f.get('nom'), f.get('role'), f.get('score_compo'),
                           f.get('ratio_argiles'), f.get('ratio_fer'), f.get('ndvi')]);
  }).aggregate_array('ligne'));

// -----------------------------------------------------------------------------
// 5. CARTE : focus sur un site (changer FOCUS en haut pour en voir un autre)
// -----------------------------------------------------------------------------
var site_focus = ee.Feature(sites.toList(sites.size()).get(FOCUS));
Map.centerObject(site_focus, 12);
Map.addLayer(s2, {bands: ['B4', 'B3', 'B2'], min: 0, max: 3000}, 'Sentinel-2 couleurs naturelles');
Map.addLayer(s2, {bands: ['B12', 'B11', 'B4'], min: 0, max: 4000}, 'Fausses couleurs géologie (SWIR)', false);
Map.addLayer(argiles, {min: 1.0, max: 1.4, palette: ['black', 'yellow', 'white']}, 'Ratio argiles B11/B12', false);
Map.addLayer(fer, {min: 1.0, max: 2.0, palette: ['black', 'orange', 'red']}, 'Ratio oxydes de fer B4/B2', false);
Map.addLayer(score_compo, {min: 0, max: 0.8, palette: ['black', 'purple', 'orange', 'white']}, 'Score composition');
Map.addLayer(zones.style({color: 'cyan', fillColor: '00000000'}), {}, 'Zones analysées (2 km)');

// -----------------------------------------------------------------------------
// 6. EXPORT CSV (onglet Tasks -> Run)
// -----------------------------------------------------------------------------
Export.table.toDrive({
  collection: resultats, description: 'composition_top20', fileFormat: 'CSV',
  selectors: ['nom', 'role', 'score_compo', 'ratio_argiles', 'ratio_fer', 'ndvi']
});
