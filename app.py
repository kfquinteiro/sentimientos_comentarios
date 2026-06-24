"""Interfaz: subir la hoja de cálculo de posts y orquestar la exportación de
comentarios vía ExportComments."""
import io
import os
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import charts
import consolidate as cons
import orchestrator as orc
import report as rep
import run_analysis as ra
import spreadsheet_reader as sr
import topic_classifier as tc
import ipds
from i18n import t

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(PROJECT_DIR, "input")
RUNS_DIR = os.path.join(PROJECT_DIR, "runs")
CURRENT_RUN_DIR = os.path.join(RUNS_DIR, "current")
UPLOADS_DIR = os.path.join(PROJECT_DIR, "uploads")

os.makedirs(RUNS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
UPLOADED_BASE_FILENAME = "base_comentarios.xlsx"
FINISHED_STATUSES = {"done", "error", "timeout", "skipped"}

def _status_labels():
    return {
        "pending": _t("status_pending"),
        "creating": _t("status_creating"),
        "queueing": _t("status_queueing"),
        "progress": _t("status_progress"),
        "done": _t("status_done"),
        "error": _t("status_error"),
        "timeout": _t("status_timeout"),
        "skipped": _t("status_skipped"),
    }

def _column_labels():
    return {
        "link": _t("col_label_link"),
        "network": _t("col_label_network"),
        "status": _t("col_label_status"),
        "total": _t("col_label_comments"),
        "total_exported": _t("col_label_comments_collected"),
        "error": _t("col_label_error"),
        "file_name": _t("col_label_file"),
    }


def display_status(item):
    """Etiqueta de estado para mostrar en la interfaz. Para items con
    status=="error" distingue entre falla al crear el job, posts sin
    comentarios y posts eliminados/no disponibles, en vez de mostrar
    siempre "Error"."""
    status = item["status"]
    labels = _status_labels()
    if status != "error":
        return labels.get(status, status)

    error = item.get("error") or ""
    if item.get("guid") is None:
        return labels["error"]
    if "No comments have been found" in error or "No comments have been received" in error:
        return _t("status_no_comments")
    if "404 Client Error" in error and "/exports/" in error:
        return _t("status_no_comments")
    if "Cannot access specified post" in error or "Video unavailable" in error:
        return _t("status_post_deleted")
    return labels["error"]

_STAGE_KEYS = {
    "consolidando": "stage_consolidating",
    "cargando_modelo": "stage_loading_model",
    "analizando_sentimiento": "stage_analyzing",
    "generando_reporte": "stage_generating_report",
    "completado": "stage_completed",
    "error": "stage_error",
}


def _stage_label(stage):
    key = _STAGE_KEYS.get(stage, stage)
    return _t(key)

REPORT_COLUMN_LABELS = rep.COLUMN_LABELS
CORRECTED_FILENAME = "analisis_sentimiento_corregido.xlsx"


@st.cache_data
def load_report_data(report_path, mtime):
    return pd.read_excel(report_path, sheet_name="Comentarios")


@st.cache_data
def build_wordcloud_image(report_path, mtime, red=None, sentimiento=None, marca=None,
                          tema=None, colormap=None, extra_stopwords=None):
    df = load_report_data(report_path, mtime)
    if red:
        df = df[df["Red"] == red]
    if sentimiento:
        df = df[df["Sentimiento"] == sentimiento]
    if marca:
        df = df[df["Marca"] == marca]
    if tema:
        df = df[df["Tema"] == tema]
    return charts.wordcloud_image(df["Comentario"].dropna(), colormap=colormap, extra_stopwords=extra_stopwords)


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
        _bmap = {}
        _bmap_fuzzy = {}
        for profile, desired in brand_mapping.items():
            _bmap[profile.strip().lower()] = desired
            auto = cons.normalize_brand(profile)
            if auto:
                _bmap[auto.lower()] = desired
            fuzzy_key = re.sub(r"[\s_.]+", "", profile.lower())
            _bmap_fuzzy[fuzzy_key] = desired

        def _apply_brand(m):
            if pd.isna(m):
                return m
            s = str(m).strip()
            low = s.lower()
            if low in _bmap:
                return _bmap[low]
            fuzzy = re.sub(r"[\s_.]+", "", low)
            if fuzzy in _bmap_fuzzy:
                return _bmap_fuzzy[fuzzy]
            return s

        df["Marca"] = df["Marca"].apply(_apply_brand)

    total = len(df)
    counts = df["Sentimiento"].value_counts()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(_t("comments_analyzed"), total)
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
    col1.plotly_chart(charts.donut_sentiment(chart_df, lang=_lang()), use_container_width=True)
    col2.plotly_chart(charts.bar_by_network(chart_df, lang=_lang()), use_container_width=True)

    _time_marcas = ["Todas"] + sorted(chart_df["marca"].dropna().unique().tolist()) if "marca" in chart_df.columns else ["Todas"]
    _time_marca = st.selectbox(
        _t("brand"), _time_marcas,
        key="{}_time_marca".format(key_prefix),
    ) if len(_time_marcas) > 2 else "Todas"
    _time_df = chart_df if _time_marca == "Todas" else chart_df[chart_df["marca"] == _time_marca]

    time_fig = charts.line_over_time(_time_df, lang=_lang())
    if time_fig is not None:
        st.plotly_chart(time_fig, use_container_width=True)

    time_by_network_fig = charts.line_over_time_by_network(_time_df, lang=_lang())
    if time_by_network_fig is not None:
        st.plotly_chart(time_by_network_fig, use_container_width=True)

    # ── Clasificación por tema ────────────────────────────────────────────
    st.subheader(_t("topic_analysis"))
    selected_dict_key = st.session_state.get("selected_dict_key", "servicios_financieros")

    chart_df["tema"] = tc.classify_series(
        chart_df["comentario"].fillna(""), selected_dict_key, lang=_lang())

    total_classified = (chart_df["tema"] != tc.otros_label(_lang())).sum()
    total_otros = (chart_df["tema"] == tc.otros_label(_lang())).sum()
    pct_classified = round(total_classified / len(chart_df) * 100) if len(chart_df) else 0
    mc1, mc2, mc3 = st.columns(3)
    mc1.metric(_t("classified"), "{} ({}%)".format(total_classified, pct_classified))
    mc2.metric(_t("unclassified"), total_otros)
    mc3.metric(_t("topics_detected"), chart_df[chart_df["tema"] != tc.otros_label(_lang())]["tema"].nunique())

    _viz_opts = [_t("viz_topics_sentiment"), _t("viz_priority"), _t("viz_topics_network")]
    tema_chart = st.radio(
        _t("visualization"), _viz_opts,
        horizontal=True, key="{}_tema_chart".format(key_prefix),
    )
    if tema_chart == _viz_opts[0]:
        fig = charts.bubble_matrix_tema_sentimiento(chart_df, lang=_lang())
    elif tema_chart == _viz_opts[1]:
        fig = charts.bubble_prioridad(chart_df, lang=_lang())
    else:
        fig = charts.heatmap_tema_red(chart_df, lang=_lang())
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)

    if total_otros > 0:
        with st.expander(_t("explore_otros").format(total_otros)):
            otros_df = chart_df[chart_df["tema"] == tc.otros_label(_lang())]
            otros_words = charts.top_words(otros_df["comentario"].dropna(), n=30)
            if otros_words:
                st.caption(_t("frequent_words_otros"))
                word_labels = ["{} ({})".format(w, c) for w, c in otros_words]
                sel_otros = st.pills(
                    _t("click_word_examples"), word_labels,
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

    # ── Stopwords personalizadas ───────────────────────────────────────────
    sw_raw = st.text_input(
        _t("stopwords_label"),
        key="{}_stopwords".format(key_prefix),
        help=_t("stopwords_help"),
    )
    extra_sw = frozenset(w.strip().lower() for w in sw_raw.split(",") if w.strip()) if sw_raw else None

    st.subheader(_t("wordcloud_by_network"))
    wc_cols = st.columns(2)
    for i, red in enumerate(networks):
        img = build_wordcloud_image(active_path, mtime, red=red, extra_stopwords=extra_sw)
        with wc_cols[i % 2]:
            st.caption(red)
            if img is not None:
                st.image(img, use_container_width=True)
            else:
                st.caption(_t("not_enough_text_cloud"))

    cloud_words = charts.top_words(df["Comentario"].dropna(), n=50, extra_stopwords=extra_sw)
    if cloud_words:
        word_labels = ["{} ({})".format(w, c) for w, c in cloud_words]
        selected_pill = st.pills(
            _t("click_word_comments"),
            word_labels, key="{}_wc_pill".format(key_prefix),
        )
        if selected_pill:
            word = selected_pill.split(" (")[0]
            matches = df[df["Comentario"].str.lower().str.contains(word, na=False)]
            if not matches.empty:
                fcol1, fcol2 = st.columns(2)
                red_opts = ["Todas"] + sorted(matches["Red"].dropna().unique().tolist()) if "Red" in matches.columns else ["Todas"]
                sent_opts = ["Todos"] + charts.SENTIMENT_ORDER
                sel_r = fcol1.selectbox(_t("col_network"), red_opts, key="{}_wc_red_f".format(key_prefix))
                sel_s = fcol2.selectbox(_t("sentiment_label"), sent_opts, key="{}_wc_sent_f".format(key_prefix))

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
                st.caption(_t("comments_with_word").format(len(matches), word))

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
                st.caption(_t("no_comments_found_word").format(word))

    st.subheader(_t("wordcloud_by_sentiment"))
    network_options = ["Todas"] + networks
    selected_network = st.selectbox(
        _t("col_network"), network_options, key="wc_red_{}".format(key_prefix)
    )
    red_filter = None if selected_network == "Todas" else selected_network

    wc_sent_cols = st.columns(3)
    for col, sentimiento in zip(wc_sent_cols, charts.SENTIMENT_ORDER):
        img = build_wordcloud_image(
            active_path, mtime, red=red_filter, sentimiento=sentimiento,
            colormap=charts.SENTIMENT_COLORMAPS[sentimiento],
            extra_stopwords=extra_sw,
        )
        with col:
            st.caption(sentimiento)
            if img is not None:
                st.image(img, use_container_width=True)
            else:
                st.caption(_t("not_enough_text_cloud"))

    # ── Nuvem por tema ─────────────────────────────────────────────────────
    if "Tema" in df.columns:
        st.subheader(_t("wordcloud_by_topic"))
        temas = sorted(df["Tema"].dropna().unique().tolist())
        otros = tc.otros_label(_lang())
        temas = [t for t in temas if t != otros]
        wc_tema_cols = st.columns(2)
        for i, tema in enumerate(temas):
            img = build_wordcloud_image(active_path, mtime, tema=tema, extra_stopwords=extra_sw)
            with wc_tema_cols[i % 2]:
                st.caption(tema)
                if img is not None:
                    st.image(img, use_container_width=True)
                else:
                    st.caption(_t("not_enough_text_cloud"))

    st.subheader(_t("word_tree"))
    st.caption(_t("word_tree_caption"))
    _wt_marcas = ["Todas"] + sorted(df["Marca"].dropna().unique().tolist()) if "Marca" in df.columns else ["Todas"]
    _wt_c1, _wt_c2 = st.columns([3, 1])
    root_phrase = _wt_c1.text_input(
        _t("word_or_phrase"), key="wordtree_root_{}".format(key_prefix)
    )
    _wt_marca = _wt_c2.selectbox("Marca", _wt_marcas, key="wt_marca_{}".format(key_prefix))

    if root_phrase.strip():
        wt_df = df if _wt_marca == "Todas" else df[df["Marca"] == _wt_marca]
        wt_comments = wt_df["Comentario"].dropna()
        if wt_comments.empty:
            st.caption(_t("no_comments_brand"))
        else:
            wt_tagged = charts.tag_texts_for_wordtree(wt_comments.tolist())
            wt_texts = wt_comments.tolist()
            wt_likes = wt_df.loc[wt_comments.index, "Likes"].fillna(0).tolist() if "Likes" in wt_df.columns else None
            wt_sents = wt_df.loc[wt_comments.index, "Sentimiento"].tolist() if "Sentimiento" in wt_df.columns else None
            tree_data = charts.build_word_tree(wt_tagged, root_phrase,
                                               full_texts=wt_texts, likes=wt_likes, sentiments=wt_sents)
            if tree_data is None:
                st.caption(_t("no_comments_word"))
            else:
                components.html(
                    charts.word_tree_html(tree_data, width=1400),
                    height=charts.word_tree_height(tree_data),
                )

    st.subheader(_t("most_interacted"))
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
        st.caption(_t("no_likes_data"))

    st.subheader(_t("detractors_lovers"))
    st.caption(_t("detractors_caption"))
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
        st.markdown("**{}**".format(_t("main_detractors")))
        negativos = with_author[with_author["Sentimiento"] == "Negativo"]
        if not negativos.empty:
            _neg_col = _t("negative_comments_col")
            top_neg = (
                negativos.groupby("Autor").size()
                .reset_index(name=_neg_col)
                .sort_values(_neg_col, ascending=False)
                .head(10)
            )
            st.dataframe(top_neg, hide_index=True, use_container_width=True)
        else:
            st.caption(_t("no_negative_comments"))

    with lover_col:
        st.markdown("**{}**".format(_t("main_lovers")))
        positivos = with_author[with_author["Sentimiento"] == "Positivo"]
        if not positivos.empty:
            _pos_col = _t("positive_comments_col")
            top_pos = (
                positivos.groupby("Autor").size()
                .reset_index(name=_pos_col)
                .sort_values(_pos_col, ascending=False)
                .head(10)
            )
            st.dataframe(top_pos, hide_index=True, use_container_width=True)
        else:
            st.caption(_t("no_positive_comments"))

    st.subheader(_t("posts_by_month"))
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
        st.caption(_t("no_pub_dates"))

    if show_brand_comparison and "Marca" in df.columns:
        marcas = sorted(df["Marca"].dropna().unique().tolist())
        if len(marcas) > 1:
            st.subheader(_t("brand_comparison"))

            st.plotly_chart(charts.bar_by_brand(chart_df, lang=_lang()), use_container_width=True)

            st.markdown("**{}**".format(_t("wordcloud_by_brand")))
            sel_marca_wc = st.selectbox(
                "Marca", marcas, key="{}_wc_marca_select".format(key_prefix),
            )
            marca_texts = df[df["Marca"] == sel_marca_wc]["Comentario"].dropna()
            img = charts.wordcloud_image(marca_texts, extra_stopwords=extra_sw) if not marca_texts.empty else None
            if img is not None:
                st.image(img, use_container_width=True)
            else:
                st.caption(_t("not_enough_text_cloud"))


os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(RUNS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

st.set_page_config(
    page_title="Análise de Redes Sociais",
    layout="wide",
)


def _lang():
    return st.session_state.get("lang", "pt")


def _t(key):
    return t(key, _lang())


def _check_password():
    pwd = st.secrets.get("PASSWORD") or os.environ.get("PASSWORD", "")
    if not pwd:
        return True
    if st.session_state.get("authenticated"):
        return True
    col = st.columns([1, 1, 1])[1]
    with col:
        with st.form("login"):
            st.markdown("#### " + _t("login_title"))
            entered = st.text_input(_t("login_password"), type="password")
            if st.form_submit_button(_t("login_enter"), use_container_width=True):
                if entered == pwd:
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error(_t("login_error"))
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

_col_title, _col_lang = st.columns([6, 1])
with _col_title:
    st.title(_t("page_title"))
    st.caption(_t("page_subtitle"))
with _col_lang:
    _lang_sel = st.radio("", ["🇧🇷", "🇪🇸"], horizontal=True,
                         index=0 if _lang() == "pt" else 1, key="lang_toggle",
                         label_visibility="collapsed")
    if (_lang_sel == "🇧🇷" and _lang() != "pt") or (_lang_sel == "🇪🇸" and _lang() != "es"):
        st.session_state["lang"] = "pt" if _lang_sel == "🇧🇷" else "es"
        st.rerun()



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
    [_t("tab_export"), _t("tab_runs"), _t("tab_analysis"),
     _t("tab_classification"), _t("tab_ipds")]
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
        _t("upload_posts"), type=["xlsx", "csv"],
        key="uploader_{}".format(st.session_state["uploader_key"]),
    )

    if uploaded is not None:
        if st.button(_t("clear_selection")):
            st.session_state["uploader_key"] += 1
            st.rerun()

        save_path = os.path.join(INPUT_DIR, uploaded.name)
        with open(save_path, "wb") as f:
            f.write(uploaded.getbuffer())

        try:
            raw_df = sr.read_raw_file(save_path)
            columns = raw_df.columns.tolist()
        except Exception as e:
            st.error(_t("error_reading_file").format(e))
            raw_df = None
            columns = []

        if raw_df is not None and columns:
            st.caption(_t("map_columns"))
            none_opt = _t("col_not_available")
            opt_cols = [none_opt] + columns

            mc1, mc2 = st.columns(2)
            auto_link = _auto_col("link", columns)
            col_link = mc1.selectbox(
                _t("col_link"), columns,
                index=columns.index(auto_link) if auto_link else 0,
                key="map_link",
            )
            col_net = mc2.selectbox(
                _t("col_network"), opt_cols,
                index=opt_cols.index(_auto_col("network", columns) or none_opt),
                key="map_network",
            )
            col_profile = mc1.selectbox(
                _t("col_profile"), opt_cols,
                index=opt_cols.index(_auto_col("profile", columns) or none_opt),
                key="map_profile",
            )
            col_date = mc2.selectbox(
                _t("col_date"), opt_cols,
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
                st.error(_t("error_processing").format(e))
                links_df = None

            if links_df is not None:
                st.success(_t("links_found").format(len(links_df)))
                if "network" in links_df.columns:
                    counts = (links_df["network"].value_counts()
                              .rename_axis("Red").reset_index(name=_t("network_count_column")))
                    st.dataframe(counts, hide_index=True, use_container_width=True)
                st.dataframe(links_df.head(20), use_container_width=True)

                has_existing = os.path.isfile(orc.state_path(CURRENT_RUN_DIR))
                if has_existing:
                    st.warning(_t("replace_warning"))
                if st.button(_t("start_export"), type="primary"):
                    if has_existing:
                        files_path = orc.files_dir(CURRENT_RUN_DIR)
                        if os.path.exists(files_path):
                            shutil.rmtree(files_path)
                        stop_path = orc.stop_flag_path(CURRENT_RUN_DIR)
                        if os.path.exists(stop_path):
                            os.remove(stop_path)
                    orc.init_run(CURRENT_RUN_DIR, links_df, source_file=save_path,
                                 column_mapping=mapping)
                    launch_run(CURRENT_RUN_DIR)
                    st.rerun()


with tab_runs:
    run_dir = CURRENT_RUN_DIR
    if not os.path.isfile(orc.state_path(run_dir)):
        st.info(_t("no_runs"))
    else:
        with st.expander(_t("reset_execution")):
            st.warning(_t("reset_warning"))
            run_active = is_running(run_dir) or ra.is_analysis_running(run_dir)
            if run_active:
                st.caption(_t("cannot_delete_running"))
            confirm_reset = st.checkbox(
                _t("reset_confirm"),
                key="confirm_reset",
                disabled=run_active,
            )
            with st.container(key="reset_run_button"):
                if st.button(_t("reset_button"), disabled=not confirm_reset or run_active, type="primary"):
                    state = orc.load_state(run_dir)
                    for item in state["items"]:
                        item["status"] = "pending"
                        item["guid"] = None
                        item["file_name"] = None
                        item["download_url"] = None
                        item["error"] = None
                        item["total"] = None
                        item["total_exported"] = None
                        item["attempts"] = 0
                        item["started_at"] = None
                        item["updated_at"] = None
                    orc.save_state(run_dir, state)
                    files_path = orc.files_dir(run_dir)
                    if os.path.exists(files_path):
                        shutil.rmtree(files_path)
                        os.makedirs(files_path)
                    stop_path = orc.stop_flag_path(run_dir)
                    if os.path.exists(stop_path):
                        os.remove(stop_path)
                    st.rerun()

        _status_refresh = "5s" if is_running(run_dir) else None

        @st.fragment(run_every=_status_refresh)
        def render_run_status(run_dir):
            state = orc.load_state(run_dir)
            items = state["items"]
            total = len(items)

            status_counts = pd.Series([item["status"] for item in items]).value_counts()
            finished = sum(int(status_counts.get(s, 0)) for s in FINISHED_STATUSES)
            pending = int(status_counts.get("pending", 0))
            running = is_running(run_dir)

            col1, col2, col3 = st.columns(3)
            col1.metric(_t("total_links"), total)
            col2.metric(_t("completed"), finished)
            col3.metric(_t("process"), _t("running") if running else _t("stopped"))

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
                    _t("avg_time_eta").format(
                        format_duration(avg), format_duration(eta), pending
                    )
                )

            display_counts = pd.Series([display_status(item) for item in items]).value_counts()
            status_table = display_counts.rename_axis(_t("col_label_status")).reset_index(name=_t("network_count_column"))
            st.dataframe(status_table, hide_index=True, use_container_width=True)

            if running:
                if st.button(_t("stop"), key="stop_current"):
                    open(orc.stop_flag_path(run_dir), "w").close()
                    st.rerun()
            elif finished < total:
                if st.button(_t("continue"), key="resume_current"):
                    stop_path = orc.stop_flag_path(run_dir)
                    if os.path.exists(stop_path):
                        os.remove(stop_path)
                    launch_run(run_dir)
                    st.rerun()

            failed_jobs = [item for item in items if item["status"] == "error" and item.get("guid") is None]
            if failed_jobs:
                st.caption(_t("failed_jobs_caption").format(len(failed_jobs)))
                if st.button(
                    _t("retry_failed_jobs"),
                    key="retry_failed_current",
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

            with st.expander(_t("details_per_link")):
                df = pd.DataFrame(items)
                _col_labels = _column_labels()
                cols = [c for c in _col_labels if c in df.columns]
                df = df[cols].rename(columns=_col_labels)
                df[_t("col_label_status")] = [display_status(item) for item in items]

                comentarios_col = _col_labels["total"]
                recolectados_col = _col_labels["total_exported"]
                totals_row = {c: "" for c in df.columns}
                totals_row[_col_labels["link"]] = "Total"
                if comentarios_col in df.columns:
                    totals_row[comentarios_col] = pd.to_numeric(df[comentarios_col], errors="coerce").sum()
                if recolectados_col in df.columns:
                    totals_row[recolectados_col] = pd.to_numeric(df[recolectados_col], errors="coerce").sum()
                df = pd.concat([df, pd.DataFrame([totals_row])], ignore_index=True)

                st.dataframe(df, use_container_width=True)

        render_run_status(run_dir)

        # ── Definir marcas ──────────────────────────────────────────────────
        _state = orc.load_state(run_dir)
        _profiles = sorted({
            item.get("profile", "") for item in _state["items"]
            if item.get("profile")
        })
        if _profiles:
            _saved = _state.get("brand_mapping", {})
            _expanded = not _saved
            with st.expander(_t("define_brands"), expanded=_expanded):
                st.caption(_t("define_brands_caption"))
                with st.form("brand_mapping"):
                    cols = st.columns(2)
                    _mapping = {}
                    for idx, profile in enumerate(_profiles):
                        default = _saved.get(profile) or cons.normalize_brand(profile) or profile
                        _mapping[profile] = cols[idx % 2].text_input(
                            profile, value=default,
                            key="bm_{}".format(profile),
                        )
                    if st.form_submit_button(_t("save_brands"), type="primary"):
                        _state["brand_mapping"] = {
                            p: v.strip() or cons.normalize_brand(p)
                            for p, v in _mapping.items()
                        }
                        orc.save_state(run_dir, _state)
                        st.success(_t("brands_saved"))

        _dl_refresh = "3s" if is_running(run_dir) else None

        @st.fragment(run_every=_dl_refresh)
        def render_run_downloads(run_dir):
            state = orc.load_state(run_dir)
            done_count = sum(1 for item in state["items"] if item["status"] == "done")

            if done_count == 0:
                return

            zip_bytes = make_zip_bytes_cached(run_dir, done_count)
            dl_col, _, analyze_col = st.columns([2, 3, 2])
            dl_col.download_button(
                _t("download_zip"),
                data=zip_bytes,
                file_name="export.zip",
                mime="application/zip",
            )
            with analyze_col:
                if st.button(_t("analyze_now"), key="go_analyze",
                             type="primary", use_container_width=True):
                    st.session_state["analyze_run"] = True

            if st.session_state.get("analyze_run"):
                st.info(_t("go_to_analysis"))

        render_run_downloads(run_dir)


def _current_has_exports():
    if not os.path.isfile(orc.state_path(CURRENT_RUN_DIR)):
        return False
    state = orc.load_state(CURRENT_RUN_DIR)
    return any(i["status"] == "done" for i in state["items"])


with tab_analysis:
    _src_opts = [_t("exported_run"), _t("upload_own_base")]
    source = st.radio(
        _t("data_source"),
        _src_opts,
        horizontal=True,
        key="analysis_source",
    )

    if source == _src_opts[0]:
        if not _current_has_exports():
            st.info(_t("no_runs_with_data"))
        else:
            run_dir = CURRENT_RUN_DIR

            _analysis_refresh = "3s" if ra.is_analysis_running(run_dir) else None

            @st.fragment(run_every=_analysis_refresh)
            def render_analysis(run_dir):
                state = orc.load_state(run_dir)
                done_count = sum(1 for item in state["items"] if item["status"] == "done")

                st.caption(_t("posts_exported").format(done_count))

                running = ra.is_analysis_running(run_dir)
                analysis_state = ra.load_analysis_state(run_dir)

                if running:
                    stage = (analysis_state or {}).get("stage", "consolidando")
                    st.caption(_stage_label(stage))
                    if stage == "analizando_sentimiento" and analysis_state.get("total"):
                        processed = analysis_state.get("processed", 0)
                        total = analysis_state["total"]
                        st.progress(processed / total if total else 0)
                        st.caption(_t("comments_counter").format(processed, total))
                    else:
                        st.progress(0)
                else:
                    label = _t("generate_analysis")
                    if analysis_state and analysis_state.get("stage") == "completado":
                        label = _t("regenerate_analysis")

                    use_ai = st.checkbox(
                        _t("use_ai"),
                        key="use_ai_analysis",
                        help=_t("use_ai_help"),
                    )

                    if st.button(label, key="analyze_btn", type="primary"):
                        launch_analysis(run_dir, "ai" if use_ai else "local")
                        st.rerun()

                    if analysis_state and analysis_state.get("stage") == "error":
                        st.error(_t("analysis_error").format(
                            analysis_state.get("error")))

                if analysis_state and analysis_state.get("stage") == "completado":
                    engine_label = (_t("engine_ai") if analysis_state.get("engine") == "ai"
                                    else _t("engine_local"))
                    st.caption(_t("analysis_generated_with").format(engine_label))

                    report_path = os.path.join(run_dir, analysis_state["report_file"])
                    corrected_path = os.path.join(run_dir, CORRECTED_FILENAME)

                    with st.expander(_t("corrected_base")):
                        if os.path.exists(corrected_path):
                            st.success(_t("using_corrected"))
                            if st.button(_t("remove_corrected"),
                                         key="remove_corrected_a"):
                                os.remove(corrected_path)
                                st.rerun()
                        else:
                            st.caption(_t("upload_corrected_caption"))

                        uploader_key_name = "corrected_upload_key_a"
                        if uploader_key_name not in st.session_state:
                            st.session_state[uploader_key_name] = 0

                        uploaded_corrected = st.file_uploader(
                            _t("upload_corrected_xlsx"), type=["xlsx"],
                            key="corrected_a_{}".format(
                                st.session_state[uploader_key_name]),
                        )
                        if uploaded_corrected is not None:
                            try:
                                test_df = pd.read_excel(
                                    uploaded_corrected, sheet_name="Comentarios")
                            except Exception as e:
                                st.error(_t("error_reading_file").format(e))
                                test_df = None

                            if test_df is not None:
                                required = {"Red", "Sentimiento", "Comentario"}
                                if not required.issubset(test_df.columns):
                                    st.error(_t("error_corrected_columns"))
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
                            active_path, mtime, key_prefix="analysis",
                            brand_mapping=_brand_map, show_brand_comparison=True)

                        with open(active_path, "rb") as f:
                            report_bytes = f.read()
                        st.download_button(
                            _t("download_analysis"),
                            data=report_bytes,
                            file_name="analisis.xlsx",
                            mime="application/vnd.openxmlformats-officedocument"
                                 ".spreadsheetml.sheet",
                        )

            render_analysis(run_dir)

    else:
        st.caption(_t("upload_any_file"))

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
            _t("upload_xlsx_csv"), type=["xlsx", "csv"],
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
                st.error(_t("error_reading_file").format(e))
                raw_up = None
                up_cols = []

            if raw_up is not None and up_cols:
                st.caption(_t("map_columns"))
                _na = _t("col_not_available")
                _opt = [_na] + up_cols

                _ac1, _ac2 = st.columns(2)
                _det = _detect_analysis_col
                m_comment = _ac1.selectbox(
                    _t("col_comment_required"), up_cols,
                    index=up_cols.index(_det("Comentario", up_cols)) if _det("Comentario", up_cols) else 0,
                    key="umap_comment",
                )
                m_red = _ac2.selectbox(
                    _t("col_network_required"), up_cols,
                    index=up_cols.index(_det("Red", up_cols)) if _det("Red", up_cols) else 0,
                    key="umap_red",
                )
                m_sent = _ac1.selectbox(
                    _t("col_sentiment"), _opt,
                    index=_opt.index(_det("Sentimiento", up_cols) or _na),
                    key="umap_sent",
                )
                m_marca = _ac2.selectbox(
                    _t("col_brand"), _opt,
                    index=_opt.index(_det("Marca", up_cols) or _na),
                    key="umap_marca",
                )
                m_autor = _ac1.selectbox(
                    _t("col_author"), _opt,
                    index=_opt.index(_det("Autor", up_cols) or _na),
                    key="umap_autor",
                )
                m_likes = _ac2.selectbox(
                    _t("col_likes"), _opt,
                    index=_opt.index(_det("Likes", up_cols) or _na),
                    key="umap_likes",
                )
                m_fecha = _ac1.selectbox(
                    _t("col_comment_date"), _opt,
                    index=_opt.index(_det("Fecha del comentario", up_cols) or _na),
                    key="umap_fecha",
                )
                m_link = _ac2.selectbox(
                    _t("col_post_link"), _opt,
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

                st.caption(_t("rows_columns_mapped").format(
                    len(mapped_up), len(col_map)))
                preview_cols = [c for c in ["Red", "Marca", "Autor", "Comentario",
                                            "Likes", "Sentimiento"] if c in mapped_up.columns]
                st.dataframe(mapped_up[preview_cols].head(10), hide_index=True,
                             use_container_width=True)

                if st.button(_t("load_base"), type="primary", key="load_base"):
                    mapped_up.to_excel(base_path, sheet_name="Comentarios", index=False)
                    st.session_state["upload_base_uploader_key"] += 1
                    st.rerun()

        if os.path.exists(base_path):
            if st.button(_t("remove_uploaded_base")):
                os.remove(base_path)
                st.rerun()

            mtime = os.path.getmtime(base_path)
            render_sentiment_dashboard(
                base_path, mtime, key_prefix="upload_base",
                show_brand_comparison=True)
        else:
            st.info(_t("upload_file_prompt"))


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
    """Retorna (path, brand_mapping) do arquivo ativo para edição."""
    _clasif_src_opts = [_t("clasif_source_run"), _t("clasif_source_upload")]
    source = st.radio(
        _t("data_source"), _clasif_src_opts,
        horizontal=True, key="clasif_source",
    )
    if source == _clasif_src_opts[0]:
        if not _current_has_exports():
            st.info(_t("no_runs_with_analysis"))
            return None, {}
        run_dir = CURRENT_RUN_DIR
        analysis_state = ra.load_analysis_state(run_dir)
        if not analysis_state or analysis_state.get("stage") != "completado":
            st.info(_t("no_analysis_completed"))
            return None, {}
        report_path = os.path.join(run_dir, analysis_state["report_file"])
        corrected = os.path.join(run_dir, CORRECTED_FILENAME)
        bmap = orc.load_state(run_dir).get("brand_mapping", {})
        path = corrected if os.path.exists(corrected) else report_path
        return path, bmap
    else:
        base_path = os.path.join(UPLOADS_DIR, UPLOADED_BASE_FILENAME)
        if not os.path.exists(base_path):
            st.info(_t("no_uploaded_base"))
            return None, {}
        return base_path, {}


with tab_clasif:
    st.caption(_t("clasif_caption"))

    clasif_path, clasif_brand_map = _resolve_clasif_path()
    if clasif_path is not None:
        clasif_df = pd.read_excel(clasif_path, sheet_name="Comentarios")
        clasif_df.columns = [str(c).strip() for c in clasif_df.columns]

        if clasif_brand_map and "Marca" in clasif_df.columns:
            _clm = {}
            for _prof, _desired in clasif_brand_map.items():
                _clm[_prof.strip().lower()] = _desired
                _auto = cons.normalize_brand(_prof)
                if _auto:
                    _clm[_auto.lower()] = _desired
            clasif_df["Marca"] = clasif_df["Marca"].apply(
                lambda m: _clm.get(str(m).strip().lower(), m) if pd.notna(m) else m
            )

        dict_options = tc.available_dictionaries(lang=_lang())
        dict_labels = [name for _, name in dict_options]
        dict_keys = [k for k, _ in dict_options]
        _default_dict = st.session_state.get("selected_dict_key", "servicios_financieros")
        _default_idx = dict_keys.index(_default_dict) if _default_dict in dict_keys else 0
        selected_dict_label = st.selectbox(
            _t("topic_dict"), dict_labels,
            index=_default_idx, key="clasif_dict_select",
        )
        sel_dict_key = dict_keys[dict_labels.index(selected_dict_label)]
        st.session_state["selected_dict_key"] = sel_dict_key

        clasif_df["Tema"] = tc.classify_series(
            clasif_df["Comentario"].fillna(""), sel_dict_key, lang=_lang())

        topic_list = sorted(tc.topic_names(sel_dict_key, _lang())) + [tc.otros_label(_lang())]

        clasif_df["_sent_display"] = clasif_df["Sentimiento"].map(
            _SENT_DISPLAY).fillna("○ Neutral")

        # ── Filtros ──
        fc1, fc2, fc3 = st.columns(3)
        c_search = fc1.text_input(_t("clasif_search"), key="clasif_search",
                                   placeholder=_t("search_placeholder"))
        c_redes = [_t("clasif_all")] + sorted(clasif_df["Red"].dropna().unique().tolist()) if "Red" in clasif_df.columns else [_t("clasif_all")]
        c_red = fc2.selectbox("Red", c_redes, key="clasif_red_f")
        c_sent = fc3.selectbox(_t("col_sentiment"), [_t("clasif_all_m")] + _SENT_OPTIONS_DISPLAY,
                               key="clasif_sent_f")
        fc5, fc6, fc7 = st.columns(3)
        c_marcas = [_t("clasif_all")] + sorted(clasif_df["Marca"].dropna().unique().tolist()) if "Marca" in clasif_df.columns else [_t("clasif_all")]
        c_marca = fc5.selectbox("Marca", c_marcas, key="clasif_marca_f")
        c_tema = fc6.selectbox("Tema", [_t("clasif_all_m")] + topic_list, key="clasif_tema_f")
        c_links = [_t("clasif_all_m")] + sorted(clasif_df["Link del post"].dropna().unique().tolist()) if "Link del post" in clasif_df.columns else [_t("clasif_all_m")]
        c_link = fc7.selectbox(_t("col_post_link"), c_links, key="clasif_link_f")

        filtered = clasif_df.copy()
        if c_search.strip():
            filtered = filtered[filtered["Comentario"].str.lower().str.contains(
                c_search.strip().lower(), na=False)]
        if c_red != _t("clasif_all") and "Red" in filtered.columns:
            filtered = filtered[filtered["Red"] == c_red]
        if c_sent != _t("clasif_all_m"):
            real_sent = _SENT_FROM_DISPLAY.get(c_sent, c_sent)
            filtered = filtered[filtered["Sentimiento"] == real_sent]
        if c_marca != _t("clasif_all") and "Marca" in filtered.columns:
            filtered = filtered[filtered["Marca"] == c_marca]
        if c_tema != _t("clasif_all_m"):
            filtered = filtered[filtered["Tema"] == c_tema]
        if c_link != _t("clasif_all_m") and "Link del post" in filtered.columns:
            filtered = filtered[filtered["Link del post"] == c_link]

        # ── Paginação (acima da tabela) ──
        if "clasif_page_num" not in st.session_state:
            st.session_state["clasif_page_num"] = 1
        if "clasif_ps" not in st.session_state:
            st.session_state["clasif_ps"] = 50
        page_size = st.session_state["clasif_ps"]
        total_pages = max(1, -(-len(filtered) // page_size))
        if st.session_state["clasif_page_num"] > total_pages:
            st.session_state["clasif_page_num"] = 1
        _pg_prev, _pg_info, _pg_next = st.columns([1, 8, 1])
        if _pg_prev.button("←", disabled=st.session_state["clasif_page_num"] <= 1,
                           key="clasif_prev"):
            st.session_state["clasif_page_num"] -= 1
            st.rerun()
        with _pg_next:
            st.markdown("<div style='display:flex;justify-content:flex-end'>", unsafe_allow_html=True)
            if st.button("→", disabled=st.session_state["clasif_page_num"] >= total_pages,
                         key="clasif_next"):
                st.session_state["clasif_page_num"] += 1
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        page_num = st.session_state["clasif_page_num"]
        _pg_info.markdown(
            "<div style='text-align:center;padding-top:8px'>"
            "{}</div>".format(_t("page_of_html").format(
                page_num, total_pages, len(filtered))),
            unsafe_allow_html=True,
        )

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
                    "Red": st.column_config.TextColumn(_t("col_network")),
                    "_sent_display": st.column_config.SelectboxColumn(
                        _t("sentiment_label"),
                        options=_SENT_OPTIONS_DISPLAY,
                        required=True,
                    ),
                    "Tema": st.column_config.SelectboxColumn(
                        _t("topic_label"),
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
                height=min(page_size * 38 + 40, 3850),
            )
            if st.form_submit_button(_t("save_changes"), type="primary"):
                edited_sent = edited["_sent_display"].map(_SENT_FROM_DISPLAY)
                clasif_df.loc[edited.index, "Sentimiento"] = edited_sent.values
                clasif_df.loc[edited.index, "Tema"] = edited["Tema"].values
                save_cols = [c for c in clasif_df.columns if c != "_sent_display"]
                clasif_df[save_cols].to_excel(
                    clasif_path, sheet_name="Comentarios", index=False)
                st.success(_t("changes_saved"))
                st.rerun()

        _ps_sel = st.pills(_t("comments_per_page"), [25, 50, 100],
                           default=st.session_state.get("clasif_ps", 50),
                           key="clasif_ps_pills")
        if _ps_sel and _ps_sel != st.session_state.get("clasif_ps"):
            st.session_state["clasif_ps"] = _ps_sel
            st.session_state["clasif_page_num"] = 1
            st.rerun()

        st.download_button(
            _t("download_corrected"),
            data=open(clasif_path, "rb").read(),
            file_name="base_clasificada.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


with tab_ipds:
    st.caption(_t("ipds_caption"))

    with st.expander(_t("ipds_methodology")):
        st.markdown(_t("ipds_methodology_text"))


    if "ipds_uploader_key" not in st.session_state:
        st.session_state["ipds_uploader_key"] = 0

    ipds_file = st.file_uploader(
        _t("ipds_upload"), type=["xlsx", "csv"],
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
            st.error(_t("error_reading_file").format(e))
            ipds_raw = None
            ip_cols = []

        if ipds_raw is not None and ip_cols:
            st.caption(_t("ipds_map_columns"))
            _ina = _t("col_not_available")
            _iopt = [_ina] + ip_cols

            ic1, ic2 = st.columns(2)
            ip_marca = ic1.selectbox(
                _t("ipds_col_profile_required"), ip_cols,
                index=ip_cols.index(_ipds_detect("marca", ip_cols)) if _ipds_detect("marca", ip_cols) else 0,
                key="ipds_marca",
            )
            ip_red = ic2.selectbox(
                _t("ipds_col_network_required"), ip_cols,
                index=ip_cols.index(_ipds_detect("red", ip_cols)) if _ipds_detect("red", ip_cols) else 0,
                key="ipds_red",
            )
            ip_inter = ic1.selectbox(
                _t("ipds_col_interactions_required"), ip_cols,
                index=ip_cols.index(_ipds_detect("interacciones", ip_cols)) if _ipds_detect("interacciones", ip_cols) else 0,
                key="ipds_inter",
            )
            ip_fecha = ic2.selectbox(
                _t("ipds_col_pub_date"), _iopt,
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
                _t("ipds_networks_filter"), all_networks, default=all_networks,
                key="ipds_networks",
            )
            if sel_networks:
                posts_filtered = posts_mapped[posts_mapped["red"].isin(sel_networks)]
            else:
                posts_filtered = posts_mapped

            n_brands = posts_filtered["marca"].nunique()
            st.caption(_t("ipds_brands_networks").format(
                len(posts_filtered), n_brands, len(sel_networks or all_networks)))

            if n_brands < 2:
                st.warning(_t("ipds_min_brands"))
            else:
                if st.button(_t("ipds_calculate"), type="primary", key="calc_ipds"):
                    st.session_state["ipds_ready"] = True

                if st.session_state.get("ipds_ready"):
                    try:
                        ipds_result = ipds.calculate(posts_filtered, lang=_lang())

                        st.plotly_chart(ipds.thermometer_fig(ipds_result, lang=_lang()),
                                        use_container_width=True)

                        dim_fig = ipds.dimensions_bar_fig(ipds_result, lang=_lang())
                        if dim_fig is not None:
                            st.plotly_chart(dim_fig, use_container_width=True)

                        st.subheader(_t("ipds_detail"))
                        st.dataframe(ipds_result, hide_index=True,
                                     use_container_width=True)
                    except Exception as e:
                        st.error(_t("ipds_error").format(e))
