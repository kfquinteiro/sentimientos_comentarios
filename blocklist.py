"""Blocklist de palavras para exclusão automática de comentários.

Após a análise de sentimento, comentários que contenham qualquer
palavra ou padrão desta lista são REMOVIDOS do dataset.
"""

EXCLUDE_WORDS = {
    "ratera", "porquería", "fraude", "rateros", "basura", "fraudulento",
    "mala", "malos", "estafaron", "estafa", "clonan", "enemigo",
    "chingada", "huevones", "engañan", "cargos", "gobierno", "política",
    "bendiciones", "cancelar", "roban", "narco", "cartel", "dios",
    "corrupto", "tranzas", "pinches", "mentirosos", "ratas",
    "fastidiando", "pésimo", "malísimo", "milagro", "perdió", "hoyo",
    "molesto", "enojado", "bendiga", "peor", "cobran", "asco", "culera",
    "bot", "imposible", "aclaraciones", "groseros", "hueva", "mamada",
    "mal", "ilegal", "problemas", "buró", "cobranza", "hacker",
    "tiltmix", "cancelación", "molestia", "cancelarla", "error",
    "saturan", "amenazas", "engañar", "cobrar", "falla", "ratota",
    "denuncia", "abusivos", "fatal", "prestamista", "robo", "encajosos",
    "martirio", "milagros", "cupón", "amén",
    "tramitar", "solicitarla", "informes", "información", "quiero",
}

SPAM_PATTERNS = [
    "les recomiendo esta app",
    "facebook.com/share/",
    "bit.ly/",
    "click aquí",
    "gana dinero",
]


def apply_blocklist(df, comment_col="comentario"):
    """Remove comentários que contenham palavras da blocklist ou spam.

    Retorna o DataFrame filtrado e a contagem de removidos.
    """
    original = len(df)

    def _should_exclude(text):
        text = str(text).lower()
        for pattern in SPAM_PATTERNS:
            if pattern.lower() in text:
                return True
        words = set(text.split())
        return bool(words & EXCLUDE_WORDS)

    mask = df[comment_col].apply(_should_exclude)
    filtered = df[~mask].reset_index(drop=True)
    removed = original - len(filtered)
    return filtered, removed
