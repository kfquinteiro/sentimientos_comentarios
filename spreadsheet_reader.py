"""Leitura de planilhas de posts (ex: export do Wiper) para extrair links."""
import pandas as pd

LINK_COLUMN_CANDIDATES = {"link", "url"}
HEADER_SEARCH_ROWS = 15


def find_header_row(file_path):
    """Procura a linha de cabeçalho real, identificando a coluna 'Link'/'URL'."""
    raw = pd.read_excel(file_path, sheet_name=0, header=None, nrows=HEADER_SEARCH_ROWS)
    for i in range(len(raw)):
        values = {str(v).strip().lower() for v in raw.iloc[i].tolist() if pd.notna(v)}
        if values & LINK_COLUMN_CANDIDATES:
            return i
    raise ValueError("Não foi possível encontrar uma coluna 'Link' ou 'URL' na planilha")


def read_links(file_path):
    """Retorna um DataFrame com as colunas 'link' e, se existir, 'network', 'profile', 'message_id'."""
    header_row = find_header_row(file_path)
    df = pd.read_excel(file_path, sheet_name=0, header=header_row)
    df = df.dropna(axis=1, how="all")
    df.columns = [str(c).strip() for c in df.columns]

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
        raise ValueError("Coluna 'link' não encontrada após ler o cabeçalho")

    df["link"] = df["link"].astype(str).str.strip()
    df = df[df["link"].str.startswith("http")]
    df = df.drop_duplicates(subset="link").reset_index(drop=True)

    keep_cols = [c for c in ["link", "network", "profile", "message_id", "date"] if c in df.columns]
    return df[keep_cols]
