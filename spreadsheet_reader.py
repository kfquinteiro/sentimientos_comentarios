"""Leitura de planilhas de posts para extrair links — aceita qualquer
formato com mapeamento de colunas definido pelo usuário."""
import pandas as pd

LINK_COLUMN_CANDIDATES = {"link", "url"}
HEADER_SEARCH_ROWS = 15

STANDARD_COLUMNS = ["link", "network", "profile", "date"]


def _detect_header_row(file_path):
    """Tenta achar a linha de cabeçalho buscando 'Link'/'URL' nas primeiras linhas."""
    raw = pd.read_excel(file_path, sheet_name=0, header=None, nrows=HEADER_SEARCH_ROWS)
    for i in range(len(raw)):
        values = {str(v).strip().lower() for v in raw.iloc[i].tolist() if pd.notna(v)}
        if values & LINK_COLUMN_CANDIDATES:
            return i
    return 0


def read_raw_file(file_path):
    """Lee cualquier archivo (XLSX o CSV) y retorna un DataFrame crudo con
    detección automática de la fila de cabecera para XLSX."""
    if file_path.lower().endswith(".csv"):
        return pd.read_csv(file_path)
    header_row = _detect_header_row(file_path)
    df = pd.read_excel(file_path, sheet_name=0, header=header_row)
    df = df.dropna(axis=1, how="all")
    df.columns = [str(c).strip() for c in df.columns]
    return df


def read_with_mapping(file_path, column_mapping):
    """Lee un archivo y aplica el mapeo de columnas del usuario.
    column_mapping: {"link": "NombreOriginal", "network": "NombreOriginal", ...}
    """
    df = read_raw_file(file_path)
    rename = {v: k for k, v in column_mapping.items() if v}
    df = df.rename(columns=rename)

    if "link" not in df.columns:
        raise ValueError("No se encontró la columna de links en el mapeo")

    df["link"] = df["link"].astype(str).str.strip()
    df = df[df["link"].str.startswith("http")]
    df = df.drop_duplicates(subset="link").reset_index(drop=True)

    keep = [c for c in STANDARD_COLUMNS if c in df.columns]
    return df[keep]


def read_links(file_path, column_mapping=None):
    """Retorna um DataFrame com as colunas padrão (link, network, profile, date).
    Se column_mapping for fornecido, usa-o. Senão, tenta detectar automaticamente
    pelo formato Fanpage Karma."""
    if column_mapping:
        return read_with_mapping(file_path, column_mapping)

    df = read_raw_file(file_path)

    rename_map = {}
    for col in df.columns:
        key = col.strip().lower()
        if key in LINK_COLUMN_CANDIDATES:
            rename_map[col] = "link"
        elif key == "network":
            rename_map[col] = "network"
        elif key == "profile":
            rename_map[col] = "profile"
        elif key == "message-id":
            rename_map[col] = "message_id"
        elif key == "date":
            rename_map[col] = "date"
    df = df.rename(columns=rename_map)

    if "link" not in df.columns:
        raise ValueError("Coluna 'link' não encontrada na planilha")

    df["link"] = df["link"].astype(str).str.strip()
    df = df[df["link"].str.startswith("http")]
    df = df.drop_duplicates(subset="link").reset_index(drop=True)

    keep = [c for c in STANDARD_COLUMNS + ["message_id"] if c in df.columns]
    return df[keep]
