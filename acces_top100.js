// =============================================================================
// ACCESSIBILITÉ, ZONES DISPUTÉES ET AIRES PROTÉGÉES — top 100 mondial — Jezero (Mars)
// Nom à l'enregistrement dans Earth Engine : acces_top100
//
// Ajoute trois informations à chaque site du top 100 (le score du modèle ne change pas) :
//   1. ACCESSIBILITÉ : temps de trajet jusqu'à la ville la plus proche
//      (Oxford / Malaria Atlas Project, 2015, en minutes)
//        facile < 6 h · expédition 6 à 24 h · très isolé > 24 h
//   2. ZONE DISPUTÉE : territoire revendiqué par plusieurs pays (frontières LSIB, dép. d'État US)
//   3. AIRE PROTÉGÉE : site dans une aire protégée (WDPA) -> permis de recherche nécessaire
// Puis un second classement « rang accessible » qui écarte les zones disputées.
// Les sites militaires ne figurent dans aucune base mondiale : à vérifier à la main.
// =============================================================================

var sites = ee.FeatureCollection([
  ee.Feature(ee.Geometry.Point([80.7541, 33.7901]), {rang: 1, score_moyen: 0.8400, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 20'}),
  ee.Feature(ee.Geometry.Point([79.9456, 34.6166]), {rang: 2, score_moyen: 0.8337, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 20'}),
  ee.Feature(ee.Geometry.Point([80.8529, 33.7362]), {rang: 3, score_moyen: 0.8223, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 20'}),
  ee.Feature(ee.Geometry.Point([-68.1597, -25.1573]), {rang: 4, score_moyen: 0.8213, profil: 'Env A · Relief A · Compo A', signal_argiles: 'moyen', priorite: 'prioritaire (signal argileux)'}),
  ee.Feature(ee.Geometry.Point([79.1820, 35.1376]), {rang: 5, score_moyen: 0.8206, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 20'}),
  ee.Feature(ee.Geometry.Point([81.0235, 33.6554]), {rang: 6, score_moyen: 0.8172, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 20'}),
  ee.Feature(ee.Geometry.Point([-68.8873, -18.2133]), {rang: 7, score_moyen: 0.8149, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 20'}),
  ee.Feature(ee.Geometry.Point([79.9546, 34.9669]), {rang: 8, score_moyen: 0.8113, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 20'}),
  ee.Feature(ee.Geometry.Point([96.2769, 39.1082]), {rang: 9, score_moyen: 0.8086, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 20'}),
  ee.Feature(ee.Geometry.Point([81.1673, 34.0866]), {rang: 10, score_moyen: 0.8066, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 20'}),
  ee.Feature(ee.Geometry.Point([77.9603, 35.9012]), {rang: 11, score_moyen: 0.8052, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 20'}),
  ee.Feature(ee.Geometry.Point([80.7091, 33.7452]), {rang: 12, score_moyen: 0.8051, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 20'}),
  ee.Feature(ee.Geometry.Point([80.4935, 34.7693]), {rang: 13, score_moyen: 0.8044, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 20'}),
  ee.Feature(ee.Geometry.Point([92.9622, 49.4567]), {rang: 14, score_moyen: 0.8026, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 20'}),
  ee.Feature(ee.Geometry.Point([-71.2319, -16.3628]), {rang: 15, score_moyen: 0.8021, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 20'}),
  ee.Feature(ee.Geometry.Point([96.7980, 39.5483]), {rang: 16, score_moyen: 0.8013, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 20'}),
  ee.Feature(ee.Geometry.Point([80.0354, 34.6615]), {rang: 17, score_moyen: 0.8006, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 20'}),
  ee.Feature(ee.Geometry.Point([81.3200, 34.2662]), {rang: 18, score_moyen: 0.8003, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 20'}),
  ee.Feature(ee.Geometry.Point([-69.8216, -17.2971]), {rang: 19, score_moyen: 0.7998, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 20'}),
  ee.Feature(ee.Geometry.Point([80.7541, 34.6166]), {rang: 20, score_moyen: 0.7996, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 20'}),
  ee.Feature(ee.Geometry.Point([80.5025, 34.7154]), {rang: 21, score_moyen: 0.7992, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([84.5270, 33.0266]), {rang: 22, score_moyen: 0.7984, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([81.0146, 33.9608]), {rang: 23, score_moyen: 0.7982, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([51.9361, 31.0682]), {rang: 24, score_moyen: 0.7982, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([81.5625, 35.7934]), {rang: 25, score_moyen: 0.7973, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([81.0954, 34.8681]), {rang: 26, score_moyen: 0.7964, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([89.9348, 37.7158]), {rang: 27, score_moyen: 0.7962, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([79.3886, 35.0208]), {rang: 28, score_moyen: 0.7945, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([81.4997, 34.1584]), {rang: 29, score_moyen: 0.7944, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([81.3829, 33.7722]), {rang: 30, score_moyen: 0.7942, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([80.0085, 34.8322]), {rang: 31, score_moyen: 0.7940, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([96.2500, 39.0632]), {rang: 32, score_moyen: 0.7936, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([-68.4831, -19.0757]), {rang: 33, score_moyen: 0.7936, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([-67.8902, -20.7646]), {rang: 34, score_moyen: 0.7928, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([-67.8812, -20.7466]), {rang: 35, score_moyen: 0.7920, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([81.5266, 33.8261]), {rang: 36, score_moyen: 0.7920, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([80.0893, 33.5656]), {rang: 37, score_moyen: 0.7917, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([52.9332, 30.4753]), {rang: 38, score_moyen: 0.7911, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([84.8055, 32.8738]), {rang: 39, score_moyen: 0.7908, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([80.8259, 34.8861]), {rang: 40, score_moyen: 0.7907, profil: 'Env A · Relief A · Compo A', signal_argiles: 'moyen', priorite: 'prioritaire (signal argileux)'}),
  ee.Feature(ee.Geometry.Point([52.1247, 31.1221]), {rang: 41, score_moyen: 0.7907, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([80.0713, 35.0478]), {rang: 42, score_moyen: 0.7906, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([95.8008, 39.5843]), {rang: 43, score_moyen: 0.7904, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([95.7200, 39.6202]), {rang: 44, score_moyen: 0.7899, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([-69.1299, -17.8810]), {rang: 45, score_moyen: 0.7890, profil: 'Env A · Relief A · Compo A', signal_argiles: 'moyen', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([81.5176, 33.4937]), {rang: 46, score_moyen: 0.7888, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([78.0591, 35.2544]), {rang: 47, score_moyen: 0.7880, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([82.1285, 33.1164]), {rang: 48, score_moyen: 0.7879, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([81.1403, 34.6076]), {rang: 49, score_moyen: 0.7878, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([85.0211, 32.8379]), {rang: 50, score_moyen: 0.7875, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([96.5644, 46.0791]), {rang: 51, score_moyen: 0.7869, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([-67.9890, -24.9148]), {rang: 52, score_moyen: 0.7867, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([92.4950, 47.9566]), {rang: 53, score_moyen: 0.7867, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([-68.7885, -17.9618]), {rang: 54, score_moyen: 0.7865, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([80.4935, 33.6464]), {rang: 55, score_moyen: 0.7865, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([81.2751, 34.8412]), {rang: 56, score_moyen: 0.7865, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([52.4571, 30.7808]), {rang: 57, score_moyen: 0.7864, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([50.3910, 32.8828]), {rang: 58, score_moyen: 0.7859, profil: 'Env B · Relief A · Compo A', signal_argiles: 'moyen', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([81.6164, 34.1944]), {rang: 59, score_moyen: 0.7859, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([52.8434, 30.5562]), {rang: 60, score_moyen: 0.7857, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([-69.8575, -17.2432]), {rang: 61, score_moyen: 0.7857, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([51.9002, 30.9065]), {rang: 62, score_moyen: 0.7852, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([80.6912, 33.3500]), {rang: 63, score_moyen: 0.7851, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([52.0888, 30.9964]), {rang: 64, score_moyen: 0.7849, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([52.3942, 31.0862]), {rang: 65, score_moyen: 0.7848, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([51.6217, 31.5982]), {rang: 66, score_moyen: 0.7848, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([81.2571, 34.5357]), {rang: 67, score_moyen: 0.7847, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([101.7117, 38.5332]), {rang: 68, score_moyen: 0.7845, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([59.5089, 35.6317]), {rang: 69, score_moyen: 0.7835, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([81.1044, 33.3140]), {rang: 70, score_moyen: 0.7832, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([81.8949, 33.4757]), {rang: 71, score_moyen: 0.7829, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([84.6168, 32.9277]), {rang: 72, score_moyen: 0.7829, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([-68.1237, -19.7674]), {rang: 73, score_moyen: 0.7825, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([82.0297, 33.4578]), {rang: 74, score_moyen: 0.7825, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([50.6874, 32.8020]), {rang: 75, score_moyen: 0.7824, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([80.7451, 33.7811]), {rang: 76, score_moyen: 0.7823, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([96.4117, 39.3866]), {rang: 77, score_moyen: 0.7822, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([-106.1674, 38.1200]), {rang: 78, score_moyen: 0.7820, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([79.2808, 35.6047]), {rang: 79, score_moyen: 0.7819, profil: 'Env A · Relief A · Compo B', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([81.4008, 33.4937]), {rang: 80, score_moyen: 0.7818, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([78.8227, 35.0208]), {rang: 81, score_moyen: 0.7816, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([-69.1568, -18.4649]), {rang: 82, score_moyen: 0.7811, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([72.5704, 39.5214]), {rang: 83, score_moyen: 0.7811, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([-68.3932, -18.9500]), {rang: 84, score_moyen: 0.7809, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([52.7086, 30.6191]), {rang: 85, score_moyen: 0.7808, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([78.1489, 35.6946]), {rang: 86, score_moyen: 0.7807, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([52.5200, 30.9964]), {rang: 87, score_moyen: 0.7807, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([-70.2797, -17.0635]), {rang: 88, score_moyen: 0.7803, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([-68.6987, -25.9748]), {rang: 89, score_moyen: 0.7802, profil: 'Env A · Relief A · Compo A', signal_argiles: 'moyen', priorite: 'prioritaire (signal argileux)'}),
  ee.Feature(ee.Geometry.Point([84.2575, 33.0535]), {rang: 90, score_moyen: 0.7801, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([53.0410, 30.4753]), {rang: 91, score_moyen: 0.7800, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([78.3286, 35.2993]), {rang: 92, score_moyen: 0.7799, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([59.3652, 35.6496]), {rang: 93, score_moyen: 0.7799, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([90.2403, 38.7578]), {rang: 94, score_moyen: 0.7799, profil: 'Env A · Relief A · Compo B', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([78.8766, 34.8861]), {rang: 95, score_moyen: 0.7798, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([-70.4144, -16.7760]), {rang: 96, score_moyen: 0.7797, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([80.7002, 34.3740]), {rang: 97, score_moyen: 0.7795, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([80.2600, 34.7064]), {rang: 98, score_moyen: 0.7795, profil: 'Env A · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([90.2403, 38.7488]), {rang: 99, score_moyen: 0.7794, profil: 'Env A · Relief A · Compo B', signal_argiles: 'faible', priorite: 'top 100'}),
  ee.Feature(ee.Geometry.Point([-67.7464, -20.5759]), {rang: 100, score_moyen: 0.7793, profil: 'Env B · Relief A · Compo A', signal_argiles: 'faible', priorite: 'top 100'})
]);

// --- Données -----------------------------------------------------------------
var acces = ee.Image('Oxford/MAP/accessibility_to_cities_2015_v1_0').select('accessibility');
var pays = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017');
var wdpa = ee.FeatureCollection('WCMC/WDPA/current/polygons');

// Territoires disputés tels que nommés dans LSIB (liste à compléter si besoin :
// la colonne « territoire » exportée permet de vérifier chaque site)
var DISPUTES = ee.List(['Aksai Chin', 'Halaib Triangle', 'Demchok Area', 'Siachen-Saltoro Area',
  'Jammu and Kashmir', 'Jammu & Kashmir', 'Arunachal Pradesh', 'Abyei Area', 'Ilemi Triangle',
  'Bir Tawil', 'Western Sahara', 'Kalapani Area', 'Shaksgam Valley']);

// --- 1. Accessibilité ----------------------------------------------------------
var res = acces.reduceRegions({collection: sites, reducer: ee.Reducer.first(), scale: 1000})
  .map(function (f) {
    var minutes = ee.Number(ee.Algorithms.If(f.get('first'), f.get('first'), -1));
    var heures = minutes.divide(60);
    var classe = ee.String(ee.Algorithms.If(minutes.lt(0), 'inconnu',
                   ee.Algorithms.If(heures.lt(6), 'facile (< 6 h)',
                   ee.Algorithms.If(heures.lt(24), 'expédition (6 à 24 h)', 'très isolé (> 24 h)'))));
    var c = f.geometry().coordinates();
    return f.set({acces_heures: heures, acces_classe: classe, lon: c.get(0), lat: c.get(1)});
  });

// --- 2. Territoire et zone disputée ---------------------------------------------
res = res.map(function (f) {
  var p = pays.filterBounds(f.geometry());
  var territoire = ee.String(ee.Algorithms.If(p.size().gt(0), p.first().get('country_na'), 'inconnu'));
  var dispute = ee.Number(ee.Algorithms.If(DISPUTES.contains(territoire), 1, 0));
  return f.set({territoire: territoire, zone_disputee: dispute});
});

// --- 3. Aire protégée --------------------------------------------------------------
res = res.map(function (f) {
  var a = wdpa.filterBounds(f.geometry());
  var protege = ee.Number(ee.Algorithms.If(a.size().gt(0), 1, 0));
  var nom_aire = ee.String(ee.Algorithms.If(a.size().gt(0), a.first().get('NAME'), ''));
  return f.set({aire_protegee: protege, nom_aire_protegee: nom_aire});
});

// --- 4. Classement « accessible » : on retire les zones disputées -------------------
var ok = res.filter(ee.Filter.eq('zone_disputee', 0)).sort('rang');
var liste = ok.toList(ok.size());
var ok_classes = ee.FeatureCollection(ee.List.sequence(0, ok.size().subtract(1)).map(function (i) {
  return ee.Feature(liste.get(i)).set('rang_accessible', ee.Number(i).add(1));
}));
var exclus = res.filter(ee.Filter.eq('zone_disputee', 1)).map(function (f) {
  return f.set('rang_accessible', -1);   // -1 = écarté (zone disputée)
});
var final = ok_classes.merge(exclus).sort('rang');

// --- Console --------------------------------------------------------------------
print('Zones disputées dans le top 100 :', res.aggregate_sum('zone_disputee'));
print('Aires protégées dans le top 100 :', res.aggregate_sum('aire_protegee'));
print('Accessibilité (nombre de sites par classe) :', res.aggregate_histogram('acces_classe'));
print('Territoires représentés :', res.aggregate_histogram('territoire'));
print('TOP 20 ACCESSIBLE [rang accessible, rang modèle, score, territoire, accès (h), aire protégée, signal argiles] :',
  ok_classes.filter(ee.Filter.lte('rang_accessible', 20))
    .reduceColumns(ee.Reducer.toList(7), ['rang_accessible', 'rang', 'score_moyen', 'territoire',
                                          'acces_heures', 'aire_protegee', 'signal_argiles']).get('list'));

// --- Carte -------------------------------------------------------------------------
Map.centerObject(sites, 3);
Map.addLayer(acces, {min: 0, max: 2880, palette: ['white', 'yellow', 'red', 'black']}, 'Temps de trajet (min)', false);
// Vert : accessible et hors aire protégée · Orange : aire protégée (permis nécessaire) · Rouge : zone disputée
Map.addLayer(ok_classes.filter(ee.Filter.eq('aire_protegee', 0)), {color: '00ff00'}, 'Sites accessibles, hors aire protégée');
Map.addLayer(ok_classes.filter(ee.Filter.eq('aire_protegee', 1)), {color: 'ff9900'}, 'Sites en aire protégée (permis nécessaire)');
Map.addLayer(exclus, {color: 'ff0000'}, 'Sites en zone disputée');

// --- Export -------------------------------------------------------------------------
Export.table.toDrive({
  collection: final, description: 'acces_top100', fileFormat: 'CSV',
  selectors: ['rang', 'rang_accessible', 'score_moyen', 'profil', 'priorite', 'signal_argiles',
              'territoire', 'zone_disputee', 'acces_heures', 'acces_classe',
              'aire_protegee', 'nom_aire_protegee', 'lat', 'lon']
});
