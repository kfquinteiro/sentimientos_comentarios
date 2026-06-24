"""Clasificación de comentarios por tema usando diccionarios de palabras clave.

Cada comentario se asigna a exactamente un tema (el que más keywords
coincida). Si no hay coincidencia, se asigna "Otros".

Dos diccionarios disponibles:
  - politica_br: Política brasileña (segurança, saúde, educação…)
  - servicios_financieros: Servicios financieros (tarjeta, crédito, app…)

Ambos contienen keywords en PT-BR y español latinoamericano.
"""
import re

DICTIONARIES = {
    "politica_br": {
        "name": {"pt": "Política brasileira", "es": "Política brasileña"},
        "topics": {
            "Segurança pública": [
                # PT-BR
                "segurança pública", "polícia", "policial", "crime", "criminoso",
                "criminalidade", "violência urbana", "assalto", "roubo", "furto",
                "homicídio", "assassinato", "tráfico", "drogas", "arma", "armamento",
                "milícia", "facção", "pcc", "presídio", "preso", "cadeia",
                "delegacia", "bombeiro", "tiroteio", "bala perdida", "segurança",
                # ES
                "seguridad pública", "policía", "crimen", "criminal", "criminalidad",
                "asalto", "robo", "hurto", "homicidio", "asesinato", "tráfico",
                "drogas", "arma", "armamento", "milicia", "cárcel", "preso",
                "tiroteo", "bala perdida", "delincuencia",
            ],
            "Saúde": [
                # PT-BR
                "saúde", "sus", "hospital", "médico", "médica", "enfermeiro",
                "enfermeira", "vacina", "vacinação", "remédio", "medicamento",
                "ubs", "upa", "posto de saúde", "pandemia", "covid", "dengue",
                "plano de saúde", "cirurgia", "internação", "leito",
                "atendimento médico", "saúde mental", "psicólogo", "psiquiatra",
                # ES
                "salud", "hospital", "médico", "enfermero", "vacuna", "vacunación",
                "medicamento", "pandemia", "covid", "dengue", "cirugía",
                "internación", "atención médica", "salud mental", "clínica",
            ],
            "Educação": [
                # PT-BR
                "educação", "escola", "professor", "professora", "aluno", "aluna",
                "estudante", "ensino", "universidade", "faculdade", "enem",
                "vestibular", "creche", "alfabetização", "merenda", "piso salarial",
                "aula", "matrícula", "evasão escolar", "ensino público",
                "ensino superior", "bolsa de estudo",
                # ES
                "educación", "escuela", "profesor", "profesora", "alumno",
                "estudiante", "enseñanza", "universidad", "guardería",
                "alfabetización", "beca", "aula", "matrícula", "deserción escolar",
                "educación pública",
            ],
            "Violência contra a mulher": [
                # PT-BR
                "violência contra a mulher", "feminicídio", "assédio", "assédio sexual",
                "maria da penha", "lei maria da penha", "estupro", "abuso sexual",
                "violência doméstica", "agressão", "agressor", "delegacia da mulher",
                "machismo", "misoginia", "importunação sexual",
                # ES
                "violencia contra la mujer", "feminicidio", "acoso", "acoso sexual",
                "violación", "abuso sexual", "violencia doméstica", "agresión",
                "agresor", "machismo", "misoginia", "violencia de género",
            ],
            "Economia": [
                # PT-BR
                "economia", "inflação", "pib", "dólar", "juros", "selic",
                "emprego", "desemprego", "salário", "salário mínimo", "imposto",
                "tributação", "reforma tributária", "dívida pública", "orçamento",
                "fiscal", "custo de vida", "cesta básica", "gasolina", "preço",
                "carestia", "recessão",
                # ES
                "economía", "inflación", "pib", "dólar", "intereses", "empleo",
                "desempleo", "salario", "salario mínimo", "impuesto", "tributación",
                "reforma tributaria", "deuda pública", "presupuesto", "fiscal",
                "costo de vida", "canasta básica", "gasolina", "precio", "recesión",
            ],
            "Meio ambiente": [
                # PT-BR
                "meio ambiente", "desmatamento", "queimada", "amazônia", "floresta",
                "poluição", "sustentabilidade", "clima", "aquecimento global",
                "saneamento", "lixo", "reciclagem", "ibama", "pantanal", "cerrado",
                "biodiversidade", "mudança climática", "emissão de carbono",
                # ES
                "medio ambiente", "deforestación", "incendio", "amazonía", "bosque",
                "contaminación", "sustentabilidad", "clima", "calentamiento global",
                "saneamiento", "basura", "reciclaje", "biodiversidad",
                "cambio climático", "emisión de carbono",
            ],
            "Corrupção": [
                # PT-BR
                "corrupção", "corrupto", "propina", "lavagem de dinheiro", "desvio",
                "lava jato", "cpi", "impeachment", "nepotismo", "mensalão",
                "petrolão", "superfaturamento", "licitação", "fraude", "peculato",
                "improbidade", "enriquecimento ilícito",
                # ES
                "corrupción", "corrupto", "soborno", "lavado de dinero", "desvío",
                "nepotismo", "impeachment", "fraude", "licitación", "peculado",
                "improbidad", "enriquecimiento ilícito",
            ],
            "Infraestrutura": [
                # PT-BR
                "infraestrutura", "estrada", "rodovia", "ferrovia", "ponte", "obra",
                "transporte", "metrô", "ônibus", "aeroporto", "porto",
                "saneamento básico", "esgoto", "pavimentação", "mobilidade urbana",
                "pedágio", "buraco", "asfalto",
                # ES
                "infraestructura", "carretera", "ferrocarril", "puente", "obra",
                "transporte", "metro", "autobús", "aeropuerto", "puerto",
                "alcantarillado", "pavimentación", "movilidad urbana", "peaje",
                "bache", "asfalto",
            ],
            "Habitação": [
                # PT-BR
                "habitação", "moradia", "minha casa minha vida", "aluguel",
                "sem teto", "favela", "desabrigado", "conjunto habitacional",
                "urbanização", "ocupação", "despejo", "casa própria",
                "déficit habitacional", "financiamento imobiliário",
                # ES
                "vivienda", "alquiler", "sin techo", "desalojado",
                "conjunto habitacional", "urbanización", "ocupación", "desalojo",
                "casa propia", "déficit habitacional", "financiamiento inmobiliario",
            ],
            "Direitos humanos": [
                # PT-BR
                "direitos humanos", "racismo", "preconceito", "discriminação",
                "lgbt", "homofobia", "igualdade", "inclusão", "acessibilidade",
                "deficiente", "idoso", "criança", "adolescente", "indígena",
                "quilombola", "refugiado", "intolerância religiosa",
                # ES
                "derechos humanos", "racismo", "prejuicio", "discriminación",
                "lgbt", "homofobia", "igualdad", "inclusión", "accesibilidad",
                "discapacitado", "anciano", "indígena", "refugiado",
                "intolerancia religiosa",
            ],
            "Valores": [
                # PT-BR
                "família", "familiar", "valores", "moral", "costumes",
                "deus", "jesus", "abençoe", "abençoado", "abençoada", "bênção",
                "fé", "igreja", "evangélico", "cristão", "religião", "oração",
                "bíblia", "tradição", "conservador",
                # ES
                "familia", "familiar", "valores", "moral", "costumbres",
                "dios", "jesús", "bendiga", "bendecido", "bendición",
                "fe", "iglesia", "evangélico", "cristiano", "religión", "oración",
                "biblia", "tradición", "conservador",
            ],
            "Manifestação de apoio": [
                # PT-BR
                "parabéns", "parabens", "apoio", "apoiamos", "excelente",
                "orgulho", "obrigado", "obrigada", "gratidão", "mandou bem",
                "arrasou", "bravo", "maravilhoso", "maravilhosa", "melhor",
                "continue assim", "muito bom", "muito boa", "meus parabéns",
                # ES
                "felicidades", "felicitaciones", "apoyo", "apoyamos", "excelente",
                "orgullo", "gracias", "gratitud", "bravo", "maravilloso",
                "maravillosa", "mejor", "sigue así", "muy bien", "enhorabuena",
            ],
            "Democracia": [
                # PT-BR
                "democracia", "democrático", "democrática", "voto", "eleição",
                "eleições", "urna", "urna eletrônica", "constituição", "estado de direito",
                "liberdade de expressão", "liberdade de imprensa", "ditadura",
                "golpe", "golpe de estado", "autoritarismo", "autoritário",
                "censura", "plebiscito", "referendo", "congresso", "senado",
                "câmara", "deputado", "senador", "stf", "supremo",
                "poder judiciário", "separação de poderes", "soberania popular",
                # ES
                "democracia", "democrático", "democrática", "voto", "elección",
                "elecciones", "urna", "constitución", "estado de derecho",
                "libertad de expresión", "libertad de prensa", "dictadura",
                "golpe", "golpe de estado", "autoritarismo", "autoritario",
                "censura", "plebiscito", "referéndum", "congreso", "senado",
                "cámara", "diputado", "senador", "poder judicial",
                "separación de poderes", "soberanía popular",
            ],
            "Clã Bolsonaro": [
                "bolsonaro", "jair bolsonaro", "flávio bolsonaro",
                "carlos bolsonaro", "renan bolsonaro", "eduardo bolsonaro",
                "família bolsonaro", "clan bolsonaro", "bolsonarismo",
                "bolsonarista", "mito",
            ],
        },
    },
    "servicios_financieros": {
        "name": {"pt": "Serviços financeiros", "es": "Servicios financieros"},
        "topics": {
            "Crédito": [
                # PT-BR
                "crédito", "empréstimo", "financiamento", "consignado",
                "crédito pessoal", "parcela", "prestação", "score",
                "nome limpo", "nome sujo", "serasa", "spc", "inadimplente",
                "renegociação", "dívida", "endividamento", "refinanciamento",
                "juros", "taxa de juros", "aprovação de crédito", "limite de crédito",
                # ES
                "crédito", "préstamo", "financiamiento", "cuota", "mensualidad",
                "score", "buró de crédito", "deuda", "endeudamiento",
                "refinanciamiento", "moroso", "reestructuración", "intereses",
                "tasa de interés", "aprobación de crédito", "límite de crédito",
            ],
            "Benefícios": [
                # PT-BR
                "cashback", "pontos", "milhas", "promoção", "desconto",
                "programa de fidelidade", "benefício", "recompensa", "vantagem",
                "resgate", "acumular pontos", "livelo", "smiles", "tudoazul",
                "programa de pontos", "cupom", "ofertas",
                # ES
                "cashback", "puntos", "millas", "promoción", "descuento",
                "programa de lealtad", "beneficio", "recompensa", "ventaja",
                "canje", "acumular puntos", "cupón", "ofertas",
                "programa de puntos", "meses sin intereses",
            ],
            "Investimento": [
                # PT-BR
                "investimento", "renda fixa", "renda variável", "cdb", "lci", "lca",
                "tesouro direto", "ação", "ações", "bolsa", "fundo",
                "rentabilidade", "rendimento", "dividendo", "corretora", "b3",
                "poupança", "aplicação", "resgate", "carteira de investimento",
                # ES
                "inversión", "renta fija", "renta variable", "acción", "acciones",
                "bolsa", "fondo", "rentabilidad", "rendimiento", "dividendo",
                "corredor", "cetes", "bonos", "ahorro", "cartera de inversión",
            ],
            "Segurança": [
                # PT-BR
                "fraude", "golpe", "clonagem", "phishing", "estelionato",
                "hackeado", "invasão", "compra não reconhecida", "bloqueio",
                "desbloqueio", "contestação", "chargeback", "senha vazada",
                "engenharia social", "golpe do pix", "segurança", "proteção",
                "verificação", "autenticação", "token",
                # ES
                "fraude", "estafa", "clonación", "phishing", "hackeado",
                "compra no reconocida", "cargo no reconocido", "bloqueo",
                "desbloqueo", "contestación", "chargeback", "contraseña filtrada",
                "ingeniería social", "seguridad", "protección",
                "verificación", "autenticación", "token",
            ],
            "Cartões": [
                # PT-BR
                "cartão", "cartão de crédito", "cartão de débito", "anuidade",
                "fatura", "bandeira", "visa", "mastercard", "elo", "platinum",
                "gold", "black", "cartão virtual", "cartão adicional",
                "aproximação", "chip", "contactless", "cartão físico",
                # ES
                "tarjeta", "tarjeta de crédito", "tarjeta de débito", "anualidad",
                "estado de cuenta", "visa", "mastercard",
                "tarjeta virtual", "tarjeta adicional", "contactless",
                "chip", "tarjeta física", "plástico",
            ],
            "Pagamentos": [
                # PT-BR
                "pagamento", "boleto", "qr code", "vencimento", "parcelamento",
                "maquininha", "cobrança", "fatura", "débito automático",
                "pagamento por aproximação", "pagar", "compra",
                # ES
                "pago", "factura", "código qr", "vencimiento", "cuotas",
                "terminal", "cobro", "domiciliación", "débito automático",
                "pagar", "compra",
            ],
            "Criptomoedas": [
                # PT-BR
                "bitcoin", "cripto", "criptomoeda", "ethereum", "blockchain",
                "carteira digital", "exchange", "mineração", "nft", "defi",
                "stablecoin", "usdt", "binance", "web3", "altcoin",
                # ES
                "bitcoin", "cripto", "criptomoneda", "ethereum", "blockchain",
                "billetera digital", "exchange", "minería", "nft", "defi",
                "stablecoin", "usdt", "binance", "web3", "altcoin",
            ],
            "Saldo e extrato": [
                # PT-BR
                "saldo", "extrato", "depósito", "saque", "caixa eletrônico",
                "comprovante", "movimentação", "lançamento", "conta corrente",
                "conta poupança", "conta digital", "consulta",
                # ES
                "saldo", "estado de cuenta", "depósito", "retiro", "cajero",
                "cajero automático", "comprobante", "movimiento", "cuenta corriente",
                "cuenta de ahorro", "cuenta digital", "consulta",
            ],
            "Transferências": [
                # PT-BR
                "transferência", "pix", "ted", "doc", "chave pix",
                "devolução", "pix parcelado", "pix agendado", "enviar dinheiro",
                "receber", "chave aleatória", "cpf",
                # ES
                "transferencia", "spei", "clabe", "transferencia bancaria",
                "devolución", "enviar dinero", "recibir",
            ],
            "Portabilidade": [
                # PT-BR
                "portabilidade", "portabilidade de salário",
                "portabilidade de crédito", "migração", "troca de banco",
                "mudar de banco", "abertura de conta", "encerramento de conta",
                # ES
                "portabilidad", "portabilidad de nómina",
                "portabilidad de crédito", "migración", "cambio de banco",
                "cambiar de banco", "apertura de cuenta", "cierre de cuenta",
            ],
            "Assinaturas": [
                # PT-BR
                "assinatura", "recorrência", "débito automático", "plano",
                "mensalidade", "cancelamento", "streaming", "renovação",
                "cobrança recorrente", "serviço", "pacote",
                # ES
                "suscripción", "recurrencia", "domiciliación", "plan",
                "mensualidad", "cancelación", "streaming", "renovación",
                "cobro recurrente", "servicio", "paquete",
            ],
            "Seguro": [
                # PT-BR
                "seguro", "sinistro", "apólice", "cobertura", "prêmio",
                "indenização", "seguro auto", "seguro vida", "seguro residencial",
                "franquia", "seguradora", "seguro viagem", "proteção veicular",
                # ES
                "seguro", "siniestro", "póliza", "cobertura", "prima",
                "indemnización", "seguro auto", "seguro de vida",
                "seguro residencial", "deducible", "aseguradora",
                "seguro de viaje",
            ],
            "Atendimento": [
                # PT-BR
                "atendimento", "call center", "sac", "suporte", "reclamação",
                "ouvidoria", "chat", "atendente", "espera", "demora", "protocolo",
                "procon", "reclame aqui", "0800", "whatsapp", "agência",
                # ES
                "atención", "atención al cliente", "call center", "soporte",
                "reclamación", "queja", "chat", "agente", "espera", "demora",
                "protocolo", "condusef", "whatsapp", "sucursal", "sucursales",
            ],
            "Taxas e cobranças": [
                # PT-BR
                "taxa", "tarifa", "cobrança", "cobrança indevida", "juros", "iof",
                "multa", "encargo", "spread", "estorno",
                "cobrança abusiva", "anuidade",
                # ES
                "tasa", "tarifa", "cobro", "cobro indebido", "comisión",
                "multa", "recargo", "cobro abusivo",
                "anualidad",
            ],
            "App e canais digitais": [
                # PT-BR
                "app", "aplicativo", "internet banking", "site", "plataforma",
                "biometria", "reconhecimento facial", "notificação", "push",
                "bug", "erro", "instabilidade", "fora do ar", "lento",
                "atualização", "login", "senha",
                # ES
                "app", "aplicación", "banca en línea", "banca móvil", "sitio",
                "plataforma", "biometría", "reconocimiento facial", "notificación",
                "error", "inestabilidad", "fuera de servicio", "lento",
                "actualización", "login", "contraseña",
            ],
            "Acciones": [
                # PT-BR
                "campanha", "ação promocional", "ativação", "sorteio",
                "dinâmica", "concurso", "evento", "parceria", "collab",
                "lançamento", "black friday", "hot sale",
                # ES
                "campaña", "acción promocional", "activación", "sorteo",
                "dinámica", "concurso", "evento", "alianza", "collab",
                "lanzamiento", "julio regalado", "buen fin", "hot sale",
                "black friday", "cyber monday", "cumpleañeros", "vinculo",
                "dale play", "se te nota la pasión", "casa falabella",
            ],
            "Eventos": [
                # PT-BR
                "evento", "corrida", "maratona", "carrera",
                "show", "feira", "exposição", "conferência", "congresso",
                "workshop", "palestra", "meetup", "encontro", "inauguração",
                "cerimônia", "celebração", "premiação",
                # ES
                "evento", "carrera", "maratón", "feria",
                "exposición", "conferencia", "congreso", "taller",
                "charla", "encuentro", "inauguración", "ceremonia",
                "celebración", "premiación",
            ],
            "Educação financeira": [
                # PT-BR
                "educação financeira", "finanças pessoais", "orçamento",
                "planejamento financeiro", "reserva de emergência", "poupar",
                "poupança", "economizar", "organização financeira", "dicas",
                "independência financeira", "renda extra", "renda passiva",
                "controle financeiro", "planilha", "metas financeiras",
                "consumo consciente", "endividamento", "sair das dívidas",
                # ES
                "educación financiera", "finanzas personales", "presupuesto",
                "planificación financiera", "fondo de emergencia", "ahorrar",
                "ahorro", "economizar", "organización financiera", "consejos",
                "independencia financiera", "ingreso extra", "ingreso pasivo",
                "control financiero", "metas financieras",
                "consumo consciente", "salir de deudas",
            ],
            "Posicionamento de marca": [
                # PT-BR
                "marca", "branding", "identidade", "posicionamento",
                "reputação", "imagem", "reconhecimento", "presença",
                "visibilidade", "top of mind", "awareness", "propósito",
                "valor de marca", "percepção", "rebranding", "slogan",
                "tagline", "logo", "logotipo", "identidade visual",
                # ES
                "marca", "branding", "identidad", "posicionamiento",
                "reputación", "imagen", "reconocimiento", "presencia",
                "visibilidad", "top of mind", "awareness", "propósito",
                "valor de marca", "percepción", "rebranding", "slogan",
                "tagline", "logo", "logotipo", "identidad visual",
            ],
        },
    },
}


_WORD_BOUNDARY = re.compile(r"\b{}\b")


_OTROS = {"pt": "Outros", "es": "Otros"}

_TOPIC_TRANSLATIONS = {
    "servicios_financieros": {
        "Crédito": {"es": "Crédito"},
        "Benefícios": {"es": "Beneficios"},
        "Investimento": {"es": "Inversión"},
        "Segurança": {"es": "Seguridad"},
        "Cartões": {"es": "Tarjetas"},
        "Pagamentos": {"es": "Pagos"},
        "Criptomoedas": {"es": "Criptomonedas"},
        "Saldo e extrato": {"es": "Saldo y estado de cuenta"},
        "Transferências": {"es": "Transferencias"},
        "Portabilidade": {"es": "Portabilidad"},
        "Assinaturas": {"es": "Suscripciones"},
        "Seguro": {"es": "Seguro"},
        "Atendimento": {"es": "Atención al cliente"},
        "Taxas e cobranças": {"es": "Tasas y cobros"},
        "App e canais digitais": {"es": "App y canales digitales"},
        "Acciones": {"es": "Acciones"},
        "Eventos": {"es": "Eventos"},
        "Educação financeira": {"es": "Educación financiera"},
        "Posicionamento de marca": {"es": "Posicionamiento de marca"},
    },
    "politica_br": {
        "Segurança pública": {"es": "Seguridad pública"},
        "Saúde": {"es": "Salud"},
        "Educação": {"es": "Educación"},
        "Violência contra a mulher": {"es": "Violencia contra la mujer"},
        "Economia": {"es": "Economía"},
        "Meio ambiente": {"es": "Medio ambiente"},
        "Corrupção": {"es": "Corrupción"},
        "Infraestrutura": {"es": "Infraestructura"},
        "Habitação": {"es": "Vivienda"},
        "Direitos humanos": {"es": "Derechos humanos"},
        "Valores": {"es": "Valores"},
        "Manifestação de apoio": {"es": "Manifestación de apoyo"},
        "Democracia": {"es": "Democracia"},
        "Clã Bolsonaro": {"es": "Clan Bolsonaro"},
    },
}


def translate_topic(topic, dictionary_key, lang="pt"):
    if lang == "pt":
        return topic
    tr = _TOPIC_TRANSLATIONS.get(dictionary_key, {}).get(topic, {})
    return tr.get(lang, topic)


def available_dictionaries(lang="pt"):
    """Retorna lista de (key, name) dos dicionários disponíveis."""
    result = []
    for k, v in DICTIONARIES.items():
        name = v["name"]
        if isinstance(name, dict):
            name = name.get(lang, name.get("pt", str(name)))
        result.append((k, name))
    return result


def otros_label(lang="pt"):
    return _OTROS.get(lang, "Outros")


def classify_text(text, dictionary_key, lang="pt"):
    """Clasifica un texto en exactamente un tema del diccionario indicado.

    Retorna el nombre del tema con más coincidencias de keywords.
    En caso de empate, gana el tema con la keyword más larga encontrada
    (más específica). Si no hay coincidencia, retorna 'Outros'/'Otros'.
    """
    text_lower = str(text).lower()
    topics = DICTIONARIES[dictionary_key]["topics"]

    best_topic = None
    best_score = 0
    best_max_len = 0

    for topic, keywords in topics.items():
        score = 0
        max_len = 0
        for kw in keywords:
            if kw in text_lower:
                score += 1
                if len(kw) > max_len:
                    max_len = len(kw)
        if score > best_score or (score == best_score and max_len > best_max_len):
            best_score = score
            best_max_len = max_len
            best_topic = topic

    if best_topic:
        return translate_topic(best_topic, dictionary_key, lang)
    return otros_label(lang)


def classify_series(texts, dictionary_key, lang="pt"):
    """Clasifica una lista/Series de textos. Retorna lista de temas."""
    return [classify_text(t, dictionary_key, lang=lang) for t in texts]


def topic_names(dictionary_key, lang="pt"):
    """Retorna lista de nomes de temas traduzidos para o idioma."""
    topics = DICTIONARIES[dictionary_key]["topics"]
    return [translate_topic(t, dictionary_key, lang) for t in topics]
