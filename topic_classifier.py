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
        "name": "Política brasileña",
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
        },
    },
    "servicios_financieros": {
        "name": "Servicios financieros",
        "topics": {
            "Cartão / Tarjeta": [
                # PT-BR
                "cartão", "cartão de crédito", "cartão de débito", "anuidade",
                "limite", "fatura", "parcelamento", "cashback", "pontos", "milhas",
                "bandeira", "visa", "mastercard", "elo", "platinum", "gold", "black",
                "cartão virtual", "cartão adicional", "aproximação",
                # ES
                "tarjeta", "tarjeta de crédito", "tarjeta de débito", "anualidad",
                "límite de crédito", "estado de cuenta", "meses sin intereses",
                "cashback", "puntos", "millas", "visa", "mastercard",
                "tarjeta virtual", "tarjeta adicional", "contactless",
            ],
            "Atendimento / Atención": [
                # PT-BR
                "atendimento", "call center", "sac", "suporte", "reclamação",
                "ouvidoria", "chat", "atendente", "espera", "demora", "protocolo",
                "procon", "reclame aqui", "0800", "whatsapp",
                # ES
                "atención", "atención al cliente", "call center", "soporte",
                "reclamación", "queja", "chat", "agente", "espera", "demora",
                "protocolo", "condusef", "whatsapp",
            ],
            "Taxas e cobranças": [
                # PT-BR
                "taxa", "tarifa", "cobrança", "cobrança indevida", "juros", "iof",
                "multa", "mora", "encargo", "spread", "cet", "estorno",
                "cobrança abusiva",
                # ES
                "tasa", "tarifa", "cobro", "cobro indebido", "comisión", "interés",
                "multa", "mora", "cargo", "recargo", "costo", "cobro abusivo",
            ],
            "Empréstimo / Crédito": [
                # PT-BR
                "empréstimo", "crédito", "financiamento", "consignado",
                "crédito pessoal", "parcela", "prestação", "score",
                "nome limpo", "nome sujo", "serasa", "spc", "inadimplente",
                "renegociação", "dívida", "endividamento", "refinanciamento",
                # ES
                "préstamo", "crédito", "financiamiento", "cuota", "mensualidad",
                "score", "buró de crédito", "deuda", "endeudamiento",
                "refinanciamiento", "moroso", "reestructuración",
            ],
            "Conta bancária": [
                # PT-BR
                "conta", "conta corrente", "conta poupança", "saldo", "extrato",
                "depósito", "saque", "caixa eletrônico", "agência", "gerente",
                "abertura de conta", "encerramento", "portabilidade",
                "conta digital", "conta salário",
                # ES
                "cuenta", "cuenta corriente", "cuenta de ahorro", "saldo",
                "estado de cuenta", "depósito", "retiro", "cajero", "cajero automático",
                "sucursal", "gerente", "apertura de cuenta", "cuenta digital",
            ],
            "App e canais digitais": [
                # PT-BR
                "app", "aplicativo", "internet banking", "site", "plataforma",
                "token", "senha", "biometria", "reconhecimento facial",
                "notificação", "push", "bug", "erro", "instabilidade",
                "fora do ar", "lento", "atualização", "login",
                # ES
                "app", "aplicación", "banca en línea", "banca móvil", "sitio",
                "plataforma", "token", "contraseña", "biometría",
                "reconocimiento facial", "notificación", "error", "inestabilidad",
                "fuera de servicio", "lento", "actualización", "login",
            ],
            "Fraude e segurança": [
                # PT-BR
                "fraude", "golpe", "clonagem", "phishing", "estelionato",
                "hackeado", "invasão", "compra não reconhecida", "bloqueio",
                "desbloqueio", "contestação", "chargeback", "senha vazada",
                "engenharia social", "pix falso", "golpe do pix",
                # ES
                "fraude", "estafa", "clonación", "phishing", "hackeado",
                "compra no reconocida", "cargo no reconocido", "bloqueo",
                "desbloqueo", "contestación", "chargeback", "contraseña filtrada",
                "ingeniería social",
            ],
            "Investimentos": [
                # PT-BR
                "investimento", "renda fixa", "renda variável", "cdb", "lci", "lca",
                "tesouro direto", "ação", "ações", "bolsa", "fundo",
                "rentabilidade", "rendimento", "dividendo", "corretora",
                # ES
                "inversión", "renta fija", "renta variable", "acción", "acciones",
                "bolsa", "fondo", "rentabilidad", "rendimiento", "dividendo",
                "corredor", "cetes", "bonos",
            ],
            "Seguros": [
                # PT-BR
                "seguro", "sinistro", "apólice", "cobertura", "prêmio",
                "indenização", "seguro auto", "seguro vida", "seguro residencial",
                "franquia", "seguradora",
                # ES
                "seguro", "siniestro", "póliza", "cobertura", "prima",
                "indemnización", "seguro auto", "seguro de vida",
                "seguro residencial", "deducible", "aseguradora",
            ],
            "Pix e transferências": [
                # PT-BR
                "pix", "transferência", "ted", "doc", "boleto", "pagamento",
                "qr code", "chave pix", "devolução", "comprovante",
                "pix parcelado", "pix agendado",
                # ES
                "transferencia", "pago", "código qr", "devolución", "reembolso",
                "comprobante", "spei", "clabe", "transferencia bancaria",
            ],
        },
    },
}


_WORD_BOUNDARY = re.compile(r"\b{}\b")


def available_dictionaries():
    """Retorna lista de (key, name) dos dicionários disponíveis."""
    return [(k, v["name"]) for k, v in DICTIONARIES.items()]


def classify_text(text, dictionary_key):
    """Clasifica un texto en exactamente un tema del diccionario indicado.

    Retorna el nombre del tema con más coincidencias de keywords.
    En caso de empate, gana el tema con la keyword más larga encontrada
    (más específica). Si no hay coincidencia, retorna 'Otros'.
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

    return best_topic or "Otros"


def classify_series(texts, dictionary_key):
    """Clasifica una lista/Series de textos. Retorna lista de temas."""
    return [classify_text(t, dictionary_key) for t in texts]
