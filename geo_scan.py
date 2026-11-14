"""Balayage régional Earth Engine pour Planetary Analog Finder.

Grille UTM de tuiles carrées, extraction des métriques et score topographique
à tolérances fixes. Les références lunaires/martiennes doivent être mesurées.

Prérequis : ee.Initialize(project='VOTRE_ID_PROJET') dans app.py avant scan_region.
"""

import math
import ee
import pandas as pd

# Tolérances de comparaison (paramètres expérimentaux à calibrer).
SIGMAS = {"pente_deg": 7.0, "tri_m": 20.0}
ASI_VERSION = "ASI-v1-resolution"


def resolution_sigmas(resolution_m, reference_resolution_m=40.0):
    """Tolérances communes aux scans locaux et régionaux.

    Hypothèse heuristique : sigma pente = 7 deg ; sigma TRI = 20 m à
    40 m/pixel et proportionnel à la résolution nominale (80 m -> 40 m).
    """
    resolution_m = float(resolution_m)
    if not math.isfinite(resolution_m) or resolution_m <= 0:
        raise ValueError("Résolution positive et finie obligatoire.")
    return {"pente_deg": SIGMAS["pente_deg"],
            "tri_m": SIGMAS["tri_m"] * resolution_m / reference_resolution_m}


def fixed_similarity(values, target, sigmas=None):
    """Score [0, 100] indépendant de l'ensemble des candidats.

    Renvoie None si une métrique nécessaire est manquante ou invalide.
    """
    sigmas = SIGMAS if sigmas is None else sigmas
    terms = []
    for metric, sigma in sigmas.items():
        x, y = values.get(metric), target.get(metric)
        try:
            x, y, sigma = float(x), float(y), float(sigma)
        except (TypeError, ValueError):
            return None
        if not (math.isfinite(x) and math.isfinite(y) and math.isfinite(sigma)) or sigma <= 0:
            return None
        terms.append(math.exp(-abs(x - y) / sigma))
    return 100.0 * sum(terms) / len(terms) if terms else None


def _utm(lat, lon):
    if not (-80 <= lat <= 84):
        raise ValueError("Prototype limité aux latitudes UTM (-80° à 84°).")
    if not (-180 <= lon <= 180):
        raise ValueError("Longitude invalide.")
    zone = min(60, max(1, int((lon + 180) // 6) + 1))
    return f"EPSG:{(32600 if lat >= 0 else 32700) + zone}"


def build_topography(region, resolution=40, crs=None):
    """DEM, pente et rugosité RMS à résolution métrique commune.

    TRI ici = sqrt(moyenne des 8 différences d'altitude au carré).
    Ne pas comparer avec un TRI lunaire calculé selon une autre définition.
    """
    if crs is None:
        center = region.centroid(1).coordinates().getInfo()
        crs = _utm(float(center[1]), float(center[0]))

    collection = (ee.ImageCollection("COPERNICUS/DEM/GLO30_2024_1")
                  .filterBounds(region).select("DEM"))

    # COPERNICUS/DEM/GLO30 est une ImageCollection ; chaque tuile possède
    # une projection native. Fixer la projection AVANT les dérivées de terrain.
    dem = (collection.mosaic()
           .setDefaultProjection(collection.first().select("DEM").projection())
           .resample("bilinear")
           .reproject(crs=crs, scale=resolution)
           .rename("altitude_m"))

    slope = ee.Terrain.slope(dem).rename("pente_deg")

    # Moyenne des différences quadratiques avec les huit voisins, en excluant
    # explicitement le pixel central. NeighborhoodToBands garde le masque.
    neighbors = dem.neighborhoodToBands(
        ee.Kernel.square(radius=1, units="pixels", normalize=False)
    )
    # ee.Image.subtract image mono-bande -> diffusée sur les bandes voisines.
    squared = neighbors.subtract(dem).pow(2)
    # Le voisin central apporte zéro; multiplier par 9/8 pour l'exclure.
    tri = (squared.reduce(ee.Reducer.mean())
           .multiply(9.0 / 8.0).sqrt().rename("tri_m"))

    return dem.addBands(slope).addBands(tri)


def scan_region(latitude, longitude, ncols, nrows, target, resolution_m,
                start_date="2024-01-01", end_date="2025-01-01", tile_m=5000):
    """Balaye jusqu'à 25 tuiles et retourne un DataFrame classé.

    target = {'pente_deg': ..., 'tri_m': ..., 'source': ..., 'resolution_m': ...}
    L'initialisation ee.Initialize doit être effectuée par l'application.
    """
    ncols, nrows = int(ncols), int(nrows)
    resolution_m, tile_m = float(resolution_m), float(tile_m)
    latitude, longitude = float(latitude), float(longitude)

    if ncols < 1 or nrows < 1 or ncols * nrows > 25:
        raise ValueError("Sélectionner entre 1 et 25 tuiles.")
    if not 30 <= resolution_m <= 1000:
        raise ValueError("Résolution commune autorisée : 30 à 1000 m.")
    if tile_m <= 0:
        raise ValueError("La taille des tuiles doit être positive.")
    if not target.get("source") or target.get("resolution_m") is None:
        raise ValueError("Indiquer la source et la résolution de la cible mesurée.")
    if abs(float(target["resolution_m"]) - resolution_m) > 1e-6:
        raise ValueError("La résolution cible doit correspondre à la résolution de calcul.")
    if fixed_similarity(target, target, sigmas=resolution_sigmas(resolution_m)) is None:
        raise ValueError("Fournir des valeurs numériques de pente et TRI pour la cible.")

    crs = _utm(latitude, longitude)
    center = ee.Geometry.Point([longitude, latitude]).transform(crs, 1)
    xy = center.coordinates().getInfo()
    x0 = float(xy[0]) - ncols * tile_m / 2
    y0 = float(xy[1]) - nrows * tile_m / 2

    features = []
    for row in range(nrows):
        for col in range(ncols):
            x, y = x0 + col * tile_m, y0 + row * tile_m
            geometry = ee.Geometry.Rectangle(
                [x, y, x + tile_m, y + tile_m], proj=crs, geodesic=False
            )
            features.append(ee.Feature(geometry, {
                "id": f"T{row + 1:02d}-{col + 1:02d}",
            }))
    fc = ee.FeatureCollection(features)
    extent = fc.geometry()

    dem_col = (ee.ImageCollection("COPERNICUS/DEM/GLO30_2024_1")
               .filterBounds(extent).select("DEM"))
    if dem_col.size().getInfo() == 0:
        raise ValueError("Aucune donnée Copernicus DEM pour cette zone.")
    terrain = build_topography(extent, resolution_m, crs)

    s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
          .filterBounds(extent).filterDate(start_date, end_date)
          .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 70)))
    if s2.size().getInfo() == 0:
        raise ValueError("Aucune image Sentinel-2 sur cette zone/période.")

    def ndvi_mask(img):
        scl = img.select("SCL")
        valid = (scl.neq(0).And(scl.neq(1)).And(scl.neq(3))
                 .And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
                 .And(scl.neq(11)))
        return (img.normalizedDifference(["B8", "B4"])
                .rename("ndvi").updateMask(valid))

    ndvi = s2.map(ndvi_mask).median().rename("ndvi")

    modis = (ee.ImageCollection("MODIS/061/MOD11A2")
             .filterBounds(extent).filterDate(start_date, end_date))
    if modis.size().getInfo() == 0:
        raise ValueError("Aucune image MODIS sur cette zone/période.")

    def lst(img):
        qc_ok = img.select("QC_Day").bitwiseAnd(3).lte(1)
        return (img.select("LST_Day_1km").multiply(0.02)
                .subtract(273.15).rename("temperature_c")
                .updateMask(qc_ok))

    temperature = modis.map(lst).mean()
    cover = ee.ImageCollection("ESA/WorldCover/v200").first().select("Map")
    excluded = (cover.eq(10).Or(cover.eq(40)).Or(cover.eq(50))
                .Or(cover.eq(80)).Or(cover.eq(90)).Or(cover.eq(95)))
    admissible = ee.Image.constant(1).subtract(excluded).rename("fraction_admissible")

    bands = (terrain.addBands(ndvi).addBands(temperature)
             .addBands(admissible))
    reduced = bands.reduceRegions(
        collection=fc,
        reducer=ee.Reducer.mean(),
        scale=resolution_m,
        crs=crs,
        tileScale=4,
    )

    def attach_center(feature):
        coords = (feature.geometry().centroid(1)
                  .transform("EPSG:4326", 1).coordinates())
        return feature.set({"center_lon": coords.get(0),
                            "center_lat": coords.get(1)})

    raw = reduced.map(attach_center).getInfo()["features"]
    rows = []
    for feature in raw:
        p = feature["properties"]
        score = fixed_similarity({m: p.get(m) for m in SIGMAS}, target,
                                 sigmas=resolution_sigmas(resolution_m))
        rows.append({
            "tuile": p["id"],
            "latitude": p["center_lat"],
            "longitude": p["center_lon"],
            "altitude_m": p.get("altitude_m"),
            "pente_deg": p.get("pente_deg"),
            "tri_m": p.get("tri_m"),
            "ndvi": p.get("ndvi"),
            "temperature_c": p.get("temperature_c"),
            "fraction_admissible": p.get("fraction_admissible"),
            "score_topographique": score,
            "asi_version": ASI_VERSION,
            "sigma_pente_deg": resolution_sigmas(resolution_m)["pente_deg"],
            "sigma_tri_m": resolution_sigmas(resolution_m)["tri_m"],
        })
    return (pd.DataFrame(rows)
            .sort_values("score_topographique", ascending=False,
                         na_position="last")
            .reset_index(drop=True))


def regional_search(latitude, longitude, grid_cols, grid_rows, target,
                    resolution_m, coarse_tile_m=15000, coarse_resolution_m=240,
                    shortlist_size=5, start_date="2024-01-01",
                    end_date="2025-01-01"):
    """Recherche exploratoire en deux phases autour d'un point terrestre.

    1) Présélection sur cellules de `coarse_tile_m`, selon la pente moyenne
       à résolution grossière. Le TRI grossier n'est PAS comparé au TRI cible.
    2) Recalcul de neuf sous-tuiles de 5x5 km (grille 3x3) au centre de
       chaque cellule de 15 km ou plus présélectionnée. Pour une cellule
       plus petite, une seule tuile centrale est analysée.

    La présélection n'est pas exhaustive : un bon site dans une cellule écartée
    ou loin du centre d'une cellule retenue peut être manqué.
    """
    grid_cols, grid_rows = int(grid_cols), int(grid_rows)
    shortlist_size = int(shortlist_size)
    coarse_tile_m = float(coarse_tile_m)
    coarse_resolution_m = float(coarse_resolution_m)
    resolution_m = float(resolution_m)
    if not 1 <= grid_cols <= 12 or not 1 <= grid_rows <= 12:
        raise ValueError("La grille régionale doit être comprise entre 1 et 12 par axe.")
    if grid_cols * grid_rows > 100:
        raise ValueError("Maximum 100 cellules de présélection.")
    if not 1 <= shortlist_size <= min(10, grid_cols * grid_rows):
        raise ValueError("Choisir entre 1 et 10 cellules finalistes.")
    if not 5000 <= coarse_tile_m <= 50000:
        raise ValueError("Taille des cellules : entre 5 et 50 km.")
    if not 120 <= coarse_resolution_m <= 1000:
        raise ValueError("Résolution de présélection : 120 à 1000 m.")
    if not target.get("source") or float(target.get("resolution_m", -1)) != resolution_m:
        raise ValueError("Source et résolution cible cohérentes obligatoires.")
    if fixed_similarity(target, target, sigmas=resolution_sigmas(resolution_m)) is None:
        raise ValueError("La pente et le TRI cibles doivent être numériques.")

    crs = _utm(float(latitude), float(longitude))
    center = ee.Geometry.Point([float(longitude), float(latitude)]).transform(crs, 1)
    cx, cy = [float(v) for v in center.coordinates().getInfo()]
    x0 = cx - grid_cols * coarse_tile_m / 2
    y0 = cy - grid_rows * coarse_tile_m / 2

    features = []
    for row in range(grid_rows):
        for col in range(grid_cols):
            x = x0 + col * coarse_tile_m
            y = y0 + row * coarse_tile_m
            geom = ee.Geometry.Rectangle(
                [x, y, x + coarse_tile_m, y + coarse_tile_m],
                proj=crs, geodesic=False,
            )
            features.append(ee.Feature(geom, {
                "id": f"R{row + 1:02d}-{col + 1:02d}",
                "utm_x": x + coarse_tile_m / 2,
                "utm_y": y + coarse_tile_m / 2,
            }))
    fc = ee.FeatureCollection(features)
    extent = fc.geometry()
    collection = (ee.ImageCollection("COPERNICUS/DEM/GLO30_2024_1")
                  .filterBounds(extent).select("DEM"))
    if collection.size().getInfo() == 0:
        raise ValueError("Aucun DEM Copernicus disponible pour cette région.")

    # La réduction collective reduceRegions() renvoyait des valeurs nulles
    # alors que reduceRegion() sur les mêmes géométries fonctionne.
    # Utiliser une réduction indépendante par cellule, avec NASADEM en
    # projection native (méthode validée par diagnostic_cellules_gee.py).
    nasadem = ee.Image("NASA/NASADEM_HGT/001").select("elevation")
    nasa_slope = ee.Terrain.slope(nasadem).rename("pente_grossiere_deg")
    coarse_source = "NASA NASADEM (présélection)"
    raw_features = []
    for feature in features:
        props = feature.toDictionary().getInfo()
        try:
            measured = nasa_slope.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=feature.geometry(),
                scale=90,
                maxPixels=10000000,
                tileScale=4,
            ).getInfo()
            props["pente_grossiere_deg"] = measured.get("pente_grossiere_deg")
        except ee.EEException as exc:
            props["pente_grossiere_deg"] = None
            props["erreur_gee"] = str(exc)
        raw_features.append({"properties": props})

    candidates = []
    missing = []
    for f in raw_features:
        p = f.get("properties", {})
        v = p.get("pente_grossiere_deg")
        try:
            slope_value = float(v)
            if not math.isfinite(slope_value):
                raise ValueError("pente non finie")
        except (TypeError, ValueError, OverflowError):
            missing.append({"cellule": p.get("id"), "pente": v, "erreur": p.get("erreur_gee")})
            continue
        candidates.append({
            "cellule_regionale": p["id"],
            "utm_x": float(p["utm_x"]),
            "utm_y": float(p["utm_y"]),
            "pente_grossiere_deg": slope_value,
            "source_dem_presélection": coarse_source,
            "ecart_pente_grossiere_deg": abs(slope_value - float(target["pente_deg"])),
        })
    if not candidates:
        raise ValueError(
            "Aucune cellule avec une pente grossière exploitable. "
            f"Cellules renvoyées par GEE : {len(raw_features)} ; "
            f"valeurs absentes/non numériques : {len(missing)} ; "
            f"exemples : {missing[:5]}. "
            "Les réductions individuelles NASADEM n’ont retourné aucune pente. "
            "Vérifier les erreurs GEE enregistrées pour chaque cellule."
        )
    candidates.sort(key=lambda r: r["ecart_pente_grossiere_deg"])
    coarse_df = pd.DataFrame(candidates)

    selected = candidates[:shortlist_size]
    detailed = []
    failures = []
    for item in selected:
        try:
            coords = (ee.Geometry.Point([item["utm_x"], item["utm_y"]], crs)
                      .transform("EPSG:4326", 1).coordinates().getInfo())
            subgrid = 3 if coarse_tile_m >= 15000 else 1
            result = scan_region(
                latitude=float(coords[1]), longitude=float(coords[0]),
                ncols=subgrid, nrows=subgrid, target=target,
                resolution_m=resolution_m,
                start_date=start_date, end_date=end_date, tile_m=5000,
            )
            result["cellule_regionale"] = item["cellule_regionale"]
            result["pente_grossiere_deg"] = item["pente_grossiere_deg"]
            result["ecart_pente_grossiere_deg"] = item["ecart_pente_grossiere_deg"]
            result["tuile"] = (item["cellule_regionale"] + "-"
                               + result["tuile"].astype(str) + "-5km")
            detailed.append(result)
        except Exception as exc:
            failures.append({"cellule_regionale": item["cellule_regionale"],
                             "erreur": str(exc)})
    if not detailed:
        raise ValueError(f"Aucun candidat détaillé exploitable. Erreurs : {failures}")
    final_df = (pd.concat(detailed, ignore_index=True)
                .sort_values("score_topographique", ascending=False,
                             na_position="last").reset_index(drop=True))
    return final_df, coarse_df, failures
