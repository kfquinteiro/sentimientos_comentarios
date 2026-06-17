"""Análisis de sentimiento en español usando Claude (Anthropic) - opcional,
alternativa con más matices que el modelo local para jerga, sarcasmo y
contexto bancario."""
import json
import os
import time

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-haiku-4-5-20251001"
BATCH_SIZE = 20
MAX_RETRIES = 3
VALID_LABELS = {"Positivo", "Negativo", "Neutral"}

SYSTEM_PROMPT = (
    "Eres un analista de redes sociales especializado en servicios "
    "financieros. Analizas comentarios en publicaciones de marcas mexicanas "
    "que operan tarjetas de crédito (Facebook, Instagram, TikTok, YouTube).\n\n"
    "Recibirás un array JSON de objetos con la forma "
    '{"id": <número>, "texto": "<comentario>"}.\n\n'
    "Para cada objeto, clasifica el sentimiento del usuario hacia la marca "
    "o la publicación como exactamente una de estas opciones: "
    '"Positivo", "Negativo" o "Neutral".\n'
    '- "Negativo": quejas, reclamos, críticas, sarcasmo negativo, insultos. '
    "Incluye temas típicos de tarjetas de crédito como comisiones o cargos "
    "no reconocidos, fraude, clonación, cobros de intereses excesivos, "
    "bloqueos o cancelaciones de tarjeta, mal servicio al cliente, demoras "
    "en aclaraciones o reembolsos, rechazo de solicitudes, y quejas sobre "
    "restricciones operativas (ej: límites de retiro en cajero, exigencia "
    "de huella/biométricos o NIP, fallas del sistema o de la app). El uso "
    "de lenguaje vulgar o groserías para expresar frustración (ej: "
    "\"nefasto\", \"mmda\", \"chingados\") refuerza que es Negativo. También "
    "clasifica como Negativo las declaraciones de rechazo o desuso de la "
    "marca (ej: \"no veo/uso/compro en [marca]\", \"ya no soy cliente\", "
    "\"me cambié de banco\").\n"
    '- "Positivo": elogios, agradecimientos, satisfacción con el servicio, '
    "o comentarios favorables sobre beneficios y promociones (cashback, "
    "puntos, millas, meses sin intereses, etc.). También cuenta como "
    "Positivo la participación en sorteos/dinámicas (ej: \"40 balones\", "
    "números o emojis de participación, hashtags de la promoción). Si el "
    "comentario es solo un nombre de persona, una mención con @ o una "
    "etiqueta a otro usuario (con o sin texto adicional), clasifícalo "
    "como Positivo: es alguien invitando a un conocido a participar en la "
    "promoción. También clasifica como Positivo las expresiones de "
    "confianza o seguridad en la marca, aunque estén formuladas como "
    "afirmaciones (ej: \"banco confiable, mi dinero está seguro\").\n"
    '- "Neutral": preguntas y comentarios informativos o ambiguos sin carga '
    "emocional clara (ej: dudas sobre cómo activar algo, horarios, "
    "requisitos, sucursales).\n\n"
    "Presta especial atención a los emojis como señal de sentimiento, "
    "incluso si el texto es mínimo o no hay texto:\n"
    '- 🔥, 😍, ❤️, 👏, 💪, 🙌, 🎉, 👍 indican entusiasmo o aprobación → '
    'Positivo (ej: "🔥🔥🔥" o "🔥 #HotSale" son Positivo).\n'
    "- 😡, 🤬, 💔, 👎, 😞 indican molestia o decepción → Negativo.\n"
    "Considera también jerga y modismos en español de México y sarcasmo.\n\n"
    "Responde ÚNICAMENTE con un array JSON de objetos con la forma "
    '{"id": <número>, "sentimiento": "Positivo"|"Negativo"|"Neutral"}, '
    "incluyendo un objeto por cada comentario recibido y conservando su "
    '"id" original. No agregues explicaciones ni texto adicional. Ejemplo '
    'de respuesta: [{"id": 0, "sentimiento": "Positivo"}, {"id": 1, '
    '"sentimiento": "Neutral"}]'
)


def _client():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Falta ANTHROPIC_API_KEY en el archivo .env para usar el análisis con IA."
        )
    return Anthropic(api_key=api_key)


def _extract_json_array(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("La respuesta de la IA no contiene un array JSON.")
    return json.loads(text[start:end + 1])


def _classify_batch(client, texts):
    indexed = [{"id": i, "texto": t} for i, t in enumerate(texts)]
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": json.dumps(indexed, ensure_ascii=False)}],
            )
            items = _extract_json_array(response.content[0].text)
            by_id = {}
            for item in items:
                label = item.get("sentimiento")
                by_id[item.get("id")] = label if label in VALID_LABELS else "Neutral"
            return [by_id.get(i, "Neutral") for i in range(len(texts))]
        except Exception:
            time.sleep(2 ** attempt)
    # Tras agotar los reintentos, no abortamos todo el análisis por un lote:
    # se clasifica como Neutral y se sigue con el resto.
    return ["Neutral"] * len(texts)


def analyze(texts, batch_size=BATCH_SIZE, on_progress=None):
    """Recibe una lista de textos y retorna (sentimientos, confianzas).

    Usa la API de Claude (Anthropic) para clasificar el sentimiento en
    lotes de `batch_size` comentarios. `confianzas` siempre es None ya que
    Claude no entrega un puntaje de probabilidad como el modelo local.
    """
    client = _client()
    texts = list(texts)
    sentiments = []

    for i in range(0, len(texts), batch_size):
        chunk = [str(t) for t in texts[i:i + batch_size]]
        sentiments.extend(_classify_batch(client, chunk))
        if on_progress:
            on_progress(min(i + batch_size, len(texts)), len(texts))

    confidences = [None] * len(sentiments)
    return sentiments, confidences
