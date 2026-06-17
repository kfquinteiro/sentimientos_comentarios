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
    "analizando_sentimiento": "Analizando sentimiento...",
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


def render_sentiment_dashboard(active_path, mtime, key_prefix, show_brand_comparison=False):
    df = load_report_data(active_path, mtime)

    total = len(df)
    counts = df["Sentimiento"].value_counts()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Comentarios analizados", total)
    col2.metric("Positivo", int(counts.get("Positivo", 0)))
    col3.metric("Neutral", int(counts.get("Neutral", 0)))
    col4.metric("Negativo", int(counts.get("Negativo", 0)))

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
        top_liked = df.dropna(subset=["Likes"]).sort_values("Likes", ascending=False).head(10)
        show_cols = [
            c for c in ["Red", "Autor", "Comentario", "Likes", "Sentimiento", "Fecha del comentario"]
            if c in top_liked.columns
        ]
        st.dataframe(top_liked[show_cols], hide_index=True, use_container_width=True)
    else:
        st.caption("No hay datos de likes disponibles.")

    st.subheader("Principales detractores y brand lovers")
    st.caption(
        "Usuarios que más veces comentaron con sentimiento negativo "
        "(detractores) o positivo (brand lovers)."
    )
    with_author = df.dropna(subset=["Autor"]) if "Autor" in df.columns else df.iloc[0:0]
    if not with_author.empty and "Marca" in with_author.columns:
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
            wc_brand_cols = st.columns(2)
            for i, marca in enumerate(marcas):
                img = build_wordcloud_image(active_path, mtime, marca=marca)
                with wc_brand_cols[i % 2]:
                    st.caption(marca)
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


tab_export, tab_runs, tab_upload = st.tabs(
    ["Nueva exportación", "Ejecuciones y análisis", "Analizar base propia"]
)

with tab_export:
    if "uploader_key" not in st.session_state:
        st.session_state["uploader_key"] = 0

    uploaded = st.file_uploader(
        "Hoja de cálculo de posts (.xlsx)", type=["xlsx"],
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
            links_df = sr.read_links(save_path)
        except Exception as e:
            st.error("Error al leer la hoja de cálculo: {}".format(e))
            links_df = None

        if links_df is not None:
            st.success("{} links encontrados".format(len(links_df)))
            if "network" in links_df.columns:
                counts = links_df["network"].value_counts().rename_axis("Red").reset_index(name="Cantidad")
                st.dataframe(counts, hide_index=True, use_container_width=True)
            st.dataframe(links_df.head(20), use_container_width=True)

            if st.button("Iniciar exportación", type="primary"):
                run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                run_dir = os.path.join(RUNS_DIR, run_id)
                orc.init_run(run_dir, links_df, source_file=save_path)
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

        @st.fragment(run_every="5s")
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

        @st.fragment(run_every="3s")
        def render_results(run_dir, run_name):
            state = orc.load_state(run_dir)
            done_count = sum(1 for item in state["items"] if item["status"] == "done")

            if done_count > 0:
                zip_bytes = make_zip_bytes_cached(run_dir, done_count)
                st.download_button(
                    "Descargar resultados (ZIP)",
                    data=zip_bytes,
                    file_name="export_{}.zip".format(run_name),
                    mime="application/zip",
                )

            st.header("Análisis de sentimiento")

            if done_count == 0:
                st.info("Todavía no hay comentarios exportados para analizar.")
                return

            st.caption("{} post(s) con comentarios exportados disponibles para analizar.".format(done_count))

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
                    key="use_ai_{}".format(run_name),
                    help=(
                        "Analiza cada comentario con Claude (Anthropic) en lugar del "
                        "modelo local. Suele entender mejor el sarcasmo, la jerga y "
                        "el contexto, pero tiene un costo por uso de la API y requiere "
                        "ANTHROPIC_API_KEY configurada en el archivo .env."
                    ),
                )

                if st.button(label, key="analyze_{}".format(run_name), type="primary"):
                    launch_analysis(run_dir, "ai" if use_ai else "local")
                    st.rerun()

                if analysis_state and analysis_state.get("stage") == "error":
                    st.error("Error al generar el análisis: {}".format(analysis_state.get("error")))

            if analysis_state and analysis_state.get("stage") == "completado":
                engine_label = "IA (Claude Haiku)" if analysis_state.get("engine") == "ai" else "modelo local (pysentimiento)"
                st.caption("Análisis generado con: {}".format(engine_label))

                report_path = os.path.join(run_dir, analysis_state["report_file"])
                corrected_path = os.path.join(run_dir, CORRECTED_FILENAME)

                with st.expander("📝 Base corregida manualmente"):
                    if os.path.exists(corrected_path):
                        st.success("Usando la base corregida que subiste manualmente.")
                        if st.button("Quitar base corregida", key="remove_corrected_{}".format(run_name)):
                            os.remove(corrected_path)
                            st.rerun()
                    else:
                        st.caption(
                            "Descarga el XLSX de abajo, corrige a mano la columna "
                            "'Sentimiento' y vuelve a subirlo aquí: los gráficos y "
                            "métricas usarán esa versión corregida."
                        )

                    uploader_key_name = "corrected_uploader_key_{}".format(run_name)
                    if uploader_key_name not in st.session_state:
                        st.session_state[uploader_key_name] = 0

                    uploaded_corrected = st.file_uploader(
                        "Subir XLSX corregido", type=["xlsx"],
                        key="corrected_{}_{}".format(run_name, st.session_state[uploader_key_name]),
                    )
                    if uploaded_corrected is not None:
                        try:
                            test_df = pd.read_excel(uploaded_corrected, sheet_name="Comentarios")
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

                active_path = corrected_path if os.path.exists(corrected_path) else report_path

                if os.path.exists(active_path):
                    mtime = os.path.getmtime(active_path)

                    render_sentiment_dashboard(active_path, mtime, key_prefix=run_name)

                    with open(active_path, "rb") as f:
                        report_bytes = f.read()
                    st.download_button(
                        "Descargar análisis (XLSX)",
                        data=report_bytes,
                        file_name="analisis_{}.xlsx".format(run_name),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

        render_results(run_dir, selected_run)


with tab_upload:
    st.caption(
        "Sube un archivo XLSX con una hoja 'Comentarios' en el mismo formato "
        "que el análisis generado por esta herramienta (columnas Red, Marca, "
        "Sentimiento, Comentario, etc.). Si la base tiene más de una marca, "
        "también se muestran gráficos comparando las marcas."
    )

    if "upload_base_uploader_key" not in st.session_state:
        st.session_state["upload_base_uploader_key"] = 0

    base_path = os.path.join(UPLOADS_DIR, UPLOADED_BASE_FILENAME)

    uploaded_base = st.file_uploader(
        "Archivo XLSX", type=["xlsx"],
        key="upload_base_{}".format(st.session_state["upload_base_uploader_key"]),
    )

    if uploaded_base is not None:
        try:
            test_df = pd.read_excel(uploaded_base, sheet_name="Comentarios")
        except Exception as e:
            st.error("Error al leer el archivo: {}".format(e))
            test_df = None

        if test_df is not None:
            required = {"Red", "Sentimiento", "Comentario"}
            if not required.issubset(test_df.columns):
                st.error(
                    "El archivo debe tener una hoja 'Comentarios' con al menos "
                    "las columnas: Red, Sentimiento, Comentario."
                )
            else:
                with open(base_path, "wb") as f:
                    f.write(uploaded_base.getbuffer())
                st.session_state["upload_base_uploader_key"] += 1
                st.rerun()

    if os.path.exists(base_path):
        if st.button("Quitar base subida"):
            os.remove(base_path)
            st.rerun()

        mtime = os.path.getmtime(base_path)
        render_sentiment_dashboard(base_path, mtime, key_prefix="upload_base", show_brand_comparison=True)
    else:
        st.info("Sube un archivo XLSX para ver el análisis.")
