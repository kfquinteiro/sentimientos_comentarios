"""Consolida os arquivos de comentários exportados com os metadados dos
posts (planilha original do Fanpage Karma) em um único DataFrame."""
import os
import re

import pandas as pd

import orchestrator as orc
import spreadsheet_reader as sr

HEADER_SEARCH_ROWS = 10

AUTHOR_CANDIDATES = ["Username", "Unique ID", "Name", "Name "]
AUTHOR_ID_CANDIDATES = ["Profile ID", "Channel ID"]
DATE_CANDIDATES = ["Date"]
LIKES_CANDIDATES = ["Likes"]
COMMENT_CANDIDATES = ["Comment"]

OUTPUT_COLUMNS = [
    "marca", "red", "link_post", "fecha_post",
    "autor", "autor_id", "fecha_comentario", "likes", "comentario",
]

CYRILLIC_RE = re.compile(r"[Ѐ-ӿ]")


def is_russian(text):
    """Heurística simple: comentarios con caracteres cirílicos se consideran
    en ruso (típicamente spam/bots) y se excluyen del análisis."""
    return bool(CYRILLIC_RE.search(str(text)))


# Perfis de redes que pertencem à mesma marca mas chegam com nomes
# diferentes em cada rede (ex: TikTok 'bancoplata'/'platacard' vs.
# Facebook/Instagram/YouTube 'Banco Plata'). A chave é o nome do perfil
# em minúsculas, sem espaços/underscores e sem o sufixo 'mx'.
BRAND_ALIASES = {
    "bancoplata": "Plata Card",
    "platacard": "Plata Card",
}


def normalize_brand(profile):
    """Normaliza variações de um mesmo perfil (ex: 'banorte_mx', 'Banorte_mx',
    'bancoplata', 'platacard') para um nome de marca único (ex: 'Banorte',
    'Plata Card')."""
    if not isinstance(profile, str) or not profile.strip():
        return None
    name = re.sub(r"[_\s]*mx$", "", profile.strip(), flags=re.IGNORECASE).strip()
    name = name or profile.strip()

    key = re.sub(r"[\s_]+", "", name.lower())
    if key in BRAND_ALIASES:
        return BRAND_ALIASES[key]

    return name[:1].upper() + name[1:]


def find_comment_header_row(file_path):
    raw = pd.read_excel(file_path, sheet_name=0, header=None, nrows=HEADER_SEARCH_ROWS)
    for i in range(len(raw)):
        values = {str(v).strip() for v in raw.iloc[i].tolist() if pd.notna(v)}
        if "Comment" in values and "Date" in values:
            return i
    raise ValueError("Não foi possível localizar o cabeçalho de comentários em {}".format(file_path))


def pick_column(columns, candidates):
    for cand in candidates:
        if cand in columns:
            return cand
    return None


def read_comment_file(file_path):
    """Lê um arquivo de export de comentários e retorna colunas canônicas:
    autor, autor_id, fecha_comentario, likes, comentario."""
    header_row = find_comment_header_row(file_path)
    df = pd.read_excel(file_path, sheet_name=0, header=header_row)
    df = df.dropna(how="all")

    columns = list(df.columns)
    author_col = pick_column(columns, AUTHOR_CANDIDATES)
    author_id_col = pick_column(columns, AUTHOR_ID_CANDIDATES)
    date_col = pick_column(columns, DATE_CANDIDATES)
    likes_col = pick_column(columns, LIKES_CANDIDATES)
    comment_col = pick_column(columns, COMMENT_CANDIDATES)

    if comment_col is None:
        raise ValueError("Coluna 'Comment' não encontrada em {}".format(file_path))

    out = pd.DataFrame()
    out["autor"] = df[author_col] if author_col else None
    out["autor_id"] = df[author_id_col] if author_id_col else None
    out["fecha_comentario"] = pd.to_datetime(df[date_col]) if date_col else None
    out["likes"] = df[likes_col] if likes_col else None
    out["comentario"] = df[comment_col]

    out = out[out["comentario"].notna()]
    out["comentario"] = out["comentario"].astype(str).str.strip()
    out = out[out["comentario"] != ""]
    return out.reset_index(drop=True)


def build_consolidated(run_dir):
    """Lê o estado da run e a planilha original, juntando cada arquivo de
    comentários exportado com os metadados do post correspondente."""
    state = orc.load_state(run_dir)
    source_file = state.get("source_file")
    posts_df = sr.read_links(source_file)
    posts_by_link = posts_df.set_index("link")

    rows = []
    errors = []
    for item in state["items"]:
        if item["status"] != "done" or not item.get("file_name"):
            continue

        file_path = os.path.join(orc.files_dir(run_dir), item["file_name"])
        if not os.path.exists(file_path):
            continue

        try:
            comments = read_comment_file(file_path)
        except Exception as e:
            errors.append((item["link"], str(e)))
            continue

        if comments.empty:
            continue

        link = item["link"]
        post_meta = posts_by_link.loc[link] if link in posts_by_link.index else {}

        comments["marca"] = normalize_brand(post_meta.get("profile") or item.get("profile"))
        comments["red"] = item.get("network") or post_meta.get("network")
        comments["link_post"] = link
        comments["fecha_post"] = post_meta.get("date")
        rows.append(comments)

    if not rows:
        return pd.DataFrame(columns=OUTPUT_COLUMNS), errors

    consolidated = pd.concat(rows, ignore_index=True)
    consolidated = consolidated[~consolidated["comentario"].apply(is_russian)]
    return consolidated[OUTPUT_COLUMNS].reset_index(drop=True), errors
