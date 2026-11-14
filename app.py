# -*- coding: utf-8 -*-
"""
🛰️ Planetary Analog Finder — NASA Space Apps Challenge
=======================================================
Parcours en 3 étapes pour comparer une zone terrestre à une cible martienne (ex. cratère Jezero) :

    ① Sélection de la zone   →  ② Analyse & métriques  →  ③ Score ASI & rapport

Lancement :  streamlit run app.py        (Streamlit >= 1.50)

──────────────────────────────────────────────────────────────────────────────
BRANCHEMENT DES SCRIPTS BACKEND DE L'ÉQUIPE (voir section 3 « ADAPTATEURS »)
──────────────────────────────────────────────────────────────────────────────
Les modules sont cherchés à côté d'app.py ou dans un sous-dossier `backend/` :

  • gee_metrics.py   (Google Earth Engine)
        initialize(project_id)
        analyze(lat, lon, rayon_m, date_debut_iso, date_fin_iso) -> dict | Series | DataFrame
        (clés reconnues pour les 6 métriques : voir ALIAS_METRIQUES)

  • asi3_engine.py   (composition & relief — moteur ASI 3.0, OPTIONNEL)
        compute_asi3(zone: dict, cible: dict, poids: dict) -> float | {"asi": float}
        (les 6 clés de chaque dict sont : pente, tri, albedo, sterilite, thermique, composition)

Si un module est absent ou lève une erreur, l'application bascule automatiquement sur son
moteur intégré / son mode démonstration et l'indique clairement à l'écran.
Pour changer les signatures, modifiez UNIQUEMENT la section 3.

⚠️ Les valeurs du catalogue et des cibles sont des ordres de grandeur illustratifs.
"""

import importlib
import io
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

import folium
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

# ----------------------------------------------------------------------------
# 1. CONFIGURATION & THÈME
# ----------------------------------------------------------------------------
st.set_page_config(page_title="Planetary Analog Finder", page_icon="🛰️",
                   layout="wide", initial_sidebar_state="expanded")

NASA_RED, NASA_BLUE, BG, PANEL = "#fc3d21", "#4a90e2", "#0b0f1a", "#141a2b"

st.markdown(
    f"""
    <style>
    .stApp {{ background: radial-gradient(circle at 15% 0%, #14204a 0%, {BG} 55%); color:#e6e9f2; }}
    section[data-testid="stSidebar"] {{ background:{PANEL}; border-right:1px solid #232c47; }}
    h1,h2,h3,h4 {{ font-family:'Helvetica Neue',Arial,sans-serif; letter-spacing:.4px; }}
    .hero {{ padding:18px 26px; border-radius:16px; margin-bottom:14px; border:1px solid #2a3558;
             background:linear-gradient(100deg,#0b3d91 0%,#141a2b 65%); }}
    .hero h1 {{ margin:0; font-size:2rem; }}
    .hero p {{ margin:4px 0 0 0; color:#b6c0e0; }}
    .tag {{ font-size:.55em; vertical-align:middle; background:{NASA_RED}; color:#fff;
            padding:3px 10px; border-radius:20px; letter-spacing:1.5px; }}
    .stepper {{ display:flex; gap:12px; margin-bottom:14px; }}
    .step {{ flex:1; background:{PANEL}; border:1px solid #2a3558; border-radius:12px; padding:10px 14px; }}
    .step.done {{ border-color:#2ecc71; }}
    .step .n {{ color:#8f9bc0; font-size:.72rem; text-transform:uppercase; letter-spacing:1px; }}
    .step .t {{ font-weight:600; }}
    .step .s {{ color:#8f9bc0; font-size:.8rem; }}
    .kpi {{ background:{PANEL}; border:1px solid #2a3558; border-left:4px solid {NASA_RED};
            border-radius:12px; padding:12px 16px; margin-bottom:10px; }}
    .kpi .label {{ font-size:.74rem; text-transform:uppercase; color:#8f9bc0; letter-spacing:1px; }}
    .kpi .value {{ font-size:1.7rem; font-weight:700; color:#fff; }}
    .kpi .sub {{ font-size:.78rem; color:#8f9bc0; }}
    .pill {{ display:inline-block; padding:2px 10px; border-radius:20px; font-size:.75rem;
             border:1px solid #2a3558; background:#0f1424; margin-right:6px; }}
    .stTabs [data-baseweb="tab"] {{ background:{PANEL}; border-radius:8px 8px 0 0; padding:10px 20px; }}
    .stTabs [aria-selected="true"] {{ border-bottom:3px solid {NASA_RED}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# 2. DONNÉES DE RÉFÉRENCE
# ----------------------------------------------------------------------------
# Les 6 métriques clés : clé → (libellé, unité, libellé court pour le radar)
METRIQUES = {
    "pente": ("Pente moyenne", "°", "Pente"),
    "tri": ("Rugosité topographique (TRI)", "m", "Rugosité TRI"),
    "albedo": ("Albédo / réflectance", "", "Albédo"),
    "sterilite": ("Stérilité végétale (1 = aucune végétation)", "0-1", "Stérilité"),
    "thermique": ("Variabilité thermique diurne", "K", "Var. thermique"),
    "composition": ("Indice de composition (argiles / SWIR)", "0-1", "Composition"),
}

CIBLES = {
    "🔴 Mars — Cratère Jezero": {
        "lat": 18.38, "lon": 77.58, "pente": 8.0, "tri": 25.0, "albedo": 0.20,
        "sterilite": 1.0, "thermique": 80.0, "composition": 0.75,
        "desc": "Ancien delta fluvial (Perseverance) : smectites et carbonates. Données : MOLA, CRISM, HiRISE."},
    "🔴 Mars — Mawrth Vallis": {
        "lat": 22.3, "lon": -16.5, "pente": 5.0, "tri": 18.0, "albedo": 0.22,
        "sterilite": 1.0, "thermique": 85.0, "composition": 0.85,
        "desc": "Vallée fluviale ancienne riche en phyllosilicates Fe/Mg. Données : MOLA, CRISM."},
    "🔴 Mars — Tharsis (tubes de lave)": {
        "lat": 0.0, "lon": -112.0, "pente": 10.0, "tri": 30.0, "albedo": 0.25,
        "sterilite": 1.0, "thermique": 90.0, "composition": 0.25,
        "desc": "Pits et structures volcaniques basaltiques. Données : MOLA, THEMIS."},
}

TYPE_CONTROLE = "Non-analogue (contrôle)"
_COLS = ["nom", "type", "lat", "lon", "pente", "tri", "albedo", "sterilite", "thermique", "composition"]
CATALOGUE = pd.DataFrame([
    ["Askja / Holuhraun (Islande)", "Champ volcanique/basaltique", 65.03, -16.75, 14.0, 38.0, 0.10, 0.97, 25.0, 0.35],
    ["Svalbard (Norvège)", "Désert froid", 78.22, 15.65, 12.0, 30.0, 0.22, 0.80, 35.0, 0.45],
    ["Désert d'Atacama (Chili)", "Désert aride", -24.50, -69.25, 6.0, 15.0, 0.30, 0.99, 30.0, 0.55],
    ["Cratère de Tsenkher (Mongolie)", "Structure d'impact", 47.90, 100.30, 16.0, 42.0, 0.18, 0.75, 40.0, 0.30],
    ["Lanzarote — tunnels de lave (Canaries)", "Tube de lave", 29.03, -13.63, 10.0, 28.0, 0.09, 0.80, 18.0, 0.30],
    ["Cratère de Lonar (Inde)", "Structure d'impact", 19.98, 76.51, 12.0, 20.0, 0.14, 0.30, 22.0, 0.50],
    ["Meteor Crater (Arizona, USA)", "Structure d'impact", 35.02, -111.02, 25.0, 45.0, 0.28, 0.75, 35.0, 0.20],
    ["Vallées sèches de McMurdo (Antarctique)", "Désert froid", -77.50, 162.50, 15.0, 30.0, 0.25, 0.98, 40.0, 0.30],
    ["Cratère de Haughton (Canada)", "Structure d'impact", 75.38, -89.66, 11.0, 26.0, 0.30, 0.95, 38.0, 0.35],
    ["Kīlauea / Mauna Loa (Hawaï, USA)", "Champ volcanique/basaltique", 19.42, -155.29, 9.0, 33.0, 0.07, 0.85, 12.0, 0.25],
    ["Makhtesh Ramon (Israël)", "Désert aride", 30.60, 34.80, 14.0, 32.0, 0.32, 0.92, 28.0, 0.50],
    ["Forêt de Fontainebleau (France)", TYPE_CONTROLE, 48.40, 2.70, 3.0, 6.0, 0.12, 0.05, 18.0, 0.05],
], columns=_COLS)

# Préréglages rapides (sidebar). « cible » charge une cible martienne, sinon une zone terrestre.
PRESETS = {
    "🔴 Jezero": {"cible": "🔴 Mars — Cratère Jezero",
                  "poids": {"pente": 20, "tri": 15, "albedo": 10, "sterilite": 15, "thermique": 10, "composition": 30}},
    "🏜️ Atacama": {"zone_nom": "Désert d'Atacama (Chili)", "lat": -24.50, "lon": -69.25, "rayon": 5000},
    "🌋 Islande": {"zone_nom": "Askja / Holuhraun (Islande)", "lat": 65.03, "lon": -16.75, "rayon": 5000},
}
POIDS_DEFAUT = {"pente": 20, "tri": 20, "albedo": 10, "sterilite": 15, "thermique": 15, "composition": 20}

# ----------------------------------------------------------------------------
# 3. ADAPTATEURS BACKEND (scripts de l'équipe) — seule section à modifier si les API changent
# ----------------------------------------------------------------------------
for _d in (Path(__file__).resolve().parent, Path(__file__).resolve().parent / "backend"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))


def charger_module(nom: str):
    """Import tolérant : renvoie (module | None, message d'erreur | None)."""
    try:
        return importlib.import_module(nom), None
    except Exception as exc:  # noqa: BLE001 — import cassé = on bascule en démo
        return None, f"{type(exc).__name__}: {exc}"


gee_metrics, ERR_GEE = charger_module("gee_metrics")
asi3_engine, ERR_ASI3 = charger_module("asi3_engine")

# Noms de champs acceptés dans la sortie de gee_metrics.analyze (insensible à la casse)
ALIAS_METRIQUES = {
    "pente": ("pente", "slope", "slope_mean", "slope_deg", "mean_slope"),
    "tri": ("tri", "ruggedness", "roughness", "tri_mean"),
    "albedo": ("albedo", "albédo", "albedo_mean"),
    "sterilite": ("sterilite", "stérilité", "sterility"),
    "thermique": ("thermique", "thermal_range", "lst_range", "lst_amplitude", "thermal_variability"),
    "composition": ("composition", "clay_index", "mineral_index", "composition_index", "spectral_index"),
}


def _aplatir(obj, prefixe="") -> dict:
    """Aplatit un dict imbriqué en {clé_minuscule: valeur}."""
    plat = {}
    for k, v in obj.items():
        if isinstance(v, dict):
            plat.update(_aplatir(v, prefixe))
        else:
            plat[str(k).lower()] = v
    return plat


def normaliser_resultat_gee(brut) -> tuple:
    """Convertit la sortie de gee_metrics.analyze en {6 métriques} ; renvoie (métriques, manquantes)."""
    if isinstance(brut, pd.DataFrame):
        brut = brut.iloc[0].to_dict()
    elif isinstance(brut, pd.Series):
        brut = brut.to_dict()
    elif not isinstance(brut, dict):
        brut = dict(vars(brut))
    plat = _aplatir(brut)
    metriques, manquantes = {}, []
    for cle, alias in ALIAS_METRIQUES.items():
        valeur = next((plat[a] for a in alias if a in plat and plat[a] is not None), None)
        if valeur is None and cle == "sterilite" and plat.get("ndvi") is not None:
            valeur = 1 - float(np.clip(plat["ndvi"], 0, 1))      # stérilité dérivée du NDVI
        try:
            metriques[cle] = float(valeur)
        except (TypeError, ValueError):
            metriques[cle] = None
            manquantes.append(cle)
    return metriques, manquantes


def distance_km(lat1, lon1, lat2, lon2):
    """Distance orthodromique (haversine) en km — accepte des tableaux numpy pour lat2/lon2."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(a))


def estimer_demo(lat: float, lon: float) -> tuple:
    """Mode démonstration : interpolation pondérée (1/d²) des sites du catalogue."""
    d = distance_km(lat, lon, CATALOGUE["lat"].to_numpy(), CATALOGUE["lon"].to_numpy())
    w = 1.0 / (d + 50.0) ** 2
    w /= w.sum()
    metriques = {m: float(np.dot(w, CATALOGUE[m].to_numpy())) for m in METRIQUES}
    return metriques, CATALOGUE.loc[int(np.argmin(d)), "nom"]


def executer_analyse(p: dict) -> dict:
    """
    Étape ② : lance l'analyse. Priorité : Google Earth Engine (gee_metrics) → repli démonstration.
    Retourne un dict stocké dans st.session_state["resultat"].
    """
    demo, proche = estimer_demo(p["lat"], p["lon"])
    res = {"params": p, "metriques": demo, "source": "Démonstration (interpolation du catalogue)",
           "avertissements": [], "horodatage": datetime.now().isoformat(timespec="seconds")}
    if p["force_demo"]:
        return res
    if gee_metrics is None:
        res["avertissements"].append(f"Module gee_metrics indisponible ({ERR_GEE}). Mode démonstration actif.")
        return res
    if not p["gee_project"]:
        res["avertissements"].append("ID de projet Google Cloud manquant. Mode démonstration actif.")
        return res
    try:
        gee_metrics.initialize(p["gee_project"])
        brut = gee_metrics.analyze(p["lat"], p["lon"], int(p["rayon"]), p["d_debut"].isoformat(), p["d_fin"].isoformat())
        metriques, manquantes = normaliser_resultat_gee(brut)
        for cle in manquantes:                       # complète les champs absents avec la démo
            metriques[cle] = demo[cle]
        res.update(metriques=metriques, source="Google Earth Engine", brut=brut if isinstance(brut, dict) else None)
        if manquantes:
            res["avertissements"].append("Métriques absentes de gee_metrics (complétées en démo) : "
                                         + ", ".join(manquantes))
    except Exception as exc:  # noqa: BLE001
        res["avertissements"].append(f"Erreur Earth Engine : {exc}. Mode démonstration actif.")
    return res


# ----------------------------------------------------------------------------
# 4. MOTEUR DE CALCUL (ASI)
# ----------------------------------------------------------------------------
def calculer_etendues(*jeux: dict) -> dict:
    """Min / étendue de chaque métrique sur toutes les valeurs connues (normalisation Min-Max)."""
    valeurs = {m: [] for m in METRIQUES}
    for jeu in jeux:
        for ligne in jeu:
            for m in METRIQUES:
                valeurs[m].append(float(ligne[m]))
    return {"min": {m: min(v) for m, v in valeurs.items()},
            "range": {m: max(max(v) - min(v), 1e-9) for m, v in valeurs.items()}}


def asi_integre(zone: dict, cible: dict, poids: dict, etendues: dict) -> float:
    """ASI = (1 − Σ wᵢ·|x_Terre,i − x_Cible,i| / Étendueᵢ) × 100, poids normalisés, borné à [0, 100]."""
    s = sum(poids.values()) or 1.0
    penalite = sum((w / s) * abs(zone[m] - cible[m]) / etendues["range"][m] for m, w in poids.items())
    return float(np.clip((1 - penalite) * 100, 0, 100))


def calculer_score(zone: dict, cible: dict, poids: dict, etendues: dict) -> tuple:
    """Utilise asi3_engine.compute_asi3 s'il est disponible, sinon le moteur intégré. → (score, nom du moteur)."""
    if asi3_engine is not None and hasattr(asi3_engine, "compute_asi3"):
        try:
            sortie = asi3_engine.compute_asi3({m: zone[m] for m in METRIQUES},
                                              {m: cible[m] for m in METRIQUES}, dict(poids))
            if isinstance(sortie, dict):
                sortie = sortie.get("asi", sortie.get("score"))
            return float(np.clip(float(sortie), 0, 100)), "asi3_engine.compute_asi3"
        except Exception as exc:  # noqa: BLE001
            return asi_integre(zone, cible, poids, etendues), f"moteur intégré (repli : {type(exc).__name__})"
    return asi_integre(zone, cible, poids, etendues), "moteur intégré"


def verdict(score: float) -> str:
    return "Excellent" if score >= 80 else "Bon" if score >= 60 else "Modéré" if score >= 40 else "Faible"


def couleur(score: float) -> str:
    return "#2ecc71" if score >= 80 else "#f1c40f" if score >= 60 else "#e67e22" if score >= 40 else "#e74c3c"


def normaliser(valeur: float, m: str, etendues: dict) -> float:
    return float(np.clip((valeur - etendues["min"][m]) / etendues["range"][m], 0, 1))


def simuler_pentes(moyenne: float, n: int = 5000, graine: int = 42) -> np.ndarray:
    """Distribution synthétique (Gamma) de pentes calée sur la moyenne, bornée à 60°."""
    return np.clip(np.random.default_rng(graine).gamma(2.0, max(moyenne, 0.1) / 2.0, n), 0, 60)


def inserer_colonne(df: pd.DataFrame, position: int, nom: str, valeur) -> pd.DataFrame:
    """Insertion sécurisée : met à jour la colonne si elle existe (jamais de ValueError)."""
    if nom in df.columns:
        df[nom] = valeur
    else:
        df.insert(min(position, len(df.columns)), nom, valeur)
    return df


def generer_rapport(res, nom_cible, cible, score, moteur, rang, nb, details) -> str:
    """Rapport de mission au format Markdown."""
    p = res["params"]
    gps = f"{abs(p['lat']):.4f}° {'N' if p['lat'] >= 0 else 'S'}, {abs(p['lon']):.4f}° {'E' if p['lon'] >= 0 else 'O'}"
    L = ["# 🛰️ Rapport d'évaluation d'analogue planétaire", "_Planetary Analog Finder — NASA Space Apps Challenge_", "",
         f"**Édité le :** {datetime.now():%Y-%m-%d %H:%M}", "", "## 1. Identification", "",
         f"- **Zone analysée :** {p['zone_nom']}", f"- **Coordonnées GPS :** {gps}", f"- **Rayon :** {p['rayon']} m",
         f"- **Période :** {p['d_debut']} → {p['d_fin']}", f"- **Cible martienne :** {nom_cible}",
         f"- **Source des métriques :** {res['source']}", "",
         "## 2. Score de similarité", "",
         f"**ASI = {score:.1f} %** — verdict **{verdict(score)}** · rang {rang}/{nb} face au catalogue · moteur : {moteur}", "",
         "## 3. Écarts par rapport à la cible", "",
         "| Métrique | Zone | Cible | Écart absolu | Écart normalisé | Poids |", "|---|---|---|---|---|---|"]
    L += [f"| {d['Métrique']} | {d['Zone']:.3f} | {d['Cible']:.3f} | {d['Écart absolu']:.3f} | "
          f"{d['Écart normalisé']:.3f} | {d['Poids']:.0%} |" for d in details]
    if res["avertissements"]:
        L += ["", "## 4. Avertissements", ""] + [f"- {a}" for a in res["avertissements"]]
    L += ["", "---", "_Les valeurs du catalogue et des cibles sont des ordres de grandeur illustratifs ; "
          "à valider sur MOLA/CRISM (cibles) et Copernicus DEM / Sentinel-2 / ERA5-Land (Terre)._"]
    return "\n".join(L)


# ----------------------------------------------------------------------------
# 5. ÉTAT DE SESSION, PRÉRÉGLAGES, CLIC SUR CARTE
# ----------------------------------------------------------------------------
def _projet_par_defaut() -> str:
    try:
        return str(st.secrets.get("gee_project", "")) or os.environ.get("GEE_PROJECT", "")
    except Exception:  # noqa: BLE001 — pas de secrets.toml
        return os.environ.get("GEE_PROJECT", "")


DEFAUTS = {"cible_nom": list(CIBLES)[0], "zone_nom": "Désert d'Atacama (Chili)", "lat": -24.50, "lon": -69.25,
           "rayon": 5000, "d_debut": date(2024, 1, 1), "d_fin": date(2025, 1, 1), "gee_project": _projet_par_defaut(),
           "force_demo": False, "resultat": None, **{f"w_{m}": v for m, v in POIDS_DEFAUT.items()}}
for _k, _v in DEFAUTS.items():
    st.session_state.setdefault(_k, _v)


def appliquer_preset(nom: str):
    """Callback des boutons de préréglage (exécuté avant le rerun → modification des widgets autorisée)."""
    p = PRESETS[nom]
    if "cible" in p:
        st.session_state["cible_nom"] = p["cible"]
        for m, v in p["poids"].items():
            st.session_state[f"w_{m}"] = v
    for cle in ("zone_nom", "lat", "lon", "rayon"):
        if cle in p:
            st.session_state[cle] = p[cle]
    st.toast(f"Préréglage « {nom} » chargé", icon="⚡")


# Clic sur la carte (étape ①) : appliqué ici, AVANT l'instanciation des widgets de la sidebar
if "clic_carte" in st.session_state:
    _lat, _lon = st.session_state.pop("clic_carte")
    st.session_state["lat"], st.session_state["lon"] = _lat, _lon
    st.session_state["zone_nom"] = f"Zone ({_lat:.3f}, {_lon:.3f})"

# ----------------------------------------------------------------------------
# 6. BARRE LATÉRALE — TOUS LES PARAMÈTRES
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🛰️ Paramètres")

    st.markdown("**⚡ Préréglages rapides**")
    for col, nom in zip(st.columns(3), PRESETS):
        col.button(nom, on_click=appliquer_preset, args=(nom,), key=f"preset_{nom}", width="stretch")

    st.divider()
    st.markdown("**🎯 Cible martienne**")
    nom_cible = st.selectbox("Cible", list(CIBLES), key="cible_nom", label_visibility="collapsed")
    cible = CIBLES[nom_cible]
    st.caption(cible["desc"])

    st.markdown("**📍 Zone terrestre à analyser**")
    st.text_input("Nom de la zone", key="zone_nom")
    c_lat, c_lon = st.columns(2)
    c_lat.number_input("Latitude", -90.0, 90.0, key="lat", format="%.5f")
    c_lon.number_input("Longitude", -180.0, 180.0, key="lon", format="%.5f")
    st.number_input("Rayon d'analyse (m)", 500, 20000, step=500, key="rayon")

    st.markdown("**🗓️ Période d'observation**")
    d1, d2 = st.columns(2)
    d1.date_input("Début", key="d_debut")
    d2.date_input("Fin (exclue)", key="d_fin")
    periode_ok = st.session_state["d_fin"] > st.session_state["d_debut"]
    if not periode_ok:
        st.error("La date de fin doit être postérieure au début.")

    st.markdown("**☁️ Backend Earth Engine**")
    st.text_input("ID du projet Google Cloud", key="gee_project", placeholder="mon-projet-gee")
    st.checkbox("Forcer le mode démonstration", key="force_demo")

    st.divider()
    st.markdown("**⚖️ Pondération des 6 métriques**")
    poids_brut = {m: st.slider(METRIQUES[m][2], 0, 100, key=f"w_{m}") for m in METRIQUES}
    total = sum(poids_brut.values())
    if total == 0:
        st.warning("Poids tous nuls : pondération uniforme appliquée.")
        poids_brut, total = {m: 1 for m in METRIQUES}, len(METRIQUES)
    poids = {m: v / total for m, v in poids_brut.items()}          # somme = 1 (100 %)
    st.caption(f"Somme saisie : **{sum(st.session_state[f'w_{m}'] for m in METRIQUES)}** → re-normalisée à **100 %**")
    st.progress(min(sum(poids.values()), 1.0))

    with st.expander("🔌 Statut des scripts backend"):
        st.markdown(f"**gee_metrics** : {'✅ chargé' if gee_metrics else '⚪ absent → démo'}")
        if ERR_GEE and gee_metrics is None:
            st.caption(ERR_GEE)
        st.markdown(f"**asi3_engine** : {'✅ chargé' if asi3_engine else '⚪ absent → moteur intégré'}")
        if ERR_ASI3 and asi3_engine is None:
            st.caption(ERR_ASI3)

# ----------------------------------------------------------------------------
# 7. CALCULS COMMUNS (catalogue, score de la zone)
# ----------------------------------------------------------------------------
lat, lon, rayon = st.session_state["lat"], st.session_state["lon"], st.session_state["rayon"]
resultat = st.session_state.get("resultat")
params_courants = {"zone_nom": st.session_state["zone_nom"], "lat": lat, "lon": lon, "rayon": rayon,
                   "d_debut": st.session_state["d_debut"], "d_fin": st.session_state["d_fin"],
                   "gee_project": st.session_state["gee_project"].strip(), "force_demo": st.session_state["force_demo"]}

lignes_cat = CATALOGUE.to_dict("records")
etendues = calculer_etendues(lignes_cat, CIBLES.values(), [resultat["metriques"]] if resultat else [])
catalogue = CATALOGUE.copy()
catalogue["ASI"] = [calculer_score(r, cible, poids, etendues)[0] for r in lignes_cat]
catalogue["Verdict"] = catalogue["ASI"].apply(verdict)

SIG = abs(hash((nom_cible, tuple(round(v, 3) for v in poids.values()), round(lat, 4), round(lon, 4), rayon,
                resultat["horodatage"] if resultat else "")))

# ----------------------------------------------------------------------------
# 8. EN-TÊTE + BANDEAU DES 3 ÉTAPES
# ----------------------------------------------------------------------------
st.markdown('<div class="hero"><h1>🛰️ Planetary Analog Finder <span class="tag">V4</span></h1>'
            '<p>Trouvez et caractérisez les analogues terrestres des sites martiens — '
            'NASA Space Apps Challenge</p></div>', unsafe_allow_html=True)

score_zone = moteur = None
if resultat:
    score_zone, moteur = calculer_score(resultat["metriques"], cible, poids, etendues)


def etape(num, titre, sous, fait):
    return (f'<div class="step {"done" if fait else ""}"><div class="n">Étape {num}</div>'
            f'<div class="t">{"✅ " if fait else ""}{titre}</div><div class="s">{sous}</div></div>')


st.markdown('<div class="stepper">'
            + etape(1, "Sélection de la zone", f"{st.session_state['zone_nom']} · {lat:.3f}, {lon:.3f}", True)
            + etape(2, "Analyse & métriques", resultat["source"] if resultat else "En attente de lancement", bool(resultat))
            + etape(3, "Score & rapport", f"ASI {score_zone:.1f} % · {verdict(score_zone)}" if resultat else "—", bool(resultat))
            + "</div>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["① Sélection de la zone", "② Analyse & métriques", "③ Score de similarité & rapport"])


def kpi(col, label, valeur, sous=""):
    col.markdown(f'<div class="kpi"><div class="label">{label}</div><div class="value">{valeur}</div>'
                 f'<div class="sub">{sous}</div></div>', unsafe_allow_html=True)


# ============================ ÉTAPE 1 — SÉLECTION ============================
with tab1:
    col_map, col_side = st.columns([3, 1.3])
    with col_map:
        vue = st.radio("Vue", ["🎯 Zone", "🌍 Monde"], horizontal=True, key="vue_carte", label_visibility="collapsed")
        carte = folium.Map(location=[lat, lon], zoom_start=10, tiles="OpenStreetMap", control_scale=True)
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri World Imagery", name="Satellite (Esri)", overlay=False).add_to(carte)

        for _, r in catalogue.iterrows():              # sites de référence colorés par ASI
            popup = (f"<div style='font-family:Arial;font-size:13px;color:#111;min-width:200px'>"
                     f"<b>{r['nom']}</b><br>{r['type']}<br>"
                     f"<b>ASI :</b> <span style='color:{couleur(r['ASI'])};font-weight:700'>{r['ASI']:.1f} %</span> "
                     f"({r['Verdict']})<br>Pente {r['pente']:.0f}° · TRI {r['tri']:.0f} m</div>")
            folium.CircleMarker([r["lat"], r["lon"]], radius=6 + r["ASI"] / 14, color=couleur(r["ASI"]),
                                fill=True, fill_opacity=0.7, popup=folium.Popup(popup, max_width=300),
                                tooltip=f"{r['nom']} — ASI {r['ASI']:.0f} %").add_to(carte)

        folium.Circle([lat, lon], radius=rayon, color=NASA_RED, weight=2, fill=True, fill_opacity=0.15).add_to(carte)
        folium.Marker([lat, lon], tooltip=st.session_state["zone_nom"],
                      icon=folium.Icon(color="red", icon="crosshairs", prefix="fa")).add_to(carte)
        folium.LayerControl(collapsed=True).add_to(carte)

        if vue == "🎯 Zone":                            # zoom sur le cercle d'analyse
            dlat = max(rayon / 111_320.0, 0.01)
            dlon = dlat / max(np.cos(np.radians(lat)), 0.2)
            carte.fit_bounds([[lat - dlat, lon - dlon], [lat + dlat, lon + dlon]], padding=(40, 40))
        else:                                           # zoom englobant tous les points + la zone
            carte.fit_bounds([[min(catalogue["lat"].min(), lat), min(catalogue["lon"].min(), lon)],
                              [max(catalogue["lat"].max(), lat), max(catalogue["lon"].max(), lon)]], padding=(30, 30))

        sortie = st_folium(carte, height=560, use_container_width=True, returned_objects=["last_clicked"],
                           key=f"carte_{vue}_{lat:.5f}_{lon:.5f}_{rayon}")
        clic = (sortie or {}).get("last_clicked")
        if clic:
            nl, nn = round(clic["lat"], 5), round(((clic["lng"] + 180) % 360) - 180, 5)
            if abs(nl - lat) > 1e-6 or abs(nn - lon) > 1e-6:
                st.session_state["clic_carte"] = (nl, nn)
                st.rerun()
        st.caption("🖱️ Cliquez sur la carte pour déplacer la zone d'analyse ; les coordonnées de la barre latérale "
                   "se mettent à jour. Les points colorés sont les sites de référence (couleur = ASI).")

    with col_side:
        kpi(st, "Zone sélectionnée", st.session_state["zone_nom"], f"{lat:.4f}°, {lon:.4f}° · rayon {rayon} m")
        kpi(st, "Cible martienne", nom_cible.split("— ")[-1], f"Réf. {cible['lat']:.2f}°, {cible['lon']:.2f}°")
        st.markdown("**📌 Sites de référence les plus proches**")
        dist = distance_km(lat, lon, catalogue["lat"].to_numpy(), catalogue["lon"].to_numpy())
        proches = catalogue.assign(distance_km=dist).nsmallest(3, "distance_km")
        for _, r in proches.iterrows():
            st.markdown(f"<span class='pill'>{r['distance_km']:,.0f} km</span> **{r['nom']}** "
                        f"— <span style='color:{couleur(r['ASI'])}'>{r['ASI']:.0f} %</span>", unsafe_allow_html=True)
        st.info("✅ Zone prête. Passez à l'onglet **② Analyse & métriques**.")

# ============================ ÉTAPE 2 — ANALYSE =============================
with tab2:
    st.markdown(f"**Zone :** {params_courants['zone_nom']} · **Rayon :** {rayon} m · "
                f"**Période :** {params_courants['d_debut']} → {params_courants['d_fin']} · **Cible :** {nom_cible}")
    if st.button("🚀 Lancer l'analyse", type="primary", width="stretch", disabled=not periode_ok):
        with st.spinner("Calcul des 6 métriques (relief, spectre, thermique)…"):
            st.session_state["resultat"] = executer_analyse(params_courants)
        st.rerun()

    if not resultat:
        st.info("Aucune analyse pour le moment. Cliquez sur **Lancer l'analyse** (mode démonstration sans projet GEE).")
    else:
        if resultat["params"] != params_courants:
            st.warning("⚠️ Les paramètres ont changé depuis la dernière analyse : relancez-la pour mettre à jour les métriques.")
        for av in resultat["avertissements"]:
            st.warning(av)
        (st.success if resultat["source"] == "Google Earth Engine" else st.info)(
            f"Source des métriques : **{resultat['source']}** — analyse du {resultat['horodatage']}")

        mz = resultat["metriques"]
        for i, m in enumerate(METRIQUES):
            if i % 3 == 0:
                cols = st.columns(3)
            lib, unite, _ = METRIQUES[m]
            kpi(cols[i % 3], lib, f"{mz[m]:.2f} {unite}".strip(), f"Cible : {cible[m]:.2f} {unite}".strip())

        g1, g2 = st.columns(2)
        with g1:
            st.markdown("#### 📈 Distribution des pentes")
            h = go.Figure()
            h.add_trace(go.Histogram(x=simuler_pentes(mz["pente"], graine=1), name="Zone", opacity=0.65,
                                     marker_color=NASA_BLUE, nbinsx=50, histnorm="probability density"))
            h.add_trace(go.Histogram(x=simuler_pentes(cible["pente"], graine=2), name="Cible", opacity=0.65,
                                     marker_color=NASA_RED, nbinsx=50, histnorm="probability density"))
            h.update_layout(barmode="overlay", template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)", height=340, xaxis_title="Pente (°)", yaxis_title="Densité",
                            legend=dict(orientation="h", y=-0.25), margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(h, width="stretch", key=f"hist_{SIG}")
            st.caption("Distribution synthétique (loi Gamma) calée sur la pente moyenne ; à remplacer par l'histogramme réel du MNT.")
        with g2:
            st.markdown("#### 🧮 Contribution de chaque métrique à l'écart")
            contrib = {METRIQUES[m][2]: poids[m] * abs(mz[m] - cible[m]) / etendues["range"][m] * 100 for m in METRIQUES}
            b = go.Figure(go.Bar(x=list(contrib.values()), y=list(contrib), orientation="h", marker_color=NASA_RED,
                                 text=[f"−{v:.1f} pts" for v in contrib.values()]))
            b.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            height=340, xaxis_title="Points d'ASI perdus", margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(b, width="stretch", key=f"contrib_{SIG}")

        st.markdown("#### 🧾 Métriques brutes")
        tableau = pd.DataFrame([{"Métrique": METRIQUES[m][0], "Unité": METRIQUES[m][1], "Zone": mz[m],
                                 "Cible": cible[m], "Écart": mz[m] - cible[m]} for m in METRIQUES])
        st.dataframe(tableau.style.format({"Zone": "{:.3f}", "Cible": "{:.3f}", "Écart": "{:+.3f}"}),
                     width="stretch", hide_index=True)
        st.success("✅ Analyse terminée. Ouvrez l'onglet **③ Score de similarité & rapport**.")

# ============================ ÉTAPE 3 — SCORE & RAPPORT =====================
with tab3:
    if not resultat:
        st.info("Lancez d'abord l'analyse (onglet ②) pour obtenir le score de similarité.")
    else:
        mz = resultat["metriques"]
        rang = int((catalogue["ASI"] > score_zone).sum()) + 1
        meilleur = catalogue.sort_values("ASI", ascending=False).iloc[0]

        cg, ck = st.columns([1.2, 1])
        with cg:
            jauge = go.Figure(go.Indicator(
                mode="gauge+number", value=score_zone, number={"suffix": " %", "font": {"size": 54}},
                title={"text": f"ASI — {st.session_state['zone_nom']}"},
                gauge={"axis": {"range": [0, 100]}, "bar": {"color": couleur(score_zone)},
                       "steps": [{"range": [0, 40], "color": "rgba(231,76,60,.25)"},
                                 {"range": [40, 60], "color": "rgba(230,126,34,.25)"},
                                 {"range": [60, 80], "color": "rgba(241,196,15,.25)"},
                                 {"range": [80, 100], "color": "rgba(46,204,113,.25)"}]}))
            jauge.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=300,
                                margin=dict(l=20, r=20, t=60, b=10))
            st.plotly_chart(jauge, width="stretch", key=f"jauge_{SIG}")
        with ck:
            kpi(st, "Verdict", verdict(score_zone), f"Moteur : {moteur}")
            kpi(st, "Rang face au catalogue", f"{rang} / {len(catalogue) + 1}", f"Meilleur site : {meilleur['nom']} ({meilleur['ASI']:.0f} %)")

        cr, cc = st.columns(2)
        with cr:
            st.markdown("#### 🕸️ Radar des 6 métriques (normalisées Min-Max)")
            theta = [METRIQUES[m][2] for m in METRIQUES]
            vz = [normaliser(mz[m], m, etendues) for m in METRIQUES]
            vc = [normaliser(cible[m], m, etendues) for m in METRIQUES]
            radar = go.Figure()
            radar.add_trace(go.Scatterpolar(r=vz + vz[:1], theta=theta + theta[:1], fill="toself",
                                            name=st.session_state["zone_nom"], line_color=NASA_BLUE,
                                            fillcolor="rgba(74,144,226,0.30)"))
            radar.add_trace(go.Scatterpolar(r=vc + vc[:1], theta=theta + theta[:1], fill="toself",
                                            name=nom_cible, line_color=NASA_RED, fillcolor="rgba(252,61,33,0.25)"))
            radar.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=430,
                                polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(range=[0, 1], showticklabels=False)),
                                legend=dict(orientation="h", y=-0.1), margin=dict(l=50, r=50, t=20, b=40))
            st.plotly_chart(radar, width="stretch", key=f"radar_{SIG}")
        with cc:
            st.markdown("#### 🏆 Classement face aux sites de référence")
            classement = pd.concat([catalogue[["nom", "ASI"]],
                                    pd.DataFrame([{"nom": f"▶ {st.session_state['zone_nom']}", "ASI": score_zone}])]
                                   ).sort_values("ASI")
            coul = [NASA_BLUE if n.startswith("▶") else couleur(a) for n, a in zip(classement["nom"], classement["ASI"])]
            bar = go.Figure(go.Bar(x=classement["ASI"], y=classement["nom"], orientation="h", marker_color=coul,
                                   text=classement["ASI"].round(1)))
            bar.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              height=430, xaxis=dict(range=[0, 105], title="ASI (%)"), margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(bar, width="stretch", key=f"rang_{SIG}")

        st.markdown("#### 🧾 Écarts détaillés")
        details = [{"Métrique": METRIQUES[m][0], "Zone": mz[m], "Cible": cible[m],
                    "Écart absolu": abs(mz[m] - cible[m]), "Écart normalisé": abs(mz[m] - cible[m]) / etendues["range"][m],
                    "Poids": poids[m]} for m in METRIQUES]
        df_det = pd.DataFrame(details)
        st.dataframe(df_det.style.format({"Zone": "{:.3f}", "Cible": "{:.3f}", "Écart absolu": "{:.3f}",
                                          "Écart normalisé": "{:.3f}", "Poids": "{:.0%}"}),
                     width="stretch", hide_index=True)

        # --- Exports -------------------------------------------------------------------
        st.markdown("#### 💾 Rapport exportable")
        rapport = generer_rapport(resultat, nom_cible, cible, score_zone, moteur, rang, len(catalogue) + 1, details)
        fiche = {"date": datetime.now().isoformat(timespec="seconds"), "zone": resultat["params"]["zone_nom"],
                 "lat": resultat["params"]["lat"], "lon": resultat["params"]["lon"], "cible": nom_cible,
                 "source": resultat["source"], "moteur": moteur, "ASI_pourcent": round(score_zone, 2),
                 "verdict": verdict(score_zone), "rang": rang,
                 "poids_normalises": {m: round(v, 4) for m, v in poids.items()},
                 "metriques_zone": {m: round(v, 4) for m, v in mz.items()}}
        df_export = df_det.copy()
        inserer_colonne(df_export, 0, "Zone analysée", resultat["params"]["zone_nom"])
        inserer_colonne(df_export, 1, "Cible", nom_cible)
        inserer_colonne(df_export, len(df_export.columns), "ASI (%)", round(score_zone, 2))
        base = "".join(c if c.isalnum() else "_" for c in resultat["params"]["zone_nom"])[:40]
        e1, e2, e3 = st.columns(3)
        e1.download_button("📄 Rapport Markdown", rapport.encode("utf-8"), f"rapport_{base}.md", "text/markdown", width="stretch")
        e2.download_button("⬇️ Fiche JSON", json.dumps(fiche, ensure_ascii=False, indent=2).encode("utf-8"),
                           f"fiche_{base}.json", "application/json", width="stretch")
        e3.download_button("⬇️ Tableau CSV", df_export.to_csv(index=False).encode("utf-8"),
                           f"ecarts_{base}.csv", "text/csv", width="stretch")
        with st.expander("👁️ Aperçu du rapport"):
            st.markdown(rapport)

        with st.expander("📖 Méthode : formule de l'ASI"):
            st.latex(r"ASI = \left(1 - \sum_i w_i \cdot \frac{\left|x_{\text{Terre},i} - x_{\text{Mars},i}\right|}{\text{Étendue}_i}\right) \times 100")
            st.caption("wᵢ : poids normalisés (Σ = 1) · Étendueᵢ = max − min de la métrique sur catalogue, cibles et zone analysée.")

st.markdown("---")
st.caption("Planetary Analog Finder · Données ouvertes NASA / ESA / USGS · NASA Space Apps Challenge")