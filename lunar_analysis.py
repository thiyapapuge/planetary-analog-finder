"""Analyse de zones lunaires LOLA (IAU:30135), avec centre géographique choisi.

Exemples :
 python lunar_analysis.py --lat -90 --lon 0 --resolutions 40 80 120
 python lunar_analysis.py --x 12000 --y -9000 --resolutions 80

Les coordonnées du rebord de Shackleton doivent être choisies/validées par
l'utilisateur : ce script n'invente pas un point précis du rebord.
"""
from pathlib import Path
import argparse
import re
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.windows import Window
from scipy.ndimage import convolve
from pyproj import CRS, Transformer

DEFAULT_DEM = Path(__file__).resolve().parent / 'LDEM_80S_40MPP_ADJ.tiff'
LUNAR_GEOGRAPHIC = CRS.from_user_input('IAU:30100')
LUNAR_POLAR = CRS.from_user_input('IAU:30135')


def geographic_to_projected(lat, lon):
    if not (-90 <= lat <= -80):
        raise ValueError('Ce DEM couvre la région polaire sud (latitude -90 à -80°).')
    if not (-180 <= lon <= 180):
        raise ValueError('Longitude hors de [-180, 180].')
    transformer = Transformer.from_crs(LUNAR_GEOGRAPHIC, LUNAR_POLAR, always_xy=True)
    x, y = transformer.transform(float(lon), float(lat))
    if not (np.isfinite(x) and np.isfinite(y)):
        raise ValueError('Transformation des coordonnées lunaires impossible.')
    return float(x), float(y)


def calculate_metrics(dem, pixel_size):
    """Moyenne pente Horn (degrés) et TRI RMS 8 voisins (m), hors bordure."""
    dem = np.asarray(dem, dtype=np.float64)
    if dem.ndim != 2 or min(dem.shape) < 3 or not np.isfinite(dem).all():
        raise ValueError('DEM invalide : minimum 3×3 pixels finis requis.')
    if pixel_size <= 0:
        raise ValueError('Résolution invalide.')
    kx = np.array([[-1,0,1],[-2,0,2],[-1,0,1]], dtype=float)/(8*pixel_size)
    ky = np.array([[-1,-2,-1],[0,0,0],[1,2,1]], dtype=float)/(8*pixel_size)
    dx = convolve(dem, kx, mode='nearest')
    dy = convolve(dem, ky, mode='nearest')
    slope = np.degrees(np.arctan(np.hypot(dx, dy)))
    kernel = np.ones((3,3), dtype=float)
    kernel[1,1] = 0
    neighbors = convolve(dem, kernel, mode='nearest')
    neighbors_sq = convolve(dem**2, kernel, mode='nearest')
    tri = np.sqrt(np.maximum((neighbors_sq - 2*dem*neighbors + 8*dem**2)/8, 0))
    return float(slope[1:-1,1:-1].mean()), float(tri[1:-1,1:-1].mean())


def analyze_site(dem_path=DEFAULT_DEM, *, lat=-90.0, lon=0.0, x=None, y=None,
                 tile_size_m=5000, resolutions=(40,80,120)):
    """Retourne (résultats, images) ; coordonnées lat/lon lunaires ou x/y IAU:30135.

    Les images sont des tableaux numpy pour visualisation locale. Les résolutions
    effectives sont calculées à partir de la fenêtre et de sa taille de sortie.
    """
    if (x is None) != (y is None):
        raise ValueError('Fournir x ET y, ou aucun des deux.')
    used_geographic = x is None
    if used_geographic:
        x, y = geographic_to_projected(lat, lon)
    if not np.isfinite([x, y]).all():
        raise ValueError('Coordonnées non finies.')
    if tile_size_m <= 0:
        raise ValueError('Taille de tuile positive requise.')
    results, images = [], {}
    with rasterio.open(dem_path) as src:
        # Rasterio/GDAL peut renvoyer le WKT complet sans reconnaître le code IAU.
        # On accepte soit l'équivalence CRS, soit l'autorité IAU:30135 déclarée
        # explicitement dans le WKT du fichier (sans se fier à une simple chaîne). 
        raster_wkt = src.crs.to_wkt() if src.crs is not None else ''
        authority_30135 = bool(re.search(
            r'(?:AUTHORITY|ID)\s*\[\s*[\"\']IAU[\"\']\s*,\s*[\"\']?30135[\"\']?\s*\]',
            raster_wkt, flags=re.IGNORECASE
        ))
        equivalent = False
        if src.crs is not None:
            try:
                equivalent = CRS.from_wkt(raster_wkt).equals(LUNAR_POLAR)
            except Exception:
                pass
        if not (authority_30135 or equivalent):
            raise ValueError(f'Projection du raster inattendue : {src.crs} (attendue IAU:30135).')
        rx, ry = map(abs, src.res)
        if abs(rx-ry) > 1e-6:
            raise ValueError('Ce script suppose des pixels carrés.')
        native_pixels = round(tile_size_m / rx)
        if native_pixels < 3:
            raise ValueError('Tuile trop petite pour le DEM.')
        # On centre une fenêtre de pixels natifs sur la coordonnée choisie.
        col_float, row_float = (~src.transform) * (x, y)
        col = round(col_float - native_pixels/2)
        row = round(row_float - native_pixels/2)
        if col < 0 or row < 0 or col+native_pixels > src.width or row+native_pixels > src.height:
            raise ValueError('La zone sélectionnée sort de l’emprise du DEM LOLA.')
        window = Window(col, row, native_pixels, native_pixels)
        footprint = native_pixels * rx
        for requested in resolutions:
            requested = float(requested)
            if requested <= 0:
                raise ValueError('Résolution demandée positive requise.')
            count = round(footprint / requested)
            if count < 3:
                raise ValueError(f'Résolution {requested:g} m trop grossière pour cette tuile.')
            effective = footprint / count
            data = src.read(1, window=window, out_shape=(count,count),
                            resampling=Resampling.bilinear, masked=True)
            if np.ma.getmaskarray(data).any():
                raise ValueError(f'Pixels invalides à {requested:g} m pour cette zone.')
            dem = np.asarray(data, dtype=np.float64) * src.scales[0] + src.offsets[0]
            slope, tri = calculate_metrics(dem, effective)
            results.append({
                'resolution_demandee_m': requested,
                'resolution_effective_m': effective,
                'pente_deg': slope,
                'tri_m': tri,
                'altitude_min_m': float(dem.min()),
                'altitude_max_m': float(dem.max()),
                'pixels': count,
                'center_x_m': x,
                'center_y_m': y,
                'center_lat': lat if used_geographic else None,
                'center_lon': lon if used_geographic else None,
                'taille_effective_m': footprint,
                'source': 'LOLA LDEM_80S_40MPP_ADJ',
            })
            images[requested] = dem
    return results, images


def main():
    p = argparse.ArgumentParser(description='Analyse topographique LOLA sur zone sélectionnée')
    p.add_argument('--dem', type=Path, default=DEFAULT_DEM)
    p.add_argument('--lat', type=float, default=-90.0)
    p.add_argument('--lon', type=float, default=0.0)
    p.add_argument('--x', type=float, default=None, help='Coordonnée projetée X (m, IAU:30135)')
    p.add_argument('--y', type=float, default=None, help='Coordonnée projetée Y (m, IAU:30135)')
    p.add_argument('--tile-size', type=int, default=5000)
    p.add_argument('--resolutions', type=int, nargs='+', default=[40,80,120])
    a = p.parse_args()
    results, _ = analyze_site(a.dem, lat=a.lat, lon=a.lon, x=a.x, y=a.y,
                              tile_size_m=a.tile_size, resolutions=a.resolutions)
    for r in results:
        print(f"\n=== Résolution demandée : {r['resolution_demandee_m']:g} m ===")
        print(f"Centre projeté : ({r['center_x_m']:.2f}, {r['center_y_m']:.2f}) m")
        print(f"Pixels : {r['pixels']} × {r['pixels']}")
        print(f"Résolution effective : {r['resolution_effective_m']:.6f} m")
        print(f"Pente Horn moyenne : {r['pente_deg']:.6f} degrés")
        print(f"TRI RMS moyen : {r['tri_m']:.6f} m")
        print(f"Altitudes min/max : {r['altitude_min_m']:.3f} / {r['altitude_max_m']:.3f} m")

if __name__ == '__main__':
    main()
