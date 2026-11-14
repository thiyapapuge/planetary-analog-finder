"""Interface Streamlit de sélection et de localisation d'une cible LOLA."""
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.windows import from_bounds, Window
import streamlit as st
from lunar_analysis import analyze_site, DEFAULT_DEM, LUNAR_GEOGRAPHIC, LUNAR_POLAR
from pyproj import Transformer


def _context_raster(src, x, y, radius_m, max_pixels=420):
    """Lire uniquement un extrait autour de la cible, en conservant ses coordonnées."""
    bounds = src.bounds
    left = max(bounds.left, x - radius_m)
    right = min(bounds.right, x + radius_m)
    bottom = max(bounds.bottom, y - radius_m)
    top = min(bounds.top, y + radius_m)
    if right <= left or top <= bottom:
        raise ValueError("La zone de contexte est hors de l'emprise du DEM.")
    w = from_bounds(left, bottom, right, top, transform=src.transform)
    w = w.round_offsets().round_lengths()
    w = w.intersection(Window(0, 0, src.width, src.height))
    height = max(2, round(w.height / max(w.width, w.height) * max_pixels))
    width = max(2, round(w.width / max(w.width, w.height) * max_pixels))
    data = src.read(1, window=w, out_shape=(height, width),
                    resampling=Resampling.bilinear, masked=True)
    data = np.ma.masked_invalid(data.astype(float) * src.scales[0] + src.offsets[0])
    transform = src.window_transform(w)
    extent = (transform.c, transform.c + transform.a * w.width,
              transform.f + transform.e * w.height, transform.f)
    return data, extent


def _plot_location(dem_path, result):
    x, y = result['center_x_m'], result['center_y_m']
    half = result['taille_effective_m'] / 2
    with rasterio.open(dem_path) as src:
        # Vue du pôle Sud (si le DEM contient le pôle) et zoom autour de la cible.
        overview_radius = max(25000, min(125000, np.hypot(x, y) + 18000))
        views = [
            ('Contexte polaire', 0.0, 0.0, overview_radius),
            ('Zoom sur la cible', x, y, max(12000, half * 3)),
        ]
        fig, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
        for ax, (title, cx, cy, radius) in zip(axes, views):
            image, extent = _context_raster(src, cx, cy, radius)
            ax.imshow(image, extent=extent, origin='upper', cmap='terrain')
            ax.add_patch(patches.Rectangle((x - half, y - half), 2 * half, 2 * half,
                                            fill=False, edgecolor='red', linewidth=2,
                                            label='Carré analysé'))
            ax.plot(x, y, 'r+', markersize=10, markeredgewidth=2)
            ax.plot(0, 0, marker='*', color='white', markeredgecolor='black',
                    markersize=11, label='Pôle Sud (90° S)')
            ax.set_title(title)
            ax.set_xlabel('X lunaire IAU:30135 (km)')
            ax.set_ylabel('Y lunaire IAU:30135 (km)')
            ax.ticklabel_format(style='plain', useOffset=False)
            from matplotlib.ticker import FuncFormatter
            ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v / 1000:g}'))
            ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v / 1000:g}'))
            ax.set_aspect('equal')
            ax.legend(loc='best', fontsize=8)
        return fig


def render_lunar_selector():
    st.subheader('🌙 Cible lunaire LOLA — sélection géographique')
    st.caption('Coordonnées planétocentriques lunaires IAU:30100 ; DEM polaire IAU:30135.')
    mode = st.radio('Mode de sélection', ['Latitude / longitude lunaires', 'X / Y projetés (m)'], horizontal=True)
    kwargs = {}
    if mode == 'Latitude / longitude lunaires':
        a, b = st.columns(2)
        kwargs['lat'] = a.number_input('Latitude lunaire (°)', min_value=-90.0, max_value=-80.0, value=-89.9, format='%.6f')
        kwargs['lon'] = b.number_input('Longitude lunaire (°)', min_value=-180.0, max_value=180.0, value=0.0, format='%.6f')
    else:
        a, b = st.columns(2)
        kwargs['x'] = a.number_input('X polaire (m)', value=0.0, step=100.0)
        kwargs['y'] = b.number_input('Y polaire (m)', value=0.0, step=100.0)
    a, b = st.columns(2)
    resolution = a.selectbox('Résolution demandée (m)', [40, 80, 120], index=1)
    tile_m = b.number_input('Côté de la zone (m)', min_value=500, max_value=20000, value=5000, step=500)
    st.info('Le contour du cratère Shackleton n’est pas fourni dans ce DEM : la carte situe précisément le carré dans la projection lunaire, mais ne certifie pas son appartenance au rebord.')
    if st.button('Analyser cette zone lunaire', type='primary'):
        try:
            results, images = analyze_site(DEFAULT_DEM, tile_size_m=int(tile_m),
                                           resolutions=[resolution], **kwargs)
            r = results[0]
            st.session_state['lunar_target'] = {
                'pente_deg': r['pente_deg'], 'tri_m': r['tri_m'],
                'source': r['source'], 'resolution_m': float(resolution),
                'resolution_effective_m': r['resolution_effective_m'],
                'center_x_m': r['center_x_m'], 'center_y_m': r['center_y_m'],
                'center_lat': r['center_lat'], 'center_lon': r['center_lon'],
                'taille_effective_m': r['taille_effective_m'],
            }
            st.session_state['lunar_result'] = r
            st.session_state['lunar_dem_preview'] = images[float(resolution)]
        except (ValueError, OSError, FileNotFoundError) as exc:
            st.error(str(exc))

    if 'lunar_result' in st.session_state:
        r = st.session_state['lunar_result']
        c1, c2, c3 = st.columns(3)
        c1.metric('Pente Horn', f"{r['pente_deg']:.3f}°")
        c2.metric('TRI RMS', f"{r['tri_m']:.3f} m")
        c3.metric('Résolution effective', f"{r['resolution_effective_m']:.3f} m")
        st.markdown('#### 📍 Localisation géoréférencée de la zone')
        try:
            fig = _plot_location(DEFAULT_DEM, r)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        except (OSError, ValueError) as exc:
            st.warning(f'Carte de localisation indisponible : {exc}')
        st.caption('Le rectangle rouge représente le carré réellement analysé ; l’étoile indique le pôle Sud. Les axes sont en kilomètres dans la projection lunaire IAU:30135. Aucun contour de Shackleton n’est supposé.')
        lat, lon = r['center_lat'], r['center_lon']
        if lat is None or lon is None:
            transformer = Transformer.from_crs(LUNAR_POLAR, LUNAR_GEOGRAPHIC, always_xy=True)
            lon, lat = transformer.transform(r['center_x_m'], r['center_y_m'])
        st.write(f"**Centre lunaire :** {lat:.6f}° latitude, {lon:.6f}° longitude  |  "
                 f"**Projection :** X = {r['center_x_m']:.1f} m, Y = {r['center_y_m']:.1f} m  |  "
                 f"**Carré :** {r['taille_effective_m']:.0f} × {r['taille_effective_m']:.0f} m")
        fig, ax = plt.subplots(figsize=(6, 5))
        im = ax.imshow(st.session_state['lunar_dem_preview'], cmap='terrain')
        ax.set_title('Relief LOLA — carré analysé')
        ax.set_xlabel('Colonne (pixels)')
        ax.set_ylabel('Ligne (pixels)')
        fig.colorbar(im, ax=ax, label='Altitude (m)')
        st.pyplot(fig)
        plt.close(fig)
        st.success('Cible calculée et conservée pour le scan terrestre GEE.')
