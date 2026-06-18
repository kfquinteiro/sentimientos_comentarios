"""Sistema de internacionalização — PT-BR (padrão) e ES."""

TEXTS = {
    # ── Layout e navegação ──
    "page_title": {
        "pt": "Análise de Redes Sociais",
        "es": "Análisis de Redes Sociales",
    },
    "page_subtitle": {
        "pt": "Exportação de comentários e análise de sentimento",
        "es": "Exportación de comentarios y análisis de sentimiento",
    },
    "tab_export": {"pt": "Nova exportação", "es": "Nueva exportación"},
    "tab_runs": {"pt": "Execuções", "es": "Ejecuciones"},
    "tab_analysis": {"pt": "Análise", "es": "Análisis"},
    "tab_classification": {"pt": "Classificação", "es": "Clasificación"},
    "tab_ipds": {"pt": "IPD-S", "es": "IPD-S"},

    # ── Login ──
    "login_title": {"pt": "Acesso restrito", "es": "Acceso restringido"},
    "login_password": {"pt": "Senha", "es": "Contraseña"},
    "login_enter": {"pt": "Entrar", "es": "Entrar"},
    "login_error": {"pt": "Senha incorreta.", "es": "Contraseña incorrecta."},

    # ── Tab Exportação ──
    "upload_posts": {
        "pt": "Planilha de posts (.xlsx, .csv)",
        "es": "Hoja de cálculo de posts (.xlsx, .csv)",
    },
    "clear_selection": {"pt": "Limpar seleção", "es": "Limpiar selección"},
    "map_columns": {"pt": "Mapeie as colunas do seu arquivo:", "es": "Mapea las columnas de tu archivo:"},
    "col_link": {"pt": "Link do post (obrigatório)", "es": "Link del post (requerido)"},
    "col_network": {"pt": "Rede social", "es": "Red social"},
    "col_profile": {"pt": "Perfil / Marca", "es": "Perfil / Marca"},
    "col_date": {"pt": "Data de publicação", "es": "Fecha de publicación"},
    "col_not_available": {"pt": "(não disponível)", "es": "(no disponible)"},
    "links_found": {"pt": "{} links encontrados", "es": "{} links encontrados"},
    "start_export": {"pt": "Iniciar exportação", "es": "Iniciar exportación"},

    # ── Tab Execuções ──
    "no_runs": {"pt": "Ainda não há execuções.", "es": "Aún no hay ejecuciones."},
    "execution": {"pt": "Execução", "es": "Ejecución"},
    "delete_execution": {"pt": "Excluir esta execução", "es": "Eliminar esta ejecución"},
    "delete_warning": {
        "pt": "Isso apagará permanentemente todos os arquivos da execução '{}'. Essa ação não pode ser desfeita.",
        "es": "Esto borrará permanentemente todos los archivos de la ejecución '{}'. Esta acción no se puede deshacer.",
    },
    "delete_confirm": {"pt": "Sim, quero excluir esta execução", "es": "Sí, quiero eliminar esta ejecución"},
    "delete_button": {"pt": "Excluir execução", "es": "Eliminar ejecución"},
    "cannot_delete_running": {
        "pt": "Não é possível excluir enquanto a exportação ou análise está em execução.",
        "es": "No se puede eliminar mientras la exportación o el análisis están en ejecución.",
    },
    "total_links": {"pt": "Total de links", "es": "Total de links"},
    "completed": {"pt": "Concluídos", "es": "Completados"},
    "process": {"pt": "Processo", "es": "Proceso"},
    "running": {"pt": "Em execução", "es": "En ejecución"},
    "stopped": {"pt": "Parado", "es": "Detenido"},
    "stop": {"pt": "Parar", "es": "Detener"},
    "continue": {"pt": "Continuar", "es": "Continuar"},
    "retry_failed": {"pt": "Tentar novamente links com erro", "es": "Reintentar links con error al crear job"},
    "details_per_link": {"pt": "Detalhes por link", "es": "Detalles por link"},
    "define_brands": {"pt": "Definir nomes de marca", "es": "Definir nombres de marca"},
    "define_brands_caption": {
        "pt": "Cada perfil de rede social será atribuído à marca que você definir aqui. Salve antes de gerar a análise.",
        "es": "Cada perfil de red social se asignará a la marca que definas aquí. Guarda antes de generar el análisis.",
    },
    "save_brands": {"pt": "Salvar marcas", "es": "Guardar marcas"},
    "brands_saved": {"pt": "Marcas salvas.", "es": "Marcas guardadas."},
    "download_zip": {"pt": "Baixar resultados (ZIP)", "es": "Descargar resultados (ZIP)"},
    "analyze_now": {"pt": "Analisar agora →", "es": "Analizar ahora →"},
    "go_to_analysis": {"pt": "Vá para a aba **Análise** para ver o dashboard.", "es": "Ve a la pestaña **Análisis** para ver el dashboard."},

    # ── Tab Análise ──
    "data_source": {"pt": "Fonte de dados", "es": "Fuente de datos"},
    "exported_run": {"pt": "Execução exportada", "es": "Ejecución exportada"},
    "upload_own_base": {"pt": "Subir base própria", "es": "Subir base propia"},
    "no_runs_with_data": {"pt": "Não há execuções com dados exportados.", "es": "No hay ejecuciones con datos exportados."},
    "posts_exported": {"pt": "{} post(s) com comentários exportados.", "es": "{} post(s) con comentarios exportados."},
    "generate_analysis": {"pt": "Gerar análise", "es": "Generar análisis"},
    "regenerate_analysis": {"pt": "Regenerar análise", "es": "Regenerar análisis"},
    "use_ai": {"pt": "Usar análise com IA (Claude Haiku)", "es": "Usar análisis con IA (Claude Haiku)"},
    "use_ai_help": {
        "pt": "Analisa cada comentário com Claude (Anthropic) em vez do modelo local. Entende melhor sarcasmo, gírias e contexto, mas tem custo por uso da API.",
        "es": "Analiza cada comentario con Claude (Anthropic) en lugar del modelo local. Suele entender mejor el sarcasmo, la jerga y el contexto, pero tiene un costo por uso de la API.",
    },
    "analysis_error": {"pt": "Erro ao gerar a análise: {}", "es": "Error al generar el análisis: {}"},
    "analysis_generated_with": {"pt": "Análise gerada com: {}", "es": "Análisis generado con: {}"},
    "corrected_base": {"pt": "Base corrigida manualmente", "es": "Base corregida manualmente"},
    "using_corrected": {"pt": "Usando a base corrigida que você enviou.", "es": "Usando la base corregida que subiste manualmente."},
    "remove_corrected": {"pt": "Remover base corrigida", "es": "Quitar base corregida"},
    "upload_corrected_caption": {
        "pt": "Baixe o XLSX abaixo, corrija a coluna 'Sentimiento' manualmente e envie aqui.",
        "es": "Descarga el XLSX de abajo, corrige a mano la columna 'Sentimiento' y vuelve a subirlo aquí.",
    },
    "upload_corrected_xlsx": {"pt": "Enviar XLSX corrigido", "es": "Subir XLSX corregido"},
    "download_analysis": {"pt": "Baixar análise (XLSX)", "es": "Descargar análisis (XLSX)"},
    "upload_any_file": {
        "pt": "Envie qualquer arquivo XLSX ou CSV com comentários. Mapeie as colunas do seu arquivo para os campos da análise.",
        "es": "Sube cualquier archivo XLSX o CSV con comentarios. Mapea las columnas de tu archivo a los campos del análisis.",
    },
    "load_base": {"pt": "Carregar base", "es": "Cargar base"},
    "remove_uploaded_base": {"pt": "Remover base enviada", "es": "Quitar base subida"},
    "upload_file_prompt": {"pt": "Envie um arquivo para ver a análise.", "es": "Sube un archivo para ver el análisis."},

    # ── Dashboard ──
    "comments_analyzed": {"pt": "Comentários analisados", "es": "Comentarios analizados"},
    "topic_analysis": {"pt": "Análise por tema", "es": "Análisis por tema"},
    "topic_dict": {"pt": "Dicionário de temas", "es": "Diccionario de temas"},
    "classified": {"pt": "Classificados", "es": "Clasificados"},
    "unclassified": {"pt": "Sem tema (Otros)", "es": "Sin tema (Otros)"},
    "topics_detected": {"pt": "Temas detectados", "es": "Temas detectados"},
    "explore_otros": {"pt": "Explorar comentários sem tema (Otros) — {} comentários", "es": "Explorar comentarios sin tema (Otros) — {} comentarios"},
    "frequent_words_otros": {"pt": "Palavras mais frequentes nos comentários sem classificar:", "es": "Palabras más frecuentes en comentarios sin clasificar:"},
    "click_word_examples": {"pt": "Clique para ver exemplos", "es": "Haz clic para ver ejemplos"},
    "wordcloud_by_network": {"pt": "Nuvem de palavras por rede", "es": "Nube de palabras por red"},
    "click_word_comments": {"pt": "Clique em uma palavra para ver os comentários", "es": "Haz clic en una palabra para ver los comentarios"},
    "comments_with_word": {"pt": "{} comentários com '{}' — mostrando top 10:", "es": "{} comentarios con '{}' — mostrando top 10:"},
    "wordcloud_by_sentiment": {"pt": "Nuvem de palavras por sentimento", "es": "Nube de palabras por sentimiento"},
    "word_tree": {"pt": "Árvore de palavras", "es": "Árbol de palabras"},
    "word_tree_caption": {
        "pt": "Escreva uma palavra ou frase e descubra como os comentários continuam. Ramos mais grossos e textos maiores indicam continuações mais frequentes.",
        "es": "Escribe una palabra o frase y descubre cómo la continúan los comentarios. Las ramas más gruesas y los textos más grandes indican continuaciones más frecuentes.",
    },
    "word_or_phrase": {"pt": "Palavra ou frase", "es": "Palabra o frase"},
    "no_comments_word": {"pt": "Nenhum comentário encontrado com essa palavra ou frase.", "es": "No se encontraron comentarios con esa palabra o frase."},
    "no_comments_brand": {"pt": "Não há comentários para essa marca.", "es": "No hay comentarios para esta marca."},
    "most_interacted": {"pt": "Comentários mais interagidos", "es": "Comentarios más interactuados"},
    "no_likes_data": {"pt": "Não há dados de likes disponíveis.", "es": "No hay datos de likes disponibles."},
    "detractors_lovers": {"pt": "Principais detratores e brand lovers", "es": "Principales detractores y brand lovers"},
    "detractors_caption": {
        "pt": "Usuários que mais comentaram com sentimento negativo (detratores) ou positivo (brand lovers).",
        "es": "Usuarios que más veces comentaron con sentimiento negativo (detractores) o positivo (brand lovers).",
    },
    "main_detractors": {"pt": "Principais detratores", "es": "Principales detractores"},
    "main_lovers": {"pt": "Principais brand lovers", "es": "Principales brand lovers"},
    "no_negative_comments": {"pt": "Não há comentários negativos com autor identificado.", "es": "No hay comentarios negativos con autor identificado."},
    "no_positive_comments": {"pt": "Não há comentários positivos com autor identificado.", "es": "No hay comentarios positivos con autor identificado."},
    "posts_by_month": {"pt": "Posts com mais comentários por mês", "es": "Posts con más comentarios por mes"},
    "brand_comparison": {"pt": "Comparação por marca", "es": "Comparación por marca"},
    "wordcloud_by_brand": {"pt": "Nuvem de palavras por marca", "es": "Nube de palabras por marca"},

    # ── Classificação ──
    "clasif_caption": {
        "pt": "Revise e corrija a classificação de sentimento e tema de cada comentário. As mudanças são salvas no arquivo XLSX que você baixa.",
        "es": "Revisa y corrige la clasificación de sentimiento y tema de cada comentario. Los cambios se guardan en el archivo XLSX que descargas.",
    },
    "clasif_search": {"pt": "Buscar", "es": "Buscar"},
    "clasif_all": {"pt": "Todas", "es": "Todas"},
    "clasif_all_m": {"pt": "Todos", "es": "Todos"},
    "page_of": {"pt": "Página **{}** de **{}** · {} comentários", "es": "Página **{}** de **{}** · {} comentarios"},
    "page_of_html": {"pt": "Página <b>{}</b> de <b>{}</b> · {} comentários", "es": "Página <b>{}</b> de <b>{}</b> · {} comentarios"},
    "save_changes": {"pt": "Salvar alterações", "es": "Guardar cambios"},
    "changes_saved": {"pt": "Alterações salvas.", "es": "Cambios guardados."},
    "download_corrected": {"pt": "Baixar base corrigida (XLSX)", "es": "Descargar base corregida (XLSX)"},
    "comments_per_page": {"pt": "Comentários por página", "es": "Comentarios por página"},
    "no_analysis_completed": {
        "pt": "Esta execução não tem análise concluída. Gere a análise na aba Análise primeiro.",
        "es": "Esta ejecución no tiene análisis completado. Genera el análisis en la pestaña Análisis primero.",
    },
    "no_uploaded_base": {
        "pt": "Não há base enviada. Envie uma na aba Análise.",
        "es": "No hay base subida. Sube una en la pestaña Análisis.",
    },

    # ── IPD-S ──
    "ipds_caption": {
        "pt": "Indicador de Presença Digital Social — compara marcas numa escala de 0 a 1 usando metodologia IDH.",
        "es": "Indicador de Presencia Digital Social — compara marcas en una escala de 0 a 1 usando metodología IDH.",
    },
    "ipds_upload": {"pt": "Base de posts (.xlsx, .csv)", "es": "Base de posts (.xlsx, .csv)"},
    "ipds_interactions": {"pt": "Interações (obrigatório)", "es": "Interacciones (requerido)"},
    "ipds_networks_filter": {"pt": "Redes a incluir", "es": "Redes a incluir"},
    "ipds_brands_networks": {"pt": "{} posts · {} marcas · {} redes", "es": "{} posts · {} marcas · {} redes"},
    "ipds_min_brands": {"pt": "O IPD-S compara marcas entre si. São necessárias pelo menos 2.", "es": "El IPD-S compara marcas entre sí. Se necesitan al menos 2 marcas."},
    "ipds_calculate": {"pt": "Calcular IPD-S", "es": "Calcular IPD-S"},
    "ipds_detail": {"pt": "Detalhe por marca", "es": "Detalle por marca"},
    "ipds_error": {"pt": "Erro ao calcular o IPD-S: {}", "es": "Error al calcular el IPD-S: {}"},

    # ── Stages de análise ──
    "stage_consolidating": {"pt": "Consolidando comentários exportados...", "es": "Consolidando comentarios exportados..."},
    "stage_loading_model": {"pt": "Carregando modelo de análise de sentimento...", "es": "Cargando modelo de análisis de sentimiento..."},
    "stage_analyzing": {"pt": "Pausa para o café... Continuaremos analisando seus dados enquanto isso!", "es": "Pausa para el café... Seguiremos analizando tus datos mientras tanto."},
    "stage_generating_report": {"pt": "Gerando relatório...", "es": "Generando reporte..."},
    "stage_completed": {"pt": "Concluído", "es": "Completado"},
    "stage_error": {"pt": "Erro", "es": "Error"},

    # ── Status labels ──
    "status_pending": {"pt": "Pendente", "es": "Pendiente"},
    "status_creating": {"pt": "Criando", "es": "Creando"},
    "status_queueing": {"pt": "Na fila", "es": "En cola"},
    "status_progress": {"pt": "Em progresso", "es": "En progreso"},
    "status_done": {"pt": "Concluído", "es": "Completado"},
    "status_error": {"pt": "Erro", "es": "Error"},
    "status_timeout": {"pt": "Tempo esgotado", "es": "Tiempo agotado"},
    "status_skipped": {"pt": "Ignorado", "es": "Omitido"},
    "status_no_comments": {"pt": "Sem comentários", "es": "Sin comentarios"},
    "status_post_deleted": {"pt": "Post excluído ou indisponível", "es": "Post eliminado o no disponible"},

    # ── Column labels ──
    "col_label_link": {"pt": "Link", "es": "Link"},
    "col_label_network": {"pt": "Rede", "es": "Red"},
    "col_label_status": {"pt": "Estado", "es": "Estado"},
    "col_label_comments": {"pt": "Comentários", "es": "Comentarios"},
    "col_label_comments_collected": {"pt": "Comentários coletados", "es": "Comentarios recolectados"},
    "col_label_error": {"pt": "Erro", "es": "Error"},
    "col_label_file": {"pt": "Arquivo", "es": "Archivo"},

    # ── Tab Exportação (strings restantes) ──
    "error_reading_file": {"pt": "Erro ao ler o arquivo: {}", "es": "Error al leer el archivo: {}"},
    "error_processing": {"pt": "Erro ao processar: {}", "es": "Error al procesar: {}"},
    "network_count_column": {"pt": "Quantidade", "es": "Cantidad"},

    # ── Tab Execuções (strings restantes) ──
    "avg_time_eta": {
        "pt": "Tempo médio por link: {} · Tempo restante estimado: {} ({} pendentes)",
        "es": "Tiempo promedio por link: {} · Tiempo restante estimado: {} ({} pendientes)",
    },
    "failed_jobs_caption": {"pt": "{} link(s) não conseguiram criar o job de exportação.", "es": "{} link(s) no pudieron crear el job de exportación."},
    "retry_failed_jobs": {"pt": "Reintentar links com erro ao criar job", "es": "Reintentar links con error al crear job"},

    # ── Dashboard (strings restantes) ──
    "visualization": {"pt": "Visualização", "es": "Visualización"},
    "viz_topics_sentiment": {"pt": "Temas × Sentimento", "es": "Temas × Sentimiento"},
    "viz_priority": {"pt": "Prioridade", "es": "Prioridad"},
    "viz_topics_network": {"pt": "Temas × Rede", "es": "Temas × Red"},
    "not_enough_text_cloud": {"pt": "Não há texto suficiente para gerar a nuvem.", "es": "No hay suficiente texto para generar la nube."},
    "no_comments_found_word": {"pt": "Não foram encontrados comentários com '{}'.", "es": "No se encontraron comentarios con '{}'."},
    "no_pub_dates": {"pt": "Não há datas de publicação disponíveis.", "es": "No hay fechas de publicación disponibles."},
    "rows_columns_mapped": {"pt": "{} linhas · {} colunas mapeadas", "es": "{} filas · {} columnas mapeadas"},

    # ── Upload base própria (selectbox labels) ──
    "col_comment_required": {"pt": "Comentário (obrigatório)", "es": "Comentario (requerido)"},
    "col_network_required": {"pt": "Rede / Plataforma (obrigatório)", "es": "Red / Plataforma (requerido)"},
    "col_sentiment": {"pt": "Sentimento", "es": "Sentimiento"},
    "col_brand": {"pt": "Marca", "es": "Marca"},
    "col_author": {"pt": "Autor", "es": "Autor"},
    "col_likes": {"pt": "Likes", "es": "Likes"},
    "col_comment_date": {"pt": "Data do comentário", "es": "Fecha del comentario"},
    "col_post_link": {"pt": "Link do post", "es": "Link del post"},
    "upload_xlsx_csv": {"pt": "Arquivo XLSX ou CSV", "es": "Archivo XLSX o CSV"},

    # ── Análise — engine label ──
    "engine_ai": {"pt": "IA (Claude Haiku)", "es": "IA (Claude Haiku)"},
    "engine_local": {"pt": "modelo local (pysentimiento)", "es": "modelo local (pysentimiento)"},

    # ── Análise — corrected upload errors ──
    "error_corrected_columns": {
        "pt": "O arquivo deve ter uma aba 'Comentarios' com pelo menos as colunas: Red, Sentimiento, Comentario.",
        "es": "El archivo debe tener una hoja 'Comentarios' con al menos las columnas: Red, Sentimiento, Comentario.",
    },

    # ── Tab Classificação (strings restantes) ──
    "clasif_source_run": {"pt": "Execução exportada", "es": "Ejecución exportada"},
    "clasif_source_upload": {"pt": "Base enviada", "es": "Base subida"},
    "no_runs_with_analysis": {"pt": "Não há execuções com análise.", "es": "No hay ejecuciones con análisis."},

    # ── IPDS (strings restantes) ──
    "ipds_methodology": {"pt": "Metodologia do IPD-S", "es": "Metodología del IPD-S"},
    "ipds_what_is": {"pt": "O que é o IPD-S?", "es": "¿Qué es el IPD-S?"},
    "ipds_what_is_desc": {
        "pt": "O Indicador de Presença Digital Social (IPD-S) é um índice composto que avalia a eficácia da comunicação digital de marcas em redes sociais. Inspirado na metodologia do IDH (Índice de Desenvolvimento Humano) do PNUD, combina múltiplas dimensões num único número de 0 a 1.",
        "es": "El Indicador de Presencia Digital Social (IPD-S) es un índice compuesto que evalúa la eficacia de la comunicación digital de marcas en redes sociales. Inspirado en la metodología del IDH (Índice de Desarrollo Humano) del PNUD, combina múltiples dimensiones en un único número de 0 a 1.",
    },
    "ipds_col_profile_required": {"pt": "Perfil / Marca (obrigatório)", "es": "Perfil / Marca (requerido)"},
    "ipds_col_network_required": {"pt": "Rede social (obrigatório)", "es": "Red social (requerido)"},
    "ipds_col_interactions_required": {"pt": "Interações (obrigatório)", "es": "Interacciones (requerido)"},
    "ipds_col_pub_date": {"pt": "Data de publicação", "es": "Fecha de publicación"},
    "ipds_map_columns": {"pt": "Mapeie as colunas do seu arquivo:", "es": "Mapea las columnas de tu archivo:"},

    # ── Comments counter during analysis ──
    "comments_counter": {"pt": "{}/{} comentários", "es": "{}/{} comentarios"},

    # ── Detractors table column headers ──
    "negative_comments_col": {"pt": "Comentários negativos", "es": "Comentarios negativos"},
    "positive_comments_col": {"pt": "Comentários positivos", "es": "Comentarios positivos"},

    # ── Misc ──
    "search_placeholder": {"pt": "Texto...", "es": "Texto..."},

    # ── IPDS methodology ──
    "ipds_methodology_text": {
        "pt": """**O que e o IPD-S?**

O Indicador de Presenca Digital Social (IPD-S) e um indice composto
que avalia a eficacia da comunicacao digital de marcas em redes
sociais. Inspirado na metodologia do IDH (Indice de Desenvolvimento
Humano) do PNUD, combina multiplas dimensoes num unico numero
de 0 a 1.

**Dimensoes**

| Dimensao | O que mede | Como se calcula |
|---|---|---|
| **Atividade** | Frequencia de publicacao | Posts/mes, normalizado por rede |
| **Engagement** | Ressonancia do conteudo | Interacoes/post, normalizado por rede |
| **Multicanal** | Diversificacao de plataformas | N de redes ativas / total de redes |
| **Sentimento** | Saude da percepcao de marca | % de comentarios positivos *(opcional)* |

**Normalizacao por plataforma**

Cada rede social tem um comportamento distinto — o volume de
interacoes no TikTok nao e comparavel ao do Facebook. Por isso, as
dimensoes de Atividade e Engagement sao calculadas **dentro de cada rede**
primeiro (comparando marcas entre si nessa plataforma) e depois sao
agregadas como media dos scores por rede.

Usa-se escala logaritmica (`log(1 + x)`) antes da normalizacao
min-max para suavizar distorcoes causadas por outliers, seguindo
a pratica do IDH para a dimensao de renda.

**Formula**

`IPD-S = (D1 x D2 x D3 x ... x Dn) ^ (1/n)` — media geometrica

A media geometrica (em vez de aritmetica) penaliza desequilibrios:
uma marca com engagement altissimo mas atividade zero nao pode
compensar uma dimensao com a outra.

**Escala e niveis**

| Nivel | Intervalo | Interpretacao |
|---|---|---|
| Muito baixo | 0,00 - 0,20 | Presenca digital fragil ou incipiente |
| Baixo | 0,20 - 0,40 | Presenca abaixo da media do grupo |
| Medio | 0,40 - 0,60 | Presenca media, com espaco para evoluir |
| Alto | 0,60 - 0,80 | Presenca solida e consistente |
| Muito alto | 0,80 - 1,00 | Referencia digital no grupo analisado |

**Como ler o termometro?**

- As marcas posicionadas **mais a esquerda** (zona vermelha/laranja)
  tem uma presenca digital fraca no grupo: publicam pouco,
  geram baixo engagement, ou estao presentes em poucas redes. Precisam
  de atencao e estrategia para melhorar seu posicionamento.
- As marcas posicionadas **mais a direita** (zona verde) dominam
  a conversa digital: publicam com frequencia, geram alto
  engagement relativo a sua plataforma, estao diversificadas em
  multiplas redes e (se ha dados) tem um sentimento positivo.
  Sao a referencia do grupo.

**Limitacoes**

- O IPD-S e relativo ao grupo de marcas analisado, nao absoluto.
  Adicionar ou remover uma marca pode alterar os scores das demais.
- Nao considera dark posts, midia paga isolada, Google, imprensa, Wikipedia
  ou outras camadas do digital fora das redes sociais.
- A dimensao de Sentimento depende da disponibilidade de analise
  de comentarios (pode ser omitida se nao ha dados).
""",
        "es": """**Que es el IPD-S?**

El Indicador de Presencia Digital Social (IPD-S) es un indice compuesto
que evalua la eficacia de la comunicacion digital de marcas en redes
sociales. Inspirado en la metodologia del IDH (Indice de Desarrollo
Humano) del PNUD, combina multiples dimensiones en un unico numero
de 0 a 1.

**Dimensiones**

| Dimension | Que mide | Como se calcula |
|---|---|---|
| **Actividad** | Frecuencia de publicacion | Posts/mes, normalizado por red |
| **Engagement** | Resonancia del contenido | Interacciones/post, normalizado por red |
| **Multicanal** | Diversificacion de plataformas | N de redes activas / total de redes |
| **Sentimiento** | Salud de la percepcion de marca | % de comentarios positivos *(opcional)* |

**Normalizacion por plataforma**

Cada red social tiene un comportamiento distinto — el volumen de
interacciones en TikTok no es comparable al de Facebook. Por eso, las
dimensiones de Actividad y Engagement se calculan **dentro de cada red**
primero (comparando marcas entre si en esa plataforma) y luego se
agregan como promedio de los scores por red.

Se usa escala logaritmica (`log(1 + x)`) antes de la normalizacion
min-max para suavizar distorsiones causadas por outliers, siguiendo
la practica del IDH para la dimension de ingreso.

**Formula**

`IPD-S = (D1 x D2 x D3 x ... x Dn) ^ (1/n)` — media geometrica

La media geometrica (en vez de aritmetica) penaliza desequilibrios:
una marca con engagement altisimo pero actividad cero no puede
compensar una dimension con la otra.

**Escala y niveles**

| Nivel | Intervalo | Interpretacion |
|---|---|---|
| Muy bajo | 0,00 - 0,20 | Presencia digital fragil o incipiente |
| Bajo | 0,20 - 0,40 | Presencia por debajo del promedio del grupo |
| Medio | 0,40 - 0,60 | Presencia promedio, con espacio para evolucionar |
| Alto | 0,60 - 0,80 | Presencia solida y consistente |
| Muy alto | 0,80 - 1,00 | Referencia digital en el grupo analizado |

**Como leer el termometro?**

- Las marcas posicionadas **mas a la izquierda** (zona roja/naranja)
  tienen una presencia digital debil en el grupo: publican poco,
  generan bajo engagement, o estan presentes en pocas redes. Requieren
  atencion y estrategia para mejorar su posicionamiento.
- Las marcas posicionadas **mas a la derecha** (zona verde) dominan
  la conversacion digital: publican con frecuencia, generan alto
  engagement relativo a su plataforma, estan diversificadas en
  multiples redes y (si hay datos) tienen un sentimiento positivo.
  Son la referencia del grupo.

**Limitaciones**

- El IPD-S es relativo al grupo de marcas analizado, no absoluto.
  Agregar o quitar una marca puede alterar los scores de las demas.
- No considera dark posts, pauta aislada, Google, prensa, Wikipedia
  u otras capas del digital fuera de las redes sociales.
- La dimension de Sentimiento depende de la disponibilidad de analisis
  de comentarios (puede omitirse si no hay datos).
""",
    },
    "brand": {"pt": "Marca", "es": "Marca"},
    "col_network": {"pt": "Rede", "es": "Red"},
    "sentiment_label": {"pt": "Sentimento", "es": "Sentimiento"},
    "topic_label": {"pt": "Tema", "es": "Tema"},
}


def t(key, lang="pt"):
    """Retorna o texto traduzido para o idioma indicado."""
    entry = TEXTS.get(key)
    if entry is None:
        return key
    return entry.get(lang, entry.get("pt", key))
