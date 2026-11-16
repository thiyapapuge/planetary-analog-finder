// =============================================================================
// MODÈLE FINAL V1 — environnement × relief × composition — Jezero (Mars)
// Nom à l'enregistrement dans Earth Engine : modele_final_v1
// NASA Space Apps Challenge 2026 — projet nasa-hackaton-513513
//
// ENTONNOIR
//   Étape 0 : terres de la zone
//   Étape 1 : filtre ENVIRONNEMENT (score env ≥ 0.45 et non éliminé)
//   Étape 2 : filtre RELIEF (env × relief ≥ 0.60)
//   Étape 3 : filtre COMPOSITION (score compo ≥ 0.40 : analogie partielle ou forte)
// SCORE FINAL = moyenne géométrique env (35 %) × relief (30 %) × composition (35 %)
// + un PROFIL par dimension (ex. « Env A · Relief A · Compo B ») : on dit où
//   l'analogie tient et où elle casse.
// SITES = cases de 0.25° (~25 km), classées par score MOYEN de la case
//   (+ part de la case qui passe) ; la meilleure parcelle donne la position
//   (corrige les « sites géants » de l'entonnoir V2).
//
// COMPOSITION (fiche de Lilian) : co-localisation mafique ET carbonates
//   MI = ASTER b12/b13 (mafique)   CI = ASTER b13/b14 (carbonates)
//   rampes relatives p50 -> p98 des terres arides du globe ; compo = √(sMI × sCI)
//   Le proxy argiles Sentinel-2 (B11/B12) reste dans composition_v1, sur le top 20.
//
// Tester d'abord sur une zone (andes, oman...), puis 'monde' + EXPORTS (Tasks).
// =============================================================================

var ZONE_CHOISIE = 'andes';

var ZONES = {
  andes:       ee.Geometry.Rectangle([-71, -28, -65, -18]),          // Atacama, Puna, Altiplano
  utah:        ee.Geometry.Rectangle([-114, 36, -108, 40]),          // MDRS
  deathvalley: ee.Geometry.Rectangle([-118.5, 34.5, -114.5, 37.5]),  // Death Valley, Mojave
  ladakh:      ee.Geometry.Rectangle([76, 31, 82, 36]),               // Ladakh, Tibet occidental
  qaidam:      ee.Geometry.Rectangle([88, 35, 100, 40]),              // Bassin du Qaidam
  oman:        ee.Geometry.Rectangle([55.5, 22, 59.5, 25.5]),         // Ophiolite de Samail (test composition)
  france:      ee.Geometry.Rectangle([-2, 43, 7, 50]),                // Témoin négatif
  monde:       ee.Geometry.Rectangle([-180, -60, 180, 80], null, false)
};
var MONDE = ZONE_CHOISIE === 'monde';
var ZONE = ZONES[ZONE_CHOISIE];
var MONDE_GEOM = ZONES.monde;
var ECHELLE_STATS = MONDE ? 10000 : 2000;
var ECHELLE_SITES = MONDE ? 5000 : 2000;

var SEUIL_ENV = 0.45;      // étape 1
var SEUIL_ENV_RELIEF = 0.60; // étape 2
var SEUIL_COMPO = 0.40;    // étape 3 (fiche : ≥ 0.4 = analogie partielle ou forte)
var POIDS = {env: 0.35, relief: 0.30, compo: 0.35};
var COMPO_MODE = 'MI';      // 'MI' (recommandé) ou 'MI_CI' (version de la fiche, pour comparer)
var PART_MIN = 0.10;       // part minimale de la case qui doit passer l'étape 3 pour devenir un site

var DEBUT = '2023-01-01', FIN = '2024-01-01';
var PROJ_1KM = ee.Projection('EPSG:4326').atScale(1000);

// Bornes fixes (nombres JS) et bornes calculées (ee.Number)
function borner(img, v0, v1) { return img.subtract(v0).divide(v1 - v0).clamp(0.01, 1); }
function borner_ee(img, lo, hi) {
  // Les bornes viennent du serveur (percentiles) : conversion explicite en image constante
  var lo_img = ee.Image.constant(ee.Number(lo));
  var ecart = ee.Image.constant(ee.Number(hi).subtract(ee.Number(lo)));
  return img.subtract(lo_img).divide(ecart).clamp(0.01, 1);
}
function trapeze(img, a, b, c, d) {
  return img.subtract(a).divide(b - a).min(ee.Image(d).subtract(img).divide(d - c)).clamp(0.01, 1);
}

// -----------------------------------------------------------------------------
// 1. ENVIRONNEMENT
// -----------------------------------------------------------------------------
var lst = ee.ImageCollection('MODIS/061/MOD11A2').filterDate(DEBUT, FIN);
var terre = lst.select('LST_Day_1km').count().gt(0);

var amplitude = lst.map(function (i) {
  return i.select('LST_Day_1km').subtract(i.select('LST_Night_1km')).multiply(0.02);
}).median().rename('amplitude_K');
var temp_moy = lst.map(function (i) {
  return i.select('LST_Day_1km').add(i.select('LST_Night_1km')).multiply(0.01).subtract(273.15);
}).mean().rename('temp_moy_C');
var ndvi_max = ee.ImageCollection('MODIS/061/MOD13A2').filterDate(DEBUT, FIN)
  .select('NDVI').max().multiply(0.0001).rename('ndvi_max');
var ndvi_moy = ee.ImageCollection('MODIS/061/MOD13A2').filterDate(DEBUT, FIN)
  .select('NDVI').mean().multiply(0.0001).rename('ndvi_moy');
var tc = ee.ImageCollection('IDAHO_EPSCOR/TERRACLIMATE').filterDate(DEBUT, FIN);
var pluie = tc.select('pr').sum().rename('pluie_mm');
var aridite = pluie.divide(tc.select('pet').sum().multiply(0.1)).rename('aridite');

var score_env = borner(amplitude, 10, 35).log().multiply(0.30)
  .add(borner(temp_moy, 25, -15).log().multiply(0.20))
  .add(borner(ndvi_max, 0.5, 0.05).log().multiply(0.25))
  .add(borner(aridite, 0.65, 0.03).log().multiply(0.25))
  .exp().updateMask(terre).rename('score_env');
// Eau actuelle (JRC) : éliminé au-delà de 10 % d'occurrence (aligné sur le code de Lilian)
var eau = ee.Image('JRC/GSW1_4/GlobalSurfaceWater').select('occurrence').unmask(0);
var elimine = ndvi_max.gt(0.4).or(aridite.gt(0.5)).or(eau.gt(10));

// -----------------------------------------------------------------------------
// 2. RELIEF (MNT MERIT natif 90 m)
// -----------------------------------------------------------------------------
var dem90 = ee.Image('MERIT/DEM/v1_0_3').select('dem');
var pente90 = ee.Terrain.slope(dem90);
var frac_plat = pente90.lt(5).reduceResolution({reducer: ee.Reducer.mean(), maxPixels: 1024})
  .reproject(PROJ_1KM).rename('frac_plat');
var pente_moy = pente90.reduceResolution({reducer: ee.Reducer.mean(), maxPixels: 1024})
  .reproject(PROJ_1KM).rename('pente_moy_deg');
var dem1k = dem90.reduceResolution({reducer: ee.Reducer.mean(), maxPixels: 1024}).reproject(PROJ_1KM);
var relief_local = dem1k.focalMax(3000, 'circle', 'meters').subtract(dem1k.focalMin(3000, 'circle', 'meters'))
  .reproject(PROJ_1KM).rename('relief_local_m');
var tpi = dem1k.subtract(dem1k.focalMean(10000, 'circle', 'meters')).reproject(PROJ_1KM).rename('tpi_m');

var score_relief = borner(frac_plat, 0.2, 0.8).log().multiply(0.40)
  .add(trapeze(relief_local, 20, 100, 500, 1500).log().multiply(0.35))
  .add(borner(tpi, 50, -50).log().multiply(0.25))
  .exp().updateMask(terre).rename('score_relief');

// -----------------------------------------------------------------------------
// 3. COMPOSITION (ASTER GED, émissivité TIR, 100 m)
// -----------------------------------------------------------------------------
var aster = ee.Image('NASA/ASTER_GED/AG100_003');
var e12 = aster.select('emissivity_band12');
var e13 = aster.select('emissivity_band13');
var e14 = aster.select('emissivity_band14');
var valide = e12.gt(0).and(e13.gt(0)).and(e14.gt(0));
var MI = e12.divide(e13).updateMask(valide).rename('MI');   // mafique / ultramafique
var CI = e13.divide(e14).updateMask(valide).rename('CI');   // carbonates

// Rampes relatives : p50 -> p98 des TERRES ARIDES (p90 saturait : CI varie à peine)
// Rampes relatives (définition des terres arides) : (pluie < 100 mm/an, NDVI moyen < 0.1, 50°S-50°N)
// Même définition que le script de Lilian (jezero_analog_gee.js).
// Calculées une seule fois sur le monde : le score est comparable d'une zone à l'autre.
var arides = pluie.lt(100).and(ndvi_moy.lt(0.1));
var ZONE_REF = ee.Geometry.Rectangle([-180, -50, 180, 50], null, false);
var pc = MI.addBands(CI).updateMask(arides).reduceRegion({
  reducer: ee.Reducer.percentile([50, 98]), geometry: ZONE_REF,
  scale: 10000, maxPixels: 1e10, bestEffort: true, tileScale: 8
});
var s_MI = borner_ee(MI, pc.get('MI_p50'), pc.get('MI_p98'));
var s_CI = borner_ee(CI, pc.get('CI_p50'), pc.get('CI_p98'));

// Co-localisation : le produit impose que LES DEUX signaux soient présents
// Végétation (NDVI max > 0.3) : composition non mesurable -> score minimal (fiche : la végétation biaise les indices)
// Choix du score de composition :
//  - 'MI'    : mafique seul. L'indice carbonate (CI) est trop peu contrasté dans ASTER GED à 100 m :
//              p98 des terres arides ≈ 1.007, alors qu'un signal carbonate net correspond à CI > 1.05
//              (Ninomiya). Le CI reste exporté comme information.
//  - 'MI_CI' : co-localisation √(MI × CI), définition de la fiche de Lilian.
var compo_brut = COMPO_MODE === 'MI_CI' ? s_MI.multiply(s_CI).sqrt() : s_MI;
var score_compo = compo_brut.where(ndvi_max.gt(0.3), 0.01)
  .updateMask(terre).rename('score_compo');

// -----------------------------------------------------------------------------
// 4. SCORES COMBINÉS ET ENTONNOIR
// -----------------------------------------------------------------------------
var score_env_relief = score_env.log().multiply(0.55).add(score_relief.log().multiply(0.45)).exp();

var score_final = score_env.log().multiply(POIDS.env)
  .add(score_relief.log().multiply(POIDS.relief))
  .add(score_compo.log().multiply(POIDS.compo))
  .exp().rename('score_final');

var terre_zone = terre.clip(ZONE);
var etape1 = terre_zone.and(elimine.not()).and(score_env.gte(SEUIL_ENV)).selfMask();
var etape2 = etape1.and(score_env_relief.gte(SEUIL_ENV_RELIEF)).selfMask();
var etape3 = etape2.and(score_compo.gte(SEUIL_COMPO)).selfMask();

// Étiquettes
var morphotype = ee.Image(5)
  .where(relief_local.lt(50), 2)
  .where(relief_local.gte(600).and(relief_local.lt(1500)), 3)
  .where(relief_local.gte(1500), 4)
  .where(tpi.lt(-100).and(relief_local.gte(100)).and(relief_local.lt(600)), 1)
  .rename('morphotype');
var typologie = ee.Image(4)
  .where(temp_moy.lt(20), 3)
  .where(temp_moy.lt(10).and(dem1k.lt(2500)), 2)
  .where(temp_moy.lt(10).and(dem1k.gte(2500)), 1)
  .rename('typologie');
var NOMS_MORPHO = ee.Dictionary({'1': 'Bassin à relief modéré (type Jezero)', '2': 'Plaine plate / salar',
  '3': 'Relief accidenté', '4': 'Montagne', '5': 'Intermédiaire'});
var NOMS_TYPO = ee.Dictionary({'1': "Désert froid d'altitude", '2': 'Désert froid de plaine/polaire',
  '3': 'Désert tempéré', '4': 'Désert chaud'});
function nom(dico, v) { return dico.get(ee.Number(v).round().int().format()); }

// Lettre par dimension : A / B / C / D
function lettre(v, a, b, c) {
  v = ee.Number(v);
  return ee.String(ee.Algorithms.If(v.gte(a), 'A',
                   ee.Algorithms.If(v.gte(b), 'B',
                   ee.Algorithms.If(v.gte(c), 'C', 'D'))));
}
// env et relief : A ≥ 0.60, B ≥ 0.45, C ≥ 0.30 ; compo (fiche) : A ≥ 0.70, B ≥ 0.40, sinon C
function profil(env, relief, compo) {
  return ee.String('Env ').cat(lettre(env, 0.60, 0.45, 0.30))
    .cat(' · Relief ').cat(lettre(relief, 0.60, 0.45, 0.30))
    .cat(' · Compo ').cat(lettre(compo, 0.70, 0.40, -1));
}

// -----------------------------------------------------------------------------
// 5. VALIDATION (sites témoins de la fiche + analogues connus)
// -----------------------------------------------------------------------------
var temoins = ee.FeatureCollection([
  ee.Feature(ee.Geometry.Point([58.50, 22.90]),    {nom: 'Oman, ophiolite de Samail', attendu: 'compo élevée'}),
  ee.Feature(ee.Geometry.Point([-70.00, -24.10]),  {nom: 'Atacama, Yungay', attendu: 'env élevé, compo faible'}),
  ee.Feature(ee.Geometry.Point([51.00, 20.00]),    {nom: "Rub' al Khali", attendu: 'MI bas (sable quartzeux)'}),
  ee.Feature(ee.Geometry.Point([-60.00, -3.00]),   {nom: 'Amazonie', attendu: 'tout bas'}),
  ee.Feature(ee.Geometry.Point([-110.79, 38.41]),  {nom: 'MDRS (Utah)', attendu: 'env et relief corrects'}),
  ee.Feature(ee.Geometry.Point([-69.196, -27.501]),{nom: 'Andes #1', attendu: 'env et relief A'}),
  ee.Feature(ee.Geometry.Point([94.77, 39.30]),    {nom: 'Qaidam (site du top 30)', attendu: 'env et relief A'})
]);
// Moyenne sur un disque de 10 km autour de chaque témoin (comme Lilian)
var bandes_val = score_final.addBands([score_env, score_relief, score_compo, MI, CI]);
var val = bandes_val.reduceRegions({collection: temoins.map(function (f) { return f.buffer(10000); }),
                                    reducer: ee.Reducer.mean(), scale: 1000, tileScale: 4})
  .filter(ee.Filter.notNull(['score_env', 'score_relief', 'score_compo']));
print('Rampes composition (terres arides du globe) :', pc);
print('VALIDATION [nom, attendu, score final, profil, env, relief, compo, MI, CI] :',
  val.map(function (f) {
    return f.set('ligne', [f.get('nom'), f.get('attendu'), f.get('score_final'),
      profil(f.get('score_env'), f.get('score_relief'), f.get('score_compo')),
      f.get('score_env'), f.get('score_relief'), f.get('score_compo'), f.get('MI'), f.get('CI')]);
  }).aggregate_array('ligne'));

// -----------------------------------------------------------------------------
// 6. SURFACES DE L'ENTONNOIR
// -----------------------------------------------------------------------------
function surface_km2(masque) {
  return ee.Number(ee.Image.pixelArea().divide(1e6).updateMask(masque).reduceRegion({
    reducer: ee.Reducer.sum(), geometry: ZONE, scale: ECHELLE_STATS,
    maxPixels: 1e10, bestEffort: true, tileScale: 16
  }).get('area'));
}
var s0 = surface_km2(terre_zone), s1 = surface_km2(etape1), s2 = surface_km2(etape2), s3 = surface_km2(etape3);
var entonnoir = ee.Dictionary({
  'Étape 0 - terres (km²)': s0.round(),
  'Étape 1 - après environnement (km²)': s1.round(),
  'Étape 2 - après relief (km²)': s2.round(),
  'Étape 3 - après composition (km²)': s3.round(),
  'Étape 1 - % restant': s1.divide(s0).multiply(100),
  'Étape 2 - % restant': s2.divide(s0).multiply(100),
  'Étape 3 - % restant': s3.divide(s0).multiply(100)
});
if (!MONDE) print('ENTONNOIR (' + ZONE_CHOISIE + ') :', entonnoir);
else print('Mode MONDE : carte et Console désactivées (trop lourd). Onglet Tasks -> Run all.');

// -----------------------------------------------------------------------------
// 7. SITES = CASES DE 0.25° : meilleure parcelle de chaque case ayant passé l'étape 3
// -----------------------------------------------------------------------------
var ll = ee.Image.pixelLonLat();
var label = ll.select('latitude').add(90).divide(0.25).floor().multiply(2000)
  .add(ll.select('longitude').add(180).divide(0.25).floor())
  .toInt().rename('cellule');
// 1) liste des numéros de cases contenant au moins un pixel de l'étape 3
var ids = label.updateMask(etape3).reduceToVectors({
  geometry: ZONE, scale: ECHELLE_SITES, geometryType: 'polygon', eightConnected: false,
  labelProperty: 'cellule', maxPixels: 1e10, bestEffort: true, tileScale: 16
}).aggregate_array('cellule').distinct();
// 2) une seule case carrée de 0.25° par numéro (évite plusieurs sites dans la même case)
var cellules = ee.FeatureCollection(ids.map(function (id) {
  id = ee.Number(id);
  var lat0 = id.divide(2000).floor().multiply(0.25).subtract(90);
  var lon0 = id.mod(2000).multiply(0.25).subtract(180);
  return ee.Feature(ee.Geometry.Rectangle(ee.List([lon0, lat0, lon0.add(0.25), lat0.add(0.25)]),
                                          'EPSG:4326', false), {cellule: id});
}));

// Score de la CASE (plus robuste que le meilleur pixel, qui sature souvent à 1.0) :
//   score_moyen = moyenne du score final sur les pixels de la case ayant passé l'étape 3
//   part_case   = part des terres de la case qui passe l'étape 3 (0 à 1)
var stats_case = score_final.updateMask(etape3).rename('score_moyen')
  .addBands(etape3.unmask(0).updateMask(terre_zone).rename('part_case'))
  .addBands(score_env.updateMask(etape3).rename('env_moy'))
  .addBands(score_relief.updateMask(etape3).rename('relief_moy'))
  .addBands(score_compo.updateMask(etape3).rename('compo_moy'));
cellules = stats_case.reduceRegions({collection: cellules, reducer: ee.Reducer.mean(), scale: 1000, tileScale: 16});

// Ordre des bandes = sorties max, max1, ..., max15
var image_scan = score_final.updateMask(etape3)
  .addBands(ll.select(['latitude', 'longitude']))
  .addBands([score_env, score_relief, score_compo, MI, CI, morphotype, typologie,
             pente_moy, relief_local, amplitude, temp_moy, ndvi_max, aridite]);

var sites = image_scan.reduceRegions({
  collection: cellules, reducer: ee.Reducer.max(16), scale: 1000, tileScale: 16
}).filter(ee.Filter.notNull(['max', 'max1', 'max2', 'max3', 'max4', 'max5', 'env_moy', 'relief_moy', 'compo_moy']))
  .filter(ee.Filter.gte('part_case', PART_MIN))   // on ignore les cases où seule une petite tache passe
  .map(function (f) {
    return ee.Feature(ee.Geometry.Point([f.getNumber('max2'), f.getNumber('max1')]), {
      score_moyen: f.get('score_moyen'), part_case: f.get('part_case'),
      env_moy: f.get('env_moy'), relief_moy: f.get('relief_moy'), compo_moy: f.get('compo_moy'),
      // profil calculé sur les MOYENNES de la case (le meilleur pixel est presque toujours « A partout »)
      profil: profil(f.get('env_moy'), f.get('relief_moy'), f.get('compo_moy')),
      score_final: f.get('max'), lat: f.get('max1'), lon: f.get('max2'),
      score_env: f.get('max3'), score_relief: f.get('max4'), score_compo: f.get('max5'),
      MI: f.get('max6'), CI: f.get('max7'),
      morphotype: nom(NOMS_MORPHO, f.get('max8')), typologie: nom(NOMS_TYPO, f.get('max9')),
      pente_moy_deg: f.get('max10'), relief_local_m: f.get('max11'),
      amplitude_K: f.get('max12'), temp_moy_C: f.get('max13'),
      ndvi_max: f.get('max14'), aridite: f.get('max15')
    });
  }).sort('score_moyen', false);   // classement par score moyen de la case

if (!MONDE) {
  print('Nombre de sites (cases de 25 km) :', sites.size());
  print('TOP 20 [score moyen case, part de la case, meilleur pixel, profil, typologie, morphotype, lat, lon] :',
    sites.limit(20).reduceColumns(ee.Reducer.toList(8),
      ['score_moyen', 'part_case', 'score_final', 'profil', 'typologie', 'morphotype', 'lat', 'lon']).get('list'));
}

// -----------------------------------------------------------------------------
// 8. CARTE (zones de test uniquement)
// -----------------------------------------------------------------------------
if (!MONDE) {
  Map.centerObject(ZONE, 6);
  Map.addLayer(terre_zone.selfMask(), {palette: ['#bbbbbb']}, 'Étape 0 : terres');
  Map.addLayer(etape1, {palette: ['#fdae61']}, 'Étape 1 : environnement');
  Map.addLayer(etape2, {palette: ['#a6d96a']}, 'Étape 2 : relief');
  Map.addLayer(etape3, {palette: ['#1a9850']}, 'Étape 3 : composition');
  Map.addLayer(score_compo.clip(ZONE), {min: 0, max: 1, palette: ['black', 'purple', 'orange', 'white']},
               'Score composition (MI × CI)', false);
  Map.addLayer(score_final.clip(ZONE), {min: 0, max: 0.8, palette: ['black', 'purple', 'orange', 'white']},
               'Score final', false);
  Map.addLayer(sites, {color: 'cyan'}, 'Sites (meilleure parcelle par case)');
}

// -----------------------------------------------------------------------------
// 9. EXPORTS (onglet Tasks -> Run all ; obligatoires en mode monde)
// -----------------------------------------------------------------------------
Export.table.toDrive({
  collection: ee.FeatureCollection([ee.Feature(null, entonnoir.set('zone', ZONE_CHOISIE))]),
  description: 'final_surfaces_' + ZONE_CHOISIE, fileFormat: 'CSV'
});
Export.table.toDrive({
  collection: sites, description: 'final_sites_' + ZONE_CHOISIE, fileFormat: 'CSV',
  selectors: ['score_moyen', 'part_case', 'profil', 'env_moy', 'relief_moy', 'compo_moy', 'score_final', 'score_env', 'score_relief', 'score_compo', 'MI', 'CI',
              'typologie', 'morphotype', 'lat', 'lon', 'pente_moy_deg', 'relief_local_m',
              'amplitude_K', 'temp_moy_C', 'ndvi_max', 'aridite']
});
