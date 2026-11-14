# -*- coding: utf-8 -*-
"""
🛰️ Planetary Analog Finder — NASA Space Apps Challenge
=======================================================
Application Streamlit — Focus 100 % Mars (Cratère Jezero & Analogues Terrestres)

Lancement :  streamlit run app.py
"""

import io
import json
from datetime import datetime
from html import escape

import folium
from branca.colormap import LinearColormap
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pyproj import CRS, Transformer
import streamlit as st
from streamlit_folium import st_folium

# ----------------------------------------------------------------------------
# 1. CONFIGURATION & THÈME "NASA SPACE DASHBOARD"
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Planetary Analog Finder — Mars Jezero",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

NASA_RED = "#fc3d21"
NASA_BLUE = "#4a90e2"
BG = "#0b0f1a"
PANEL = "#141a2b"

st.markdown(
    f"""
    <style>
    .stApp {{ background: radial-gradient(circle at 20% 0%, #121a33 0%, {BG} 60%); color:#e6e9f2; }}
    section[data-testid="stSidebar"] {{ background:{PANEL}; border-right:1px solid #232c47; }}
    h1, h2, h3 {{ font-family: 'Helvetica Neue', Arial, sans-serif; letter-spacing:.5px; }}
    .hero {{ padding:18px 24px; border-radius:14px; margin-bottom:14px;
             background:linear-gradient(90deg,#0b3d91 0%,#141a2b 70%); border:1px solid #2a3558; }}
    .hero h1 {{ margin:0; font-size:2rem; }}
    .hero p {{ margin:4px 0 0 0; color:#aab4d4; }}
    .kpi {{ background:{PANEL}; border:1px solid #2a3558; border-left:4px solid {NASA_RED};
            border-radius:12px; padding:14px 18px; }}
    .kpi .label {{ font-size:.78rem; text-transform:uppercase; color:#8f9bc0; letter-spacing:1px; }}
    .kpi .value {{ font-size:1.9rem; font-weight:700; color:#fff; }}
    .kpi .sub {{ font-size:.8rem; color:#8f9bc0; }}
    .stTabs [data-baseweb="tab"] {{ background:{PANEL}; border-radius:8px 8px 0 0; padding:10px 18px; }}
    .stTabs [aria-selected="true"] {{ border-bottom:3px solid {NASA_RED}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# 2. BASE DE DONNÉES (Cibles martiennes + sites terrestres)
# ----------------------------------------------------------------------------
METRIQUES = {
    "pente": "Pente moyenne (°)",
    "tri": "Rugosité TRI (m)",
    "albedo": "Albédo / Réflectance",
    "sterilite": "Stérilité végétale (0-1)",
    "thermique": "Variabilité thermique (K)",
}

CIBLES = {
    "🔴 Mars — Cratère Jezero": {
        "lat": 18.38, "lon": 77.58, "pente": 8.0, "tri": 25.0, "albedo": 0.20,
        "sterilite": 1.0, "thermique": 80.0,
        "desc": "Ancien delta fluvial (Perseverance), argiles smectites et carbonates. Données : MOLA, CRISM, HiRISE.",
    },
    "🔴 Mars — Mawrth Vallis": {
        "lat": 23.98, "lon": -341.04, "pente": 5.0, "tri": 18.0, "albedo": 0.22,
        "sterilite": 1.0, "thermique": 85.0,
        "desc": "Ancienne vallée fluviale riche en argiles riches en Fe/Mg. Données : MOLA, CRISM.",
    },
    "🔴 Mars — Tharsis (Tubes de lave)": {
        "lat": 0.0, "lon": -112.0, "pente": 10.0, "tri": 30.0, "albedo": 0.25,
        "sterilite": 1.0, "thermique": 90.0,
        "desc": "Pits et structures volcaniques basaltiques. Données : MOLA, THEMIS.",
    },
}

TYPES = ["Désert froid", "Champ volcanique/basaltique", "Structure d'impact", "Tube de lave"]
TYPE_CONTROLE = "Non-analogue (contrôle)"
TYPE_UTILISATEUR = "Site utilisateur"

SITES_BASE = pd.DataFrame([
    ["Askja (Islande)", "Champ volcanique/basaltique", 65.03, -16.75, 14.0, 38.0, 0.10, 0.97, 25.0],
    ["Svalbard (Norvège)", "Désert froid", 78.22, 15.65, 12.0, 30.0, 0.22, 0.80, 35.0],
    ["Atacama (Chili)", "Désert froid", -24.50, -69.25, 6.0, 15.0, 0.30, 0.99, 30.0],
    ["Cratère de Tsenkher (Mongolie)", "Structure d'impact", 47.90, 100.30, 16.0, 42.0, 0.18, 0.75, 40.0],
    ["Tubes de lave (Canaries)", "Tube de lave", 28.35, -16.72, 10.0, 28.0, 0.09, 0.60, 15.0],
    ["Forêt de Fontainebleau (France)", TYPE_CONTROLE, 48.40, 2.70, 3.0, 6.0, 0.12, 0.05, 18.0],
], columns=["nom", "type", "lat", "lon", "pente", "tri", "albedo", "sterilite", "thermique"])


# ----------------------------------------------------------------------------
# 3. MOTEUR DE CALCUL
# ----------------------------------------------------------------------------
def calculer_etendues(sites: pd.DataFrame) -> dict:
    etendues, minimums = {}, {}
    for m in METRIQUES:
        valeurs = list(sites[m]) + [c[m] for c in CIBLES.values()]
        minimums[m] = min(valeurs)
        etendues[m] = max(max(valeurs) - min(valeurs), 1e-9)
    return {"min": minimums, "range": etendues}


def calculer_asi(site: pd.Series, cible: dict, poids: dict, etendues: dict) -> float:
    sigma = {"pente": 7.0, "tri": 20.0, "albedo": 0.15, "sterilite": 0.25}
    total = sum(poids.values())
    if total <= 0:
        return 0.0
    score = sum((w / total) * np.exp(-abs(float(site[m]) - float(cible[m])) / sigma[m])
                for m, w in poids.items() if m in sigma)
    return float(100 * score)


def classer_asi(score: float) -> str:
    if score >= 80:
        return "Excellent"
    if score >= 60:
        return "Bon"
    if score >= 40:
        return "Modéré"
    return "Faible"


def couleur_asi(score: float) -> str:
    return "#2ecc71" if score >= 80 else "#f1c40f" if score >= 60 else "#e67e22" if score >= 40 else "#e74c3c"


def simuler_pentes(pente_moy: float, n: int = 5000, graine: int = 42) -> np.ndarray:
    rng = np.random.default_rng(graine)
    k = 2.0
    return np.clip(rng.gamma(k, pente_moy / k, n), 0, 60)


def normaliser(valeur: float, metrique: str, etendues: dict) -> float:
    return (valeur - etendues["min"][metrique]) / etendues["range"][metrique]


def pente_tri_depuis_mnt(mnt: np.ndarray, resolution_m: float) -> tuple:
    mnt = np.where(np.isfinite(mnt), mnt, np.nanmean(mnt))
    gy, gx = np.gradient(mnt, resolution_m)
    pente = np.degrees(np.arctan(np.hypot(gx, gy)))
    somme = np.zeros_like(mnt)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                somme += (np.roll(np.roll(mnt, dy, 0), dx, 1) - mnt) ** 2
    tri = np.sqrt(somme)[1:-1, 1:-1]
    return float(np.mean(pente)), float(np.mean(tri))


def vrm_depuis_mnt(mnt: np.ndarray, resolution_m: float) -> float:
    gy, gx = np.gradient(np.nan_to_num(mnt), resolution_m)
    norme = np.sqrt(gx**2 + gy**2 + 1)
    nx, ny, nz = -gx / norme, -gy / norme, 1 / norme
    sx = sy = sz = np.zeros_like(nx)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            sx = sx + np.roll(np.roll(nx, dy, 0), dx, 1)
            sy = sy + np.roll(np.roll(ny, dy, 0), dx, 1)
            sz = sz + np.roll(np.roll(nz, dy, 0), dx, 1)
    vrm = 1 - np.sqrt(sx**2 + sy**2 + sz**2) / 9
    return float(np.mean(vrm[1:-1, 1:-1]))


# ----------------------------------------------------------------------------
# 4. BARRE LATÉRALE
# ----------------------------------------------------------------------------
st.markdown(
    """<div class="hero"><h1>🛰️ Planetary Analog Finder</h1>
    <p>Sélection & caractérisation de sites analogues terrestres pour Mars —
    NASA Space Apps Challenge</p></div>""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("⚙️ Paramétrage de l'Analogue")
    nom_cible = st.selectbox("🎯 Cible martienne", list(CIBLES.keys()))
    cible = CIBLES[nom_cible]
    st.caption(cible["desc"])

    st.subheader("⚖️ Pondération des métriques")
    w_pente = st.slider("Pente", 0, 100, 30)
    w_tri = st.slider("Rugosité topographique (TRI)", 0, 100, 25)
    w_comp = st.slider("Composition / Spectre (albédo)", 0, 100, 20)
    w_arid = st.slider("Aridité / Végétation", 0, 100, 25)
    poids = {"pente": w_pente, "tri": w_tri, "albedo": w_comp, "sterilite": w_arid}
    total_w = sum(poids.values())
    if total_w == 0:
        poids = {k: 1 for k in poids}
        total_w = 4

    poids_norm = {k: v / total_w for k, v in poids.items()}
    st.markdown("**Somme des poids saisis :** " + f"`{sum([w_pente, w_tri, w_comp, w_arid])}`"
                + " → re-normalisée à **100 %**")
    st.progress(min(sum(poids_norm.values()), 1.0))
    poids = poids_norm

    st.subheader("🏔️ Type de terrain terrestre")
    types_choisis = st.multiselect(
        "Filtrer les sites", TYPES + [TYPE_CONTROLE], default=TYPES + [TYPE_CONTROLE]
    )

# ----------------------------------------------------------------------------
# 5. PRÉPARATION DES DONNÉES
# ----------------------------------------------------------------------------
sites = SITES_BASE.copy()
if "sites_utilisateur" in st.session_state and len(st.session_state["sites_utilisateur"]):
    sites = pd.concat([sites, st.session_state["sites_utilisateur"]], ignore_index=True)

etendues = calculer_etendues(sites)
sites["ASI"] = sites.apply(lambda r: calculer_asi(r, cible, poids, etendues), axis=1)
sites["Verdict"] = sites["ASI"].apply(classer_asi)

masque = sites["type"].isin(types_choisis) | (sites["type"] == TYPE_UTILISATEUR)
sites_f = sites[masque].sort_values("ASI", ascending=False).reset_index(drop=True)

# ----------------------------------------------------------------------------
# 6. ONGLETS
# ----------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab_monde, tab_validation, tab_asi3, tab_mars = st.tabs([
    "🗺️ Exploration Cartographique & Scoring",
    "📊 Analyse Comparative & Métriques (Terre vs Mars)",
    "📡 Catalogue des Données Ouvertes (Open Data Hub)",
    "📖 Guide Méthodologique",
    "🧭 Découverte automatique (GEE)",
    "🌍 Recherche multi-régions",
    "🔬 Validation topographique",
    "🚀 Classement ASI 3.0",
    "🔴 Cible MNT / MOLA"
])


def kpi(col, label, valeur, sous=""):
    col.markdown(
        f'<div class="kpi"><div class="label">{label}</div>'
        f'<div class="value">{valeur}</div><div class="sub">{sous}</div></div>',
        unsafe_allow_html=True,
    )


# ============================ ONGLET 1 ======================================
with tab1:
    if sites_f.empty:
        st.warning("Aucun site ne correspond au filtre sélectionné.")
    else:
        meilleur = sites_f.iloc[0]
        ecart_pente = (sites_f["pente"] - cible["pente"]).abs().mean()
        c1, c2, c3, c4 = st.columns(4)
        kpi(c1, "Sites répertoriés", len(sites_f), f"sur {len(sites)} au total")
        kpi(c2, "Meilleur match global", f"{meilleur['ASI']:.1f} %", meilleur["nom"])
        kpi(c3, "Écart moyen des pentes", f"{ecart_pente:.1f}°", f"vs cible ({cible['pente']:.0f}°)")
        kpi(c4, "Cible active", nom_cible.split(" — ")[0], nom_cible.split("— ")[-1])

        st.markdown("")
        col_carte, col_rang = st.columns([3, 2])

        with col_carte:
            carte = folium.Map(location=[30, 10], zoom_start=2, tiles="OpenStreetMap")
            for _, r in sites_f.iterrows():
                popup = (
                    f"<div style='font-family:Arial;font-size:13px;color:#111;min-width:210px'>"
                    f"<h4 style='margin:0 0 6px 0'>{r['nom']}</h4>"
                    f"<b>Type de terrain :</b> {r['type']}<br>"
                    f"<b>Score ASI :</b> <span style='color:{couleur_asi(r['ASI'])};font-weight:700'>"
                    f"{r['ASI']:.1f} %</span> ({r['Verdict']})<br>"
                    f"<b>Coordonnées :</b> {r['lat']:.2f}, {r['lon']:.2f}<hr style='margin:6px 0'>"
                    f"Pente : {r['pente']:.0f}° · TRI : {r['tri']:.0f} m<br>"
                    f"Albédo : {r['albedo']:.2f} · Stérilité : {r['sterilite']:.2f}<br>"
                    f"Var. thermique : {r['thermique']:.0f} K</div>"
                )
                folium.CircleMarker(
                    location=[r["lat"], r["lon"]],
                    radius=8 + r["ASI"] / 10,
                    color=couleur_asi(r["ASI"]), fill=True, fill_opacity=0.75,
                    popup=folium.Popup(popup, max_width=300),
                    tooltip=f"{r['nom']} — ASI {r['ASI']:.0f} %",
                ).add_to(carte)
            if len(sites_f) == 1:
                carte.location = [sites_f.iloc[0]["lat"], sites_f.iloc[0]["lon"]]
            else:
                carte.fit_bounds(
                    [[sites_f["lat"].min(), sites_f["lon"].min()],
                     [sites_f["lat"].max(), sites_f["lon"].max()]],
                    padding=(40, 40),
                )
            st_folium(carte, height=520, use_container_width=True, returned_objects=[])

        with col_rang:
            st.subheader("🏆 Classement ASI")
            fig = px.bar(
                sites_f.sort_values("ASI"), x="ASI", y="nom", orientation="h",
                color="ASI", color_continuous_scale=["#e74c3c", "#f1c40f", "#2ecc71"],
                range_color=[0, 100], text=sites_f.sort_values("ASI")["ASI"].round(1),
            )
            fig.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                height=470, yaxis_title="", xaxis_title="ASI (%)", coloraxis_showscale=False,
                margin=dict(l=0, r=10, t=10, b=0), xaxis_range=[0, 105],
            )
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            sites_f[["nom", "type", "ASI", "Verdict", "pente", "tri", "albedo", "sterilite"]]
            .rename(columns={"nom": "Site", "type": "Type", "pente": "Pente (°)", "tri": "TRI (m)",
                             "albedo": "Albédo", "sterilite": "Stérilité"}),
            use_container_width=True, hide_index=True,
        )

# ============================ ONGLET 2 ======================================
with tab2:
    if sites_f.empty:
        st.warning("Aucun site à comparer.")
    else:
        nom_site = st.selectbox("Site terrestre à comparer", sites_f["nom"].tolist())
        site = sites_f[sites_f["nom"] == nom_site].iloc[0]

        st.metric("ASI du site sélectionné", f"{site['ASI']:.1f} %", site["Verdict"])

        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("🕸️ Profil radar")
            axes = list(METRIQUES.keys())
            labels = ["Pente", "Rugosité (TRI)", "Albédo", "Stérilité végétale", "Variabilité thermique"]
            v_site = [normaliser(site[m], m, etendues) for m in axes]
            v_cible = [normaliser(cible[m], m, etendues) for m in axes]
            radar = go.Figure()
            radar.add_trace(go.Scatterpolar(
                r=v_site + v_site[:1], theta=labels + labels[:1], fill="toself",
                name=nom_site, line_color=NASA_BLUE, fillcolor="rgba(74,144,226,0.30)"))
            radar.add_trace(go.Scatterpolar(
                r=v_cible + v_cible[:1], theta=labels + labels[:1], fill="toself",
                name=nom_cible, line_color=NASA_RED, fillcolor="rgba(252,61,33,0.25)"))
            radar.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=450,
                polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(range=[0, 1], showticklabels=False)),
                legend=dict(orientation="h", y=-0.1), margin=dict(l=40, r=40, t=30, b=30),
            )
            st.plotly_chart(radar, use_container_width=True)

        with col_b:
            st.subheader("📈 Distribution des pentes")
            hist = go.Figure()
            hist.add_trace(go.Histogram(x=simuler_pentes(site["pente"], graine=1), name=nom_site,
                                        opacity=0.65, marker_color=NASA_BLUE, nbinsx=50, histnorm="probability density"))
            hist.add_trace(go.Histogram(x=simuler_pentes(cible["pente"], graine=2), name=nom_cible,
                                        opacity=0.65, marker_color=NASA_RED, nbinsx=50, histnorm="probability density"))
            hist.update_layout(
                barmode="overlay", template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)", height=450, xaxis_title="Pente (°)",
                yaxis_title="Densité", legend=dict(orientation="h", y=-0.2),
            )
            st.plotly_chart(hist, use_container_width=True)

# ============================ ONGLET 3 ======================================
with tab3:
    st.subheader("🛰️ Analyse réelle — Google Earth Engine")
    with st.form("gee_form"):
        gee_project = st.text_input("ID du projet Google Cloud", placeholder="identify-earth-locations")
        g1, g2, g3 = st.columns(3)
        with g1:
            gee_lat = st.number_input("Latitude", -90.0, 90.0, -24.50, format="%.5f")
        with g2:
            gee_lon = st.number_input("Longitude", -180.0, 180.0, -69.25, format="%.5f")
        with g3:
            gee_radius = st.number_input("Rayon (m)", 500, 20000, 5000, step=500)
        d1, d2 = st.columns(2)
        with d1:
            gee_start = st.date_input("Début des observations", datetime(2024, 1, 1))
        with d2:
            gee_end = st.date_input("Fin des observations (exclue)", datetime(2025, 1, 1))
        gee_submit = st.form_submit_button("🔎 Analyser les 6 métriques", type="primary")
    if gee_submit:
        try:
            from gee_metrics import initialize, analyze
            with st.spinner("Interrogation Earth Engine…"):
                initialize(gee_project)
                st.session_state["gee_result"] = analyze(
                    gee_lat, gee_lon, int(gee_radius),
                    gee_start.isoformat(), gee_end.isoformat())
        except Exception as exc:
            st.error(f"Erreur Earth Engine : {exc}")

    st.subheader("📡 Inventaire des jeux de données ouverts (Mars & Terre)")
    catalogue = pd.DataFrame([
        ["🔴 Mars", "MOLA (MGS)", "MNT global de Mars, 463 m/pixel.", "NASA / USGS",
         "https://astrogeology.usgs.gov/search/map/mars_mgs_mola_dem_463m"],
        ["🔴 Mars", "CRISM (MRO)", "Spectro-imageur : argiles, carbonates, sulfates.", "NASA / JHUAPL",
         "https://crism.jhuapl.edu/"],
        ["🔴 Mars", "HiRISE (MRO)", "Imagerie très haute résolution (25-30 cm/pixel).", "NASA / UArizona",
         "https://www.uahirise.org/"],
        ["🌍 Terre", "Copernicus DEM (GLO-30)", "MNT mondial à 30 m : pente, TRI, VRM.", "ESA / Copernicus",
         "https://spacedata.copernicus.eu/collections/copernicus-digital-elevation-model"],
        ["🌍 Terre", "Sentinel-2 (MSI)", "Bandes VNIR/SWIR 10-20 m : albédo, NDVI.", "ESA / Copernicus",
         "https://sentinels.copernicus.eu/web/sentinel/missions/sentinel-2"],
    ], columns=["Corps", "Jeu de données", "Description & usage", "Agence", "Lien officiel"])
    st.dataframe(catalogue, use_container_width=True, hide_index=True)

# ============================ ONGLET 4 ======================================
with tab4:
    st.subheader("📖 Guide méthodologique")
    st.markdown("Calcul de l'Indice de Similarité Analogue (ASI) appliqué aux spécificités martiennes.")
    st.latex(r"ASI = \left(1 - \sum_i w_i \cdot \frac{\left|x_{\text{Terre},i} - x_{\text{Mars},i}\right|}{\text{Étendue}_i}\right) \times 100")

# ============================ ONGLET CIBLE MARSIENNE ========================
with tab5:
    st.subheader("🧭 Recherche automatique de nouveaux analogues terrestres pour Mars")
    mars_target = st.session_state.get("mars_target")
    with st.form("scan_form"):
        project = st.text_input("ID Google Cloud", value=st.session_state.get("scan_project", ""))
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input("Latitude centre", -90.0, 90.0, -24.5, format="%.5f")
            cols = st.slider("Colonnes", 1, 5, 3)
        with c2:
            lon = st.number_input("Longitude centre", -180.0, 180.0, -69.25, format="%.5f")
            rows = st.slider("Lignes", 1, 5, 3)
        submitted = st.form_submit_button("🔎 Balayer la région", type="primary")

# ============================ ONGLET MULTI-RÉGIONS ==========================
REGIONS_ANALOGUES = {
    "Atacama — Chili": (-24.50, -69.25),
    "Askja — Islande": (65.03, -16.75),
    "Death Valley — États-Unis": (36.50, -116.85),
}

with tab_monde:
    st.subheader("🌍 Recherche multi-régions d'analogues martiens")
    st.write("Comparez des régions terrestres face aux critères du Cratère Jezero.")

with tab_validation:
    st.subheader("🔬 Validation topographique")

with tab_asi3:
    st.subheader("🚀 Classement ASI 3.0 expérimental")

with tab_mars:
    st.subheader("🔴 Paramètres de la cible martienne active")
    st.json(cible)