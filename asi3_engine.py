"""ASI 3.0 experimental: multi-directional, multi-scale profile reranking.

This is a 1D profile multi-scale analysis, NOT a 2D raster multi-scale analysis.
Earth slopes use Earth Engine and lunar slopes Horn; not scientifically calibrated.
"""
import numpy as np
import pandas as pd
import ee
from scipy.ndimage import gaussian_filter1d
from identify_earth_locations.geo_scan import _utm, build_topography
from identify_earth_locations.validation_topographique import (
    analyse_terre, distributions_lunaires, histogram_similarity,
    profile_shape_similarity,
)

DIRECTIONS = {'E–O': (1., 0.), 'N–S': (0., 1.), 'NE–SO': (2**-.5, 2**-.5), 'NO–SE': (-2**-.5, 2**-.5)}


def lunar_profiles(dem, resolution_m, side_m=5000, n=65):
    a = np.asarray(dem, dtype=float)
    if a.ndim != 2 or min(a.shape) < 5 or not np.isfinite(a).all():
        raise ValueError('Raster LOLA manquant ou invalide (minimum 5 × 5 pixels).')
    if resolution_m <= 0:
        raise ValueError('Résolution lunaire invalide.')
    cy, cx = (np.array(a.shape) - 1) / 2
    distance = np.linspace(-side_m / 2, side_m / 2, n)
    from scipy.ndimage import map_coordinates
    profiles = {}
    for name, (dx, dy) in DIRECTIONS.items():
        xs = cx + distance * dx / resolution_m
        ys = cy - distance * dy / resolution_m
        if xs.min() < 0 or xs.max() > a.shape[1] - 1 or ys.min() < 0 or ys.max() > a.shape[0] - 1:
            raise ValueError('Le raster LOLA ne couvre pas les 5 km dans toutes les directions. Réduire la zone ou choisir une cible plus grande.')
        profiles[name] = map_coordinates(a, [ys, xs], order=1, mode='nearest')
    return profiles


def earth_profiles(lat, lon, resolution_m=80, side_m=5000, n=65):
    crs = _utm(float(lat), float(lon))
    center = ee.Geometry.Point([float(lon), float(lat)]).transform(crs, 1)
    x, y = map(float, center.coordinates().getInfo())
    half = side_m / 2
    geom = ee.Geometry.Rectangle([x-half, y-half, x+half, y+half], proj=crs, geodesic=False)
    terrain = build_topography(geom, resolution=resolution_m, crs=crs).select('altitude_m')
    feats = []
    for direction, (dx, dy) in DIRECTIONS.items():
        for i, distance in enumerate(np.linspace(-half, half, n)):
            feats.append(ee.Feature(ee.Geometry.Point([x + distance*dx, y + distance*dy], crs),
                                    {'direction': direction, 'index': i, 'distance_m': float(distance + half)}))
    result = terrain.reduceRegions(ee.FeatureCollection(feats), ee.Reducer.first(),
                                   scale=resolution_m, crs=crs, tileScale=4).getInfo()['features']
    df = pd.DataFrame([{'direction': f['properties']['direction'],
                        'index': f['properties']['index'],
                        'distance_m': f['properties']['distance_m'],
                        'altitude_m': f['properties'].get('first')} for f in result])
    df['altitude_m'] = pd.to_numeric(df['altitude_m'], errors='coerce')
    profiles = {}
    for direction in DIRECTIONS:
        part = df[df.direction == direction].sort_values('index')
        z = part.altitude_m.to_numpy(dtype=float)
        if len(z) != n or np.isfinite(z).sum() < n * .9:
            raise ValueError(f'Profil terrestre incomplet : {direction}')
        if not np.isfinite(z).all():
            good = np.isfinite(z)
            z = np.interp(np.arange(n), np.flatnonzero(good), z[good])
        profiles[direction] = z
    return profiles


def multiscale_similarity(earth, moon, side_m=5000, scales=(80, 160, 320)):
    n = len(moon)
    if n < 5 or len(earth) != n:
        return float('nan'), {}
    spacing = side_m / (n-1)
    detail = {}
    for scale in scales:
        sigma = max(0.0, (scale / spacing) / 2.355)
        e = gaussian_filter1d(earth, sigma=sigma) if sigma else earth
        m = gaussian_filter1d(moon, sigma=sigma) if sigma else moon
        rms = np.sqrt(np.mean(((e - e.mean()) - (m - m.mean())) ** 2))
        ref = max(np.std(e), np.std(m), 1.)
        detail[int(scale)] = float(100 * np.exp(-rms / ref))
    return float(np.mean(list(detail.values()))), detail


def validate_candidate(row, lunar_dem, lunar_resolution, target, side_m=5000, n=65):
    lat, lon = float(row['latitude']), float(row['longitude'])
    resolution = float(target['resolution_m'])
    terrain = analyse_terre(lat, lon, resolution_m=resolution, cote_m=side_m, points_profil=n)
    moon_slope, moon_tri, _ = distributions_lunaires(lunar_dem, lunar_resolution)
    dist_slope = histogram_similarity(terrain['pente_hist'], moon_slope)
    dist_tri = histogram_similarity(terrain['tri_hist'], moon_tri)
    dist_score = float(np.mean([dist_slope, dist_tri]))
    moon_lines = lunar_profiles(lunar_dem, lunar_resolution, side_m=side_m, n=n)
    earth_lines = earth_profiles(lat, lon, resolution_m=resolution, side_m=side_m, n=n)
    directional, scale_details = {}, {}
    for direction in DIRECTIONS:
        earth_line = earth_lines[direction]
        moon_line = moon_lines[direction]
        df = pd.DataFrame({'distance_m': np.linspace(0, side_m, n), 'altitude_m': earth_line})
        directional[direction] = profile_shape_similarity(df, moon_line, side_m)
        _, scales = multiscale_similarity(earth_line, moon_line, side_m)
        scale_details[direction] = scales
    directional_score = float(np.mean(list(directional.values())))
    multiscale_score = float(np.mean([v for scales in scale_details.values() for v in scales.values()]))
    mean_score = float(row['score_topographique'])
    # Explicitly experimental, uncalibrated weighting.
    asi3 = .30*mean_score + .25*dist_score + .25*directional_score + .20*multiscale_score
    return {
        'region': str(row.get('region', '?')), 'tuile': str(row['tuile']),
        'latitude': lat, 'longitude': lon,
        'ASI_initial': mean_score, 'Distributions': dist_score,
        'Profils_4_directions': directional_score,
        'Profils_multiechelles_1D': multiscale_score, 'ASI_3_experimental': asi3,
        'direction_scores': directional, 'scale_scores': scale_details,
        'earth_profiles': earth_lines, 'moon_profiles': moon_lines,
    }
