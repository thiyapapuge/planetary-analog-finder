"""Validation exploratoire d'un analogue terrestre, à partir des rasters réels.

Le calcul GEE de pente (ee.Terrain.slope) n'est pas identique à Horn (LOLA).
Ne pas interpréter les comparaisons de distributions comme une validation
scientifique tant que les opérateurs ne sont pas harmonisés.
"""
import math
import numpy as np
import pandas as pd
import ee
from scipy.ndimage import convolve
from identify_earth_locations.geo_scan import _utm, build_topography


def distributions_lunaires(dem, resolution_m):
    """Pente Horn et TRI RMS 8 voisins, sans bordure, comme lunar_analysis.py."""
    a = np.asarray(dem, dtype=float)
    if a.ndim != 2 or min(a.shape) < 3 or not np.isfinite(a).all():
        raise ValueError("Le raster lunaire doit être une matrice finie d'au moins 3x3.")
    d = float(resolution_m)
    kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]) / (8 * d)
    ky = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]]) / (8 * d)
    slope = np.degrees(np.arctan(np.hypot(convolve(a, kx, mode="nearest"), convolve(a, ky, mode="nearest"))))
    kernel = np.ones((3, 3)); kernel[1, 1] = 0
    neighbors = convolve(a, kernel, mode="nearest")
    neighbors_sq = convolve(a*a, kernel, mode="nearest")
    tri = np.sqrt(np.maximum((neighbors_sq - 2*a*neighbors + 8*a*a)/8, 0))
    return slope[1:-1, 1:-1].ravel(), tri[1:-1, 1:-1].ravel(), a[a.shape[0]//2, :]


def analyse_terre(lat, lon, resolution_m=80, cote_m=5000, points_profil=65):
    """Histogrammes GEE (pixels), profil centre E-O et statistiques 5x5 km."""
    lat, lon, resolution_m, cote_m = map(float, (lat, lon, resolution_m, cote_m))
    crs = _utm(lat, lon)
    center = ee.Geometry.Point([lon, lat]).transform(crs, 1)
    x, y = map(float, center.coordinates().getInfo())
    half = cote_m / 2
    geom = ee.Geometry.Rectangle([x-half, y-half, x+half, y+half], proj=crs, geodesic=False)
    terrain = build_topography(geom, resolution=resolution_m, crs=crs)
    # Histogrammes explicites : les bornes sont fixes, indépendantes du candidat.
    h_slope = terrain.select('pente_deg').reduceRegion(
        ee.Reducer.fixedHistogram(0, 90, 45), geom, resolution_m, crs=crs,
        maxPixels=1000000, tileScale=4).getInfo().get('pente_deg')
    h_tri = terrain.select('tri_m').reduceRegion(
        ee.Reducer.fixedHistogram(0, 200, 50), geom, resolution_m, crs=crs,
        maxPixels=1000000, tileScale=4).getInfo().get('tri_m')
    if not h_slope or not h_tri:
        raise ValueError('Aucun pixel topographique exploitable pour cette zone.')
    pts = []
    for i in range(points_profil):
        xx = x - half + (i + .5) * cote_m / points_profil
        pts.append(ee.Feature(ee.Geometry.Point([xx, y], crs), {'distance_m': (i + .5) * cote_m / points_profil}))
    sampled = terrain.select('altitude_m').reduceRegions(
        ee.FeatureCollection(pts), ee.Reducer.first(), scale=resolution_m,
        crs=crs, tileScale=4).getInfo()['features']
    profile = pd.DataFrame([{
        'distance_m': f['properties']['distance_m'],
        'altitude_m': f['properties'].get('first'),
    } for f in sampled]).sort_values('distance_m')
    profile['altitude_m'] = pd.to_numeric(profile['altitude_m'], errors='coerce')
    if profile['altitude_m'].notna().sum() < 3:
        raise ValueError('Profil altimétrique insuffisant pour cette tuile.')
    return {'pente_hist': h_slope, 'tri_hist': h_tri, 'profil': profile,
            'crs': crs, 'centre': (lat, lon), 'cote_m': cote_m}


def quantiles_histogramme(hist):
    """Quantiles approximatifs par histogramme, non valeurs raster exactes."""
    lowers = np.array([float(h[0]) for h in hist])
    step = float(np.median(np.diff(lowers))) if len(lowers) > 1 else 1.0
    centers = lowers + step / 2
    weights = np.array([float(h[1]) for h in hist])
    if weights.sum() <= 0:
        return {}
    cdf = np.cumsum(weights) / weights.sum()
    return {f'P{q}': float(np.interp(q/100, cdf, centers)) for q in (10, 50, 90)}


def quantiles_pixels(values):
    """Quantiles exacts du tableau de pixels lunaire disponible en session."""
    a = np.asarray(values, dtype=float).ravel()
    a = a[np.isfinite(a)]
    if not len(a):
        return {}
    return {f"P{q}": float(np.percentile(a, q)) for q in (10, 50, 90)}


def histogram_similarity(hist, lunar_pixels):
    """Intersection des histogrammes normalisés (0..100), mêmes bornes."""
    h = np.asarray(hist, dtype=float)
    if h.ndim != 2 or h.shape[1] < 2 or len(h) < 2:
        return float('nan')
    lower = h[:, 0]
    step = float(np.median(np.diff(lower)))
    edges = np.r_[lower, lower[-1] + step]
    earth = np.maximum(h[:, 1], 0)
    lunar = np.asarray(lunar_pixels, dtype=float)
    lunar = lunar[np.isfinite(lunar)]
    lunar_counts, _ = np.histogram(lunar, bins=edges)
    if earth.sum() <= 0 or lunar_counts.sum() <= 0:
        return float('nan')
    return float(100 * np.minimum(earth / earth.sum(), lunar_counts / lunar_counts.sum()).sum())


def profile_shape_similarity(earth_profile, lunar_profile, lunar_length_m=5000):
    """Similarité de forme après centrage et mise à l'échelle, sensible au relief."""
    df = earth_profile.dropna(subset=['distance_m', 'altitude_m']).sort_values('distance_m')
    if len(df) < 3:
        return float('nan')
    earth_x = np.asarray(df['distance_m'], dtype=float)
    earth_y = np.asarray(df['altitude_m'], dtype=float)
    moon_y = np.asarray(lunar_profile, dtype=float)
    if len(moon_y) < 3 or not np.isfinite(moon_y).all():
        return float('nan')
    moon_x = np.linspace(0, float(lunar_length_m), len(moon_y))
    moon_interp = np.interp(earth_x, moon_x, moon_y)
    # Remove vertical offset only, preserve absolute relief amplitude.
    earth_y = earth_y - earth_y.mean()
    moon_interp = moon_interp - moon_interp.mean()
    rms = np.sqrt(np.mean((earth_y - moon_interp) ** 2))
    reference = max(float(np.std(moon_interp)), float(np.std(earth_y)), 1.0)
    return float(100 * np.exp(-rms / reference))
