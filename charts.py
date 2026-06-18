"""Gráficos interactivos (Plotly) para el análisis de sentimiento."""
import json
import re

import plotly.express as px
from wordcloud import WordCloud

SENTIMENT_ORDER = ["Positivo", "Neutral", "Negativo"]
SENTIMENT_COLORS = {"Positivo": "#2ecc71", "Neutral": "#95a5a6", "Negativo": "#e74c3c"}

WIPER_PALETTE = ["#182E4C", "#09B7E9", "#A73253", "#8B9297", "#C5A745"]
SENTIMENT_COLORMAPS = {"Positivo": "Greens", "Neutral": "Greys", "Negativo": "Reds"}

SPANISH_STOPWORDS = {
    "a", "al", "algo", "algunas", "algunos", "ante", "antes", "como", "con",
    "contra", "cual", "cuando", "de", "del", "desde", "donde", "durante",
    "e", "el", "ella", "ellas", "ellos", "en", "entre", "era", "eres", "es",
    "esa", "esas", "ese", "eso", "esos", "esta", "estaba", "estado", "estamos",
    "estan", "estar", "estas", "este", "esto", "estos", "estoy", "fue",
    "fueron", "fui", "ha", "habia", "hace", "hacer", "hago", "han", "hasta",
    "hay", "la", "las", "le", "les", "lo", "los", "mas", "me", "mi", "mis",
    "mucho", "muchos", "muy", "nada", "ni", "no", "nos", "nosotros",
    "nuestra", "nuestro", "nuestros", "o", "otra", "otro", "otros", "para",
    "pero", "poco", "por", "porque", "que", "quien", "se", "sera", "ser",
    "si", "sin", "sobre", "son", "soy", "su", "sus", "tambien", "tan",
    "tanto", "te", "tener", "tengo", "ti", "tiene", "tienen", "todo",
    "todos", "tu", "tus", "vez", "cada", "etc", "tras", "sino", "van",
    "dan",
    "un", "una", "uno", "unos", "usted", "ustedes", "vosotros", "y", "ya",
    "yo",
    # con tilde — variantes acentuadas de palabras ya incluidas sin tilde
    "más", "qué", "está", "esté", "están", "así", "día", "días", "puede",
    "pueden", "ahí", "sólo", "aquí", "cómo", "dónde", "cuándo", "según",
    "también", "además", "aún", "sí", "cuál", "quién", "quiénes",
    "éste", "ésta", "éstos", "éstas", "ése", "ésa", "ésos", "ésas",
    "están", "estás", "están", "después", "qué",
    # adverbios y conectores frecuentes que no aportan contenido
    "ahora", "solo", "siempre", "nunca", "jamás", "luego", "pues",
    "entonces", "igual", "tampoco", "mientras", "todavía", "acá",
    "apenas", "claro", "bueno", "allá", "allí",
    # abreviaturas de mensajes de texto
    "x", "q", "k", "m", "tb", "tmb", "xq", "xa",
    # ruido típico de redes sociales
    "jaja", "jajaja", "jajajaja", "jeje", "jejeje", "like", "follow", "vs",
    "https", "http", "com", "www",
    # PT-BR — pronomes, verbos auxiliares e conectores frequentes
    "uma", "umas", "uns", "tem", "pra", "vai", "essa", "isso", "sua",
    "dos", "seu", "foi", "nem", "sem", "mesmo", "pelo", "pela", "fas",
    "você", "vocês", "dele", "dela", "deles", "delas", "nas", "nos",
    "num", "numa", "são", "está", "estão", "ser", "ter", "não", "meu",
    "minha", "teu", "tua", "esse", "esta", "esses", "essas", "isso",
    "aqui", "ali", "lá", "bem", "mal", "sim", "ele", "ela", "eles",
    "elas", "nós", "gente", "tão", "pro", "das", "aos", "dum", "duma",
    "haha", "kkk", "kkkk", "kkkkk", "rsrs",
}

URL_RE = re.compile(r"https?://\S+|www\.\S+")
MENTION_RE = re.compile(r"@\w+")
EMOJI_RE = re.compile(
    "["
    "\U0001F1E6-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U00002190-\U000021FF"
    "️"
    "]+",
    flags=re.UNICODE,
)
WORD_RE = re.compile(r"[a-záàâãéêíóôõúüçñ]+")


def _clean_text_for_wordcloud(text):
    text = text.lower()
    text = URL_RE.sub(" ", text)
    text = MENTION_RE.sub(" ", text)
    text = EMOJI_RE.sub(" ", text)
    text = text.replace("#", " ")
    words = WORD_RE.findall(text)
    words = [w for w in words if len(w) > 2 and w not in SPANISH_STOPWORDS]
    return " ".join(words)


def top_words(texts, n=20):
    """Retorna las n palabras más frecuentes (misma limpieza que la nube)."""
    from collections import Counter
    all_words = []
    for text in texts:
        all_words.extend(_clean_text_for_wordcloud(str(text)).split())
    return Counter(all_words).most_common(n)


def interactive_wordcloud_html(word_counts, click_red=None):
    """Nube de palabras HTML con palabras clicables.
    Usa postMessage para comunicar al padre qué palabra fue clickeada."""
    if not word_counts:
        return None
    max_c = word_counts[0][1]
    min_c = word_counts[-1][1] if len(word_counts) > 1 else max_c
    rng = max(max_c - min_c, 1)

    red_js = "'{}'".format(click_red) if click_red else "null"

    spans = []
    for i, (word, count) in enumerate(word_counts):
        size = 14 + int(28 * (count - min_c) / rng)
        color = WIPER_PALETTE[i % len(WIPER_PALETTE)]
        weight = "bold" if size > 24 else "normal"
        spans.append(
            '<span data-word="{word}" '
            'style="font-size:{size}px;color:{color};cursor:pointer;'
            'padding:3px 6px;display:inline-block;font-weight:{weight};'
            'text-decoration:none;transition:opacity .15s;user-select:none" '
            'onmouseover="this.style.opacity=0.6;this.style.textDecoration=\'underline\'" '
            'onmouseout="this.style.opacity=1;this.style.textDecoration=\'none\'">'
            '{word}</span>'.format(
                size=size, color=color, weight=weight, word=word,
            )
        )

    return (
        '<div style="display:flex;flex-wrap:wrap;align-items:center;'
        'justify-content:center;gap:2px;padding:12px;'
        'background:white;border-radius:8px;min-height:100px">'
        '{spans}</div>'
        '<script>'
        'document.querySelectorAll("[data-word]").forEach(function(el){{'
        'el.addEventListener("click",function(){{'
        'var w=this.dataset.word,r={red};'
        'try{{'
        'var u=new URL(window.parent.location.href);'
        'u.searchParams.set("wc_word",w);'
        'if(r)u.searchParams.set("wc_red",r);'
        'window.parent.location.href=u.toString();'
        '}}catch(e){{'
        'window.parent.postMessage({{type:"wc_click",word:w,red:r}},"*");'
        '}}'
        '}});'
        '}});'
        '</script>'.format(spans='\n'.join(spans), red=red_js)
    )


def _wiper_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    if random_state is not None:
        return random_state.choice(WIPER_PALETTE)
    return WIPER_PALETTE[0]


def wordcloud_image(texts, width=600, height=350, colormap=None):
    """Genera una nube de palabras a partir de una lista de comentarios.
    Retorna una imagen PIL, o None si no queda texto suficiente."""
    full_text = " ".join(str(t) for t in texts)
    cleaned = _clean_text_for_wordcloud(full_text)
    if not cleaned.strip():
        return None

    kwargs = {"colormap": colormap} if colormap else {"color_func": _wiper_color_func}
    wc = WordCloud(
        width=width, height=height, background_color="white", max_words=80,
        collocations=False, **kwargs
    )
    return wc.generate(cleaned).to_image()


def donut_sentiment(df):
    counts = df["sentimiento"].value_counts().reindex(SENTIMENT_ORDER, fill_value=0).reset_index()
    counts.columns = ["Sentimiento", "Cantidad"]
    return px.pie(
        counts, names="Sentimiento", values="Cantidad", hole=0.5,
        color="Sentimiento", color_discrete_map=SENTIMENT_COLORS,
        title="Sentimiento general",
    )


def bar_by_network(df):
    by_network = df.groupby(["red", "sentimiento"]).size().reset_index(name="Cantidad")
    return px.bar(
        by_network, x="red", y="Cantidad", color="sentimiento",
        barmode="group", category_orders={"sentimiento": SENTIMENT_ORDER},
        color_discrete_map=SENTIMENT_COLORS,
        title="Sentimiento por red", labels={"red": "Red", "sentimiento": "Sentimiento"},
    )


def line_over_time(df):
    with_date = df.dropna(subset=["fecha_comentario"]).copy()
    if with_date.empty:
        return None
    with_date["mes"] = with_date["fecha_comentario"].dt.to_period("M").astype(str)
    over_time = with_date.groupby(["mes", "sentimiento"]).size().reset_index(name="Cantidad")
    return px.line(
        over_time, x="mes", y="Cantidad", color="sentimiento",
        category_orders={"sentimiento": SENTIMENT_ORDER},
        color_discrete_map=SENTIMENT_COLORS,
        title="Sentimiento en el tiempo", markers=True,
        labels={"mes": "Mes", "sentimiento": "Sentimiento"},
    )


def bar_by_brand(df):
    by_brand = df.groupby(["marca", "sentimiento"]).size().reset_index(name="Cantidad")
    return px.bar(
        by_brand, x="marca", y="Cantidad", color="sentimiento",
        barmode="group", category_orders={"sentimiento": SENTIMENT_ORDER},
        color_discrete_map=SENTIMENT_COLORS,
        title="Sentimiento por marca", labels={"marca": "Marca", "sentimiento": "Sentimiento"},
    )


def line_over_time_by_brand(df):
    with_date = df.dropna(subset=["fecha_comentario"]).copy()
    if with_date.empty:
        return None
    with_date["mes"] = with_date["fecha_comentario"].dt.to_period("M").astype(str)
    brand_networks = with_date.groupby("marca")["red"].apply(
        lambda s: ", ".join(sorted(s.dropna().unique()))).to_dict()
    with_date["_marca_label"] = with_date["marca"].map(
        lambda m: "{} ({})".format(m, brand_networks.get(m, "")) if brand_networks.get(m) else m
    )
    over_time = with_date.groupby(["mes", "_marca_label", "sentimiento"]).size().reset_index(name="Cantidad")
    n_brands = over_time["_marca_label"].nunique()
    fig = px.line(
        over_time, x="mes", y="Cantidad", color="sentimiento", facet_col="_marca_label",
        facet_col_wrap=1,
        category_orders={"sentimiento": SENTIMENT_ORDER},
        color_discrete_map=SENTIMENT_COLORS,
        title="Sentimiento por marca en el tiempo", markers=True,
        labels={"mes": "Mes", "sentimiento": "Sentimiento", "_marca_label": "Marca"},
    )
    fig.update_yaxes(matches=None, showticklabels=True)
    fig.update_layout(height=max(350, n_brands * 200))
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=", 1)[-1]))
    return fig


def line_over_time_by_network(df):
    with_date = df.dropna(subset=["fecha_comentario"]).copy()
    if with_date.empty:
        return None
    with_date["mes"] = with_date["fecha_comentario"].dt.to_period("M").astype(str)
    over_time = with_date.groupby(["mes", "red", "sentimiento"]).size().reset_index(name="Cantidad")
    fig = px.line(
        over_time, x="mes", y="Cantidad", color="sentimiento", facet_col="red", facet_col_wrap=2,
        category_orders={"sentimiento": SENTIMENT_ORDER},
        color_discrete_map=SENTIMENT_COLORS,
        title="Sentimiento por red en el tiempo", markers=True,
        labels={"mes": "Mes", "sentimiento": "Sentimiento", "red": "Red"},
    )
    fig.update_yaxes(matches=None, showticklabels=True)
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=", 1)[-1]))
    return fig


def bubble_matrix_tema_sentimiento(df, tema_col="tema"):
    """Bubble matrix: Tema × Sentimiento. Tamaño = cantidad de comentarios."""
    if tema_col not in df.columns or "sentimiento" not in df.columns:
        return None
    filtered = df[~df[tema_col].isin(["Otros", "Outros"])]
    agg = (filtered.groupby([tema_col, "sentimiento"]).size()
           .reset_index(name="Cantidad"))
    if agg.empty:
        return None
    fig = px.scatter(
        agg, x="sentimiento", y=tema_col, size="Cantidad", color="sentimiento",
        size_max=50,
        category_orders={"sentimiento": SENTIMENT_ORDER},
        color_discrete_map=SENTIMENT_COLORS,
        title="Temas × Sentimiento",
        labels={tema_col: "Tema", "sentimiento": "Sentimiento", "Cantidad": "Comentarios"},
    )
    fig.update_layout(showlegend=False, yaxis={"categoryorder": "total ascending"})
    return fig


def bubble_prioridad(df, tema_col="tema"):
    """Bubble de prioridad: X=volumen, Y=%negativo, tamaño=likes, color=tema."""
    if tema_col not in df.columns or "sentimiento" not in df.columns:
        return None
    filtered = df[~df[tema_col].isin(["Otros", "Outros"])]
    grouped = filtered.groupby(tema_col).agg(
        Comentarios=("sentimiento", "size"),
        Negativos=("sentimiento", lambda s: (s == "Negativo").sum()),
        Likes=("likes", lambda s: s.fillna(0).sum() if "likes" in df.columns else 0),
    ).reset_index()
    grouped["% Negativo"] = (grouped["Negativos"] / grouped["Comentarios"] * 100).round(1)
    grouped["Likes"] = grouped["Likes"].fillna(0).astype(int)
    grouped = grouped[grouped["Comentarios"] > 0]
    if grouped.empty:
        return None
    fig = px.scatter(
        grouped, x="Comentarios", y="% Negativo",
        size="Likes", color=tema_col, text=tema_col,
        size_max=50,
        title="Prioridad: volumen × negatividad × engagement",
        labels={tema_col: "Tema"},
    )
    fig.update_traces(textposition="top center", textfont_size=10)
    fig.update_layout(showlegend=False)
    return fig


def heatmap_tema_red(df, tema_col="tema"):
    """Heatmap: Tema × Red. Color = cantidad de comentarios."""
    if tema_col not in df.columns or "red" not in df.columns:
        return None
    filtered = df[~df[tema_col].isin(["Otros", "Outros"])]
    agg = (filtered.groupby([tema_col, "red"]).size()
           .reset_index(name="Cantidad"))
    if agg.empty:
        return None
    pivot = agg.pivot(index=tema_col, columns="red", values="Cantidad").fillna(0)
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=True).index]
    import plotly.graph_objects as go
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[[0, "#f0f2f6"], [1, "#A73253"]],
        texttemplate="%{z:.0f}",
        hovertemplate="Tema: %{y}<br>Red: %{x}<br>Comentarios: %{z}<extra></extra>",
    ))
    fig.update_layout(
        title="Temas × Red",
        xaxis_title="Red",
        yaxis_title="Tema",
    )
    return fig


TREE_WORD_RE = re.compile(r"[a-záàâãéêíóôõúüçñ]+")


def _tokenize_for_wordtree(text):
    text = str(text).lower()
    text = URL_RE.sub(" ", text)
    text = MENTION_RE.sub(" ", text)
    text = EMOJI_RE.sub(" ", text)
    text = text.replace("#", " ")
    return TREE_WORD_RE.findall(text)


WORD_TREE_VERSION = "11"

# Pontuação forte que marca fim de oração
_SENT_PUNCT_RE = re.compile(r"[.!?;]")


def _truncate(text, max_len=100):
    s = str(text).strip()
    return s if len(s) <= max_len else s[:max_len - 1].rstrip() + "…"


def tag_texts_for_wordtree(texts):
    """Tokeniza los comentarios en palabras + marcadores __PUNCT__ de límite
    de oración. Sin POS-tagging — el árbol de 3 niveles no lo necesita."""
    result = []
    for text in texts:
        tagged = []
        for segment in _SENT_PUNCT_RE.split(str(text)):
            for w in TREE_WORD_RE.findall(segment.lower()):
                tagged.append((w, "WORD"))
            tagged.append(("__PUNCT__", "PUNCT"))
        result.append(tagged)
    return result


def build_word_tree(tagged_texts, root_phrase, max_children=6, max_phrase_words=6,
                    full_texts=None, likes=None, sentiments=None):
    """Árbol de 3 niveles: keyword → palabras más usadas → comentarios reales.

    Nivel 1: palabras de contenido más frecuentes en las continuaciones de
    root_phrase (sin stopwords).
    Nivel 2: si se proporcionan full_texts, los comentarios originales que
    contienen la palabra, ordenados por likes descendente (deduplicados por
    índice). Sin full_texts, cae a frases de continuación como antes.

    Retorna un dict {"name", "value", "children"} para d3.hierarchy,
    o None si root_phrase no aparece en los textos."""
    root_tokens = TREE_WORD_RE.findall(root_phrase.lower())
    if not root_tokens:
        return None

    n = len(root_tokens)
    root_node = {"name": " ".join(root_tokens), "value": 0}
    word_counts = {}
    # full_texts mode:  word → {text_idx → (likes_val, display_text)}
    # fallback mode:    word → {phrase_str → count}
    word_leaves = {}

    for text_idx, tagged in enumerate(tagged_texts):
        words = [w for w, _ in tagged]

        # pre-resolve comment data for this index
        if full_texts is not None:
            display_text = str(full_texts[text_idx]).strip()
            try:
                lk = float(likes[text_idx]) if likes is not None else 0.0
                likes_val = lk if lk == lk else 0.0  # NaN guard
            except (TypeError, ValueError):
                likes_val = 0.0
            sentiment_val = str(sentiments[text_idx]) if sentiments is not None else "Neutral"
        else:
            display_text = None
            likes_val = 0.0
            sentiment_val = "Neutral"

        for i in range(len(words) - n + 1):
            if words[i:i + n] != root_tokens:
                continue

            root_node["value"] += 1

            continuation = []
            for k in range(i + n, len(words)):
                w = words[k]
                if w == "__PUNCT__":
                    break
                if len(w) >= 2:
                    continuation.append(w)
                if len(continuation) >= max_phrase_words:
                    break

            if not continuation:
                continue

            seen = set()
            for w in continuation:
                if w in SPANISH_STOPWORDS or len(w) < 3 or w in seen:
                    continue
                seen.add(w)
                word_counts[w] = word_counts.get(w, 0) + 1
                if w not in word_leaves:
                    word_leaves[w] = {}

                if full_texts is not None:
                    # deduplicate by comment index; keep highest likes on conflict
                    if text_idx not in word_leaves[w]:
                        word_leaves[w][text_idx] = (likes_val, display_text, sentiment_val)
                    elif likes_val > word_leaves[w][text_idx][0]:
                        word_leaves[w][text_idx] = (likes_val, display_text, sentiment_val)
                else:
                    phrase = " ".join(continuation)
                    word_leaves[w][phrase] = word_leaves[w].get(phrase, 0) + 1

    if root_node["value"] == 0:
        return None

    top_words = sorted(word_counts.items(), key=lambda x: -x[1])[:max_children]

    root_node["children"] = []
    for word, count in top_words:
        leaves = word_leaves.get(word, {})
        if full_texts is not None:
            sorted_leaves = sorted(leaves.values(), key=lambda x: -x[0])[:max_children]
            leaf_nodes = [{"name": text, "value": max(int(lk), 1), "sentiment": sent}
                          for lk, text, sent in sorted_leaves]
        else:
            top_phrases = sorted(leaves.items(), key=lambda x: -x[1])[:max_children]
            leaf_nodes = [{"name": ph, "value": cnt} for ph, cnt in top_phrases]

        root_node["children"].append({
            "name": word,
            "value": count,
            "children": leaf_nodes,
        })

    return root_node


def _count_leaves(node):
    children = node.get("children")
    if not children:
        return 1
    return sum(_count_leaves(c) for c in children)


def word_tree_height(tree_data, node_height=34, min_height=320):
    # Fixed height — user navigates the tree by dragging (pan/zoom)
    return 580


_WORD_TREE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
  html, body { margin: 0; padding: 0; overflow: hidden; width: 100%; height: 100%; background: white; }
  body { font-family: -apple-system, Segoe UI, Roboto, sans-serif; }
  svg { display: block; width: 100%; height: 100%; cursor: grab; user-select: none; }
  svg:active { cursor: grabbing; }
  #hint { position: fixed; bottom: 8px; right: 10px; font-size: 11px; color: #bbb;
          pointer-events: none; font-family: -apple-system, Segoe UI, sans-serif; }
</style>
</head>
<body>
<svg id="tree"></svg>
<div id="hint">Arrastra para navegar &nbsp;·&nbsp; Scroll para ampliar</div>
<script>
const data = __DATA_JSON__;

const root = d3.hierarchy(data);
const dx = 28;
const dy = window.innerWidth / (root.height + 1);

const treeLayout = d3.tree().nodeSize([dx, dy]);
treeLayout(root);

const maxValue = data.value || 1;
const strokeScale = d3.scaleLinear().domain([0, maxValue]).range([1.5, 16]).clamp(true);
const fontScale = d3.scaleLinear().domain([0, maxValue]).range([13, 24]).clamp(true);
const diagonal = d3.linkHorizontal().x(d => d.y).y(d => d.x);

const svg = d3.select("#tree");
const g = svg.append("g");

g.append("g")
    .attr("fill", "none")
    .attr("stroke", "#C8CDD2")
  .selectAll("path")
  .data(root.links())
  .join("path")
    .attr("stroke-width", d => strokeScale(d.target.data.value))
    .attr("d", diagonal);

const node = g.append("g")
  .selectAll("g")
  .data(root.descendants())
  .join("g")
    .attr("transform", d => `translate(${d.y},${d.x})`);

node.append("circle")
    .attr("fill", d => {
      if (d.depth === 0) return "#A73253";
      if (!d.children) {
        if (d.data.sentiment === "Positivo") return "#2ecc71";
        if (d.data.sentiment === "Negativo") return "#e74c3c";
        return "#95a5a6";
      }
      return "#09B7E9";
    })
    .attr("r", d => d.depth === 0 ? 7 : (d.children ? 4 : 5));

node.append("text")
    .attr("dy", "0.31em")
    .attr("x", d => d.children ? -8 : 8)
    .attr("text-anchor", d => d.children ? "end" : "start")
    .attr("font-size", d => fontScale(d.data.value))
    .attr("font-weight", d => d.depth === 0 ? "bold" : "normal")
    .attr("fill", "#182E4C")
    .text(d => d.children ? d.data.name + " (" + d.data.value + ")" : d.data.name)
  .clone(true).lower()
    .attr("stroke", "white")
    .attr("stroke-width", 3);

// Pan + zoom: drag moves the tree, scroll wheel zooms in/out
const zoom = d3.zoom()
    .scaleExtent([0.1, 4])
    .on("zoom", event => g.attr("transform", event.transform));

svg.call(zoom);

// Initial position: root circle 60px from left edge, vertically centred
const initX = 60;
const initY = window.innerHeight / 2 - root.x;
svg.call(zoom.transform, d3.zoomIdentity.translate(initX, initY));
</script>
</body>
</html>
"""


def word_tree_html(tree_data, width=1100):
    return _WORD_TREE_TEMPLATE.replace(
        "__DATA_JSON__", json.dumps(tree_data, ensure_ascii=False)
    )
