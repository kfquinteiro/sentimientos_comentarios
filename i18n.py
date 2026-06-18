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
}


def t(key, lang="pt"):
    """Retorna o texto traduzido para o idioma indicado."""
    entry = TEXTS.get(key)
    if entry is None:
        return key
    return entry.get(lang, entry.get("pt", key))
