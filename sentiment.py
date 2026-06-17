"""Análise de sentimento em espanhol usando pysentimiento (RoBERTuito)."""
from pysentimiento import create_analyzer

LABEL_MAP = {
    "POS": "Positivo",
    "NEG": "Negativo",
    "NEU": "Neutral",
}

_analyzer = None


def get_analyzer():
    global _analyzer
    if _analyzer is None:
        _analyzer = create_analyzer(task="sentiment", lang="es")
    return _analyzer


def analyze(texts, chunk_size=200, on_progress=None):
    """Recebe uma lista de textos e retorna (sentimientos, confianzas).

    Processa em blocos de `chunk_size` para limitar o uso de memória e,
    se `on_progress` for informado, chama on_progress(processados, total)
    após cada bloco.
    """
    analyzer = get_analyzer()
    texts = list(texts)
    sentiments, confidences = [], []

    for i in range(0, len(texts), chunk_size):
        chunk = texts[i:i + chunk_size]
        results = analyzer.predict(chunk)
        sentiments.extend(LABEL_MAP.get(r.output, r.output) for r in results)
        confidences.extend(round(r.probas[r.output], 4) for r in results)
        if on_progress:
            on_progress(min(i + chunk_size, len(texts)), len(texts))

    return sentiments, confidences
