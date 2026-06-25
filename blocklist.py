"""Blocklist de palavras para negativização automática de comentários.

Após a análise de sentimento, comentários que contenham qualquer
palavra desta lista são forçados para 'Negativo'.
Também filtra spam (links de promoção externa, bots).
"""

NEGATIVE_WORDS = {
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
}

NEUTRAL_WORDS = {
    "tramitar", "solicitarla", "informes", "información", "quiero",
}

SPAM_PATTERNS = [
    "les recomiendo esta app",
    "facebook.com/share/",
    "bit.ly/",
    "click aquí",
    "gana dinero",
]


def apply_blocklist(df, comment_col="comentario", sentiment_col="sentimiento"):
    """Aplica a blocklist ao DataFrame de comentários.

    - Palavras em NEGATIVE_WORDS → força sentimento para 'Negativo'
    - Palavras em NEUTRAL_WORDS → força sentimento para 'Neutral'
    - SPAM_PATTERNS → força sentimento para 'Negativo'

    Retorna o DataFrame modificado e a contagem de alterações.
    """
    changes = 0
    for idx, row in df.iterrows():
        text = str(row.get(comment_col, "")).lower()
        current = row.get(sentiment_col, "")

        for pattern in SPAM_PATTERNS:
            if pattern.lower() in text:
                if current != "Negativo":
                    df.at[idx, sentiment_col] = "Negativo"
                    changes += 1
                break
        else:
            words = set(text.split())
            if words & NEGATIVE_WORDS and current != "Negativo":
                df.at[idx, sentiment_col] = "Negativo"
                changes += 1
            elif words & NEUTRAL_WORDS and not (words & NEGATIVE_WORDS) and current == "Positivo":
                df.at[idx, sentiment_col] = "Neutral"
                changes += 1

    return df, changes
