"""Interfaz: subir la hoja de cálculo de posts y orquestar la exportación de
comentarios vía ExportComments."""
import io
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

import charts
import consolidate as cons
import orchestrator as orc
import report as rep
import run_analysis as ra
import spreadsheet_reader as sr
import topic_classifier as tc
import ipds

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(PROJECT_DIR, "input")
RUNS_DIR = os.path.join(PROJECT_DIR, "runs")
UPLOADS_DIR = os.path.join(PROJECT_DIR, "uploads")

os.makedirs(RUNS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
UPLOADED_BASE_FILENAME = "base_comentarios.xlsx"
FINISHED_STATUSES = {"done", "error", "timeout", "skipped"}

STATUS_LABELS = {
    "pending": "Pendiente",
    "creating": "Creando",
    "queueing": "En cola",
    "progress": "En progreso",
    "done": "Completado",
    "error": "Error",
    "timeout": "Tiempo agotado",
    "skipped": "Omitido",
}

COLUMN_LABELS = {
    "link": "Link",
    "network": "Red",
    "status": "Estado",
    "total": "Comentarios",
    "total_exported": "Comentarios recolectados",
    "error": "Error",
    "file_name": "Archivo",
}


def display_status(item):
    """Etiqueta de estado para mostrar en la interfaz. Para items con
    status=="error" distingue entre falla al crear el job, posts sin
    comentarios y posts eliminados/no disponibles, en vez de mostrar
    siempre "Error"."""
    status = item["status"]
    if status != "error":
        return STATUS_LABELS.get(status, status)

    error = item.get("error") or ""
    if item.get("guid") is None:
        return STATUS_LABELS["error"]
    if "No comments have been found" in error or "No comments have been received" in error:
        return "Sin comentarios"
    if "404 Client Error" in error and "/exports/" in error:
        return "Sin comentarios"
    if "Cannot access specified post" in error or "Video unavailable" in error:
        return "Post eliminado o no disponible"
    return STATUS_LABELS["error"]

ANALYSIS_STAGE_LABELS = {
    "consolidando": "Consolidando comentarios exportados...",
    "cargando_modelo": "Cargando modelo de análisis de sentimiento...",
    "analizando_sentimiento": "Pausa para el café... Seguiremos analizando tus datos mientras tanto.",
    "generando_reporte": "Generando reporte...",
    "completado": "Completado",
    "error": "Error",
}

REPORT_COLUMN_LABELS = rep.COLUMN_LABELS
CORRECTED_FILENAME = "analisis_sentimiento_corregido.xlsx"


@st.cache_data
def load_report_data(report_path, mtime):
    return pd.read_excel(report_path, sheet_name="Comentarios")


@st.cache_data
def build_wordcloud_image(report_path, mtime, red=None, sentimiento=None, marca=None, colormap=None):
    df = load_report_data(report_path, mtime)
    if red:
        df = df[df["Red"] == red]
    if sentimiento:
        df = df[df["Sentimiento"] == sentimiento]
    if marca:
        df = df[df["Marca"] == marca]
    return charts.wordcloud_image(df["Comentario"].dropna(), colormap=colormap)


@st.cache_data
def get_tagged_texts(report_path, mtime, tag_version="1"):
    """POS-tagging de todos os comentários — cacheia por dataset, não por frase."""
    df = load_report_data(report_path, mtime)
    return charts.tag_texts_for_wordtree(df["Comentario"].dropna().tolist())


@st.cache_data
def build_word_tree_data(report_path, mtime, root_phrase, tree_version="1"):
    df = load_report_data(report_path, mtime)
    tagged = get_tagged_texts(report_path, mtime, tag_version=tree_version)
    valid = df["Comentario"].notna()
    full_texts = df.loc[valid, "Comentario"].tolist()
    likes_col = df.loc[valid, "Likes"].fillna(0).tolist() if "Likes" in df.columns else None
    sent_col = df.loc[valid, "Sentimiento"].tolist() if "Sentimiento" in df.columns else None
    return charts.build_word_tree(tagged, root_phrase, full_texts=full_texts,
                                  likes=likes_col, sentiments=sent_col)


def render_sentiment_dashboard(active_path, mtime, key_prefix, show_brand_comparison=False,
                               brand_mapping=None):
    df = load_report_data(active_path, mtime)

    if brand_mapping and "Marca" in df.columns:
        _lower_map = {}
        for profile, desired in brand_mapping.items():
            _lower_map[profile.strip().lower()] = desired
            auto = cons.normalize_brand(profile)
            if auto:
                _lower_map[auto.lower()] = desired
        df["Marca"] = df["Marca"].apply(
            lambda m: _lower_map.get(str(m).strip().lower(), m) if pd.notna(m) else m
        )

    total = len(df)
    counts = df["Sentimiento"].value_counts()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Comentarios analizados", total)
    _sent_html = (
        '<div style="text-align:center">'
        '<p style="font-size:0.85rem;color:#666;margin:0">{label}</p>'
        '<p style="font-size:1.8rem;font-weight:700;color:{color};margin:0">{value}</p>'
        '</div>'
    )
    col2.markdown(_sent_html.format(label="Positivo", color="#2ecc71",
                  value=int(counts.get("Positivo", 0))), unsafe_allow_html=True)
    col3.markdown(_sent_html.format(label="Neutral", color="#95a5a6",
                  value=int(counts.get("Neutral", 0))), unsafe_allow_html=True)
    col4.markdown(_sent_html.format(label="Negativo", color="#e74c3c",
                  value=int(counts.get("Negativo", 0))), unsafe_allow_html=True)

    chart_df = df.rename(columns={v: k for k, v in REPORT_COLUMN_LABELS.items()})

    col1, col2 = st.columns(2)
    col1.plotly_chart(charts.donut_sentiment(chart_df), use_container_width=True)
    col2.plotly_chart(charts.bar_by_network(chart_df), use_container_width=True)

    time_fig = charts.line_over_time(chart_df)
    if time_fig is not None:
        st.plotly_chart(time_fig, use_container_width=True)

    time_by_network_fig = charts.line_over_time_by_network(chart_df)
    if time_by_network_fig is not None:
        st.plotly_chart(time_by_network_fig, use_container_width=True)

    # ── Clasificación por tema ────────────────────────────────────────────
    st.subheader("Análisis por tema")
    dict_options = tc.available_dictionaries()
    dict_labels = [name for _, name in dict_options]
    dict_keys = [k for k, _ in dict_options]
    selected_dict_label = st.selectbox(
        "Diccionario de temas", dict_labels,
        key="{}_dict_select".format(key_prefix),
    )
    selected_dict_key = dict_keys[dict_labels.index(selected_dict_label)]
    st.session_state["selected_dict_key"] = selected_dict_key

    chart_df["tema"] = tc.classify_series(
        chart_df["comentario"].fillna(""), selected_dict_key)

    total_classified = (chart_df["tema"] != "Otros").sum()
    total_otros = (chart_df["tema"] == "Otros").sum()
    pct_classified = round(total_classified / len(chart_df) * 100) if len(chart_df) else 0
    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("Clasificados", "{} ({}%)".format(total_classified, pct_classified))
    mc2.metric("Sin tema (Otros)", total_otros)
    mc3.metric("Temas detectados", chart_df[chart_df["tema"] != "Otros"]["tema"].nunique())

    tema_chart = st.radio(
        "Visualización", ["Temas × Sentimiento", "Prioridad", "Temas × Red"],
        horizontal=True, key="{}_tema_chart".format(key_prefix),
    )
    if tema_chart == "Temas × Sentimiento":
        fig = charts.bubble_matrix_tema_sentimiento(chart_df)
    elif tema_chart == "Prioridad":
        fig = charts.bubble_prioridad(chart_df)
    else:
        fig = charts.heatmap_tema_red(chart_df)
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)

    if total_otros > 0:
        with st.expander("Explorar comentarios sin tema (Otros) — {} comentarios".format(total_otros)):
            otros_df = chart_df[chart_df["tema"] == "Otros"]
            otros_words = charts.top_words(otros_df["comentario"].dropna(), n=30)
            if otros_words:
                st.caption("Palabras más frecuentes en comentarios sin clasificar:")
                word_labels = ["{} ({})".format(w, c) for w, c in otros_words]
                sel_otros = st.pills(
                    "Haz clic para ver ejemplos", word_labels,
                    key="{}_otros_pill".format(key_prefix),
                )
                if sel_otros:
                    w = sel_otros.split(" (")[0]
                    examples = otros_df[otros_df["comentario"].str.lower().str.contains(w, na=False)]
                    if "likes" in examples.columns:
                        examples = examples.sort_values("likes", ascending=False)
                    st.dataframe(
                        examples[["comentario"]].head(10).rename(columns={"comentario": "Comentario"}),
                        hide_index=True, use_container_width=True,
                    )

    networks = sorted(df["Red"].dropna().unique().tolist())

    st.subheader("Nube de palabras por red")
    wc_cols = st.columns(2)
    for i, red in enumerate(networks):
        img = build_wordcloud_image(active_path, mtime, red=red)
        with wc_cols[i % 2]:
            st.caption(red)
            if img is not None:
                st.image(img, use_container_width=True)
            else:
                st.caption("No hay suficiente texto para generar la nube.")

    cloud_words = charts.top_words(df["Comentario"].dropna(), n=50)
    if cloud_words:
        word_labels = ["{} ({})".format(w, c) for w, c in cloud_words]
        selected_pill = st.pills(
            "Haz clic en una palabra para ver los comentarios",
            word_labels, key="{}_wc_pill".format(key_prefix),
        )
        if selected_pill:
            word = selected_pill.split(" (")[0]
            matches = df[df["Comentario"].str.lower().str.contains(word, na=False)]
            if not matches.empty:
                fcol1, fcol2 = st.columns(2)
                red_opts = ["Todas"] + sorted(matches["Red"].dropna().unique().tolist()) if "Red" in matches.columns else ["Todas"]
                sent_opts = ["Todos"] + charts.SENTIMENT_ORDER
                sel_r = fcol1.selectbox("Red", red_opts, key="{}_wc_red_f".format(key_prefix))
                sel_s = fcol2.selectbox("Sentimiento", sent_opts, key="{}_wc_sent_f".format(key_prefix))

                if sel_r != "Todas" and "Red" in matches.columns:
                    matches = matches[matches["Red"] == sel_r]
                if sel_s != "Todos" and "Sentimiento" in matches.columns:
                    matches = matches[matches["Sentimiento"] == sel_s]

                if "Likes" in matches.columns:
                    matches = matches.sort_values("Likes", ascending=False)
                top = matches.head(10)
                show = [c for c in ["Red", "Marca", "Autor", "Comentario", "Likes", "Sentimiento"]
                        if c in top.columns]
                if "Link del post" in top.columns:
                    show.append("Link del post")
                st.caption("{} comentarios con '{}' — mostrando top 10:".format(len(matches), word))

                def _color_sent(val):
                    return {"Positivo": "color: #2ecc71; font-weight: bold",
                            "Negativo": "color: #e74c3c; font-weight: bold",
                            "Neutral": "color: #95a5a6"}.get(val, "")

                styled = top[show].style.map(_color_sent, subset=["Sentimiento"]) if "Sentimiento" in top.columns else top[show]
                st.dataframe(
                    styled, hide_index=True, use_container_width=True,
                    column_config={
                        "Link del post": st.column_config.LinkColumn("Link", display_text="🔗", width="small"),
                    },
                )
            else:
                st.caption("No se encontraron comentarios con '{}'.".format(word))

    st.subheader("Nube de palabras por sentimiento")
    network_options = ["Todas"] + networks
    selected_network = st.selectbox(
        "Red", network_options, key="wc_red_{}".format(key_prefix)
    )
    red_filter = None if selected_network == "Todas" else selected_network

    wc_sent_cols = st.columns(3)
    for col, sentimiento in zip(wc_sent_cols, charts.SENTIMENT_ORDER):
        img = build_wordcloud_image(
            active_path, mtime, red=red_filter, sentimiento=sentimiento,
            colormap=charts.SENTIMENT_COLORMAPS[sentimiento],
        )
        with col:
            st.caption(sentimiento)
            if img is not None:
                st.image(img, use_container_width=True)
            else:
                st.caption("No hay suficiente texto para generar la nube.")

    st.subheader("Árbol de palabras")
    st.caption(
        "Escribe una palabra o frase y descubre cómo la continúan los "
        "comentarios. Las ramas más gruesas y los textos más grandes "
        "indican continuaciones más frecuentes."
    )
    root_phrase = st.text_input(
        "Palabra o frase", key="wordtree_root_{}".format(key_prefix)
    )
    if root_phrase.strip():
        tree_data = build_word_tree_data(active_path, mtime, root_phrase, charts.WORD_TREE_VERSION)
        if tree_data is None:
            st.caption("No se encontraron comentarios con esa palabra o frase.")
        else:
            components.html(
                charts.word_tree_html(tree_data, width=1400),
                height=charts.word_tree_height(tree_data),
            )

    st.subheader("Comentarios más interactuados")
    if df["Likes"].notna().any():
        filter_cols = st.columns(2)
        marcas_disp = sorted(df["Marca"].dropna().unique().tolist()) if "Marca" in df.columns else []
        redes_disp = sorted(df["Red"].dropna().unique().tolist()) if "Red" in df.columns else []
        sel_marca = filter_cols[0].multiselect(
            "Marca", marcas_disp, default=marcas_disp,
            key="{}_interacted_marca".format(key_prefix),
        ) if marcas_disp else marcas_disp
        sel_red = filter_cols[1].multiselect(
            "Red", redes_disp, default=redes_disp,
            key="{}_interacted_red".format(key_prefix),
        ) if redes_disp else redes_disp

        filtered = df.dropna(subset=["Likes"])
        if sel_marca and "Marca" in filtered.columns:
            filtered = filtered[filtered["Marca"].isin(sel_marca)]
        if sel_red and "Red" in filtered.columns:
            filtered = filtered[filtered["Red"].isin(sel_red)]

        top_liked = filtered.sort_values("Likes", ascending=False).head(10)
        show_cols = [
            c for c in ["Red", "Marca", "Autor", "Comentario", "Likes", "Sentimiento"]
            if c in top_liked.columns
        ]
        if "Link del post" in top_liked.columns:
            show_cols.append("Link del post")
        st.dataframe(
            top_liked[show_cols], hide_index=True, use_container_width=True,
            column_config={
                "Link del post": st.column_config.LinkColumn(
                    "Link", display_text="🔗", width="small",
                ),
            },
        )
    else:
        st.caption("No hay datos de likes disponibles.")

    st.subheader("Principales detractores y brand lovers")
    st.caption(
        "Usuarios que más veces comentaron con sentimiento negativo "
        "(detractores) o positivo (brand lovers)."
    )
    with_author = df.dropna(subset=["Autor"]) if "Autor" in df.columns else df.iloc[0:0]
    if not with_author.empty and "Marca" in with_author.columns:
        if brand_mapping:
            own_names = set()
            for profile, brand in brand_mapping.items():
                own_names.add(profile.lower())
                if brand:
                    own_names.add(brand.lower())
            own_account = with_author["Autor"].apply(
                lambda a: str(a).strip().lower() in own_names
            )
        else:
            own_account = with_author.apply(
                lambda r: cons.normalize_brand(r["Autor"]) == r["Marca"], axis=1
            )
        with_author = with_author[~own_account]
    det_col, lover_col = st.columns(2)

    with det_col:
        st.markdown("**Principales detractores**")
        negativos = with_author[with_author["Sentimiento"] == "Negativo"]
        if not negativos.empty:
            top_neg = (
                negativos.groupby("Autor").size()
                .reset_index(name="Comentarios negativos")
                .sort_values("Comentarios negativos", ascending=False)
                .head(10)
            )
            st.dataframe(top_neg, hide_index=True, use_container_width=True)
        else:
            st.caption("No hay comentarios negativos con autor identificado.")

    with lover_col:
        st.markdown("**Principales brand lovers**")
        positivos = with_author[with_author["Sentimiento"] == "Positivo"]
        if not positivos.empty:
            top_pos = (
                positivos.groupby("Autor").size()
                .reset_index(name="Comentarios positivos")
                .sort_values("Comentarios positivos", ascending=False)
                .head(10)
            )
            st.dataframe(top_pos, hide_index=True, use_container_width=True)
        else:
            st.caption("No hay comentarios positivos con autor identificado.")

    st.subheader("Posts con más comentarios por mes")
    with_post_date = df.copy()
    with_post_date["Mes"] = pd.to_datetime(with_post_date["Fecha de publicación"], errors="coerce").dt.to_period("M").astype(str)
    with_post_date = with_post_date[with_post_date["Mes"] != "NaT"]
    if not with_post_date.empty:
        group_cols = [c for c in ["Mes", "Red", "Marca", "Link del post"] if c in with_post_date.columns]
        by_post = with_post_date.groupby(group_cols).size().reset_index(name="Comentarios")
        top_posts = (
            by_post.sort_values(["Mes", "Comentarios"], ascending=[True, False])
            .groupby("Mes").head(5)
            .reset_index(drop=True)
        )
        st.dataframe(top_posts, hide_index=True, use_container_width=True)
    else:
        st.caption("No hay fechas de publicación disponibles.")

    if show_brand_comparison and "Marca" in df.columns:
        marcas = sorted(df["Marca"].dropna().unique().tolist())
        if len(marcas) > 1:
            st.subheader("Comparación por marca")

            st.plotly_chart(charts.bar_by_brand(chart_df), use_container_width=True)

            time_by_brand_fig = charts.line_over_time_by_brand(chart_df)
            if time_by_brand_fig is not None:
                st.plotly_chart(time_by_brand_fig, use_container_width=True)

            st.markdown("**Nube de palabras por marca**")
            sel_marca_wc = st.selectbox(
                "Marca", marcas, key="{}_wc_marca_select".format(key_prefix),
            )
            marca_texts = df[df["Marca"] == sel_marca_wc]["Comentario"].dropna()
            img = charts.wordcloud_image(marca_texts) if not marca_texts.empty else None
            if img is not None:
                st.image(img, use_container_width=True)
            else:
                st.caption("No hay suficiente texto para generar la nube.")


os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(RUNS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

LOGO_PATH = os.path.join(PROJECT_DIR, "assets", "wiper-isologo.png")

st.set_page_config(
    page_title="Wiper · Análisis de redes sociales",
    layout="wide",
    page_icon=LOGO_PATH if os.path.exists(LOGO_PATH) else None,
)


def _check_password():
    pwd = st.secrets.get("PASSWORD") or os.environ.get("PASSWORD", "")
    if not pwd:
        return True
    if st.session_state.get("authenticated"):
        return True
    col = st.columns([1, 1, 1])[1]
    with col:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=120)
        with st.form("login"):
            st.markdown("#### Acceso restringido")
            entered = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                if entered == pwd:
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta.")
    return False


if not _check_password():
    st.stop()


st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; max-width: 1400px; }
    div[data-testid="stMetric"] {
        background-color: #EAEAED;
        border: 1px solid #8B9297;
        border-radius: 0.5rem;
        padding: 0.75rem 1rem;
    }
    div[data-testid="stImage"] img {
        border-radius: 0 !important;
    }
    div[data-testid="stTabs"] button[data-baseweb="tab"]:nth-child(1) p {
        color: #09B7E9;
        font-weight: 600;
    }
    div[data-testid="stTabs"] button[data-baseweb="tab"]:nth-child(2) p {
        color: #A73253;
        font-weight: 600;
    }
    .st-key-delete_run_button button[kind="primary"] {
        background-color: #A73253;
        border-color: #A73253;
        color: #FFFFFF;
    }
    .st-key-delete_run_button button[kind="primary"]:hover {
        background-color: #8E2A44;
        border-color: #8E2A44;
        color: #FFFFFF;
    }
    .st-key-delete_run_button button[kind="primary"]:disabled {
        background-color: #A73253;
        border-color: #A73253;
        color: #FFFFFF;
        opacity: 0.4;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def _load_logo(path, pad_y=8):
    img = Image.open(path).convert("RGBA")
    padded = Image.new("RGBA", (img.width, img.height + pad_y * 2), (0, 0, 0, 0))
    padded.paste(img, (0, pad_y), img)
    return padded


col_logo, col_title = st.columns([1, 6])
if os.path.exists(LOGO_PATH):
    col_logo.image(_load_logo(LOGO_PATH), width=80)
with col_title:
    st.title("Análisis de redes sociales")
    st.caption("Exportación de comentarios y análisis de sentimiento · Wiper Agency")


def list_runs():
    if not os.path.isdir(RUNS_DIR):
        return []
    runs = []
    for name in sorted(os.listdir(RUNS_DIR), reverse=True):
        run_dir = os.path.join(RUNS_DIR, name)
        if os.path.isfile(orc.state_path(run_dir)):
            runs.append(name)
    return runs


def is_running(run_dir):
    return os.path.exists(os.path.join(run_dir, "running.flag"))


def launch_subprocess(script_name, run_dir, extra_args=None):
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    args = [sys.executable, os.path.join(PROJECT_DIR, script_name), run_dir]
    if extra_args:
        args.extend(extra_args)
    subprocess.Popen(
        args,
        cwd=PROJECT_DIR,
        creationflags=creationflags,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def launch_run(run_dir):
    launch_subprocess("run_export.py", run_dir)


def launch_analysis(run_dir, engine="local"):
    launch_subprocess("run_analysis.py", run_dir, extra_args=[engine])


def make_zip_bytes(run_dir):
    buf = io.BytesIO()
    files_dir = orc.files_dir(run_dir)
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in sorted(os.listdir(files_dir)):
            zf.write(os.path.join(files_dir, fname), fname)
    buf.seek(0)
    return buf.getvalue()


@st.cache_data
def make_zip_bytes_cached(run_dir, done_count):
    return make_zip_bytes(run_dir)


def format_duration(seconds):
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return "{}h {}min".format(h, m)
    if m:
        return "{}min {}s".format(m, s)
    return "{}s".format(s)


tab_export, tab_runs, tab_analysis, tab_clasif, tab_ipds = st.tabs(
    ["Nueva exportación", "Ejecuciones", "Análisis", "Clasificación", "IPD-S"]
)

_COL_DETECT = {
    "link": {"link", "url", "enlace", "post_url", "link del post"},
    "network": {"network", "red", "red social", "plataforma", "platform"},
    "profile": {"profile", "perfil", "marca", "cuenta", "brand", "account"},
    "date": {"date", "fecha", "fecha de publicación", "published"},
}


def _auto_col(field, columns):
    for c in columns:
        if c.strip().lower() in _COL_DETECT.get(field, set()):
            return c
    return None


with tab_export:
    if "uploader_key" not in st.session_state:
        st.session_state["uploader_key"] = 0

    uploaded = st.file_uploader(
        "Hoja de cálculo de posts (.xlsx, .csv)", type=["xlsx", "csv"],
        key="uploader_{}".format(st.session_state["uploader_key"]),
    )

    if uploaded is not None:
        if st.button("Limpiar selección"):
            st.session_state["uploader_key"] += 1
            st.rerun()

        save_path = os.path.join(INPUT_DIR, uploaded.name)
        with open(save_path, "wb") as f:
            f.write(uploaded.getbuffer())

        try:
            raw_df = sr.read_raw_file(save_path)
            columns = raw_df.columns.tolist()
        except Exception as e:
            st.error("Error al leer el archivo: {}".format(e))
            raw_df = None
            columns = []

        if raw_df is not None and columns:
            st.caption("Mapea las columnas de tu archivo:")
            none_opt = "(no disponible)"
            opt_cols = [none_opt] + columns

            mc1, mc2 = st.columns(2)
            auto_link = _auto_col("link", columns)
            col_link = mc1.selectbox(
                "Link del post (requerido)", columns,
                index=columns.index(auto_link) if auto_link else 0,
                key="map_link",
            )
            col_net = mc2.selectbox(
                "Red social", opt_cols,
                index=opt_cols.index(_auto_col("network", columns) or none_opt),
                key="map_network",
            )
            col_profile = mc1.selectbox(
                "Perfil / Marca", opt_cols,
                index=opt_cols.index(_auto_col("profile", columns) or none_opt),
                key="map_profile",
            )
            col_date = mc2.selectbox(
                "Fecha de publicación", opt_cols,
                index=opt_cols.index(_auto_col("date", columns) or none_opt),
                key="map_date",
            )

            mapping = {"link": col_link}
            if col_net != none_opt:
                mapping["network"] = col_net
            if col_profile != none_opt:
                mapping["profile"] = col_profile
            if col_date != none_opt:
                mapping["date"] = col_date

            try:
                links_df = sr.read_with_mapping(save_path, mapping)
            except Exception as e:
                st.error("Error al procesar: {}".format(e))
                links_df = None

            if links_df is not None:
                st.success("{} links encontrados".format(len(links_df)))
                if "network" in links_df.columns:
                    counts = (links_df["network"].value_counts()
                              .rename_axis("Red").reset_index(name="Cantidad"))
                    st.dataframe(counts, hide_index=True, use_container_width=True)
                st.dataframe(links_df.head(20), use_container_width=True)

                if st.button("Iniciar exportación", type="primary"):
                    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                    run_dir = os.path.join(RUNS_DIR, run_id)
                    orc.init_run(run_dir, links_df, source_file=save_path,
                                 column_mapping=mapping)
                    launch_run(run_dir)
                    st.session_state["active_run"] = run_id
                    st.rerun()


with tab_runs:
    runs = list_runs()
    if not runs:
        st.info("Aún no hay ejecuciones.")
    else:
        active_run = st.session_state.get("active_run")
        default_index = runs.index(active_run) if active_run in runs else 0
        selected_run = st.selectbox("Ejecución", runs, index=default_index)
        run_dir = os.path.join(RUNS_DIR, selected_run)

        with st.expander("Eliminar esta ejecución"):
            st.warning(
                "Esto borrará permanentemente todos los archivos de la ejecución "
                "'{}' (exportaciones, estado y análisis). Esta acción no se "
                "puede deshacer.".format(selected_run)
            )
            run_active = is_running(run_dir) or ra.is_analysis_running(run_dir)
            if run_active:
                st.caption("No se puede eliminar mientras la exportación o el análisis están en ejecución.")
            confirm_delete = st.checkbox(
                "Sí, quiero eliminar esta ejecución",
                key="confirm_delete_{}".format(selected_run),
                disabled=run_active,
            )
            with st.container(key="delete_run_button"):
                if st.button("Eliminar ejecución", disabled=not confirm_delete or run_active, type="primary"):
                    shutil.rmtree(run_dir)
                    st.session_state.pop("active_run", None)
                    st.rerun()

        _status_refresh = "5s" if is_running(run_dir) else None

        @st.fragment(run_every=_status_refresh)
        def render_run_status(run_dir, run_name):
            state = orc.load_state(run_dir)
            items = state["items"]
            total = len(items)

            status_counts = pd.Series([item["status"] for item in items]).value_counts()
            finished = sum(int(status_counts.get(s, 0)) for s in FINISHED_STATUSES)
            pending = int(status_counts.get("pending", 0))
            running = is_running(run_dir)

            col1, col2, col3 = st.columns(3)
            col1.metric("Total de links", total)
            col2.metric("Completados", finished)
            col3.metric("Proceso", "En ejecución" if running else "Detenido")

            st.progress(finished / total if total else 0)

            durations = []
            for item in items:
                if item["status"] in FINISHED_STATUSES and item.get("started_at") and item.get("updated_at"):
                    start = datetime.fromisoformat(item["started_at"])
                    end = datetime.fromisoformat(item["updated_at"])
                    durations.append((end - start).total_seconds())

            if durations and pending:
                avg = sum(durations) / len(durations)
                eta = avg * pending
                st.caption(
                    "Tiempo promedio por link: {} · Tiempo restante estimado: {} ({} pendientes)".format(
                        format_duration(avg), format_duration(eta), pending
                    )
                )

            display_counts = pd.Series([display_status(item) for item in items]).value_counts()
            status_table = display_counts.rename_axis("Estado").reset_index(name="Cantidad")
            st.dataframe(status_table, hide_index=True, use_container_width=True)

            if running:
                if st.button("Detener", key="stop_{}".format(run_name)):
                    open(orc.stop_flag_path(run_dir), "w").close()
                    st.rerun()
            elif finished < total:
                if st.button("Continuar", key="resume_{}".format(run_name)):
                    stop_path = orc.stop_flag_path(run_dir)
                    if os.path.exists(stop_path):
                        os.remove(stop_path)
                    launch_run(run_dir)
                    st.rerun()

            failed_jobs = [item for item in items if item["status"] == "error" and item.get("guid") is None]
            if failed_jobs:
                st.caption("{} link(s) no pudieron crear el job de exportación.".format(len(failed_jobs)))
                if st.button(
                    "🔁 Reintentar links con error al crear job",
                    key="retry_failed_{}".format(run_name),
                    disabled=running,
                ):
                    for item in failed_jobs:
                        item["status"] = "pending"
                        item["error"] = None
                        item["attempts"] = 0
                        item["started_at"] = None
                        item["updated_at"] = None
                    orc.save_state(run_dir, state)
                    stop_path = orc.stop_flag_path(run_dir)
                    if os.path.exists(stop_path):
                        os.remove(stop_path)
                    launch_run(run_dir)
                    st.rerun()

            with st.expander("Detalles por link"):
                df = pd.DataFrame(items)
                cols = [c for c in COLUMN_LABELS if c in df.columns]
                df = df[cols].rename(columns=COLUMN_LABELS)
                df["Estado"] = [display_status(item) for item in items]

                comentarios_col = COLUMN_LABELS["total"]
                recolectados_col = COLUMN_LABELS["total_exported"]
                totals_row = {c: "" for c in df.columns}
                totals_row[COLUMN_LABELS["link"]] = "Total"
                if comentarios_col in df.columns:
                    totals_row[comentarios_col] = pd.to_numeric(df[comentarios_col], errors="coerce").sum()
                if recolectados_col in df.columns:
                    totals_row[recolectados_col] = pd.to_numeric(df[recolectados_col], errors="coerce").sum()
                df = pd.concat([df, pd.DataFrame([totals_row])], ignore_index=True)

                st.dataframe(df, use_container_width=True)

        render_run_status(run_dir, selected_run)

        # ── Definir marcas ──────────────────────────────────────────────────
        _state = orc.load_state(run_dir)
        _profiles = sorted({
            item.get("profile", "") for item in _state["items"]
            if item.get("profile")
        })
        if _profiles:
            _saved = _state.get("brand_mapping", {})
            _expanded = not _saved
            with st.expander("Definir nombres de marca", expanded=_expanded):
                st.caption(
                    "Cada perfil de red social se asignará a la marca que definas aquí. "
                    "Guarda antes de generar el análisis."
                )
                with st.form("brand_mapping_{}".format(selected_run)):
                    cols = st.columns(2)
                    _mapping = {}
                    for idx, profile in enumerate(_profiles):
                        default = _saved.get(profile) or cons.normalize_brand(profile) or profile
                        _mapping[profile] = cols[idx % 2].text_input(
                            profile, value=default,
                            key="bm_{}_{}".format(selected_run, profile),
                        )
                    if st.form_submit_button("Guardar marcas", type="primary"):
                        _state["brand_mapping"] = {
                            p: v.strip() or cons.normalize_brand(p)
                            for p, v in _mapping.items()
                        }
                        orc.save_state(run_dir, _state)
                        st.success("Marcas guardadas.")

        _dl_refresh = "3s" if is_running(run_dir) else None

        @st.fragment(run_every=_dl_refresh)
        def render_run_downloads(run_dir, run_name):
            state = orc.load_state(run_dir)
            done_count = sum(1 for item in state["items"] if item["status"] == "done")

            if done_count == 0:
                return

            zip_bytes = make_zip_bytes_cached(run_dir, done_count)
            dl_col, analyze_col = st.columns(2)
            dl_col.download_button(
                "Descargar resultados (ZIP)",
                data=zip_bytes,
                file_name="export_{}.zip".format(run_name),
                mime="application/zip",
            )
            with analyze_col:
                if st.button("Analizar ahora →", key="go_analyze_{}".format(run_name),
                             type="primary"):
                    st.session_state["analyze_run"] = run_name

            if st.session_state.get("analyze_run") == run_name:
                st.info("Ve a la pestaña **Análisis** para ver el dashboard.")

        render_run_downloads(run_dir, selected_run)


def _runs_with_exports():
    """Retorna runs que tienen al menos 1 link exportado."""
    result = []
    for name in list_runs():
        rd = os.path.join(RUNS_DIR, name)
        state = orc.load_state(rd)
        if any(i["status"] == "done" for i in state["items"]):
            result.append(name)
    return result


with tab_analysis:
    source = st.radio(
        "Fuente de datos",
        ["Ejecución exportada", "Subir base propia"],
        horizontal=True,
        key="analysis_source",
    )

    if source == "Ejecución exportada":
        run_options = _runs_with_exports()
        if not run_options:
            st.info("No hay ejecuciones con datos exportados.")
        else:
            default_run = st.session_state.get("analyze_run")
            default_idx = run_options.index(default_run) if default_run in run_options else 0
            selected = st.selectbox("Ejecución", run_options, index=default_idx,
                                    key="analysis_run_select")
            run_dir = os.path.join(RUNS_DIR, selected)

            _analysis_refresh = "3s" if ra.is_analysis_running(run_dir) else None

            @st.fragment(run_every=_analysis_refresh)
            def render_analysis(run_dir, run_name):
                state = orc.load_state(run_dir)
                done_count = sum(1 for item in state["items"] if item["status"] == "done")

                st.caption("{} post(s) con comentarios exportados.".format(done_count))

                running = ra.is_analysis_running(run_dir)
                analysis_state = ra.load_analysis_state(run_dir)

                if running:
                    stage = (analysis_state or {}).get("stage", "consolidando")
                    st.caption(ANALYSIS_STAGE_LABELS.get(stage, stage))
                    if stage == "analizando_sentimiento" and analysis_state.get("total"):
                        processed = analysis_state.get("processed", 0)
                        total = analysis_state["total"]
                        st.progress(processed / total if total else 0)
                        st.caption("{}/{} comentarios".format(processed, total))
                    else:
                        st.progress(0)
                else:
                    label = "Generar análisis"
                    if analysis_state and analysis_state.get("stage") == "completado":
                        label = "Regenerar análisis"

                    use_ai = st.checkbox(
                        "Usar análisis con IA (Claude Haiku)",
                        key="use_ai_analysis_{}".format(run_name),
                        help=(
                            "Analiza cada comentario con Claude (Anthropic) en lugar del "
                            "modelo local. Suele entender mejor el sarcasmo, la jerga y "
                            "el contexto, pero tiene un costo por uso de la API y requiere "
                            "ANTHROPIC_API_KEY configurada."
                        ),
                    )

                    if st.button(label, key="analyze_btn_{}".format(run_name), type="primary"):
                        launch_analysis(run_dir, "ai" if use_ai else "local")
                        st.rerun()

                    if analysis_state and analysis_state.get("stage") == "error":
                        st.error("Error al generar el análisis: {}".format(
                            analysis_state.get("error")))

                if analysis_state and analysis_state.get("stage") == "completado":
                    engine_label = ("IA (Claude Haiku)" if analysis_state.get("engine") == "ai"
                                    else "modelo local (pysentimiento)")
                    st.caption("Análisis generado con: {}".format(engine_label))

                    report_path = os.path.join(run_dir, analysis_state["report_file"])
                    corrected_path = os.path.join(run_dir, CORRECTED_FILENAME)

                    with st.expander("Base corregida manualmente"):
                        if os.path.exists(corrected_path):
                            st.success("Usando la base corregida que subiste manualmente.")
                            if st.button("Quitar base corregida",
                                         key="remove_corrected_a_{}".format(run_name)):
                                os.remove(corrected_path)
                                st.rerun()
                        else:
                            st.caption(
                                "Descarga el XLSX de abajo, corrige a mano la columna "
                                "'Sentimiento' y vuelve a subirlo aquí."
                            )

                        uploader_key_name = "corrected_upload_key_a_{}".format(run_name)
                        if uploader_key_name not in st.session_state:
                            st.session_state[uploader_key_name] = 0

                        uploaded_corrected = st.file_uploader(
                            "Subir XLSX corregido", type=["xlsx"],
                            key="corrected_a_{}_{}".format(
                                run_name, st.session_state[uploader_key_name]),
                        )
                        if uploaded_corrected is not None:
                            try:
                                test_df = pd.read_excel(
                                    uploaded_corrected, sheet_name="Comentarios")
                            except Exception as e:
                                st.error("Error al leer el archivo: {}".format(e))
                                test_df = None

                            if test_df is not None:
                                required = {"Red", "Sentimiento", "Comentario"}
                                if not required.issubset(test_df.columns):
                                    st.error(
                                        "El archivo debe tener una hoja 'Comentarios' con "
                                        "al menos las columnas: Red, Sentimiento, Comentario."
                                    )
                                else:
                                    with open(corrected_path, "wb") as f:
                                        f.write(uploaded_corrected.getbuffer())
                                    st.session_state[uploader_key_name] += 1
                                    st.rerun()

                    active_path = (corrected_path if os.path.exists(corrected_path)
                                   else report_path)

                    if os.path.exists(active_path):
                        mtime = os.path.getmtime(active_path)

                        _run_state = orc.load_state(run_dir)
                        _brand_map = _run_state.get("brand_mapping", {})
                        render_sentiment_dashboard(
                            active_path, mtime, key_prefix="a_{}".format(run_name),
                            brand_mapping=_brand_map, show_brand_comparison=True)

                        with open(active_path, "rb") as f:
                            report_bytes = f.read()
                        st.download_button(
                            "Descargar análisis (XLSX)",
                            data=report_bytes,
                            file_name="analisis_{}.xlsx".format(run_name),
                            mime="application/vnd.openxmlformats-officedocument"
                                 ".spreadsheetml.sheet",
                        )

            render_analysis(run_dir, selected)

    else:
        st.caption(
            "Sube cualquier archivo XLSX o CSV con comentarios. "
            "Mapea las columnas de tu archivo a los campos del análisis."
        )

        _ANALYSIS_DETECT = {
            "Comentario": {"comentario", "comment", "texto", "text", "message"},
            "Red": {"red", "network", "plataforma", "platform", "red social"},
            "Sentimiento": {"sentimiento", "sentiment", "sentimento"},
            "Marca": {"marca", "brand"},
            "Autor": {"autor", "author", "username", "usuario", "user", "name"},
            "Likes": {"likes", "me gusta"},
            "Fecha del comentario": {"fecha del comentario", "fecha", "date"},
            "Link del post": {"link del post", "link", "url", "post url"},
        }

        def _detect_analysis_col(field, cols):
            for c in cols:
                if c.strip().lower() in _ANALYSIS_DETECT.get(field, set()):
                    return c
            return None

        if "upload_base_uploader_key" not in st.session_state:
            st.session_state["upload_base_uploader_key"] = 0

        base_path = os.path.join(UPLOADS_DIR, UPLOADED_BASE_FILENAME)

        uploaded_base = st.file_uploader(
            "Archivo XLSX o CSV", type=["xlsx", "csv"],
            key="upload_base_{}".format(st.session_state["upload_base_uploader_key"]),
        )

        if uploaded_base is not None:
            try:
                if uploaded_base.name.lower().endswith(".csv"):
                    raw_up = pd.read_csv(uploaded_base)
                else:
                    try:
                        raw_up = pd.read_excel(uploaded_base, sheet_name="Comentarios")
                    except Exception:
                        raw_up = pd.read_excel(uploaded_base, sheet_name=0)
                raw_up = raw_up.dropna(axis=1, how="all")
                raw_up.columns = [str(c).strip() for c in raw_up.columns]
                up_cols = raw_up.columns.tolist()
            except Exception as e:
                st.error("Error al leer el archivo: {}".format(e))
                raw_up = None
                up_cols = []

            if raw_up is not None and up_cols:
                st.caption("Mapea las columnas de tu archivo:")
                _na = "(no disponible)"
                _opt = [_na] + up_cols

                _ac1, _ac2 = st.columns(2)
                _det = _detect_analysis_col
                m_comment = _ac1.selectbox(
                    "Comentario (requerido)", up_cols,
                    index=up_cols.index(_det("Comentario", up_cols)) if _det("Comentario", up_cols) else 0,
                    key="umap_comment",
                )
                m_red = _ac2.selectbox(
                    "Red / Plataforma (requerido)", up_cols,
                    index=up_cols.index(_det("Red", up_cols)) if _det("Red", up_cols) else 0,
                    key="umap_red",
                )
                m_sent = _ac1.selectbox(
                    "Sentimiento", _opt,
                    index=_opt.index(_det("Sentimiento", up_cols) or _na),
                    key="umap_sent",
                )
                m_marca = _ac2.selectbox(
                    "Marca", _opt,
                    index=_opt.index(_det("Marca", up_cols) or _na),
                    key="umap_marca",
                )
                m_autor = _ac1.selectbox(
                    "Autor", _opt,
                    index=_opt.index(_det("Autor", up_cols) or _na),
                    key="umap_autor",
                )
                m_likes = _ac2.selectbox(
                    "Likes", _opt,
                    index=_opt.index(_det("Likes", up_cols) or _na),
                    key="umap_likes",
                )
                m_fecha = _ac1.selectbox(
                    "Fecha del comentario", _opt,
                    index=_opt.index(_det("Fecha del comentario", up_cols) or _na),
                    key="umap_fecha",
                )
                m_link = _ac2.selectbox(
                    "Link del post", _opt,
                    index=_opt.index(_det("Link del post", up_cols) or _na),
                    key="umap_link",
                )

                col_map = {
                    "Comentario": m_comment,
                    "Red": m_red,
                }
                for field, val in [("Sentimiento", m_sent), ("Marca", m_marca),
                                   ("Autor", m_autor), ("Likes", m_likes),
                                   ("Fecha del comentario", m_fecha),
                                   ("Link del post", m_link)]:
                    if val != _na:
                        col_map[field] = val

                rename_up = {v: k for k, v in col_map.items() if v != k}
                mapped_up = raw_up.rename(columns=rename_up)

                st.caption("{} filas · {} columnas mapeadas".format(
                    len(mapped_up), len(col_map)))
                preview_cols = [c for c in ["Red", "Marca", "Autor", "Comentario",
                                            "Likes", "Sentimiento"] if c in mapped_up.columns]
                st.dataframe(mapped_up[preview_cols].head(10), hide_index=True,
                             use_container_width=True)

                if st.button("Cargar base", type="primary", key="load_base"):
                    mapped_up.to_excel(base_path, sheet_name="Comentarios", index=False)
                    st.session_state["upload_base_uploader_key"] += 1
                    st.rerun()

        if os.path.exists(base_path):
            if st.button("Quitar base subida"):
                os.remove(base_path)
                st.rerun()

            mtime = os.path.getmtime(base_path)
            render_sentiment_dashboard(
                base_path, mtime, key_prefix="upload_base",
                show_brand_comparison=True)
        else:
            st.info("Sube un archivo para ver el análisis.")


_IPDS_COL_DETECT = {
    "interacciones": {"interactions", "interacciones", "interações", "total interactions",
                      "engagement", "engajamento"},
    "red": {"network", "red", "red social", "plataforma", "platform"},
    "marca": {"profile", "perfil", "marca", "cuenta", "brand", "account"},
    "fecha": {"date", "fecha", "fecha de publicación", "published"},
}


def _ipds_detect(field, cols):
    for c in cols:
        if c.strip().lower() in _IPDS_COL_DETECT.get(field, set()):
            return c
    return None


_SENT_DISPLAY = {"Positivo": "🟢 Positivo", "Neutral": "🟡 Neutral", "Negativo": "🔴 Negativo"}
_SENT_FROM_DISPLAY = {v: k for k, v in _SENT_DISPLAY.items()}
_SENT_OPTIONS_DISPLAY = ["🟢 Positivo", "🟡 Neutral", "🔴 Negativo"]


def _resolve_clasif_path():
    """Retorna o path do arquivo ativo para edição, ou None."""
    source = st.radio(
        "Fuente de datos", ["Ejecución exportada", "Base subida"],
        horizontal=True, key="clasif_source",
    )
    if source == "Ejecución exportada":
        run_opts = _runs_with_exports()
        if not run_opts:
            st.info("No hay ejecuciones con análisis.")
            return None
        sel = st.selectbox("Ejecución", run_opts, key="clasif_run")
        run_dir = os.path.join(RUNS_DIR, sel)
        analysis_state = ra.load_analysis_state(run_dir)
        if not analysis_state or analysis_state.get("stage") != "completado":
            st.info("Esta ejecución no tiene análisis completado. "
                    "Genera el análisis en la pestaña Análisis primero.")
            return None
        report_path = os.path.join(run_dir, analysis_state["report_file"])
        corrected = os.path.join(run_dir, CORRECTED_FILENAME)
        return corrected if os.path.exists(corrected) else report_path
    else:
        base_path = os.path.join(UPLOADS_DIR, UPLOADED_BASE_FILENAME)
        if not os.path.exists(base_path):
            st.info("No hay base subida. Sube una en la pestaña Análisis.")
            return None
        return base_path


with tab_clasif:
    st.caption("Revisa y corrige la clasificación de sentimiento y tema de cada "
               "comentario. Los cambios se guardan en el archivo XLSX que descargas.")

    clasif_path = _resolve_clasif_path()
    if clasif_path is not None:
        clasif_df = pd.read_excel(clasif_path, sheet_name="Comentarios")
        clasif_df.columns = [str(c).strip() for c in clasif_df.columns]

        sel_dict_key = st.session_state.get("selected_dict_key", "servicios_financieros")

        if "Tema" not in clasif_df.columns:
            clasif_df["Tema"] = tc.classify_series(
                clasif_df["Comentario"].fillna(""), sel_dict_key)

        topic_list = sorted(tc.DICTIONARIES[sel_dict_key]["topics"].keys()) + ["Otros"]

        clasif_df["_sent_display"] = clasif_df["Sentimiento"].map(
            _SENT_DISPLAY).fillna("○ Neutral")

        # ── Filtros ──
        fc1, fc2, fc3 = st.columns(3)
        c_search = fc1.text_input("Buscar", key="clasif_search",
                                   placeholder="Texto...")
        c_redes = ["Todas"] + sorted(clasif_df["Red"].dropna().unique().tolist()) if "Red" in clasif_df.columns else ["Todas"]
        c_red = fc2.selectbox("Red", c_redes, key="clasif_red_f")
        c_sent = fc3.selectbox("Sentimiento", ["Todos"] + _SENT_OPTIONS_DISPLAY,
                               key="clasif_sent_f")
        fc5, fc6 = st.columns(2)
        c_tema = fc5.selectbox("Tema", ["Todos"] + topic_list, key="clasif_tema_f")
        c_links = ["Todos"] + sorted(clasif_df["Link del post"].dropna().unique().tolist()) if "Link del post" in clasif_df.columns else ["Todos"]
        c_link = fc6.selectbox("Link del post", c_links, key="clasif_link_f")

        filtered = clasif_df.copy()
        if c_search.strip():
            filtered = filtered[filtered["Comentario"].str.lower().str.contains(
                c_search.strip().lower(), na=False)]
        if c_red != "Todas" and "Red" in filtered.columns:
            filtered = filtered[filtered["Red"] == c_red]
        if c_sent != "Todos":
            real_sent = _SENT_FROM_DISPLAY.get(c_sent, c_sent)
            filtered = filtered[filtered["Sentimiento"] == real_sent]
        if c_tema != "Todos":
            filtered = filtered[filtered["Tema"] == c_tema]
        if c_link != "Todos" and "Link del post" in filtered.columns:
            filtered = filtered[filtered["Link del post"] == c_link]

        # ── Paginação ──
        pg1, pg2, pg3 = st.columns([1, 1, 2])
        page_size = pg1.selectbox("Por página", [25, 50, 100], index=1,
                                   key="clasif_pagesize")
        total_pages = max(1, -(-len(filtered) // page_size))
        page_num = pg2.number_input("Página", 1, total_pages, 1,
                                     key="clasif_page")
        pg3.caption("{} comentarios · {} páginas".format(len(filtered), total_pages))

        start = (page_num - 1) * page_size
        page_slice = filtered.iloc[start:start + page_size].copy()

        show = [c for c in ["Red", "Marca", "Autor", "Comentario", "Likes",
                            "_sent_display", "Tema", "Link del post"]
                if c in page_slice.columns]
        locked = [c for c in show if c not in ("_sent_display", "Tema")]

        with st.form("clasif_form"):
            edited = st.data_editor(
                page_slice[show],
                column_config={
                    "_sent_display": st.column_config.SelectboxColumn(
                        "Sentimiento",
                        options=_SENT_OPTIONS_DISPLAY,
                        required=True,
                    ),
                    "Tema": st.column_config.SelectboxColumn(
                        "Tema",
                        options=topic_list,
                        required=True,
                    ),
                    "Link del post": st.column_config.LinkColumn(
                        "Link", display_text="🔗", width="small",
                    ),
                },
                disabled=locked,
                hide_index=True,
                use_container_width=True,
            )
            if st.form_submit_button("Guardar cambios", type="primary"):
                edited_sent = edited["_sent_display"].map(_SENT_FROM_DISPLAY)
                clasif_df.loc[edited.index, "Sentimiento"] = edited_sent.values
                clasif_df.loc[edited.index, "Tema"] = edited["Tema"].values
                save_cols = [c for c in clasif_df.columns if c != "_sent_display"]
                clasif_df[save_cols].to_excel(
                    clasif_path, sheet_name="Comentarios", index=False)
                st.success("Cambios guardados.")
                st.rerun()

        st.download_button(
            "Descargar base corregida (XLSX)",
            data=open(clasif_path, "rb").read(),
            file_name="base_clasificada.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


with tab_ipds:
    st.caption(
        "Indicador de Presencia Digital Social — compara marcas "
        "en una escala de 0 a 1 usando metodología IDH."
    )

    with st.expander("Metodología del IPD-S"):
        st.markdown("""
**¿Qué es el IPD-S?**

El Indicador de Presencia Digital Social (IPD-S) es un índice compuesto
que evalúa la eficacia de la comunicación digital de marcas en redes
sociales. Inspirado en la metodología del IDH (Índice de Desarrollo
Humano) del PNUD, combina múltiples dimensiones en un único número
de 0 a 1.

**Dimensiones**

| Dimensión | Qué mide | Cómo se calcula |
|---|---|---|
| **Actividad** | Frecuencia de publicación | Posts/mes, normalizado por red |
| **Engagement** | Resonancia del contenido | Interacciones/post, normalizado por red |
| **Multicanal** | Diversificación de plataformas | Nº de redes activas / total de redes |
| **Sentimiento** | Salud de la percepción de marca | % de comentarios positivos *(opcional)* |

**Normalización por plataforma**

Cada red social tiene un comportamiento distinto — el volumen de
interacciones en TikTok no es comparable al de Facebook. Por eso, las
dimensiones de Actividad y Engagement se calculan **dentro de cada red**
primero (comparando marcas entre sí en esa plataforma) y luego se
agregan como promedio de los scores por red.

Se usa escala logarítmica (`log(1 + x)`) antes de la normalización
min-max para suavizar distorsiones causadas por outliers, siguiendo
la práctica del IDH para la dimensión de ingreso.

**Fórmula**

`IPD-S = (D₁ × D₂ × D₃ × … × Dₙ) ^ (1/n)` — media geométrica

La media geométrica (en vez de aritmética) penaliza desequilibrios:
una marca con engagement altísimo pero actividad cero no puede
compensar una dimensión con la otra.

**Escala y niveles**

| Nivel | Intervalo | Interpretación |
|---|---|---|
| Muy bajo | 0,00 – 0,20 | Presencia digital frágil o incipiente |
| Bajo | 0,20 – 0,40 | Presencia por debajo del promedio del grupo |
| Medio | 0,40 – 0,60 | Presencia promedio, con espacio para evolucionar |
| Alto | 0,60 – 0,80 | Presencia sólida y consistente |
| Muy alto | 0,80 – 1,00 | Referencia digital en el grupo analizado |

**¿Cómo leer el termómetro?**

- Las marcas posicionadas **más a la izquierda** (zona roja/naranja)
  tienen una presencia digital débil en el grupo: publican poco,
  generan bajo engagement, o están presentes en pocas redes. Requieren
  atención y estrategia para mejorar su posicionamiento.
- Las marcas posicionadas **más a la derecha** (zona verde) dominan
  la conversación digital: publican con frecuencia, generan alto
  engagement relativo a su plataforma, están diversificadas en
  múltiples redes y (si hay datos) tienen un sentimiento positivo.
  Son la referencia del grupo.

**Limitaciones**

- El IPD-S es relativo al grupo de marcas analizado, no absoluto.
  Agregar o quitar una marca puede alterar los scores de las demás.
- No considera dark posts, pauta aislada, Google, prensa, Wikipedia
  u otras capas del digital fuera de las redes sociales.
- La dimensión de Sentimiento depende de la disponibilidad de análisis
  de comentarios (puede omitirse si no hay datos).
""")


    if "ipds_uploader_key" not in st.session_state:
        st.session_state["ipds_uploader_key"] = 0

    ipds_file = st.file_uploader(
        "Base de posts (.xlsx, .csv)", type=["xlsx", "csv"],
        key="ipds_upload_{}".format(st.session_state["ipds_uploader_key"]),
    )

    if ipds_file is not None:
        try:
            if ipds_file.name.lower().endswith(".csv"):
                ipds_raw = pd.read_csv(ipds_file)
            else:
                ipds_raw = sr.read_raw_file(
                    os.path.join(INPUT_DIR, ipds_file.name))
                with open(os.path.join(INPUT_DIR, ipds_file.name), "wb") as f:
                    ipds_file.seek(0)
                    f.write(ipds_file.getbuffer())
                ipds_raw = sr.read_raw_file(os.path.join(INPUT_DIR, ipds_file.name))
            ipds_raw = ipds_raw.dropna(axis=1, how="all")
            ipds_raw.columns = [str(c).strip() for c in ipds_raw.columns]
            ip_cols = ipds_raw.columns.tolist()
        except Exception as e:
            st.error("Error al leer el archivo: {}".format(e))
            ipds_raw = None
            ip_cols = []

        if ipds_raw is not None and ip_cols:
            st.caption("Mapea las columnas de tu archivo:")
            _ina = "(no disponible)"
            _iopt = [_ina] + ip_cols

            ic1, ic2 = st.columns(2)
            ip_marca = ic1.selectbox(
                "Perfil / Marca (requerido)", ip_cols,
                index=ip_cols.index(_ipds_detect("marca", ip_cols)) if _ipds_detect("marca", ip_cols) else 0,
                key="ipds_marca",
            )
            ip_red = ic2.selectbox(
                "Red social (requerido)", ip_cols,
                index=ip_cols.index(_ipds_detect("red", ip_cols)) if _ipds_detect("red", ip_cols) else 0,
                key="ipds_red",
            )
            ip_inter = ic1.selectbox(
                "Interacciones (requerido)", ip_cols,
                index=ip_cols.index(_ipds_detect("interacciones", ip_cols)) if _ipds_detect("interacciones", ip_cols) else 0,
                key="ipds_inter",
            )
            ip_fecha = ic2.selectbox(
                "Fecha de publicación", _iopt,
                index=_iopt.index(_ipds_detect("fecha", ip_cols) or _ina),
                key="ipds_fecha",
            )

            ipds_mapping = {"marca": ip_marca, "red": ip_red, "interacciones": ip_inter}
            if ip_fecha != _ina:
                ipds_mapping["fecha"] = ip_fecha

            rename_ip = {v: k for k, v in ipds_mapping.items() if v != k}
            posts_mapped = ipds_raw.rename(columns=rename_ip)

            all_networks = sorted(posts_mapped["red"].dropna().unique().tolist())
            sel_networks = st.multiselect(
                "Redes a incluir", all_networks, default=all_networks,
                key="ipds_networks",
            )
            if sel_networks:
                posts_filtered = posts_mapped[posts_mapped["red"].isin(sel_networks)]
            else:
                posts_filtered = posts_mapped

            n_brands = posts_filtered["marca"].nunique()
            st.caption("{} posts · {} marcas · {} redes".format(
                len(posts_filtered), n_brands, len(sel_networks or all_networks)))

            if n_brands < 2:
                st.warning("El IPD-S compara marcas entre sí. Se necesitan al menos 2 marcas.")
            else:
                if st.button("Calcular IPD-S", type="primary", key="calc_ipds"):
                    st.session_state["ipds_ready"] = True

                if st.session_state.get("ipds_ready"):
                    try:
                        ipds_result = ipds.calculate(posts_filtered)

                        st.plotly_chart(ipds.thermometer_fig(ipds_result),
                                        use_container_width=True)

                        dim_fig = ipds.dimensions_bar_fig(ipds_result)
                        if dim_fig is not None:
                            st.plotly_chart(dim_fig, use_container_width=True)

                        st.subheader("Detalle por marca")
                        st.dataframe(ipds_result, hide_index=True,
                                     use_container_width=True)
                    except Exception as e:
                        st.error("Error al calcular el IPD-S: {}".format(e))
