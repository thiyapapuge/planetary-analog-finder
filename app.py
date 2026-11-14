# -*- coding: utf-8 -*-
"""
Planetary Analog Finder -- NASA Space Apps Challenge 2026
==========================================================
Where on Earth looks like Jezero crater, Mars?
Team: Proteus 2

Page 1 · THE MODEL   : big world map + before/after slider through the model, plain-language explanation,
                       site details only when a site is clicked.
Page 2 · TOP 100     : the 100 most relevant sites, colour-coded by field status, with legend and site details.

Data (searched next to app.py, in data/, in the current folder or in $PAF_DATA_DIR):
  - acces_top100V2_avecapprofondissement.csv  or  top100_final_appli.csv  or  classement_final_top100.csv
  - classement_final_monde.csv  (world scan, 4 553 sites)
Run:  python -m streamlit run app.py
Dependencies: streamlit, folium, streamlit-folium, plotly, pandas, numpy
"""

import io
import os
import re
import unicodedata
from html import escape
from pathlib import Path

import folium
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

# ----------------------------------------------------------------------------
# 1. CONFIGURATION & STYLE
# ----------------------------------------------------------------------------
# Proteus logos, embedded so app.py works on its own (white on transparent PNG, base64)
LOGO_ICON_B64 = "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"
LOGO_FULL_B64 = "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"


def _logo_image():
    import base64 as _b64
    from PIL import Image
    return Image.open(io.BytesIO(_b64.b64decode(LOGO_ICON_B64)))


st.set_page_config(page_title="Planetary Analog Finder | Proteus 2", layout="wide", page_icon=_logo_image())

st.markdown("""
<style>
    .stApp { background-color: #05070b; color: #d0d6de; }
    section[data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #1f2937 !important; }
    .block-container { padding-top: 1.6rem; }
    header[data-testid="stHeader"] { background: #05070b; }
    div[data-baseweb="slider"] div[role="slider"] { background-color: #f2b134 !important; box-shadow: none !important; }
    div[data-testid="stSliderThumbValue"], div[data-testid="stThumbValue"] { color: #f2b134 !important; }
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] h3 { color: #c9d1d9 !important; }
    h1, h2, h3, h4 { color: #f0f3f6; font-weight: 600; }
    .lead { font-size: 1.05rem; color: #9aa4b1; margin-top: -0.4rem; }
    .card { border: 1px solid #1f2937; background: #0b0f15; padding: 14px 16px; margin-bottom: 10px; }
    .card .t { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1px; color: #7d8590; }
    .card .v { font-size: 1.35rem; font-weight: 600; color: #f0f3f6; margin-top: 2px; }
    .card .s { font-size: 0.8rem; color: #9aa4b1; margin-top: 4px; }
    .step { border: 1px solid #1f2937; background: #0b0f15; padding: 14px 16px; height: 100%; }
    .step .n { font-size: 0.72rem; color: #7d8590; letter-spacing: 1px; text-transform: uppercase; }
    .step .h { font-size: 1.05rem; font-weight: 600; color: #f0f3f6; margin: 4px 0 6px; }
    .step .p { font-size: 0.88rem; color: #aab3bf; line-height: 1.45; }
    .step .k { font-size: 0.8rem; color: #7d8590; margin-top: 8px; }
    .legend { display: flex; flex-wrap: wrap; gap: 18px; font-size: 0.9rem; color: #c9d1d9; margin: 4px 0 10px; }
    .legend .dot { display: inline-block; width: 12px; height: 12px; border-radius: 6px; margin-right: 7px; vertical-align: -1px; }
    .legend .ring { display: inline-block; width: 12px; height: 12px; border-radius: 7px; border: 2px solid #ffffff; margin-right: 7px; vertical-align: -2px; }
    .stage { font-size: 0.95rem; color: #c9d1d9; border-left: 3px solid #f2b134; padding: 6px 12px; background: #0b0f15; }
    table.cmp { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
    table.cmp td, table.cmp th { border-bottom: 1px solid #1f2937; padding: 5px 4px; text-align: left; }
    table.cmp th { color: #7d8590; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# 2. DATA
# ----------------------------------------------------------------------------
FILES_TOP100 = ("acces_top100V2_avecapprofondissement.csv", "top100_final_appli.csv", "classement_final_top100.csv")
FILE_WORLD = "classement_final_monde.csv"
REPORT_FILE = "Rapport_analogues_Jezero.pdf"

# Team priority targets (rank in the top 100): clay signal sites
PRIORITY_TARGETS = {4: "Puna", 40: "W. Tibet", 89: "Puna"}

# Accepted column names -> internal name
ALIASES = {
    "rang": ("rang", "rank", "classement", "position"),
    "rang_accessible": ("rang_accessible", "rank_accessible", "rang_acces"),
    "lat": ("lat", "latitude", "centre_lat", "lat_centre"),
    "lon": ("lon", "lng", "long", "longitude", "centre_lon", "lon_centre"),
    "score": ("score_moyen", "score_global", "score_final", "score_total", "score"),
    "priorite": ("priorite", "priority", "prioritaire"),
    "signal_argiles": ("signal_argiles", "signal_argileux", "signal_argile", "clay_signal"),
    "ratio_argiles": ("ratio_argiles", "ratio_argile", "clay_ratio"),
    "profil": ("profil", "profile"),
    "territoire": ("territoire", "territory", "pays", "country"),
    "zone_disputee": ("zone_disputee", "zone_contestee", "disputed"),
    "acces_heures": ("acces_heures", "access_hours", "heures_acces"),
    "acces_classe": ("acces_classe", "access_class", "classe_acces"),
    "aire_protegee": ("aire_protegee", "protected_area", "zone_protegee"),
    "nom_aire_protegee": ("nom_aire_protegee", "protected_area_name", "nom_aire"),
    "statut_carte": ("statut_carte", "statut", "map_status"),
    "recommande": ("recommande", "recommended"),
    "typologie": ("typologie", "typology"),
    "morphotype": ("morphotype", "morphologie"),
    "amplitude_k": ("amplitude_k", "amplitude"),
    "temp_moy_c": ("temp_moy_c", "temp_moy"),
    "ndvi_max": ("ndvi_max",),
    "aridite": ("aridite", "aridity"),
    "pente_moy_deg": ("pente_moy_deg", "pente_moy", "pente"),
    "relief_local_m": ("relief_local_m", "relief_local"),
    "env_moy": ("env_moy", "score_env"),
    "relief_moy": ("relief_moy", "score_relief"),
    "compo_moy": ("compo_moy", "score_compo"),
}
TEXT_COLS = ["priorite", "signal_argiles", "profil", "territoire", "acces_classe", "nom_aire_protegee",
             "statut_carte", "recommande", "typologie", "morphotype"]


def _key(name) -> str:
    t = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode().lower().strip()
    return re.sub(r"[^a-z0-9]+", "_", t).strip("_")


def find_file(name: str):
    base = Path(__file__).resolve().parent
    dirs = ([Path(os.environ["PAF_DATA_DIR"])] if os.environ.get("PAF_DATA_DIR") else []) + [
        base, base / "data", Path.cwd(), Path.cwd() / "data"]
    return next((d / name for d in dirs if (d / name).is_file()), None)


def find_first(names):
    return next((p for p in (find_file(n) for n in names) if p is not None), None)


def file_stamp(*names) -> float:
    return float(sum(p.stat().st_mtime for p in (find_file(n) for n in names) if p is not None))


def read_csv_robust(raw: bytes) -> pd.DataFrame:
    """Separator auto (, ; tab), UTF-8 or Latin-1, comma decimals."""
    text = None
    for enc in ("utf-8-sig", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    df = pd.read_csv(io.StringIO(text), sep=None, engine="python")
    for c in df.columns:
        if not pd.api.types.is_numeric_dtype(df[c]) and df[c].notna().any():
            conv = pd.to_numeric(df[c].astype(str).str.replace(",", ".", regex=False).str.strip(), errors="coerce")
            if conv.notna().sum() >= 0.9 * df[c].notna().sum():
                df[c] = conv
    return df


def harmonize(df: pd.DataFrame) -> pd.DataFrame:
    index = {_key(c): c for c in df.columns}
    rename = {}
    for target, alias in ALIASES.items():
        col = next((index[a] for a in (target,) + alias if a in index), None)
        if col is not None and col not in rename and target not in rename.values():
            rename[col] = target
    df = df.rename(columns=rename)
    for c in df.columns:
        if c in TEXT_COLS:
            df[c] = df[c].fillna("").astype(str)
    for c in ("zone_disputee", "aire_protegee"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    return df


def status_of(r) -> str:
    """'ok' (green) / 'protected' (orange) / 'disputed' (red)."""
    s = _key(r.get("statut_carte", ""))
    if s.startswith("rouge") or r.get("zone_disputee", 0) == 1:
        return "disputed"
    if s.startswith("orange") or r.get("aire_protegee", 0) == 1:
        return "protected"
    return "ok"


def access_key(text) -> str:
    t = _key(text)
    return "easy" if t.startswith("facile") else "expedition" if t.startswith("exp") else \
        "remote" if t.startswith("tres") or t.startswith("remote") else ""


@st.cache_data
def load_top100(stamp: float):
    path = find_first(FILES_TOP100)
    if path is None:
        return None, None
    df = harmonize(read_csv_robust(path.read_bytes()))
    df = df.dropna(subset=["rang", "lat", "lon"]).reset_index(drop=True)
    df["rang"] = df["rang"].astype(int)
    if df["score"].max() <= 1.0:
        df["score"] = df["score"] * 100.0
    df["status"] = df.apply(status_of, axis=1)
    df["priority"] = df["rang"].isin(list(PRIORITY_TARGETS))
    if "priorite" in df.columns:
        df["priority"] |= df["priorite"].str.lower().str.contains("prioritaire")
    if "acces_classe" in df.columns:
        df["access"] = df["acces_classe"].map(access_key)
    elif "acces_heures" in df.columns:
        df["access"] = np.select([df["acces_heures"] < 6, df["acces_heures"] < 24], ["easy", "expedition"], "remote")
    return df, path.name


@st.cache_data
def load_world(stamp: float):
    path = find_file(FILE_WORLD)
    if path is None:
        return None
    df = harmonize(read_csv_robust(path.read_bytes()))
    df = df.dropna(subset=["lat", "lon"])
    df = df[df["lat"].between(-90, 90) & df["lon"].between(-180, 180)].reset_index(drop=True)
    if "rang" in df.columns:
        df["rang"] = df["rang"].astype(int)
    if "score" in df.columns and df["score"].max() <= 1.0:
        df["score"] = df["score"] * 100.0
    return df


TOP, TOP_FILE = load_top100(file_stamp(*FILES_TOP100))
WORLD = load_world(file_stamp(FILE_WORLD))

if TOP is None:
    st.error(f"No top 100 file found. Put one of {', '.join(FILES_TOP100)} next to app.py or in data/.")
    st.stop()

# ----------------------------------------------------------------------------
# 3. SHARED: COLOURS, SITE DETAILS
# ----------------------------------------------------------------------------
STATUS = {  # code: (colour, label, explanation)
    "ok": ("#2e9e5b", "Accessible", "no dispute, no protected area"),
    "protected": ("#ff9900", "Protected area", "inside a national park or reserve: permit needed"),
    "disputed": ("#e03b2e", "Disputed territory", "claimed by two countries: not recommended"),
}
C_WORLD, C_TOP, C_PRIO = "#6f8fb8", "#f2b134", "#ffffff"
ACCESS_TXT = {"easy": "Easy (< 6 h)", "expedition": "Expedition (6–24 h)", "remote": "Very remote (> 24 h)", "": "—"}
ACCESS_COLOR = {"easy": "#4fc3f7", "expedition": "#2b7bb9", "remote": "#3a4a63", "": "#6e7681"}

# Model parameters: (column, label, unit, value giving score 1, format)
PARAMS = [
    ("amplitude_k", "Day–night temperature swing", "K", "≥ 35 K (Jezero up to ≈ 87 K)", "{:.0f} K"),
    ("temp_moy_c", "Mean surface temperature", "°C", "≤ −15 °C", "{:.1f} °C"),
    ("ndvi_max", "Vegetation (max NDVI)", "", "≤ 0.05 (none)", "{:.2f}"),
    ("aridite", "Aridity index", "", "≤ 0.03 (hyper-arid)", "{:.3f}"),
    ("pente_moy_deg", "Mean slope", "°", "flat floor (< 5°)", "{:.1f}°"),
    ("relief_local_m", "Local relief within 3 km", "m", "100–500 m (crater-like)", "{:.0f} m"),
]

# Reference values on Mars (Jezero), used to say where the analogy breaks down
JEZERO_SWING_K = 87          # Perseverance MEDA: diurnal ground-temperature amplitude up to ~87 K (Martínez et al. 2023)
NOT_ON_EARTH = [
    "Gravity: 1 g on Earth vs 0.38 g on Mars",
    "Atmosphere: about 1,000 hPa on Earth vs about 6.4 hPa, mostly CO₂, on Mars",
    "Radiation: Earth's magnetic field and thick air block what reaches the Martian surface",
]

# Well-known Mars analog sites: (name, lat, lon, radius in km that counts as "the same site/region")
KNOWN_ANALOGS = [
    ("Atacama (Yungay)", -24.08, -69.92, 100),
    ("MDRS, Utah", 38.406, -110.792, 100),
    ("Death Valley", 36.46, -116.87, 100),
    ("Qaidam basin", 37.2, 94.9, 450),
    ("Haughton crater", 75.38, -89.68, 100),
    ("Iceland", 64.9, -18.6, 300),
    ("Hawaii", 19.6, -155.5, 250),
    ("Rio Tinto", 37.69, -6.59, 100),
]
NEAR_KM = 250   # within radius + 250 km: "near a known analog"
NOVELTY = {  # code: (label, colour)
    "new": ("New site", "#4fc3f7"),
    "near": ("Near a known analog", "#c9b37e"),
    "known": ("Known analog region", "#8b949e"),
}


def add_novelty(df: pd.DataFrame) -> pd.DataFrame:
    """Distance to the nearest well-known analog -> 'known' / 'near' / 'new'."""
    if df is None or df.empty:
        return df
    lat1, lon1 = np.radians(df["lat"].to_numpy())[:, None], np.radians(df["lon"].to_numpy())[:, None]
    lat2 = np.radians([k[1] for k in KNOWN_ANALOGS])[None, :]
    lon2 = np.radians([k[2] for k in KNOWN_ANALOGS])[None, :]
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    dist = 6371.0 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))          # km, sites x known analogs
    radius = np.array([k[3] for k in KNOWN_ANALOGS])[None, :]
    j = np.argmin(dist - radius, axis=1)                                 # closest relative to each zone
    d = dist[np.arange(len(df)), j]
    r = radius[0, j]
    df = df.copy()
    df["novelty"] = np.where(d <= r, "known", np.where(d <= r + NEAR_KM, "near", "new"))
    df["nearest_known"] = [KNOWN_ANALOGS[k][0] for k in j]
    df["dist_known_km"] = d.round(0)
    return df


def novelty_text(r) -> str:
    lab = NOVELTY[r["novelty"]][0]
    if r["novelty"] == "known":
        return f"{lab}: inside the {r['nearest_known']} area"
    return f"{lab}: {r['dist_known_km']:,.0f} km from the nearest known analog, {r['nearest_known']}"


def trap(v, a, b, c, d):
    return float(np.clip(min((v - a) / (b - a), 1, (d - v) / (d - c)), 0, 1))


def analogy(r):
    """Strong points and limits of one site, with the model's own scoring rules."""
    strong, weak = [], []
    g = lambda c: r[c] if c in r.index and pd.notna(r[c]) else None
    sw, t, nd, ar, sl, rl = (g(c) for c in ("amplitude_k", "temp_moy_c", "ndvi_max", "aridite", "pente_moy_deg", "relief_local_m"))
    if sw is not None:
        weak.append(f"Day–night swing: <b>{sw:.0f} K</b> here vs <b>≈ {JEZERO_SWING_K} K</b> on Jezero. "
                    "Earth's thick atmosphere damps the swing, so no place on Earth gets close.")
    if t is not None:
        if t <= -15:
            strong.append(f"Cold: mean surface temperature {t:.1f} °C")
        else:
            weak.append(f"Mean surface temperature: <b>{t:.1f} °C</b>, much warmer than Mars "
                        "(Jezero ground swings by up to ≈ 87 K every day, Perseverance MEDA).")
    if nd is not None:
        (strong if nd <= 0.1 else weak).append(f"{'No' if nd <= 0.1 else 'Some'} vegetation (max NDVI {nd:.2f})")
    if ar is not None:
        (strong if ar <= 0.05 else weak).append(f"{'Hyper-arid' if ar <= 0.05 else 'Not hyper-arid'} (aridity index {ar:.3f})")
    if sl is not None:
        (strong if sl < 5 else weak).append(f"{'Flat' if sl < 5 else 'Steep'} floor: mean slope {sl:.1f}°")
    if rl is not None:
        ok = trap(rl, 20, 100, 500, 1500) >= 0.8
        (strong if ok else weak).append(f"Local relief {rl:.0f} m within 3 km "
                                        + ("(basin with a rim, like a crater floor)" if ok else "(not crater-like)"))
    cm = g("compo_moy")
    if cm is not None:
        (strong if cm >= 0.7 else weak).append("Dark mafic rock, like Jezero's olivine-rich floor" if cm >= 0.7
                                               else "Rock is less mafic than Jezero's floor")
    sig = str(r.get("signal_argiles", "") or "").lower()
    if sig:
        if sig.startswith(("moyen", "fort", "medium", "strong")):
            strong.append(f"Clay signal: {escape(clay_en(sig))}, a possible trace of past water, like the Jezero delta")
        else:
            weak.append(f"Clay signal: {escape(clay_en(sig))}, little sign of water-altered minerals")
    return strong, weak


# What a mission could test on the recommended site(s)
# ---- Mars: Jezero reference (every value is sourced) ---------------------------------------
SRC = {
    "nasa2018": ("NASA (2018), NASA Announces Landing Site for Mars 2020 Rover",
                 "https://www.nasa.gov/news-release/nasa-announces-landing-site-for-mars-2020-rover/"),
    "mangold2021": ("Mangold et al. (2021), Science 374, Perseverance rover reveals an ancient delta-lake system and flood deposits",
                    "https://doi.org/10.1126/science.abl4051"),
    "farley2022": ("Farley et al. (2022), Science, Aqueously altered igneous rocks sampled on the floor of Jezero crater",
                   "https://doi.org/10.1126/science.abo2196"),
    "martinez2023": ("Martínez et al. (2023), JGR Planets 128, Surface energy budget, albedo and thermal inertia at Jezero (MEDA)",
                     "https://doi.org/10.1029/2022JE007537"),
    "factsheet": ("NASA NSSDCA, Mars Fact Sheet", "https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html"),
    "pia23239": ("NASA/JPL-Caltech/MSSS/JHU-APL, PIA23239: Jezero Crater, Mars 2020's Landing Site",
                 "https://science.nasa.gov/photojournal/jezero-crater-mars-2020s-landing-site/"),
}
JEZERO_IMG = "https://assets.science.nasa.gov/content/dam/science/psd/photojournal/pia/pia23/pia23239/PIA23239.jpg"
JEZERO_FACTS = [  # (characteristic, value, source key)
    ("Location", "Western edge of Isidis Planitia, just north of the Martian equator", "nasa2018"),
    ("Size", "Impact crater about 45 km wide", "nasa2018"),
    ("History", "Ancient lake–delta system; landforms up to 3.6 billion years old", "nasa2018"),
    ("Delta", "River delta built into the lake; steady flow first, then intermittent floods as Mars dried out", "mangold2021"),
    ("Sediments", "Clays and carbonates, with high potential to preserve signs of past life", "nasa2018"),
    ("Crater floor", "Igneous rocks altered by water: olivine-rich Séítah (with Fe-Mg carbonates) under Máaz lava flows", "farley2022"),
    ("Salts", "Sulfates and perchlorates in rock voids, likely left by evaporating brines", "farley2022"),
    ("Temperature", "Daily ground-temperature swing of ≈ 56 to 87 K (Perseverance MEDA)", "martinez2023"),
    ("Surface", "Thermal inertia 180 (sand dunes) to 605 (bedrock) SI units", "martinez2023"),
    ("Gravity, air", "3.71 m/s² (0.38 g); surface pressure ≈ 6.4 hPa, mostly CO₂", "factsheet"),
]

# The process shared by Jezero and site #4: a lake that dried out
PROCESS = [
    ("1 · A lake fills a basin", "Rivers flowed into Jezero crater, built a delta and deposited clay-rich sediments.",
     "Water collects in a closed basin with no outlet to the sea."),
    ("2 · The lake dries out", "As Mars lost its water, flow became intermittent floods, then stopped.",
     "In the hyper-arid Puna, evaporation removes the water faster than it arrives."),
    ("3 · Salts are left behind", "Evaporating brines left sulfates and perchlorates in the rocks of the crater floor.",
     "Evaporation leaves a white salt crust: the salt flat visible from orbit."),
]
PROCESS_SHORT = {
    4: "Same process as Jezero: a lake that filled a closed basin, then dried out. On Mars, evaporating brines left "
       "salts in the crater floor; here, evaporation in the hyper-arid Puna left the white salt flat seen from orbit. "
       "Studying how clays and salts form and are preserved here helps read what Perseverance finds in Jezero.",
}

# Validation: test sites run through the model (results from the team's Earth Engine runs)
VALIDATION = [
    ("Samail ophiolite, Oman", "Right rock, wrong climate", "Composition B · environment D", "✓ as expected"),
    ("Qaidam basin, China", "Known Mars analog", "Environment A · composition B", "✓ found on its own"),
    ("Atacama, Yungay (Chile)", "Very dry, but coastal and mild", "Environment C · composition C", "✓ partial match"),
    ("Rub' al Khali sand sea", "Negative test: sand, not rock", "Composition score at minimum", "✓ rejected"),
    ("Amazon rainforest", "Negative test: wet and green", "Eliminated (vegetation, water)", "✓ rejected"),
    ("France (whole country)", "Negative test", "0 % of land kept", "✓ rejected"),
]


CLAY_EN = {"faible": "weak", "moyen": "moderate", "fort": "strong"}


def clay_en(v) -> str:
    v = str(v or "").strip()
    return CLAY_EN.get(v.lower(), v)


def sources_md(keys):
    return " · ".join(f"[{SRC[k][0]}]({SRC[k][1]})" for k in keys)


TESTS = {
    4: [
        ("Rover mobility on a salt-basin floor", "driving, slipping and navigating on a flat, crusted former lake bed, like Jezero's floor"),
        ("Clay and salt detection", "testing spectrometers like Perseverance's (SuperCam, PIXL) on clays and evaporite salts"),
        ("Biosignature preservation", "studying how traces of life are kept, or destroyed, in the deposits of an ancient lake"),
        ("Sample collection", "rehearsing coring and sample caching in a dry, salty basin before doing it on Mars"),
    ],
}


def card(col, title, value, sub=""):
    col.markdown(f'<div class="card"><div class="t">{title}</div><div class="v">{value}</div>'
                 f'<div class="s">{sub}</div></div>', unsafe_allow_html=True)


def site_row(rank: int):
    """Merge world row + top 100 extras for one rank."""
    r = None
    if WORLD is not None and "rang" in WORLD.columns:
        w = WORLD[WORLD["rang"] == rank]
        if len(w):
            r = w.iloc[0].copy()
    t = TOP[TOP["rang"] == rank]
    if len(t):
        r = t.iloc[0].copy() if r is None else pd.concat([r, t.iloc[0]])
        r = r[~r.index.duplicated(keep="last")]
    return r


def nearest_rank(df: pd.DataFrame, click) -> int | None:
    if not click or df is None or df.empty:
        return None
    d = (df["lat"] - click["lat"]) ** 2 + (((df["lon"] - click["lng"] + 180) % 360) - 180) ** 2
    i = d.idxmin()
    return int(df.loc[i, "rang"]) if d[i] < 0.5 ** 2 else None


def site_panel(rank: int, sel_key: str):
    r = site_row(rank)
    if r is None:
        st.info("Site not found.")
        return
    in_top = rank in set(TOP["rang"])
    where = escape(str(r.get("territoire", "") or ""))
    st.markdown(f"### Site #{rank}" + (f" · {where}" if where else ""))
    if rank in PRIORITY_TARGETS:
        st.markdown("**Priority target** (clay signal: possible trace of past water)")
    if "novelty" in r.index:
        c = NOVELTY[r["novelty"]][1]
        st.markdown(f"<span style='color:{c}'>●</span> {escape(novelty_text(r))}", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    card(c1, "Similarity score", f"{r['score']:.0f} / 100", "mean over the 25 km cell")
    card(c2, "Profile", escape(str(r.get("profil", "—"))).replace("Env", "Env.").replace(" · ", "<br>"), "A = best, D = weakest")
    typ = " · ".join(x for x in (str(r.get("typologie", "") or ""), str(r.get("morphotype", "") or "")) if x)
    if typ:
        st.caption(typ)

    rows = []
    for col, label, _, target, fmt in PARAMS:
        if col in r.index and pd.notna(r[col]):
            rows.append(f"<tr><td>{label}</td><td><b>{fmt.format(r[col])}</b></td><td>{target}</td></tr>")
    if "signal_argiles" in r.index and str(r["signal_argiles"]):
        ratio = f" (ratio {r['ratio_argiles']:.2f})" if "ratio_argiles" in r.index and pd.notna(r["ratio_argiles"]) else ""
        rows.append(f"<tr><td>Clay signal</td><td><b>{escape(str(r['signal_argiles']))}{ratio}</b></td><td>strong = past water</td></tr>")
    if rows:
        st.markdown("<table class='cmp'><tr><th>Parameter</th><th>This site</th><th>Most Jezero-like</th></tr>"
                    + "".join(rows) + "</table>", unsafe_allow_html=True)

    strong, weak = analogy(r)
    st.markdown("#### How good is the analogy?")
    if strong:
        st.markdown("<div class='card'><div class='t' style='color:#2e9e5b'>Strong analogy</div><div class='s'>"
                    + "<br>".join(f"✓ {x}" for x in strong) + "</div></div>", unsafe_allow_html=True)
    if weak:
        st.markdown("<div class='card'><div class='t' style='color:#ff9900'>Where it breaks down</div><div class='s'>"
                    + "<br>".join(f"✗ {x}" for x in weak) + "</div></div>", unsafe_allow_html=True)
    st.markdown("<div class='card'><div class='t'>Not reproducible anywhere on Earth</div><div class='s'>"
                + "<br>".join(NOT_ON_EARTH) + "</div></div>", unsafe_allow_html=True)

    if rank in PROCESS_SHORT:
        st.markdown("#### Same process as Jezero")
        st.markdown(f"<div class='card'><div class='s' style='font-size:0.9rem'>{PROCESS_SHORT[rank]}</div></div>",
                    unsafe_allow_html=True)

    if rank in TESTS:
        st.markdown("#### What could be tested here")
        st.markdown("".join(f"<div class='card'><div class='v' style='font-size:1rem'>{h}</div><div class='s'>{d}</div></div>"
                            for h, d in TESTS[rank]), unsafe_allow_html=True)

    if in_top:
        tr = TOP[TOP["rang"] == rank].iloc[0]
        fig = use_case_bars(tr)
        if fig is not None:
            st.markdown("#### Best suited for")
            st.plotly_chart(fig, use_container_width=True, key=f"uc_{sel_key}_{rank}")
            st.caption("How each test-use is computed: page 3 · Compare sites.")
        st.markdown("")
        c3, c4 = st.columns(2)
        if "acces_heures" in r.index and pd.notna(r["acces_heures"]):
            card(c3, "Field access", f"{r['acces_heures']:.1f} h", ACCESS_TXT.get(r.get("access", ""), "") + " from the nearest city")
        colr, lab, expl = STATUS[r["status"]]
        name = str(r.get("nom_aire_protegee", "") or "")
        card(c4, "Status", f"<span style='color:{colr}'>●</span> {lab}", escape(name) if name else expl)
    else:
        st.caption("Outside the top 100: field access and status were checked for the top 100 only.")
    st.caption(f"GPS {r['lat']:.4f}, {r['lon']:.4f} · "
               f"[open in OpenStreetMap](https://www.openstreetmap.org/?mlat={r['lat']:.4f}&mlon={r['lon']:.4f}#map=9/{r['lat']:.4f}/{r['lon']:.4f})")
    if st.button("Close", key=f"close_{rank}"):
        st.session_state.pop(sel_key, None)
        st.rerun()


# Map backgrounds: chosen with a Streamlit control (sidebar), so the choice survives every slider move
BASEMAPS = {
    "Dark": ("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
             "Esri, HERE, Garmin, © OpenStreetMap contributors", 16),
    "Satellite": ("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                  "Esri, Maxar, Earthstar Geographics", 18),
    "Relief": ("https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
               "Esri, HERE, Garmin, USGS, NGA", 18),
}


def current_basemap() -> str:
    b = st.session_state.get("basemap", "Dark")
    return b if b in BASEMAPS else "Dark"


def base_map(center=(20, 10), zoom=2):
    m = folium.Map(location=center, zoom_start=zoom, tiles=None, prefer_canvas=True, world_copy_jump=True,
                   control_scale=True, min_zoom=2)
    url, attr, mz = BASEMAPS[current_basemap()]
    folium.TileLayer(url, name=current_basemap(), attr=attr, max_zoom=mz, control=False).add_to(m)
    return m


def add_points(m, df, color, radius, name, opacity=0.8):
    fg = folium.FeatureGroup(name=name)
    for _, r in df.iterrows():
        folium.CircleMarker([r["lat"], r["lon"]], radius=radius, color="#05070b", weight=0.6, fill=True,
                            fill_color=color, fill_opacity=opacity,
                            tooltip=f"#{int(r['rang'])} · score {r['score']:.0f}").add_to(fg)
    fg.add_to(m)


RECOMMENDED = 4


# Which side the label goes, so neighbouring pins do not hide each other: (side, vertical shift in px)
PIN_LABEL = {4: ("right", -16), 89: ("left", 14), 40: ("left", 0)}
KNOWN_LABEL = {"Death Valley": ("left", 0), "Atacama (Yungay)": ("left", -22), "MDRS, Utah": ("right", -14)}


def _pin(color, size, label, sub="", big=False, side="right", dy=0):
    """A visible map pin: coloured disc with white border + a label box next to it."""
    fs = 13 if big else 11
    pos = f"left:{size + 8}px" if side == "right" else f"right:{size + 8}px"
    return folium.DivIcon(icon_size=(0, 0), html=(
        f"<div style='position:relative;transform:translate(-{size // 2}px,-{size // 2}px);white-space:nowrap'>"
        f"<div style='width:{size}px;height:{size}px;border-radius:50%;background:{color};border:3px solid #fff;"
        f"box-shadow:0 0 0 3px rgba(0,0,0,.55),0 0 14px {color}'></div>"
        f"<div style='position:absolute;{pos};top:{size // 2 - 12 + dy}px;background:#05070be6;border:1px solid {color};"
        f"color:#fff;font:600 {fs}px sans-serif;padding:3px 7px;line-height:1.25'>{label}"
        + (f"<br><span style='font-weight:400;color:#c9d1d9;font-size:{fs - 1}px'>{sub}</span>" if sub else "")
        + "</div></div>"))


def add_priority(m, df):
    fg = folium.FeatureGroup(name="Priority targets")
    for _, r in df[df["priority"]].iterrows():
        rk = int(r["rang"])
        rec = rk == RECOMMENDED
        where = escape(str(r.get("territoire", "") or ""))
        folium.Marker([r["lat"], r["lon"]], tooltip=f"Priority target #{rk}",
                      icon=_pin(C_TOP if rec else "#4fc3f7", 24 if rec else 18,
                                f"★ #{rk} · {where}" if rec else f"#{rk} · {where}",
                                "Recommended site" if rec else "Clay signal", big=rec,
                                side=PIN_LABEL.get(rk, ("right", 0))[0], dy=PIN_LABEL.get(rk, ("right", 0))[1])).add_to(fg)
    fg.add_to(m)


def add_known(m):
    fg = folium.FeatureGroup(name="Well-known analog sites")
    for name, la, lo, _ in KNOWN_ANALOGS:
        side, dy = KNOWN_LABEL.get(name, ("right", 0))
        tag = (f"<span style='position:absolute;{'left:20px' if side == 'right' else 'right:20px'};top:{1 + dy}px;"
               f"background:#05070bd9;border:1px solid #8b949e;padding:2px 6px'>{escape(name)}</span>")
        folium.Marker([la, lo], tooltip=f"Well-known analog: {name}", icon=folium.DivIcon(icon_size=(0, 0), html=(
            "<div style='position:relative;transform:translate(-9px,-12px);white-space:nowrap;font:600 12px sans-serif;color:#fff'>"
            "<span style='font-size:18px;color:#ffffff;text-shadow:0 0 3px #000,0 0 6px #000'>▲</span>"
            f"{tag}</div>"))).add_to(fg)
    fg.add_to(m)


def show_map(m, df_click, key, sel_key, height=600):
    folium.LayerControl(collapsed=True).add_to(m)
    out = st_folium(m, height=height, use_container_width=True, returned_objects=["last_object_clicked"], key=key)
    rk = nearest_rank(df_click, (out or {}).get("last_object_clicked"))
    if rk is not None and st.session_state.get(sel_key + "_click") != (out or {}).get("last_object_clicked"):
        st.session_state[sel_key] = rk
        st.session_state[sel_key + "_click"] = out["last_object_clicked"]
        st.rerun()


# ---- Use cases: which site is best for which kind of test ----------------------------------
def _ramp(v, worst, best):
    return np.clip((v - worst) / (best - worst), 0, 1)


def add_use_cases(df: pd.DataFrame) -> pd.DataFrame:
    """Sub-scores 0-1 from real columns, then 5 use-case scores (weighted means, shown in the app)."""
    df = df.copy()
    g = lambda c, default=np.nan: df[c] if c in df.columns else pd.Series(default, index=df.index)
    df["m_climate"] = g("env_moy")
    df["m_terrain"] = g("relief_moy")
    df["m_rock"] = g("compo_moy")
    df["m_clay"] = _ramp(g("ratio_argiles"), 1.0, 1.27)               # 1.27 = site #4, moderate signal
    df["m_flat"] = _ramp(g("pente_moy_deg"), 5.0, 0.0)                # 0° = 1, 5° = 0
    df["m_dry"] = _ramp(g("aridite"), 0.65, 0.03)                     # model's aridity ramp
    df["m_bare"] = _ramp(g("ndvi_max"), 0.5, 0.05)                    # model's NDVI ramp
    df["m_swing"] = _ramp(g("amplitude_k"), 10, 35)                   # model's swing ramp
    df["m_access"] = _ramp(g("acces_heures"), 24, 2)                  # ≤ 2 h = 1, ≥ 24 h = 0
    df["m_status"] = g("status", "ok").map({"ok": 1.0, "protected": 0.5, "disputed": 0.0})
    for code, (_, parts, _) in USE_CASES.items():
        df[code] = sum(w * df[c] for c, w in parts.items()) / sum(parts.values())
    return df


METRIC_LABELS = {"m_climate": "Climate", "m_terrain": "Terrain", "m_rock": "Rock (mafic)", "m_clay": "Clay signal",
                 "m_flat": "Flatness", "m_dry": "Dryness", "m_bare": "No vegetation", "m_swing": "Day–night swing",
                 "m_access": "Access", "m_status": "Legal status"}
USE_CASES = {  # code: (label, weights of sub-scores, why)
    "uc_rover": ("Rover mobility & landing tests", {"m_flat": 0.4, "m_terrain": 0.4, "m_access": 0.2},
                 "a flat, crater-like floor to drive and land on, reachable with heavy equipment"),
    "uc_instr": ("Instrument & geology tests", {"m_rock": 0.6, "m_clay": 0.4},
                 "Jezero-like rocks and clays to calibrate spectrometers"),
    "uc_env": ("Environment & thermal tests", {"m_climate": 0.6, "m_swing": 0.4},
               "cold, dry, with big day–night swings to stress hardware"),
    "uc_bio": ("Astrobiology & biosignatures", {"m_dry": 0.35, "m_bare": 0.25, "m_clay": 0.4},
               "almost lifeless and dry, with clays that may preserve traces of life"),
    "uc_field": ("Field campaign logistics", {"m_access": 0.7, "m_status": 0.3},
                 "short trip from a city, no dispute, no permit"),
}
UC_COLORS = {"uc_rover": "#f2b134", "uc_instr": "#4fc3f7", "uc_env": "#bc8cff", "uc_bio": "#2e9e5b", "uc_field": "#e0e0e0"}


def plot_dark(fig, height=380):
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=height,
                      margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.2),
                      xaxis=dict(gridcolor="#1f2937"), yaxis=dict(gridcolor="#1f2937"))
    return fig


def use_case_bars(r):
    """Horizontal bars: how well one site fits each use case."""
    codes = [c for c in USE_CASES if c in r.index and pd.notna(r[c])]
    if not codes:
        return None
    codes = sorted(codes, key=lambda c: r[c])
    fig = go.Figure(go.Bar(x=[r[c] * 100 for c in codes], y=[USE_CASES[c][0] for c in codes], orientation="h",
                           marker_color=[UC_COLORS[c] for c in codes], text=[f"{r[c] * 100:.0f}" for c in codes],
                           textposition="outside"))
    fig.update_xaxes(range=[0, 110], title="Fit (/100)")
    return plot_dark(fig, height=240)


def page_title(text: str):
    icon = f"<img src='data:image/png;base64,{LOGO_ICON_B64}' style='height:1.6em;vertical-align:-0.3em;margin-right:12px' alt=''>"
    st.markdown(f"<h2 style='margin-bottom:0.2rem'>{icon}{escape(text)}</h2>", unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# 4. NAVIGATION
# ----------------------------------------------------------------------------
if hasattr(st, "logo"):   # Streamlit >= 1.35: logo pinned at the top-left of the sidebar
    import base64 as _b64
    from PIL import Image as _Image
    _full = _Image.open(io.BytesIO(_b64.b64decode(LOGO_FULL_B64)))
    try:
        st.logo(_full, size="large", icon_image=_logo_image())
    except TypeError:     # Streamlit 1.35-1.38: no size argument
        st.logo(_full, icon_image=_logo_image())
    st.markdown("<style>img[data-testid='stLogo'], [data-testid='stSidebarHeader'] img { height: 2.6rem !important; "
                "max-width: 220px !important; }</style>", unsafe_allow_html=True)

with st.sidebar:
    if not hasattr(st, "logo"):   # older Streamlit: logo at the top of the sidebar content
        st.markdown(f"<img src='data:image/png;base64,{LOGO_FULL_B64}' style='width:100%;max-width:220px;"
                    "margin:0 0 18px 0' alt='Proteus Group'>", unsafe_allow_html=True)
    st.markdown("### Planetary Analog Finder")
    st.caption("Where on Earth looks like Jezero crater, Mars?")
    page = st.radio("Page", ["1 · The model", "2 · Top 100 sites", "3 · Compare sites", "4 · Jezero vs site #4"],
                    label_visibility="collapsed")
    st.radio("Map background", list(BASEMAPS), horizontal=True, key="basemap")
    st.markdown("---")
    st.caption("NASA Space Apps Challenge 2026 · Team Proteus 2")
    st.caption("App version: v2.8 · 14 Nov 17:05")
    st.caption(f"Data: {TOP_FILE}" + (f" · {FILE_WORLD}" if WORLD is not None else " · world scan not loaded"))

N_WORLD = len(WORLD) if WORLD is not None else 4553
TOP = add_novelty(TOP)
WORLD = add_novelty(WORLD)
TOP = add_use_cases(TOP)

# ----------------------------------------------------------------------------
# 5. PAGE 1 · THE MODEL
# ----------------------------------------------------------------------------
if page.startswith("1"):
    page_title("Where on Earth looks like Jezero?")
    st.markdown("<p class='lead'>Jezero is the ancient lake crater on Mars where the Perseverance rover landed. "
                "We scanned every piece of land on Earth to find places with the same climate, terrain and rocks.</p>",
                unsafe_allow_html=True)

    STAGES = ["Before the model", f"After the model: {N_WORLD:,} sites", "Ranked: top 100", "Recommended targets"]
    map_area = st.container()          # the map is drawn here, above the slider
    stage = st.select_slider("Filter: move the slider to run the model", options=STAGES, value=STAGES[1])
    i = STAGES.index(stage)
    TEXT = [
        "All land on Earth, from 60° S to 80° N: <b>138 million km²</b>. Nothing selected yet.",
        f"Only <b>0.5 %</b> of land passes the three tests (climate, terrain, rock). It is cut into 25 km cells: "
        f"<b>{N_WORLD:,} candidate sites</b>.",
        "Sites are ranked by similarity score. The <b>top 100</b> cluster in western Tibet, the Andes, Iran, "
        f"the Qaidam basin and Mongolia. The model finds known analogs on its own (▲), but <b>{int((TOP['novelty'] == 'new').sum())} "
        "of the 100</b> are far from any well-known analog site.",
        "Among the top 100, the team picked the sites with a <b>clay signal</b> (possible trace of past water), "
        "reachable and allowed: <b>#4</b> in the Puna, Argentina, is our recommendation.",
    ]
    st.markdown(f"<div class='stage'>{TEXT[i]}</div>", unsafe_allow_html=True)
    if WORLD is None and i == 1:
        st.warning(f"{FILE_WORLD} not found next to app.py: the {N_WORLD:,} candidate sites cannot be drawn. "
                   "Showing the top 100 instead.")
    st.markdown("")

    sel_key = "sel_p1"
    sel = st.session_state.get(sel_key)
    if i == 0:
        sel = None
    with map_area:
        col_map, col_info = st.columns([2.3, 1]) if sel else (st.container(), None)

    with col_map:
        if i == 3:
            focus = TOP[TOP["rang"] == 4]
            center, zoom = ((focus.iloc[0]["lat"], focus.iloc[0]["lon"]), 4) if len(focus) else ((20, 10), 2)
        else:
            center, zoom = (20, 10), 2
        m = base_map(center, zoom)
        click_df = None
        if i >= 1 and WORLD is not None:
            add_points(m, WORLD, C_WORLD, 3, f"Candidate sites ({len(WORLD):,})", opacity=0.7 if i == 1 else 0.35)
            click_df = WORLD
        if i >= 2 or (i == 1 and WORLD is None):
            add_points(m, TOP, C_TOP, 5, "Top 100", opacity=0.9)
            click_df = TOP if WORLD is None else WORLD
        if i >= 1:
            add_known(m)
            add_priority(m, TOP)
        show_map(m, click_df, f"map_p1_{i}_{current_basemap()}", sel_key, height=620)
        legend = []
        if i >= 1:
            legend.append(f"<span><span class='dot' style='background:{C_WORLD}'></span>Candidate site</span>")
        if i >= 2 or (i == 1 and WORLD is None):
            legend.append(f"<span><span class='dot' style='background:{C_TOP}'></span>Top 100</span>")
        if i >= 1:
            legend.append(f"<span><span class='dot' style='background:{C_TOP};border:2px solid #fff'></span>★ #4 Recommended site</span>")
            legend.append("<span><span class='dot' style='background:#4fc3f7;border:2px solid #fff'></span>Priority target (clay signal)</span>")
            legend.append("<span>▲ Well-known analog (Atacama, Utah, Qaidam…)</span>")
        if legend:
            st.markdown("<div class='legend'>" + "".join(legend) + "<span style='color:#7d8590'>Click a point to see the site</span></div>",
                        unsafe_allow_html=True)

    if col_info is not None:
        with col_info:
            site_panel(sel, sel_key)

    # Plain-language explanation of the model
    st.markdown("---")
    st.markdown("### How the model works")
    st.markdown("<p class='lead'>Three tests, applied to every square kilometre of land with open satellite data "
                "(Google Earth Engine). A site must pass all three. Each test gives a score from 0 to 1.</p>",
                unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3)
    steps = [
        ("Step 1 · Climate", "Is it cold, dry and dead like Mars?",
         "Big gap between day and night temperature, cold on average, no plants, almost no rain.",
         "MODIS temperature & vegetation, TerraClimate rain", "138 M km² → 4.4 M km² (3.2 %)"),
        ("Step 2 · Terrain", "Does it look like a crater floor?",
         "A wide flat floor, surrounded by moderate relief, sitting lower than its surroundings, like a basin.",
         "MERIT elevation model, 90 m", "4.4 M km² → 1.4 M km² (1.0 %)"),
        ("Step 3 · Rock", "Are the rocks like Jezero's floor?",
         "Dark, iron- and magnesium-rich (mafic) rock, like the olivine and basalt seen by Perseverance.",
         "ASTER thermal infrared, 100 m", f"1.4 M km² → 0.73 M km² (0.5 %) → {N_WORLD:,} sites"),
    ]
    for col, (n, h, p, k, f) in zip((s1, s2, s3), steps):
        col.markdown(f"<div class='step'><div class='n'>{n}</div><div class='h'>{h}</div><div class='p'>{p}</div>"
                     f"<div class='k'>Data: {k}</div><div class='k'><b style='color:#f2b134'>{f}</b></div></div>",
                     unsafe_allow_html=True)
    st.markdown("")
    st.markdown("**Final score** = climate<sup>0.35</sup> × terrain<sup>0.30</sup> × rock<sup>0.35</sup>. "
                "Multiplying means one weak test pulls the whole site down: a site has to be good at everything.",
                unsafe_allow_html=True)
    st.markdown("**Why only Mars, and only Jezero?** The challenge covers the Moon and Mars. We chose to go deep on one "
                "real mission site, where Perseverance gives ground-truth measurements, rather than cover everything "
                "superficially. The same method can be rerun with a lunar profile.")
    with st.expander("All parameters and thresholds"):
        st.dataframe(pd.DataFrame([
            ["Climate", "Day–night surface temperature swing", "MODIS", "≥ 35 K", "30 %"],
            ["Climate", "Mean surface temperature", "MODIS", "≤ −15 °C", "20 %"],
            ["Climate", "Vegetation (max NDVI)", "MODIS", "≤ 0.05", "25 %"],
            ["Climate", "Aridity index", "TerraClimate", "≤ 0.03", "25 %"],
            ["Terrain", "Share of flat land (< 5°)", "MERIT DEM 90 m", "≥ 80 %", "40 %"],
            ["Terrain", "Local relief within 3 km", "MERIT DEM 90 m", "100–500 m", "35 %"],
            ["Terrain", "Position vs. surroundings (10 km)", "MERIT DEM 90 m", "≥ 50 m lower", "25 %"],
            ["Rock", "Mafic index (ASTER band 12 / 13)", "ASTER GED 100 m", "top 2 % of arid land", "100 %"],
        ], columns=["Test", "Parameter", "Data", "Score 1 when", "Weight"]), hide_index=True, use_container_width=True)
        st.caption("Eliminated outright: max NDVI > 0.4, aridity > 0.5, or more than 10 % surface water. "
                   "Thresholds come from Perseverance measurements and UN aridity classes; weights are team choices.")
    with st.expander("Known vs new: how we tell"):
        st.markdown("A site is a **known analog region** if it lies inside the area of a well-known Mars analog, "
                    f"**near** if it is within {NEAR_KM} km more, and **new** otherwise.")
        st.dataframe(pd.DataFrame([(n, la, lo, rad) for n, la, lo, rad in KNOWN_ANALOGS],
                                  columns=["Well-known analog", "Lat", "Lon", "Area radius (km)"]),
                     hide_index=True, use_container_width=True)
    # Validation
    st.markdown("---")
    st.markdown("### Does the model find the right places?")
    st.markdown("<p class='lead'>We never told the model where known analogs are. So we ran it on test sites "
                "where we know the answer: places that should partly match, and places that must be rejected.</p>",
                unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(VALIDATION, columns=["Test site", "What we expect", "Model result", "Verdict"]),
                 hide_index=True, use_container_width=True)
    nk = int((TOP["novelty"] == "known").sum())
    v1, v2, v3 = st.columns(3)
    card(v1, "Known analogs found blind", f"{nk} of 100",
         "top-100 sites inside a well-known analog region (all in the Qaidam basin)")
    card(v2, "Negative tests rejected", "3 of 3", "sand sea, rainforest, France")
    card(v3, "Perfect match on Earth", "none",
         "no site matches Jezero on every dimension: that is why each site gets a profile, A to D")
    st.caption("Test-site results come from the team's Earth Engine runs on each site (same model, same thresholds).")

    report = find_file(REPORT_FILE)
    if report is not None:
        st.download_button("Download the full report (PDF, French)", report.read_bytes(), REPORT_FILE, "application/pdf")

# ----------------------------------------------------------------------------
# 6. PAGE 2 · TOP 100
# ----------------------------------------------------------------------------
elif page.startswith("2"):
    page_title("The 100 most Jezero-like places on Earth")
    st.markdown("<p class='lead'>A good analog is only useful if a team can go there. Each site is checked for "
                "travel time, disputed borders and protected areas.</p>", unsafe_allow_html=True)

    n = TOP["status"].value_counts()
    k1, k2, k3, k4, k5 = st.columns(5)
    card(k1, "Accessible", f"<span style='color:{STATUS['ok'][0]}'>{n.get('ok', 0)}</span>", STATUS["ok"][2])
    card(k2, "Protected area", f"<span style='color:{STATUS['protected'][0]}'>{n.get('protected', 0)}</span>", STATUS["protected"][2])
    card(k3, "Disputed territory", f"<span style='color:{STATUS['disputed'][0]}'>{n.get('disputed', 0)}</span>", STATUS["disputed"][2])
    card(k4, "Priority targets", f"{int(TOP['priority'].sum())}", "clay signal: " + ", ".join(f"#{r}" for r in sorted(TOP.loc[TOP['priority'], 'rang'])))
    nv = TOP["novelty"].value_counts()
    card(k5, "New sites", f"<span style='color:{NOVELTY['new'][1]}'>{nv.get('new', 0)}</span>",
         f"far from any well-known analog · {nv.get('near', 0)} near, {nv.get('known', 0)} known")

    f1, f2, f4, f3 = st.columns([2, 2, 2, 1.3])
    show_status = f1.multiselect("Show", list(STATUS), default=list(STATUS), format_func=lambda s: STATUS[s][1])
    if "access" in TOP.columns:
        acc_opts = [a for a in ("easy", "expedition", "remote") if a in set(TOP["access"])]
        show_access = f2.multiselect("Access", acc_opts, default=acc_opts, format_func=lambda a: ACCESS_TXT[a])
    else:
        show_access = None
    show_nov = f4.multiselect("Novelty", list(NOVELTY), default=list(NOVELTY), format_func=lambda k: NOVELTY[k][0])
    only_prio = f3.checkbox("Priority targets only", value=False)

    view = TOP[TOP["status"].isin(show_status)]
    if show_access is not None:
        view = view[view["access"].isin(show_access) | (view["access"] == "")]
    view = view[view["novelty"].isin(show_nov)]
    if only_prio:
        view = view[view["priority"]]

    # ---- Map, with a before/after slider for the field check underneath ----
    map_area = st.container()
    FC = ["Before field check", "Disputed territories", "Protected areas", "After field check", "Usable now"]
    j = FC.index(st.select_slider("Filter: field check, before → after", options=FC, value=FC[3], key="fc_stage"))
    C_UNCHECKED = "#9aa4b1"
    n_dis, n_pro = int(n.get("disputed", 0)), int(n.get("protected", 0))
    usable = (TOP["status"] == "ok") & (TOP.get("access", pd.Series("", index=TOP.index)) == "easy")
    FC_TEXT = [
        "<b>Before</b>: the top 100 as the model ranks them, on resemblance to Jezero only. "
        "Nothing is known yet about who can go there.",
        f"<b>Step 1</b>: international borders. <b>{n_dis} sites</b> fall in a territory claimed by two countries "
        "(Aksai Chin): not recommended for a field campaign.",
        f"<b>Step 2</b>: protected areas (WDPA). <b>{n_pro} sites</b> are inside a national park or reserve: "
        "possible, but a permit is needed.",
        f"<b>After</b>: <b>{n.get('ok', 0)} of 100</b> sites are free of disputes and protection. "
        "Travel time from the nearest city is now known for every site.",
        f"<b>Usable now</b>: no restriction <i>and</i> less than 6 h from a city: <b>{int(usable.sum())} sites</b>. "
        f"Our recommended site <b>#{RECOMMENDED}</b> is one of them (5.5 h).",
    ]
    st.markdown(f"<div class='stage'>{FC_TEXT[j]}</div>", unsafe_allow_html=True)

    def fc_style(r):
        """Colour and opacity of one site at the current field-check step."""
        stt = r["status"]
        if j == 0:
            return C_UNCHECKED, 0.9
        if j == 1:
            return (STATUS["disputed"][0], 0.95) if stt == "disputed" else (C_UNCHECKED, 0.6)
        if j == 2:
            return (STATUS[stt][0], 0.95) if stt != "ok" else (C_UNCHECKED, 0.6)
        if j == 3:
            return STATUS[stt][0], 0.9
        ok = stt == "ok" and r.get("access", "") == "easy"
        return (STATUS["ok"][0], 1.0) if ok else (STATUS[stt][0], 0.18)

    leg = {0: [(C_UNCHECKED, "Top 100 site, not checked yet")],
           1: [(STATUS["disputed"][0], "Disputed territory"), (C_UNCHECKED, "Not checked yet")],
           2: [(STATUS["disputed"][0], "Disputed territory"), (STATUS["protected"][0], "Protected area"), (C_UNCHECKED, "Not checked yet")],
           3: [(c, f"{lab} — {ex}") for c, lab, ex in STATUS.values()],
           4: [(STATUS["ok"][0], "Usable now: no restriction, < 6 h"), ("#3a3f47", "Faded: restricted or > 6 h away")]}[j]
    st.markdown(
        "<div class='legend'>"
        + "".join(f"<span><span class='dot' style='background:{c}'></span><b>{lab}</b></span>" for c, lab in leg)
        + "<span><span class='ring'></span><b>Priority target</b> — clay signal</span>"
        + "<span>▲ <b>Well-known analog</b></span>"
        + "<span style='color:#7d8590'>Bigger point = better rank · click a point for details</span></div>",
        unsafe_allow_html=True)

    sel_key = "sel_p2"
    sel = st.session_state.get(sel_key)
    with map_area:
        col_map, col_info = st.columns([2.3, 1]) if sel else (st.container(), None)
        with col_map:
            m = base_map((20, 10), 2)
            fg = folium.FeatureGroup(name="Top 100")
            for _, r in view.sort_values("rang", ascending=False).iterrows():
                c, op = fc_style(r)
                rad = 4 + (100 - min(r["rang"], 100)) / 20
                folium.CircleMarker([r["lat"], r["lon"]], radius=rad if op > 0.3 else rad * 0.7, color="#05070b",
                                    weight=1, fill=True, fill_color=c, fill_opacity=op, opacity=max(op, 0.3),
                                    tooltip=f"#{int(r['rang'])} · {r.get('territoire', '')} · score {r['score']:.0f} · "
                                            f"{STATUS[r['status']][1] if j >= 3 else ''}").add_to(fg)
            fg.add_to(m)
            add_priority(m, view)
            add_known(m)
            if len(view):
                m.fit_bounds([[view["lat"].min() - 3, view["lon"].min() - 3], [view["lat"].max() + 3, view["lon"].max() + 3]])
            show_map(m, view, f"map_p2_{j}_{current_basemap()}_{hash(tuple(view['rang']))}", sel_key, height=560)
        if col_info is not None:
            with col_info:
                site_panel(sel, sel_key)

    # ---- Field access & constraints (top 100) ----
    st.markdown("---")
    st.markdown("### Field access & constraints")
    if "access" in TOP.columns:
        na = TOP["access"].value_counts()
        a1, a2, a3, a4, a5 = st.columns(5)
        card(a1, "Easy access", f"<span style='color:{ACCESS_COLOR['easy']}'>{na.get('easy', 0)}</span>", "< 6 h from a city")
        card(a2, "Expedition", f"<span style='color:{ACCESS_COLOR['expedition']}'>{na.get('expedition', 0)}</span>", "6 to 24 h")
        card(a3, "Very remote", f"{na.get('remote', 0)}", "> 24 h")
        card(a4, "Disputed zones", f"<span style='color:{STATUS['disputed'][0]}'>{n.get('disputed', 0)}</span>",
             "excluded from the accessible ranking")
        names = sorted({x for x in TOP.get("nom_aire_protegee", pd.Series(dtype=str)) if x})
        card(a5, "Protected areas", f"<span style='color:{STATUS['protected'][0]}'>{n.get('protected', 0)}</span>",
             escape(", ".join(names)) if names else "none")

    g1, g2, g3 = st.columns(3)
    with g1:
        st.markdown("#### Selection funnel")
        stages = []
        if WORLD is not None:
            stages.append(("World scan", len(WORLD)))
        stages.append(("Top 100", len(TOP)))
        cur = TOP[TOP["status"] != "disputed"]
        stages.append(("Outside disputed zones", len(cur)))
        cur = cur[cur["status"] != "protected"]
        stages.append(("Outside protected areas", len(cur)))
        if "access" in cur.columns:
            cur = cur[cur["access"] == "easy"]
            stages.append(("Easy access (< 6 h)", len(cur)))
        fun = go.Figure(go.Funnel(y=[x[0] for x in stages], x=[x[1] for x in stages], textinfo="value",
                                  marker=dict(color=["#6f8fb8", "#f2b134", "#e07a5f", "#ff9900", "#4fc3f7"][:len(stages)]),
                                  connector=dict(fillcolor="#1f2937")))
        st.plotly_chart(plot_dark(fun, height=360), use_container_width=True)
        st.caption("From all candidate sites to the ones a team could visit next month.")

    with g2:
        st.markdown("#### Access time vs. score")
        if "acces_heures" in TOP.columns:
            fig = go.Figure()
            for code, (c, lab, _) in STATUS.items():
                d = view[view["status"] == code]
                fig.add_trace(go.Scatter(x=d["acces_heures"], y=d["score"], mode="markers", name=lab,
                                         marker=dict(color=c, size=8, line=dict(width=0.5, color="#05070b")),
                                         text=[f"#{r} · {t}" for r, t in zip(d["rang"], d.get("territoire", [""] * len(d)))],
                                         hovertemplate="%{text}<br>%{x:.1f} h · score %{y:.0f}<extra></extra>"))
            p = view[view["priority"]]
            fig.add_trace(go.Scatter(x=p["acces_heures"], y=p["score"], mode="markers+text", name="Priority",
                                     text=[f"#{r}" for r in p["rang"]], textposition="top center", textfont=dict(color="#fff"),
                                     marker=dict(symbol="circle-open", size=16, color="#fff", line=dict(width=2))))
            fig.add_vline(x=6, line=dict(color="#30363d", dash="dot"), annotation_text="6 h", annotation_font_color="#7d8590")
            fig.update_layout(xaxis_title="Travel time (h)", yaxis_title="Score (/100)")
            st.plotly_chart(plot_dark(fig, height=360), use_container_width=True)
            st.caption("Top-left is best: high score, short trip.")

    with g3:
        st.markdown("#### Sites by territory")
        if "territoire" in TOP.columns and "access" in TOP.columns:
            ct = pd.crosstab(TOP["territoire"], TOP["access"])
            ct = ct.loc[ct.sum(axis=1).sort_values(ascending=False).index]
            bar = go.Figure()
            for k in ("easy", "expedition", "remote", ""):
                if k in ct.columns:
                    bar.add_trace(go.Bar(name=ACCESS_TXT[k] if k else "Unknown", x=ct.index, y=ct[k], marker_color=ACCESS_COLOR[k]))
            bar.update_layout(barmode="stack", yaxis_title="Sites")
            st.plotly_chart(plot_dark(bar, height=360), use_container_width=True)
            st.caption("Colour = travel time from the nearest city.")

    st.markdown(f"### List ({len(view)} sites)")
    tbl = view.sort_values("rang").copy()
    tbl["Status"] = tbl["status"].map(lambda s: STATUS[s][1])
    tbl["Novelty"] = tbl["novelty"].map(lambda s: NOVELTY[s][0])
    tbl["Nearest known analog"] = tbl["nearest_known"] + " (" + tbl["dist_known_km"].map(lambda d: f"{d:,.0f} km") + ")"
    cols = {"rang": "Rank", "territoire": "Country", "score": "Score", "profil": "Profile", "signal_argiles": "Clay signal",
            "acces_heures": "Access (h)", "Status": "Status", "Novelty": "Novelty", "Nearest known analog": "Nearest known analog", "nom_aire_protegee": "Protected area", "lat": "Lat", "lon": "Lon"}
    tbl = tbl[[c for c in cols if c in tbl.columns]].rename(columns=cols)
    st.dataframe(tbl, hide_index=True, use_container_width=True, column_config={
        "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%.0f"),
        "Access (h)": st.column_config.NumberColumn(format="%.1f"),
        "Lat": st.column_config.NumberColumn(format="%.3f"), "Lon": st.column_config.NumberColumn(format="%.3f")})
    st.download_button("Download this list (CSV)", tbl.to_csv(index=False).encode("utf-8"), "top100_sites.csv", "text/csv")

# ----------------------------------------------------------------------------
# 7. PAGE 3 · COMPARE SITES: which site is best for which use
# ----------------------------------------------------------------------------
elif page.startswith("3"):
    page_title("Which site is best for which test?")
    st.markdown("<p class='lead'>No place on Earth matches Jezero on everything. Depending on what a mission wants to "
                "test, a different site wins. Every score below comes from the satellite measurements of each site.</p>",
                unsafe_allow_html=True)

    # 1. Use case ranking
    uc = st.radio("Use case", list(USE_CASES), format_func=lambda c: USE_CASES[c][0], horizontal=True)
    label, parts, why = USE_CASES[uc]
    st.markdown(f"<div class='stage'><b>{label}</b>: {why}.<br><span style='color:#9aa4b1'>Score = "
                + " + ".join(f"{w:.0%} {METRIC_LABELS[c]}" for c, w in parts.items()) + "</span></div>",
                unsafe_allow_html=True)
    best = TOP.sort_values(uc, ascending=False).head(15).iloc[::-1]
    fig = go.Figure(go.Bar(
        x=best[uc] * 100, orientation="h",
        y=[f"#{r} · {t}" + (" ★" if r == RECOMMENDED else "") for r, t in zip(best["rang"], best.get("territoire", [""] * len(best)))],
        marker=dict(color=[STATUS[s][0] for s in best["status"]],
                    line=dict(color=["#ffffff" if p else "rgba(0,0,0,0)" for p in best["priority"]], width=2)),
        text=[f"{v * 100:.0f}" for v in best[uc]], textposition="outside",
        hovertemplate="%{y}: %{x:.0f}/100<extra></extra>"))
    fig.update_xaxes(range=[0, 108], title=f"{label} (/100)")
    st.plotly_chart(plot_dark(fig, height=520), use_container_width=True)
    pos4 = int((TOP[uc] > TOP.loc[TOP["rang"] == RECOMMENDED, uc].max()).sum()) + 1 if RECOMMENDED in set(TOP["rang"]) else None
    st.caption("Top 15 of the top 100 for this use. Colour = field status (green accessible, orange protected, "
               "red disputed); white outline = priority target."
               + (f" Site #4 ranks {pos4} of 100 for this use." if pos4 else ""))

    # 2. Heatmap: sites x use cases
    st.markdown("### Every use case at a glance")
    default = sorted(set(TOP.nsmallest(10, "rang")["rang"]) | set(TOP.loc[TOP["priority"], "rang"]))
    picks = st.multiselect("Sites", sorted(TOP["rang"]), default=default, format_func=lambda r: f"#{r}")
    sub = TOP[TOP["rang"].isin(picks)].sort_values("rang")
    if len(sub):
        codes = list(USE_CASES)
        pct = np.column_stack([TOP[c].rank(pct=True).loc[sub.index] * 100 for c in codes])
        vals = np.column_stack([sub[c] * 100 for c in codes])
        hm = go.Figure(go.Heatmap(
            z=pct, x=[USE_CASES[c][0] for c in codes],
            y=[f"#{r} · {t}" for r, t in zip(sub["rang"], sub.get("territoire", [""] * len(sub)))],
            text=np.vectorize(lambda v: f"{v:.0f}")(vals), texttemplate="%{text}", zmin=0, zmax=100,
            colorscale=[[0, "#3b0f0f"], [0.5, "#5c4a12"], [1, "#2e9e5b"]],
            colorbar=dict(title="Percentile<br>in top 100"),
            hovertemplate="%{y}<br>%{x}: score %{text}, better than %{z:.0f}% of the top 100<extra></extra>"))
        hm.update_yaxes(autorange="reversed")
        st.plotly_chart(plot_dark(hm, height=90 + 34 * len(sub)), use_container_width=True)
        st.caption("Number = score /100. Colour = how the site ranks against the rest of the top 100 "
                   "(green = among the best for this use).")

    # 3. Radar of sub-scores
    st.markdown("### Site profiles")
    c1, c2 = st.columns([1.3, 1])
    with c1:
        rp = st.multiselect("Compare", sorted(TOP["rang"]),
                            default=[r for r in (RECOMMENDED, 40, 89, 1) if r in set(TOP["rang"])],
                            format_func=lambda r: f"#{r}", key="radar_sites", max_selections=5)
        axes = ["m_climate", "m_swing", "m_dry", "m_terrain", "m_flat", "m_rock", "m_clay", "m_access"]
        theta = [METRIC_LABELS[a] for a in axes] + [METRIC_LABELS[axes[0]]]
        rad = go.Figure()
        rad.add_trace(go.Scatterpolar(r=[1] * (len(axes) + 1), theta=theta, name="Perfect Jezero match",
                                      line=dict(color="#e03b2e", dash="dot"), fill=None))
        pal = ["#f2b134", "#4fc3f7", "#bc8cff", "#2e9e5b", "#e0e0e0"]
        for k, rk in enumerate(rp):
            r = TOP[TOP["rang"] == rk].iloc[0]
            v = [float(r[a]) if pd.notna(r[a]) else 0 for a in axes]
            rad.add_trace(go.Scatterpolar(r=v + v[:1], theta=theta, name=f"#{rk} · {r.get('territoire', '')}",
                                          line=dict(color=pal[k % 5]), fill="toself", opacity=0.55))
        rad.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(range=[0, 1], gridcolor="#1f2937", showticklabels=False),
                                     angularaxis=dict(gridcolor="#1f2937")))
        st.plotly_chart(plot_dark(rad, height=460), use_container_width=True)
    with c2:
        st.markdown("**How each axis is scored (0 → 1)**")
        st.markdown("""
- **Climate, Terrain, Rock**: the model's three step scores
- **Day–night swing**: 10 K → 35 K
- **Dryness**: aridity index 0.65 → 0.03
- **Flatness**: mean slope 5° → 0°
- **Clay signal**: clay ratio 1.00 → 1.27
- **Access**: 24 h → 2 h from the nearest city
""")
        st.caption("Even the best sites never reach 1 on the day–night swing: Jezero's ≈ 87 K is out of reach on Earth.")

    # 4. Metric explorer
    st.markdown("### Explore two measurements")
    RAW = {c: lab for c, lab, *_ in PARAMS if c in TOP.columns}
    RAW.update({c: METRIC_LABELS[c] for c in ("m_climate", "m_terrain", "m_rock") if c in TOP.columns})
    if "acces_heures" in TOP.columns:
        RAW["acces_heures"] = "Travel time (h)"
    if "ratio_argiles" in TOP.columns:
        RAW["ratio_argiles"] = "Clay ratio"
    keys = list(RAW)
    e1, e2 = st.columns(2)
    xk = e1.selectbox("X axis", keys, index=keys.index("acces_heures") if "acces_heures" in keys else 0, format_func=RAW.get)
    yk = e2.selectbox("Y axis", keys, index=keys.index("ratio_argiles") if "ratio_argiles" in keys else 1, format_func=RAW.get)
    sc = go.Figure()
    for code, (c, lab, _) in STATUS.items():
        d = TOP[TOP["status"] == code]
        sc.add_trace(go.Scatter(x=d[xk], y=d[yk], mode="markers", name=lab, marker=dict(color=c, size=9),
                                text=[f"#{r} · {t}" for r, t in zip(d["rang"], d.get("territoire", [""] * len(d)))],
                                hovertemplate="%{text}<br>%{x:.3g} · %{y:.3g}<extra></extra>"))
    p = TOP[TOP["priority"]]
    sc.add_trace(go.Scatter(x=p[xk], y=p[yk], mode="markers+text", name="Priority target", text=[f"#{r}" for r in p["rang"]],
                            textposition="top center", textfont=dict(color="#fff"),
                            marker=dict(symbol="circle-open", size=18, color="#fff", line=dict(width=2))))
    sc.update_layout(xaxis_title=RAW[xk], yaxis_title=RAW[yk])
    st.plotly_chart(plot_dark(sc, height=420), use_container_width=True)

    with st.expander("Use-case scores for all 100 sites (table)"):
        t = TOP.sort_values("rang")[["rang"] + (["territoire"] if "territoire" in TOP.columns else []) + list(USE_CASES)].copy()
        for c in USE_CASES:
            t[c] = (t[c] * 100).round(0)
        t = t.rename(columns={"rang": "Rank", "territoire": "Country", **{c: USE_CASES[c][0] for c in USE_CASES}})
        st.dataframe(t, hide_index=True, use_container_width=True)
        st.download_button("Download (CSV)", t.to_csv(index=False).encode("utf-8"), "use_case_scores.csv", "text/csv")
    st.caption("Use-case weights are team choices, made to be transparent rather than optimal. "
               "Sub-scores reuse the model's own thresholds where they exist.")

# ----------------------------------------------------------------------------
# 8. PAGE 4 · MARS: JEZERO AND ITS EARTH ANALOG
# ----------------------------------------------------------------------------
else:
    page_title("Jezero on Mars, and its analog on Earth")
    st.markdown("<p class='lead'>The target: Jezero crater, where NASA's Perseverance rover has been exploring since "
                "February 2021. Everything on this page about Mars comes from NASA data and published mission results.</p>",
                unsafe_allow_html=True)

    used = []                      # numbered source list, in order of first use
    for _, _, src in JEZERO_FACTS:
        if src not in used:
            used.append(src)
    used.append("pia23239")
    c1, c2 = st.columns([1.15, 1])
    with c1:
        st.markdown(f"<img src='{JEZERO_IMG}' style='width:100%;border:1px solid #1f2937' "
                    "alt='Jezero crater seen from orbit, with its delta coloured by minerals' "
                    "onerror=\"this.outerHTML='<div class=card><div class=s>The NASA image could not load (no internet?). "
                    f"<a href={SRC['pia23239'][1]} target=_blank>Open it on science.nasa.gov</a></div></div>'\">",
                    unsafe_allow_html=True)
        st.caption("Jezero crater from orbit (NASA Mars Reconnaissance Orbiter, CRISM + CTX). Colours show minerals: "
                   f"the delta is rich in clays and carbonates. Credit: [NASA/JPL-Caltech/MSSS/JHU-APL, PIA23239]({SRC['pia23239'][1]})")
    with c2:
        st.markdown("### Jezero fact sheet")
        rows = "".join(f"<tr><td style='color:#9aa4b1;width:28%'>{k}</td><td>{v} "
                       f"<a href='{SRC[src][1]}' target='_blank' style='color:#7d8590'>[{used.index(src) + 1}]</a></td></tr>"
                       for k, v, src in JEZERO_FACTS)
        st.markdown(f"<table class='cmp'>{rows}</table>", unsafe_allow_html=True)

    # Point-by-point parallel
    st.markdown("---")
    st.markdown("### Point by point: Jezero vs. an Earth site")
    rk = st.selectbox("Earth site", sorted(TOP["rang"]), index=sorted(TOP["rang"]).index(RECOMMENDED)
                      if RECOMMENDED in set(TOP["rang"]) else 0,
                      format_func=lambda r: f"#{r}" + (" (recommended)" if r == RECOMMENDED else ""))
    r = site_row(rk)
    g = lambda c: r[c] if c in r.index and pd.notna(r[c]) else None
    where = escape(str(r.get("territoire", "") or ""))
    clay = str(r.get("signal_argiles", "") or "")
    ratio = g("ratio_argiles")
    rows = [  # (dimension, Jezero, this site, verdict 'yes'/'part'/'no')
        ("Basin", "45 km impact crater that held a lake",
         "Salt basin (former lake bed) in the volcanic Puna; not an impact crater" if rk == RECOMMENDED
         else escape(" · ".join(x for x in (str(r.get('typologie', '') or ''), str(r.get('morphotype', '') or '')) if x) or "—"),
         "part"),
        ("Past water", "Ancient lake and river delta",
         "Closed basin where a lake dried out, leaving a salt flat" if rk == RECOMMENDED else "Not assessed for this site",
         "yes" if rk == RECOMMENDED else "part"),
        ("Salts", "Sulfates and perchlorates from evaporating brines",
         "Salt crust from evaporation (white salt flat in Sentinel-2)" if rk == RECOMMENDED else "Not assessed for this site",
         "yes" if rk == RECOMMENDED else "part"),
        ("Clays", "Clays in the delta sediments",
         f"Clay signal: {escape(clay_en(clay))}" + (f" (ratio {ratio:.2f}, ASTER)" if ratio is not None else ""),
         "part" if clay.lower().startswith(("moyen", "fort")) else "no"),
        ("Rock", "Olivine-rich and basaltic (mafic) floor",
         f"Mafic index score {g('compo_moy'):.2f} (ASTER)" if g("compo_moy") is not None else "—",
         "yes" if (g("compo_moy") or 0) >= 0.7 else "part"),
        ("Floor", "Flat crater floor",
         f"Mean slope {g('pente_moy_deg'):.1f}°" if g("pente_moy_deg") is not None else "—",
         "yes" if (g("pente_moy_deg") or 9) < 5 else "no"),
        ("Relief", "Crater rim around the floor",
         f"Local relief {g('relief_local_m'):.0f} m within 3 km" if g("relief_local_m") is not None else "—", "part"),
        ("Water today", "None at the surface", f"Max NDVI {g('ndvi_max'):.2f}, aridity index {g('aridite'):.3f}"
         if g("ndvi_max") is not None and g("aridite") is not None else "—",
         "yes" if (g("aridite") or 1) <= 0.05 else "part"),
        ("Daily swing", "Ground swings by ≈ 56 to 87 K", f"{g('amplitude_k'):.0f} K" if g("amplitude_k") is not None else "—", "no"),
        ("Temperature", "Far below freezing on average", f"Mean surface {g('temp_moy_c'):.1f} °C" if g("temp_moy_c") is not None else "—",
         "no" if (g("temp_moy_c") or 0) > -15 else "part"),
        ("Gravity, air, radiation", "0.38 g, ≈ 6.4 hPa CO₂, no magnetic shield", "1 g, ≈ 1,000 hPa, magnetic field", "no"),
    ]
    V = {"yes": ("✓ Strong", "#2e9e5b"), "part": ("~ Partial", "#f2b134"), "no": ("✗ Breaks down", "#e03b2e")}
    body = "".join(f"<tr><td style='color:#9aa4b1'>{d}</td><td>{j}</td><td>{e}</td>"
                   f"<td style='color:{V[v][1]};white-space:nowrap'><b>{V[v][0]}</b></td></tr>" for d, j, e, v in rows)
    st.markdown(f"<table class='cmp'><tr><th>Dimension</th><th>Jezero (Mars)</th><th>Site #{rk}"
                + (f" · {where}" if where else "") + f"</th><th>Analogy</th></tr>{body}</table>", unsafe_allow_html=True)
    nv = pd.Series([v for *_, v in rows]).value_counts()
    st.caption(f"{nv.get('yes', 0)} strong, {nv.get('part', 0)} partial, {nv.get('no', 0)} where the analogy breaks down. "
               "Site values: MODIS, TerraClimate, MERIT DEM and ASTER, computed in Google Earth Engine.")

    # Process
    st.markdown("---")
    st.markdown("### Same story, different planet")
    st.markdown("<p class='lead'>The challenge asks to think about processes as well as places. Jezero and site #4 share "
                "one: a lake in a closed basin that dried out and left clays and salts behind.</p>", unsafe_allow_html=True)
    cols = st.columns(3)
    for col, (h, mars, earth) in zip(cols, PROCESS):
        col.markdown(f"<div class='step'><div class='h'>{h}</div>"
                     f"<div class='n' style='margin-top:6px'>Jezero, billions of years ago</div><div class='p'>{mars}</div>"
                     f"<div class='n' style='margin-top:10px'>Site #4, Puna, today</div><div class='p'>{earth}</div></div>",
                     unsafe_allow_html=True)
    st.markdown("")
    st.markdown("**Why it matters for exploration:** the clays and salts left by a drying lake are where Perseverance looks "
                "for signs of past life. Site #4 lets teams study how such deposits form and what they preserve, "
                "with instruments and methods they can then use on Mars.")

    st.markdown("---")
    st.markdown("**Sources for Mars**")
    st.markdown("\n".join(f"{i + 1}. [{SRC[k][0]}]({SRC[k][1]})" for i, k in enumerate(used)))