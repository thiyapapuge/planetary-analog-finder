// =============================================================================
// ÉTAPES DE L'ENTONNOIR — export mondial pour le curseur de l'app
// Nom à l'enregistrement dans Earth Engine : etapes_monde_export
// NASA Space Apps Challenge 2026 — Team Proteus 2
//
// Même modèle que modele_final_v1 (sections 1 à 4 copiées sans changement).
// V2 (après « User memory limit exceeded ») : export d'une IMAGE GeoTIFF à 0.05° (~5.5 km), 4 bandes :
//   land : terres (1/0)
//   e1   : passe l'étape 1 (environnement)
//   e2   : passe les étapes 1 + 2 (environnement + relief)
//   e3   : passe les étapes 1 + 2 + 3 (environnement + relief + composition)
//
// 1) Tester avec ZONE_CHOISIE = 'andes' : la carte montre les 3 étapes (orange, vert clair, vert foncé).
// 2) Passer à 'monde', Run, puis onglet Tasks -> Run. Le fichier arrive dans Google Drive.
// AI disclosure: written with the help of an AI assistant (Claude), reviewed by the team.
// =============================================================================

var ZONE_CHOISIE = 'andes';     // 'andes' pour tester, puis 'monde'

var ZONES = {
  andes: ee.Geometry.Rectangle([-71, -28, -65, -18]),
  monde: ee.Geometry.Rectangle([-180, -60, 180, 80], null, false)
};
var MONDE = ZONE_CHOISIE === 'monde';
var ZONE = ZONES[ZONE_CHOISIE];

var SEUIL_ENV = 0.45, SEUIL_ENV_RELIEF = 0.60, SEUIL_COMPO = 0.40;
var POIDS = {env: 0.35, relief: 0.30, compo: 0.35};
var COMPO_MODE = 'MI';
var DEBUT = '2023-01-01', FIN = '2024-01-01';
var PROJ_1KM = ee.Projection('EPSG:4326').atScale(1000);

function borner(img, v0, v1) { return img.subtract(v0).divide(v1 - v0).clamp(0.01, 1); }
function borner_ee(img, lo, hi) {
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

// -----------------------------------------------------------------------------
// 5. MASQUES DES 3 ÉTAPES (1 = passe, 0 = terre qui ne passe pas)
// -----------------------------------------------------------------------------
// V2 : export en IMAGE (GeoTIFF) au lieu d'un tableau. Earth Engine découpe alors le calcul en
// petites tuiles (shardSize), ce qui évite « User memory limit exceeded ».
// Résolution de sortie : 0.05° (~5.5 km), largement suffisant pour l'affichage sur la carte et le globe.
// L'app regroupera ensuite les pixels en cases de 0.25°.
var masques = ee.Image.cat([
    terre_zone.unmask(0).rename('land'),
    etape1.unmask(0).rename('e1'),
    etape2.unmask(0).rename('e2'),
    etape3.unmask(0).rename('e3')
  ]).toByte();

if (!MONDE) {
  Map.centerObject(ZONE, 6);
  Map.addLayer(masques.select('e1').selfMask(), {palette: ['#fdae61']}, 'Étape 1 : environnement');
  Map.addLayer(masques.select('e2').selfMask(), {palette: ['#a6d96a']}, 'Étapes 1+2 : + relief');
  Map.addLayer(masques.select('e3').selfMask(), {palette: ['#1a9850']}, 'Étapes 1+2+3 : + composition');
} else {
  print('Mode MONDE : Console et carte désactivées (trop lourd). Onglet Tasks -> Run.');
}

// -----------------------------------------------------------------------------
// 6. EXPORT (onglet Tasks -> Run) : GeoTIFF dans Google Drive
// -----------------------------------------------------------------------------
var PAS = 0.05;   // degrés par pixel ; si l'export échoue encore : 0.1
var EMPRISE = MONDE ? [-180, 80] : [-71, -18];   // coin haut-gauche (lon, lat) de la zone
Export.image.toDrive({
  image: masques,
  description: 'etapes_masques_' + ZONE_CHOISIE,
  fileNamePrefix: 'etapes_masques_' + ZONE_CHOISIE,
  region: ZONE,
  crs: 'EPSG:4326',
  crsTransform: [PAS, 0, EMPRISE[0], 0, -PAS, EMPRISE[1]],
  maxPixels: 1e10,
  shardSize: 32,          // petites tuiles de calcul : moins de mémoire par tuile
  fileFormat: 'GeoTIFF',
  formatOptions: {cloudOptimized: false}
});
