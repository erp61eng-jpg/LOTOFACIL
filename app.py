import streamlit as st
import streamlit.components.v1 as components
import requests
from itertools import combinations
from collections import Counter
import math
import time
import re
import json
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==============================================================================
# CONFIGURAÇÃO DE PÁGINA (STREAMLIT)
# ==============================================================================
st.set_page_config(
    page_title="LOTOFÁCIL25 - Alto Contraste & Filtro Inteligente",
    page_icon="🍀",
    layout="wide"
)

# ESTILIZAÇÃO CSS GLOBAL (ALTO CONTRASTE PRETO E BRANCO)
st.markdown('''
<style>
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stToolbar"] {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    html, body, [class*="css"], .stMarkdown, p, span, label, div, input, textarea, select {
        color: #000000 !important;
        font-weight: 800 !important;
        font-family: Arial, Helvetica, sans-serif !important;
        line-height: 1.6 !important;
    }
    h1, h2, h3, h4 { color: #000000 !important; font-weight: 900 !important; }
    
    [data-testid="stVerticalBlock"] > div[style*="border"] {
        background-color: #f8fafc !important;
        border: 3px solid #000000 !important;
        border-radius: 10px !important;
    }

    .stButton > button {
        color: #000000 !important;
        font-size: 1.35rem !important;
        font-weight: 900 !important;
        border: 3px solid #000000 !important;
        background-color: #ffffff !important;
        border-radius: 8px !important;
    }
    .stButton > button[kind="primary"] {
        background-color: #facc15 !important;
        color: #000000 !important;
        border: 3px solid #000000 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 900 !important;
        color: #000000 !important;
    }
    .progresso-gigante {
        font-size: 1.5rem !important;
        font-weight: 900 !important;
        color: #000000 !important;
        background-color: #fef08a !important;
        padding: 12px;
        border: 3px solid #000000;
        border-radius: 8px;
        text-align: center;
        margin: 10px 0;
    }
</style>
''', unsafe_allow_html=True)


# ==============================================================================
# 🛠️ ETAPA 1: CONSTANTES E BANCO DE DADOS LOCAL
# ==============================================================================

ARQUIVO_NOTAS_LOCAL = "meu_bloco_de_notas.txt"

def carregar_notas_salvas():
    if os.path.exists(ARQUIVO_NOTAS_LOCAL):
        try:
            with open(ARQUIVO_NOTAS_LOCAL, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            pass
    return "Bem-vindo ao seu Bloco de Notas automático da Lotofácil!\nEscreva aqui os seus palpites, esquemas ou matrizes favoritas..."

def salvar_notas_automaticamente(conteudo):
    try:
        with open(ARQUIVO_NOTAS_LOCAL, "w", encoding="utf-8") as f:
            f.write(conteudo)
    except Exception:
        pass

TOTAL_NUMS = 25
TAMANHO_JOGO_FINAL = 15
FIBONACCI_LOTOFACIL = {1, 2, 3, 5, 8, 13, 21}
PRIMOS_LOTOFACIL = {2, 3, 5, 7, 11, 13, 17, 19, 23}

MOLDURA_SET = (
    set(range(1, 6)) |
    set(range(21, 26)) |
    {r * 5 + 1 for r in range(5)} |
    {r * 5 + 5 for r in range(5)}
)

CRUZ_CENTRAL_SET = {3, 8, 11, 12, 13, 14, 15, 18, 23}
DEZENAS_BASE_LOTOFACIL = {1, 3, 5, 12, 13, 14, 23, 25}

FALLBACK_LOTOFACIL = [
    [1, 2, 4, 7, 10, 11, 13, 14, 15, 17, 19, 20, 22, 23, 25],
    [2, 3, 5, 6, 8, 10, 12, 14, 16, 18, 19, 21, 23, 24, 25],
    [1, 3, 4, 6, 9, 11, 13, 15, 16, 18, 20, 21, 22, 24, 25]
]

HEADERS_CAIXA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
}

PAR_LOOKUP = [False] + [(n % 2 == 0) for n in range(1, 26)]
PRIMO_LOOKUP = [False] + [(n in PRIMOS_LOTOFACIL) for n in range(1, 26)]
MOLDURA_LOOKUP = [False] + [(n in MOLDURA_SET) for n in range(1, 26)]
CRUZ_LOOKUP = [False] + [(n in CRUZ_CENTRAL_SET) for n in range(1, 26)]

ROW_LOOKUP = [0] + [(n - 1) // 5 for n in range(1, 26)]
COL_LOOKUP = [0] + [(n - 1) % 5 for n in range(1, 26)]
DC_LOOKUP = [0] + [(((n - 1) % 5) + ((n - 1) // 5)) % 5 for n in range(1, 26)]
DD_LOOKUP = [0] + [(((n - 1) % 5) - ((n - 1) // 5)) % 5 for n in range(1, 26)]

PROPS = {}
for n in range(1, 26):
    PROPS[n] = {
        "r": ROW_LOOKUP[n], "c": COL_LOOKUP[n], "dc": DC_LOOKUP[n], "dd": DD_LOOKUP[n],
        "is_primo": PRIMO_LOOKUP[n], "is_par": PAR_LOOKUP[n], "is_moldura": MOLDURA_LOOKUP[n],
        "is_cruz": CRUZ_LOOKUP[n], "is_fib": n in FIBONACCI_LOTOFACIL
    }

OPCOES_QUANTIDADE = {
    "Livre (0 a 5)": (0, 5), "0 (Nenhuma)": (0, 0), "Exatamente 1 (01)": (1, 1),
    "Exatamente 2 (02)": (2, 2), "Exatamente 3 (03)": (3, 3), "Exatamente 4": (4, 4), "Exatamente 5": (5, 5),
    "0 a 2": (0, 2), "0 a 3": (0, 3), "0 a 4": (0, 4), "0 a 5": (0, 5),
    "1 a 3": (1, 3), "1 a 4": (1, 4), "1 a 5": (1, 5),
    "2 a 3": (2, 3), "2 a 4": (2, 4), "2 a 5": (2, 5),
    "3 a 4": (3, 4), "3 a 5": (3, 5),
    "4 a 5": (4, 5)
}

PRESETS_PADRAO = {
    "PADRAO_LOTOFACIL": {
        "linhas": ["Exatamente 3 (03)", "Exatamente 3 (03)", "Exatamente 3 (03)", "Exatamente 3 (03)", "Exatamente 3 (03)"],
        "colunas": ["Exatamente 3 (03)", "Exatamente 3 (03)", "Exatamente 3 (03)", "Exatamente 3 (03)", "Exatamente 3 (03)"],
        "diag_cresc": ["1 a 3", "1 a 3", "1 a 3", "1 a 3", "1 a 3"],
        "diag_decresc": ["1 a 3", "1 a 3", "1 a 3", "1 a 3", "1 a 3"],
        "primos": [5], "pares": ["8P / 7I"], "moldura": [9], "cruz": [4, 5, 6], "soma": (170, 220)
    }
}

ARQUIVO_PRESETS_LOCAL = "meus_filtros_salvos_lotofacil.json"

def carregar_presets_persistidos():
    if os.path.exists(ARQUIVO_PRESETS_LOCAL):
        try:
            with open(ARQUIVO_PRESETS_LOCAL, "r", encoding="utf-8") as f:
                dados = json.load(f)
                if isinstance(dados, dict) and dados:
                    base = PRESETS_PADRAO.copy()
                    base.update(dados)
                    return base
        except Exception:
            pass
    return PRESETS_PADRAO.copy()

def salvar_presets_persistidos(presets):
    try:
        with open(ARQUIVO_PRESETS_LOCAL, "w", encoding="utf-8") as f:
            json.dump(presets, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def calcular_metricas_elliott(historico):
    total = len(historico)
    atrasos = {n: total for n in range(1, 26)}
    freq_3, freq_10 = {n: 0 for n in range(1, 26)}, {n: 0 for n in range(1, 26)}
    for idx_rev, sorteio in enumerate(reversed(historico)):
        for n in sorteio:
            if atrasos[n] == total: atrasos[n] = idx_rev
            if idx_rev < 3: freq_3[n] += 1
            if idx_rev < 10: freq_10[n] += 1
    dados = {}
    for n in range(1, 26):
        atr = atrasos[n]
        dist_fib = min(abs(atr - f) for f in [1, 2, 3, 5, 8, 13])
        score_retracao = max(0.0, 10.0 - (dist_fib * 2.0))
        score_impulso = (freq_3[n] * 6.0) + (freq_10[n] * 2.0)
        score_fib = 3.0 if PROPS[n]["is_fib"] else 0.0
        penalidade = -3.0 if atr > 10 else 0.0
        score_total = max(0.0, score_retracao + score_impulso + score_fib + penalidade)
        dados[n] = {
            "numero": n, "score": round(score_total, 1), "atraso": atr,
            "is_fib": PROPS[n]["is_fib"], "is_primo": PROPS[n]["is_primo"],
            "is_par": PROPS[n]["is_par"], "is_cruz": PROPS[n]["is_cruz"],
            "dc": PROPS[n]["dc"], "dd": PROPS[n]["dd"], "col": PROPS[n]["c"]
        }
    return dados

def extrair_analise_elite(dados_calor):
    ranking = sorted(dados_calor.values(), key=lambda x: x["score"], reverse=True)
    melhores_primos = [x["numero"] for x in ranking if x["is_primo"]][:5]
    melhores_pares = [x["numero"] for x in ranking if x["is_par"]][:7]
    melhores_impares = [x["numero"] for x in ranking if not x["is_par"]][:8]
    
    dc_scores, dd_scores, col_scores = {d: 0.0 for d in range(5)}, {d: 0.0 for d in range(5)}, {c: 0.0 for c in range(5)}
    for n, val in dados_calor.items():
        dc_scores[val["dc"]] += val["score"]
        dd_scores[val["dd"]] += val["score"]
        col_scores[val["col"]] += val["score"]
        
    melhores_dc = sorted(dc_scores.keys(), key=lambda d: dc_scores[d], reverse=True)[:2]
    melhores_dd = sorted(dd_scores.keys(), key=lambda d: dd_scores[d], reverse=True)[:2]
    melhores_col = sorted(col_scores.keys(), key=lambda c: col_scores[c], reverse=True)[:3]
    
    pool_elite = sorted(list(set(melhores_primos) | set(melhores_pares) | set(melhores_impares)))
    return {
        "primos": melhores_primos, "pares": melhores_pares, "impares": melhores_impares,
        "dc": melhores_dc, "dd": melhores_dd, "colunas": melhores_col, "pool_elite": pool_elite
    }

def mapear_quantidade_para_rotulo_inteligente(qtd):
    """
    Constrói um envelope flexível baseado na contagem exata (qtd) encontrada na linha/coluna,
    permitindo uma margem segura de variação para englobar variações naturais sem engessar.
    """
    if qtd <= 1:
        return "0 a 3"
    elif qtd == 2:
        return "1 a 4"
    elif qtd == 3:
        return "1 a 4"
    elif qtd == 4:
        return "2 a 5"
    else:
        return "3 a 5"

def mapear_intervalo_para_opcao(min_v, max_v, flexivel=False):
    if flexivel:
        min_v = max(0, min_v - 1)
        max_v = min(5, max_v + 1)
    for label, (low, high) in OPCOES_QUANTIDADE.items():
        if low == min_v and high == max_v: return label
    return "Livre (0 a 5)"

def extrair_filtros_de_jogo(dezenas, margem_soma=35):
    dezenas = sorted(list(set(dezenas)))
    total_dezenas = len(dezenas)
    if not (15 <= total_dezenas <= 25): 
        return None

    l_cnt, c_cnt, dc_cnt, dd_cnt = [0]*5, [0]*5, [0]*5, [0]*5
    for n in dezenas:
        l_cnt[ROW_LOOKUP[n]] += 1
        c_cnt[COL_LOOKUP[n]] += 1
        dc_cnt[DC_LOOKUP[n]] += 1
        dd_cnt[DD_LOOKUP[n]] += 1

    pares_calibrados = ["5P / 10I", "6P / 9I", "7P / 8I", "8P / 7I", "9P / 6I", "10P / 5I"]
    primos_total = sum(1 for n in dezenas if PRIMO_LOOKUP[n])
    primos_calibrados = sorted(list(range(max(2, primos_total - 2), min(9, primos_total + 3))))

    moldura_total = sum(1 for n in dezenas if MOLDURA_LOOKUP[n])
    moldura_calibrada = sorted(list(range(max(6, moldura_total - 3), min(14, moldura_total + 4))))

    cruz_total = sum(1 for n in dezenas if CRUZ_LOOKUP[n])
    cruz_calibrada = sorted(list(range(max(2, cruz_total - 2), min(9, cruz_total + 3))))

    soma_total = sum(dezenas[:15]) if total_dezenas > 15 else sum(dezenas)
    faixa_soma_min = max(140, soma_total - margem_soma)
    faixa_soma_max = min(250, soma_total + margem_soma)

    return {
        "linhas": [mapear_quantidade_para_rotulo_inteligente(q) for q in l_cnt],
        "colunas": [mapear_quantidade_para_rotulo_inteligente(q) for q in c_cnt],
        "diag_cresc": [mapear_quantidade_para_rotulo_inteligente(q) for q in dc_cnt],
        "diag_decresc": [mapear_quantidade_para_rotulo_inteligente(q) for q in dd_cnt],
        "primos": primos_calibrados,
        "pares": pares_calibrados,
        "moldura": moldura_calibrada,
        "cruz": cruz_calibrada,
        "soma": (faixa_soma_min, faixa_soma_max)
    }

def extrair_filtros_multiconcursos(lista_sorteios, modo="preciso"):
    if not lista_sorteios: return None
    is_flex = modo == "flexivel"
    min_l, max_l = [99] * 5, [-1] * 5
    min_c, max_c = [99] * 5, [-1] * 5
    min_dc, max_dc = [99] * 5, [-1] * 5
    min_dd, max_dd = [99] * 5, [-1] * 5
    conjunto_primos, conjunto_pares, conjunto_moldura, conjunto_cruz, somas_obs = set(), set(), set(), set(), []
    for sorteio in lista_sorteios:
        dezenas = sorted(sorteio)
        l_cnt, c_cnt, dc_cnt, dd_cnt = [0]*5, [0]*5, [0]*5, [0]*5
        for n in dezenas:
            l_cnt[ROW_LOOKUP[n]] += 1
            c_cnt[COL_LOOKUP[n]] += 1
            dc_cnt[DC_LOOKUP[n]] += 1
            dd_cnt[DD_LOOKUP[n]] += 1
        for r in range(5):
            min_l[r], max_l[r] = min(min_l[r], l_cnt[r]), max(max_l[r], l_cnt[r])
        for c in range(5):
            min_c[c], max_c[c] = min(min_c[c], c_cnt[c]), max(max_c[c], c_cnt[c])
        for d in range(5):
            min_dc[d], max_dc[d] = min(min_dc[d], dc_cnt[d]), max(max_dc[d], dc_cnt[d])
            min_dd[d], max_dd[d] = min(min_dd[d], dd_cnt[d]), max(max_dd[d], dd_cnt[d])
        conjunto_primos.add(sum(1 for n in dezenas if PRIMO_LOOKUP[n]))
        pa = sum(1 for n in dezenas if PAR_LOOKUP[n])
        conjunto_pares.add(f"{pa}P / {15 - pa}I")
        conjunto_moldura.add(sum(1 for n in dezenas if MOLDURA_LOOKUP[n]))
        conjunto_cruz.add(sum(1 for n in dezenas if CRUZ_LOOKUP[n]))
        somas_obs.append(sum(dezenas))
    return {
        "linhas": [mapear_intervalo_para_opcao(min_l[r], max_l[r], is_flex) for r in range(5)],
        "colunas": [mapear_intervalo_para_opcao(min_c[c], max_c[c], is_flex) for c in range(5)],
        "diag_cresc": [mapear_intervalo_para_opcao(min_dc[d], max_dc[d], is_flex) for d in range(5)],
        "diag_decresc": [mapear_intervalo_para_opcao(min_dd[d], max_dd[d], is_flex) for d in range(5)],
        "primos": sorted(list(conjunto_primos)), "pares": sorted(list(conjunto_pares)),
        "moldura": sorted(list(conjunto_moldura)), "cruz": sorted(list(conjunto_cruz)),
        "soma": (max(100, min(somas_obs)-20), min(300, max(somas_obs)+20))
    }

def validar_aposta_final_15(jogo, cfg):
    """
    VALIDADOR BLINDADO: Verifica estritamente se a contagem real de dezenas 
    em cada linha, coluna e diagonal está dentro dos limites [min, max] definidos.
    """
    soma_j = sum(jogo)
    if not (cfg["faixa_soma"][0] <= soma_j <= cfg["faixa_soma"][1]): return False
    if sum(1 for n in jogo if PAR_LOOKUP[n]) not in cfg["pares_aceitos"]: return False
    if sum(1 for n in jogo if PRIMO_LOOKUP[n]) not in cfg["primos_aceitos"]: return False
    if sum(1 for n in jogo if MOLDURA_LOOKUP[n]) not in cfg["moldura_aceita"]: return False
    if "cruz_aceita" in cfg and cfg["cruz_aceita"]:
        if sum(1 for n in jogo if CRUZ_LOOKUP[n]) not in cfg["cruz_aceita"]: return False

    l_cnt, c_cnt, dc_cnt, dd_cnt = [0]*5, [0]*5, [0]*5, [0]*5
    for n in jogo:
        l_cnt[ROW_LOOKUP[n]] += 1
        c_cnt[COL_LOOKUP[n]] += 1
        dc_cnt[DC_LOOKUP[n]] += 1
        dd_cnt[DD_LOOKUP[n]] += 1

    # Validação rigorosa dos intervalos inclusivos [min, max]
    for r in range(5):
        min_l, max_l = cfg["linhas"][r]
        if not (min_l <= l_cnt[r] <= max_l): return False
    for c in range(5):
        min_c, max_c = cfg["colunas"][c]
        if not (min_c <= c_cnt[c] <= max_c): return False
    for d in range(5):
        min_dc, max_dc = cfg["diag_cresc"][d]
        if not (min_dc <= dc_cnt[d] <= max_dc): return False
        min_dd, max_dd = cfg["diag_decresc"][d]
        if not (min_dd <= dd_cnt[d] <= max_dd): return False
        
    return True

def executar_varredura_pool(pool_dezenas, cfg, bar_progresso, ticker_metricas, teto_max=None):
    dezenas_candidatas = sorted(list(pool_dezenas))
    if len(dezenas_candidatas) < 15: return []
    total_combinacoes = math.comb(len(dezenas_candidatas), 15)
    jogos_aprovados = []
    testadas = 0
    t_ultimo_update = 0.0
    for comb in combinations(dezenas_candidatas, 15):
        testadas += 1
        if validar_aposta_final_15(comb, cfg):
            jogos_aprovados.append(sorted(list(comb)))
            if teto_max is not None and len(jogos_aprovados) >= teto_max: break
        t_agora = time.time()
        if t_agora - t_ultimo_update >= 0.25:
            t_ultimo_update = t_agora
            prog = min(1.0, testadas / total_combinacoes)
            bar_progresso.progress(prog)
            ticker_metricas.markdown(f"<div class='progresso-gigante'>PROCESSANDO: {testadas:,} / {total_combinacoes:,} ({prog*100:.1f}%) | APROVADAS: {len(jogos_aprovados):,}</div>", unsafe_allow_html=True)
    bar_progresso.progress(1.0)
    return jogos_aprovados

def processar_arquivo_upload(conteudo_bytes):
    texto = conteudo_bytes.decode("utf-8", errors="ignore")
    linhas = texto.strip().splitlines()
    jogos, invalidos = [], 0
    for linha in linhas:
        l = linha.strip()
        if not l: continue
        nums = [int(x) for x in re.findall(r"\b\d+\b", l)]
        nums_validos = sorted(list(set([n for n in nums if 1 <= n <= 25])))
        if len(nums_validos) == 15: jogos.append(nums_validos)
        else: invalidos += 1
    return jogos, invalidos

def conferir_apostas_contra_sorteio(lista_jogos, dezenas_sorteadas):
    sorteio_set = set(dezenas_sorteadas)
    placar = {15: [], 14: [], 13: [], 12: [], 11: [], 10: []}
    relatorio = []
    for idx, jogo in enumerate(lista_jogos):
        acertos = sorted(list(set(jogo) & sorteio_set))
        qtd = len(acertos)
        if qtd in placar:
            placar[qtd].append(idx + 1)
        relatorio.append({
            "num_aposta": idx + 1,
            "jogo": sorted(jogo),
            "qtd_acertos": qtd,
            "acertos": acertos
        })
    return relatorio, placar

def calcular_ciclo_lotofacil(historico):
    todas_25 = set(range(1, 26))
    if not historico:
        return {"concursos_no_ciclo": 0, "ja_deram": [], "faltam": sorted(list(todas_25)), "ciclo_fechado": False}

    dezenas_vistas = set()
    concursos_ciclo = 0

    for sorteio in historico:
        dezenas_vistas.update(sorteio)
        concursos_ciclo += 1
        if len(dezenas_vistas) == 25:
            dezenas_vistas = set()
            concursos_ciclo = 0

    faltam = sorted(list(todas_25 - dezenas_vistas)) if dezenas_vistas else []
    ja_deram = sorted(list(dezenas_vistas))

    return {
        "concursos_no_ciclo": concursos_ciclo,
        "ja_deram": ja_deram,
        "faltam": faltam,
        "ciclo_fechado": len(dezenas_vistas) == 0
    }

def render_html_seguro(conteudo_html, altura=380):
    try:
        if hasattr(st, "html"): st.html(conteudo_html)
        else: components.html(conteudo_html, height=altura, scrolling=False)
    except Exception:
        components.html(conteudo_html, height=altura, scrolling=False)

def render_cartao_sorteio_html(dezenas, titulo="CARTÃO OFICIAL DO SORTEIO"):
    bolas_html = "".join([f"<span style='display:inline-flex;align-items:center;justify-content:center;width:48px;height:48px;background:#facc15;color:#000000;font-weight:900;font-size:22px;border-radius:50%;margin:0 4px;border:3px solid #000000;font-family:monospace;'>{n:02d}</span>" for n in dezenas])
    st.markdown(f'''<div style="background:#ffffff;border:4px solid #000000;border-radius:12px;padding:14px;margin:8px 0;text-align:center;"><div style="font-weight:900;color:#000000;font-size:18px;margin-bottom:8px;text-transform:uppercase;">🏆 {titulo}</div><div style="display:flex;justify-content:center;align-items:center;flex-wrap:wrap;gap:6px;">{bolas_html}</div></div>''', unsafe_allow_html=True)

def render_volante_conferencia(jogo, dezenas_sorteio, titulo=""):
    jogo_set, sorteio_set = set(jogo), set(dezenas_sorteio)
    celulas = ""
    for r in range(5):
        for c in range(5):
            n = r * 5 + c + 1
            if n in jogo_set and n in sorteio_set: 
                celulas += f'<div style="width:50px;height:50px;background:#facc15;color:#000000;font-weight:900;border:3px solid #000000;border-radius:6px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:monospace;font-size:19px;">{n:02d}<span style="font-size:11px;line-height:6px;font-weight:900;">★</span></div>'
            elif n in jogo_set: 
                celulas += f'<div style="width:50px;height:50px;background:#38bdf8;color:#000000;font-weight:900;border:3px solid #000000;border-radius:6px;display:flex;align-items:center;justify-content:center;font-family:monospace;font-size:19px;">{n:02d}</div>'
            elif n in sorteio_set: 
                celulas += f'<div style="width:50px;height:50px;background:#ffffff;color:#000000;font-weight:900;border:3px dashed #000000;border-radius:6px;display:flex;align-items:center;justify-content:center;font-family:monospace;font-size:19px;">{n:02d}</div>'
            else: 
                celulas += f'<div style="width:50px;height:50px;background:#ffffff;color:#000000;border:1px solid #000000;font-weight:900;border-radius:6px;display:flex;align-items:center;justify-content:center;font-family:monospace;font-size:19px;">{n:02d}</div>'
    render_html_seguro(f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>*{{box-sizing:border-box;}}body{{margin:0;padding:0;display:flex;justify-content:center;background:transparent;font-family:Arial,sans-serif;}}.box{{background:#fff;border:4px solid #000000;border-radius:10px;padding:12px;width:fit-content;}}.grid{{display:grid;grid-template-columns:repeat(5,50px);gap:6px;}}</style></head><body><div class="box"><div style="font-weight:900;font-size:18px;margin-bottom:10px;color:#000000;text-align:center;">{titulo}</div><div class="grid">{celulas}</div></div></body></html>''', 360)


# ==============================================================================
# 🛠️ ETAPA 2: ESTADO DA SESSÃO & BLINDAGEM DE DADOS
# ==============================================================================

if "historico" not in st.session_state:
    st.session_state.historico = [sorted(list(j)) for j in FALLBACK_LOTOFACIL]
    st.session_state.origem = "Base Local Offline"

if "jogos_aprovados" not in st.session_state: st.session_state.jogos_aprovados = []
if "jogos_upload" not in st.session_state: st.session_state.jogos_upload = []
if "jogos_filtrados_upload" not in st.session_state: st.session_state.jogos_filtrados_upload = []

if "presets_filtros" not in st.session_state:
    st.session_state.presets_filtros = carregar_presets_persistidos()

if "input_dezenas_digitadas_texto" not in st.session_state:
    st.session_state.input_dezenas_digitadas_texto = "01 02 04 05 06 10 11 13 15 16 18 20 21 22 23"

dados_calor = calcular_metricas_elliott(st.session_state.historico)
ranking_elliott = sorted(dados_calor.values(), key=lambda x: x["score"], reverse=True)
top_20_dezenas = {item["numero"] for item in ranking_elliott[:20]}
pool_inicial = top_20_dezenas | DEZENAS_BASE_LOTOFACIL
analise_elite = extrair_analise_elite(dados_calor)

if "pool_trabalho" not in st.session_state or not isinstance(st.session_state.pool_trabalho, set):
    st.session_state.pool_trabalho = pool_inicial.copy()

def aplicar_preset(nome_preset):
    cfg_p = st.session_state.presets_filtros.get(nome_preset)
    if not cfg_p: return
    for r in range(5): st.session_state[f"sel_l_{r}"] = cfg_p["linhas"][r]
    for c in range(5): st.session_state[f"sel_c_{c}"] = cfg_p["colunas"][c]
    for d in range(5):
        st.session_state[f"sel_dc_{d}"] = cfg_p["diag_cresc"][d]
        st.session_state[f"sel_dd_{d}"] = cfg_p["diag_decresc"][d]
    st.session_state["sel_primos"] = cfg_p["primos"]
    st.session_state["sel_pares"] = cfg_p["pares"]
    st.session_state["sel_moldura"] = cfg_p["moldura"]
    st.session_state["sel_cruz"] = cfg_p.get("cruz", [3, 4, 5, 6, 7])
    soma_raw = cfg_p.get("soma", (150, 240))
    st.session_state["sel_soma"] = (int(soma_raw[0]), int(soma_raw[1]))

if "filtro_inicial_carregado" not in st.session_state:
    aplicar_preset("PADRAO_LOTOFACIL")
    st.session_state.filtro_inicial_carregado = True

def toggle_dezena(n):
    if not isinstance(st.session_state.pool_trabalho, set):
        st.session_state.pool_trabalho = set(st.session_state.pool_trabalho)
    if n in st.session_state.pool_trabalho: st.session_state.pool_trabalho.remove(n)
    else: st.session_state.pool_trabalho.add(n)


# ==============================================================================
# 🛠️ ETAPA 3: INTERFACE PRINCIPAL
# ==============================================================================

st.title("🍀 LOTOFÁCIL 25 - PAINEL BLINDADO")
st.caption("MATRIZ 5x5 • ALTO CONTRASTE PRETO E BRANCO • PLACAR COMPLETO (11 A 15 PONTOS)")

tab_cartela, tab_config, tab_volante, tab_upload, tab_historico, tab_notas = st.tabs([
    "🎟️ Cartela & Seleção Elite",
    "🎛️ Filtros & Engenharia Reversa",
    "🗺️ Volante & Raio-X",
    "📥 Upload & Filtragem Sucessiva",
    "📊 Histórico, Caixa & Ciclo",
    "📝 Bloco de Notas"
])

# ------------------------------------------------------------------------------
# ABA 1: CARTELA & SELEÇÃO ELITE
# ------------------------------------------------------------------------------
with tab_cartela:
    with st.container(border=True):
        st.markdown("### 🏆 DESTAQUES DE ELITE (ELLIOTT & MATRIZ 5x5)")
        c_el1, c_el2, c_el3, c_el4 = st.columns([1, 1, 1, 1.4])
        with c_el1:
            st.markdown("#### 💎 MELHORES PRIMOS")
            st.markdown(f"<div style='font-size:1.6rem;color:#000000;font-weight:900;'>{' • '.join([f'{n:02d}' for n in analise_elite['primos']])}</div>", unsafe_allow_html=True)
        with c_el2:
            st.markdown("#### ⚖️ MELHORES PARES")
            st.markdown(f"<div style='font-size:1.6rem;color:#000000;font-weight:900;'>{' • '.join([f'{n:02d}' for n in analise_elite['pares']])}</div>", unsafe_allow_html=True)
        with c_el3:
            st.markdown("#### 📊 MELHORES COLUNAS (C01-C05)")
            col_badges = "".join([f"<span style='display:inline-block;background:#facc15;color:#000000;font-weight:900;padding:5px 10px;margin:2px 4px;border:3px solid #000000;border-radius:6px;font-size:1.2rem;'>C{c+1:02d}</span>" for c in analise_elite["colunas"]])
            st.markdown(f"<div>{col_badges}</div>", unsafe_allow_html=True)
        with c_el4:
            st.markdown("#### 📐 MELHORES DIAGONAIS")
            dc_badges = "".join([f"<span style='display:inline-block;background:#fef08a;color:#000000;font-weight:900;padding:3px 8px;margin:2px 3px;border:2px solid #000000;border-radius:4px;font-size:1.1rem;'>DC{d+1:02d}</span>" for d in analise_elite["dc"]])
            dd_badges = "".join([f"<span style='display:inline-block;background:#fef08a;color:#000000;font-weight:900;padding:3px 8px;margin:2px 3px;border:2px solid #000000;border-radius:4px;font-size:1.1rem;'>DD{d+1:02d}</span>" for d in analise_elite["dd"]])
            st.markdown(f"<div style='margin-bottom:4px;'><b>CRESC:</b> {dc_badges}</div><div><b>DECRESC:</b> {dd_badges}</div>", unsafe_allow_html=True)

        st.divider()
        pool_elite_ordenado = analise_elite["pool_elite"]
        st.markdown(f"<div style='font-size:1.5rem;color:#000000;font-weight:900;'>🎯 POOL CONSOLIDADO DAS ELITES ({len(pool_elite_ordenado)} DEZENAS):<br><span style='background:#facc15;padding:8px 16px;border:3px solid #000000;border-radius:8px;display:inline-block;margin-top:8px;font-size:1.4rem;'>{' - '.join([f'{n:02d}' for n in pool_elite_ordenado])}</span></div>", unsafe_allow_html=True)

        c_act1, c_act2 = st.columns(2)
        with c_act1:
            if st.button("⭐ CARREGAR SOMENTE ESTE POOL DE ELITE NA CARTELA", use_container_width=True, type="primary"):
                st.session_state.pool_trabalho = set(pool_elite_ordenado)
                st.rerun()
        with c_act2:
            if st.button("🎛️ GERAR E ATIVAR FILTRO COM ESTAS CONDICIONANTES", use_container_width=True):
                bar_status = st.progress(0, text="Iniciando processamento do filtro de elite...")
                time.sleep(0.3)
                bar_status.progress(40, text="Extraindo faixas abertas e gravando arquivo JSON...")
                preset_elite = extrair_filtros_de_jogo(pool_elite_ordenado)
                st.session_state.presets_filtros["FILTRO_ELITE_CONDICIONANTES"] = preset_elite
                salvar_presets_persistidos(st.session_state.presets_filtros)
                bar_status.progress(80, text="Aplicando predefinição na interface...")
                aplicar_preset("FILTRO_ELITE_CONDICIONANTES")
                time.sleep(0.3)
                bar_status.progress(100, text="Concluído com sucesso!")
                time.sleep(0.2)
                bar_status.empty()
                st.success("✅ Filtro de elite ativado e gravado com sucesso na Aba 2!")
                st.rerun()

    st.subheader("🎟️ CARTELA DE 25 NÚMEROS (MATRIZ 5x5)")
    c_b1, c_b2, c_b3, c_b4, c_b5 = st.columns(5)
    with c_b1:
        if st.button("⭐ Base + Top 20", use_container_width=True):
            st.session_state.pool_trabalho = (top_20_dezenas | DEZENAS_BASE_LOTOFACIL).copy()
            st.rerun()
    with c_b2:
        if st.button("🔥 Apenas Quentes (Top 15)", use_container_width=True):
            st.session_state.pool_trabalho = {item["numero"] for item in ranking_elliott[:15]}
            st.rerun()
    with c_b3:
        if st.button("⚡ +7 Fibonacci", use_container_width=True):
            st.session_state.pool_trabalho = set(st.session_state.pool_trabalho) | FIBONACCI_LOTOFACIL
            st.rerun()
    with c_b4:
        if st.button("✅ Marcar Todas (25)", use_container_width=True):
            st.session_state.pool_trabalho = set(range(1, 26))
            st.rerun()
    with c_b5:
        if st.button("🧹 Limpar Cartela", use_container_width=True):
            st.session_state.pool_trabalho = set()
            st.rerun()

    set_elite = set(analise_elite["pool_elite"])
    for r in range(5):
        cols = st.columns(5)
        for c in range(5):
            n = r * 5 + c + 1
            meta = dados_calor[n]
            esta_ativa = n in st.session_state.pool_trabalho
            with cols[c]:
                if st.button(f"{n:02d}{'⭐' if n in set_elite else ''}\n({meta['score']:.0f}p)", key=f"btn_num_{n}", type="primary" if esta_ativa else "secondary", use_container_width=True):
                    toggle_dezena(n)
                    st.rerun()

    st.divider()
    col_inf1, col_inf2 = st.columns([3, 1])
    qtd_sel = len(st.session_state.pool_trabalho)
    with col_inf1:
        st.markdown(f"<div style='font-size:1.6rem;font-weight:900;background:#fef08a;border:3px solid #000000;padding:16px;border-radius:8px;'>DEZENAS ATIVAS ({qtd_sel}):<br><span style='font-size:1.4rem;'>{' - '.join([f'{n:02d}' for n in sorted(list(st.session_state.pool_trabalho))]) if qtd_sel else 'NENHUMA'}</span></div>", unsafe_allow_html=True)
    with col_inf2:
        st.metric("Total Selecionado", f"{qtd_sel} / 25")
        st.markdown(f"<div style='font-size:1.6rem;font-weight:900;margin-top:10px;'>Jogos Brutos: {math.comb(qtd_sel, 15) if qtd_sel >= 15 else 0:,}</div>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# ABA 2: CONFIGURAÇÃO DE FILTROS & ENGENHARIA REVERSA
# ------------------------------------------------------------------------------
with tab_config:
    st.markdown("### 🎛️ FILTROS ESTRUTURAIS & ENGENHARIA REVERSA")
    tipo_reverso = st.radio("Selecione a Rotina de Engenharia Reversa:", ["🏛️ Rotina 1: Histórica Multiconcursos", "⚡ Rotina 2: Dezenas Digitadas a Mão (Filtro Amplo Aberto)"], horizontal=True)

    if tipo_reverso.startswith("🏛️ Rotina 1"):
        with st.container(border=True):
            st.markdown("#### 🏛️ ENGENHARIA REVERSA MULTICONCURSOS")
            total_disp = len(st.session_state.historico)
            col_m1, col_m2, col_m3 = st.columns([1.5, 1.8, 1.7])
            with col_m1: qtd_concursos_sel = st.slider("Concursos Anteriores:", 1, max(1, total_disp), min(10, total_disp))
            with col_m2:
                nome_filtro_multi = st.text_input("Nome do Filtro:", value=f"FILTRO_ULT_{qtd_concursos_sel}_CONCURSOS")
                carregar_pool_multi = st.checkbox("Carregar Dezenas no Pool Ativo", value=True)
            with col_m3: tolerancia_multi = st.selectbox("Margem:", ["Envelope Preciso", "Envelope Flexível"], index=0)

            if st.button("🚀 PROCESSAR CONCURSOS E ATIVAR FILTRO", type="primary", use_container_width=True):
                bar_m = st.progress(0, text="Acessando histórico de concursos...")
                time.sleep(0.2)
                bar_m.progress(35, text="Calculando limites estatísticos multiconcursos...")
                sorteios_alvo = st.session_state.historico[-qtd_concursos_sel:]
                preset_multi = extrair_filtros_multiconcursos(sorteios_alvo, modo="preciso" if "Preciso" in tolerancia_multi else "flexivel")
                bar_m.progress(70, text="Gravando predefinição no arquivo JSON...")
                nome_salvar = nome_filtro_multi.strip() or f"FILTRO_ULT_{qtd_concursos_sel}_CONCURSOS"
                st.session_state.presets_filtros[nome_salvar] = preset_multi
                salvar_presets_persistidos(st.session_state.presets_filtros)
                aplicar_preset(nome_salvar)
                dezenas_unicas = sorted(list({n for j in sorteios_alvo for n in j}))
                if carregar_pool_multi: st.session_state.pool_trabalho = set(dezenas_unicas)
                bar_m.progress(100, text="Concluído com sucesso!")
                time.sleep(0.3)
                bar_m.empty()
                st.success(f"✅ Filtro '{nome_salvar}' processado, ativado e gravado com sucesso!")
                st.rerun()
    else:
        with st.container(border=True):
            st.markdown("#### ⚡ ENGENHARIA REVERSA POR DEZENAS DIGITADAS (FAIXAS ABERTAS)")
            st.caption("Gera faixas flexíveis abertas para cima (ex: 2 a 5) em linhas, colunas e diagonais, gerando um volume saudável e evitando engessamento em 1 único jogo.")
            
            entrada_dezenas_filtro = st.text_area(
                "Dezenas do Cartão de Referência (15 a 25 números):",
                value=st.session_state.input_dezenas_digitadas_texto,
                height=80,
                key="input_dezenas_digitadas_widget"
            )
            st.session_state.input_dezenas_digitadas_texto = entrada_dezenas_filtro

            col_input_res, col_input_nome = st.columns([2.5, 1.8])
            with col_input_res:
                nome_filtro_novo = st.text_input("Nome do Filtro:", value="MEU_FILTRO_FLEXIVEL")
            with col_input_nome:
                substituir_pool_opcao = st.checkbox("Substituir o Pool da Cartela com estas Dezenas", value=True)

            if st.button("⚡ EXTRAIR RESTRIÇÕES ABERTAS E ATIVAR FILTRO", type="primary", use_container_width=True):
                nums_parse = [int(x) for x in re.findall(r"\b\d+\b", entrada_dezenas_filtro)]
                dezenas_limpas = sorted(list(set([n for n in nums_parse if 1 <= n <= 25])))
                if len(dezenas_limpas) < 15: 
                    st.error("⚠️ Informe pelo menos 15 dezenas válidas da Lotofácil.")
                else:
                    bar_e = st.progress(0, text="Limpando e validando dezenas digitadas...")
                    time.sleep(0.2)
                    bar_e.progress(40, text="Mapeando faixas abertas e calibradores estatísticos...")
                    st.session_state.input_dezenas_digitadas_texto = " ".join([f"{n:02d}" for n in dezenas_limpas])
                    preset_extraido = extrair_filtros_de_jogo(dezenas_limpas)
                    bar_e.progress(75, text="Gravando predefinição no arquivo JSON local...")
                    nome_salvar = nome_filtro_novo.strip() or "MEU_FILTRO_FLEXIVEL"
                    st.session_state.presets_filtros[nome_salvar] = preset_extraido
                    salvar_presets_persistidos(st.session_state.presets_filtros)
                    aplicar_preset(nome_salvar)
                    if substituir_pool_opcao: st.session_state.pool_trabalho = set(dezenas_limpas)
                    bar_e.progress(100, text="Processo concluído!")
                    time.sleep(0.3)
                    bar_e.empty()
                    st.success(f"✅ Filtro flexível '{nome_salvar}' gerado, gravado e ativado com sucesso!")
                    st.rerun()

    # GERENCIADOR DE PREDEFINIÇÕES & GRAVAÇÃO MANUAL COM BARRA DE SERVIÇO EXPLICITA
    with st.container(border=True):
        st.markdown("#### 💾 GERENCIADOR DE PREDEFINIÇÕES & GRAVAÇÃO MANUAL")
        col_puxar, col_gravar = st.columns(2)
        with col_puxar:
            lista_nomes = list(st.session_state.presets_filtros.keys())
            filtro_escolhido = st.selectbox("Carregar Filtro Salvo:", lista_nomes, key="select_preset_load")
            c_pux1, c_pux2 = st.columns(2)
            with c_pux1:
                if st.button("🚀 APLICAR PREDEFINIÇÃO", use_container_width=True):
                    bar_p = st.progress(0, text="Carregando predefinição...")
                    time.sleep(0.2)
                    aplicar_preset(filtro_escolhido)
                    bar_p.progress(100, text="Aplicado com sucesso!")
                    time.sleep(0.2)
                    bar_p.empty()
                    st.success(f"✅ Filtro '{filtro_escolhido}' carregado com sucesso!")
                    st.rerun()
            with c_pux2:
                st.download_button("💾 BAIXAR (.JSON)", data=json.dumps(st.session_state.presets_filtros, indent=2, ensure_ascii=False), file_name="meus_filtros_lotofacil.json", mime="application/json", use_container_width=True)

        with col_gravar:
            nome_novo_filtro = st.text_input("Nome da Nova Configuração:", placeholder="Ex: Meu Filtro Top", key="input_nome_filtro_manual")
            if st.button("💾 GRAVAR CONFIGURAÇÃO MANUAL", use_container_width=True, type="primary"):
                if not nome_novo_filtro.strip():
                    st.error("⚠️ Informe um nome para a predefinição antes de gravar.")
                else:
                    bar_grav = st.progress(0, text="Iniciando gravação no disco...")
                    time.sleep(0.2)
                    bar_grav.progress(50, text="Salvando JSON de predefinições...")
                    novo_preset = {
                        "linhas": [st.session_state.get(f"sel_l_{r}", "Exatamente 3 (03)") for r in range(5)],
                        "colunas": [st.session_state.get(f"sel_c_{c}", "Exatamente 3 (03)") for c in range(5)],
                        "diag_cresc": [st.session_state.get(f"sel_dc_{d}", "1 a 3") for d in range(5)],
                        "diag_decresc": [st.session_state.get(f"sel_dd_{d}", "1 a 3") for d in range(5)],
                        "primos": st.session_state.get("sel_primos", [5]),
                        "pares": st.session_state.get("sel_pares", ["8P / 7I"]),
                        "moldura": st.session_state.get("sel_moldura", [9]),
                        "cruz": st.session_state.get("sel_cruz", [4, 5, 6]),
                        "soma": (int(st.session_state.get("sel_soma", (150, 240))[0]), int(st.session_state.get("sel_soma", (150, 240))[1]))
                    }
                    st.session_state.presets_filtros[nome_novo_filtro.strip()] = novo_preset
                    salvar_presets_persistidos(st.session_state.presets_filtros)
                    bar_grav.progress(100, text="Gravação concluída com sucesso!")
                    time.sleep(0.3)
                    bar_grav.empty()
                    st.success(f"✅ Predefinição '{nome_novo_filtro.strip()}' gravada e persistida com sucesso no disco (`{ARQUIVO_PRESETS_LOCAL}`)!")
                    st.rerun()

    st.divider()
    opcoes_nomes = list(OPCOES_QUANTIDADE.keys())

    with st.container(border=True):
        st.markdown("#### 1️⃣ LINHAS INDIVIDUAIS (L01 a L05)")
        cols_l = st.columns(5)
        limites_linhas = []
        for r in range(5):
            with cols_l[r]:
                esc = st.selectbox(f"Linha {r+1:02d}", opcoes_nomes, key=f"sel_l_{r}")
                limites_linhas.append(OPCOES_QUANTIDADE[esc])

    with st.container(border=True):
        st.markdown("#### 2️⃣ COLUNAS INDIVIDUAIS (C01 a C05)")
        cols_c = st.columns(5)
        limites_colunas = []
        for c in range(5):
            with cols_c[c]:
                esc = st.selectbox(f"Coluna {c+1:02d}", opcoes_nomes, key=f"sel_c_{c}")
                limites_colunas.append(OPCOES_QUANTIDADE[esc])

    c_diag1, c_diag2 = st.columns(2)
    with c_diag1:
        with st.container(border=True):
            st.markdown("#### 3️⃣ DIAGONAIS CRESCENTES (DC01 a DC05)")
            with st.expander("Expandir Diagonais Crescentes", expanded=False):
                limites_dc = []
                for d in range(5):
                    esc = st.selectbox(f"DC{d+1:02d}", opcoes_nomes, key=f"sel_dc_{d}")
                    limites_dc.append(OPCOES_QUANTIDADE[esc])
    with c_diag2:
        with st.container(border=True):
            st.markdown("#### 4️⃣ DIAGONAIS DECRESCENTES (DD01 a DD05)")
            with st.expander("Expandir Diagonais Decrescentes", expanded=False):
                limites_dd = []
                for d in range(5):
                    esc = st.selectbox(f"DD{d+1:02d}", opcoes_nomes, key=f"sel_dd_{d}")
                    limites_dd.append(OPCOES_QUANTIDADE[esc])

    with st.container(border=True):
        st.markdown("#### 5️⃣ RESTRIÇÕES CALIBRADORAS: PRIMOS, PARES, MOLDURA, CRUZ E SOMA")
        c_p1, c_p2, c_p3, c_p4, c_p5 = st.columns(5)
        with c_p1: primos_sel = st.multiselect("Primos:", list(range(10)), default=st.session_state.get("sel_primos", [5]), key="sel_primos")
        with c_p2:
            opcoes_par = {"8P / 7I": 8, "7P / 8I": 7, "9P / 6I": 9, "6P / 9I": 6, "10P / 5I": 10, "5P / 10I": 5}
            par_sel = st.multiselect("Pares/Ímpares:", list(opcoes_par.keys()), default=st.session_state.get("sel_pares", ["8P / 7I"]), key="sel_pares")
            pares_valores = {opcoes_par[k] for k in par_sel}
        with c_p3: moldura_sel = st.multiselect("Moldura:", list(range(16)), default=st.session_state.get("sel_moldura", [9]), key="sel_moldura")
        with c_p4: cruz_sel = st.multiselect("Cruz Central:", list(range(10)), default=st.session_state.get("sel_cruz", [4, 5, 6]), key="sel_cruz")
        with c_p5:
            val_soma_estado = st.session_state.get("sel_soma", (150, 240))
            soma_min_val, soma_max_val = (int(val_soma_estado[0]), int(val_soma_estado[1])) if isinstance(val_soma_estado, (list, tuple)) and len(val_soma_estado) == 2 else (150, 240)
            faixa_soma = st.slider("Faixa de Soma:", 100, 300, (soma_min_val, soma_max_val), key="sel_soma")

    config_total = {
        "linhas": limites_linhas, "colunas": limites_colunas, "diag_cresc": limites_dc,
        "diag_decresc": limites_dd, "primos_aceitos": set(primos_sel), "pares_aceitos": pares_valores,
        "moldura_aceita": set(moldura_sel), "cruz_aceita": set(cruz_sel), "faixa_soma": faixa_soma
    }

    st.divider()
    if st.button("🚀 GERAR E FILTRAR APOSTAS", use_container_width=True, type="primary"):
        with st.spinner("🛠️ Processando Motor Combinatório..."):
            resultados = executar_varredura_pool(st.session_state.pool_trabalho, config_total, st.empty(), st.empty(), teto_max=None)
            st.session_state.jogos_aprovados = resultados
            if resultados: st.markdown(f"<div class='progresso-gigante'>✅ SUCESSO: {len(resultados):,} APOSTAS GERADAS</div>", unsafe_allow_html=True)
            else: st.warning("⚠️ Nenhuma combinação atendeu aos filtros selecionados.")

    if st.session_state.jogos_aprovados:
        qtd_gerada = len(st.session_state.jogos_aprovados)
        st.markdown(f"<div class='progresso-gigante'>TOTAL APROVADO: {qtd_gerada:,} APOSTAS</div>", unsafe_allow_html=True)
        nome_arquivo_txt = f"lotofacil_apostas_filtradas_{qtd_gerada}j.txt"
        st.download_button("📥 BAIXAR JOGOS APROVADOS (.TXT)", data="\n".join([" ".join([f"{n:02d}" for n in sorted(j)]) for j in st.session_state.jogos_aprovados]), file_name=nome_arquivo_txt, mime="text/plain", use_container_width=True)

# ------------------------------------------------------------------------------
# ABA 3: VOLANTE VISUAL & RAIO-X
# ------------------------------------------------------------------------------
with tab_volante:
    st.subheader("DISSECAÇÃO DA CARTELA")
    jogos_exibir = st.session_state.jogos_aprovados or st.session_state.jogos_upload
    if jogos_exibir:
        total_jogos = len(jogos_exibir)
        if total_jogos > 1:
            sel_idx = st.slider("Aposta para inspecionar:", 1, total_jogos, 1)
        else:
            sel_idx = 1
        jogo_ativo = sorted(jogos_exibir[sel_idx - 1])
        render_volante_conferencia(jogo_ativo, [], f"JOGO #{sel_idx:04d}: {' - '.join([f'{n:02d}' for n in jogo_ativo])}")
    else:
        st.info("Gere apostas ou carregue um arquivo para inspecionar no volante.")

# ------------------------------------------------------------------------------
# ABA 4: UPLOAD & FILTRAGEM SUCESSIVA & CONFERÊNCIA (PLACAR 11 A 15)
# ------------------------------------------------------------------------------
with tab_upload:
    st.subheader("📥 UPLOAD, FILTRAGEM & CONFERÊNCIA")
    arquivo_enviado = st.file_uploader("Carregue seu arquivo de apostas (.txt ou .csv):", type=["txt", "csv"])

    if arquivo_enviado is not None:
        conteudo = arquivo_enviado.read()
        jogos_carregados, invalidos = processar_arquivo_upload(conteudo)
        st.session_state.jogos_upload = jogos_carregados
        if invalidos > 0:
            st.warning(f"⚠️ {invalidos} linha(s) ignoradas por formato inválido.")

    if st.session_state.jogos_upload:
        jogos_up = st.session_state.jogos_upload
        total_up = len(jogos_up)
        st.markdown(f"<div class='progresso-gigante'>ARQUIVO CARREGADO: {total_up:,} APOSTAS EM MEMÓRIA</div>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("#### ⚡ FILTRAR ARQUIVO CARREGADO COM O FILTRO ATIVO")
            c_flt1, c_flt2 = st.columns([2, 1])
            with c_flt1:
                if st.button("🔍 APLICAR FILTROS ATIVOS NO ARQUIVO", type="primary", use_container_width=True):
                    with st.spinner("Filtrando apostas..."):
                        aprovados_do_arquivo = [j for j in jogos_up if validar_aposta_final_15(tuple(j), config_total)]
                        st.session_state.jogos_filtrados_upload = aprovados_do_arquivo
                        st.markdown(f"<div class='progresso-gigante'>{len(aprovados_do_arquivo):,} DE {total_up:,} APROVADAS</div>", unsafe_allow_html=True)

            if st.session_state.jogos_filtrados_upload:
                qtd_flt = len(st.session_state.jogos_filtrados_upload)
                txt_flt = "\n".join([" ".join([f"{n:02d}" for n in sorted(j)]) for j in st.session_state.jogos_filtrados_upload])
                nome_arquivo_filtrado = f"lotofacil_lote_filtrado_{qtd_flt}j.txt"
                with c_flt2:
                    st.download_button(f"💾 BAIXAR LOTE FILTRADO ({qtd_flt:,})", data=txt_flt, file_name=nome_arquivo_filtrado, mime="text/plain", use_container_width=True)

        st.divider()
        col_diag_left, col_conf_right = st.columns([1.25, 1.0], gap="large")

        with col_diag_left:
            st.markdown("### 📊 DIAGNÓSTICO DO ARQUIVO")
            cnt_nums = Counter()
            somas = []
            for j in jogos_up:
                cnt_nums.update(j)
                somas.append(sum(j))

            m1, m2, m3 = st.columns(3)
            m1.metric("Total", f"{total_up:,}")
            m2.metric("Soma Média", f"{sum(somas)/len(somas):.1f}" if somas else "0")
            m3.metric("Mais Freq.", f"{cnt_nums.most_common(1)[0][0]:02d}" if cnt_nums else "--")

            st.markdown("#### 🔥 FREQUÊNCIA NA MATRIZ (5x5)")
            celulas_up_heat = ""
            for r in range(5):
                for c in range(5):
                    n = r * 5 + c + 1
                    freq = cnt_nums[n]
                    bg = "#ffffff" if freq == 0 else "#fef08a"
                    celulas_up_heat += f'<div style="width:50px;height:50px;background:{bg};color:#000000;border-radius:6px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:monospace;border:2px solid #000000;box-sizing:border-box;"><span style="font-size:15px;font-weight:900;">{n:02d}</span><span style="font-size:12px;font-weight:900;">{freq}x</span></div>'

            render_html_seguro(f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>*{{box-sizing:border-box;}}body{{margin:0;padding:0;background:transparent;display:flex;justify-content:center;font-family:Arial,sans-serif;}}.box{{background:#fff;border:4px solid #000000;border-radius:10px;padding:12px;width:fit-content;}}.grid{{display:grid;grid-template-columns:repeat(5,50px);gap:5px;}}</style></head><body><div class="box"><div class="grid">{celulas_up_heat}</div></div></body></html>', 320)

        with col_conf_right:
            st.markdown("### 🎯 CONFERÊNCIA DE RESULTADOS")
            modo_origem = st.radio("Origem do Sorteio:", ["Último Sorteio Oficial", "Digitar Concurso Específico", "Digitar Dezenas Manualmente"], horizontal=True)
            dezenas_conf = []

            if modo_origem == "Último Sorteio Oficial":
                dezenas_conf = sorted(st.session_state.historico[-1]) if st.session_state.historico else []
            elif modo_origem == "Digitar Concurso Específico":
                num_conc_busca = st.number_input("Digite o número do Concurso:", min_value=1, value=3000, step=1)
                if st.button("🔍 Buscar Concurso na Caixa", use_container_width=True):
                    with st.spinner(f"Consultando o concurso {num_conc_busca}..."):
                        try:
                            r_esp = requests.get(f"https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil/{num_conc_busca}", headers=HEADERS_CAIXA, timeout=10, verify=False)
                            if r_esp.status_code == 200:
                                dados_esp = r_esp.json()
                                dezenas_esp = sorted([int(x) for x in dados_esp.get("listaDezenas", [])])
                                if len(dezenas_esp) == 15:
                                    st.session_state["concurso_buscado_temp"] = dezenas_esp
                                    st.success(f"Concurso #{num_conc_busca} carregado com sucesso!")
                                else:
                                    st.error("Erro ao ler as dezenas do concurso retornado.")
                            else:
                                st.error(f"Erro na resposta da Caixa (Status: {r_esp.status_code}).")
                        except Exception as e:
                            st.error(f"Falha de conexão com a API da Caixa: {e}")
                dezenas_conf = st.session_state.get("concurso_buscado_temp", [])
            else:
                ult_def = st.session_state.historico[-1] if st.session_state.historico else [1, 2, 4, 7, 10, 11, 13, 14, 15, 17, 19, 20, 22, 23, 25]
                entrada_manual = st.text_input("15 Dezenas Sorteadas (espaços):", value=" ".join([f"{n:02d}" for n in sorted(ult_def)]))
                nums_man = [int(x) for x in re.findall(r"\b\d+\b", entrada_manual)]
                dezenas_conf = sorted(list(set([n for n in nums_man if 1 <= n <= 25])))

            if len(dezenas_conf) != 15:
                st.warning("⚠️ Selecione ou busque um concurso válido com 15 dezenas para iniciar a conferência.")
            else:
                render_cartao_sorteio_html(dezenas_conf, titulo="SORTEIO CONFERIDO")
                base_conferir = st.session_state.jogos_filtrados_upload or jogos_up
                relatorio_conf, placar_conf = conferir_apostas_contra_sorteio(base_conferir, dezenas_conf)

                c15, c14, c13, c12, c11 = st.columns(5)
                c15.metric("15 P", f"{len(placar_conf[15])}")
                c14.metric("14 P", f"{len(placar_conf[14])}")
                c13.metric("13 P", f"{len(placar_conf[13])}")
                c12.metric("12 P", f"{len(placar_conf[12])}")
                c11.metric("11 P", f"{len(placar_conf[11])}")

                tot_prem = len(placar_conf[15]) + len(placar_conf[14]) + len(placar_conf[13]) + len(placar_conf[12]) + len(placar_conf[11])
                if tot_prem > 0:
                    st.markdown(f"<div class='progresso-gigante'>🎉 {tot_prem} APOSTA(S) PREMIADA(S) (11 a 15 PONTOS)!</div>", unsafe_allow_html=True)
                    jogos_premiados_txt = "\n".join([f"{' '.join([f'{n:02d}' for n in it['jogo']])} | {it['qtd_acertos']} ACERTOS" for it in relatorio_conf if it["qtd_acertos"] >= 11])
                    nome_arquivo_premiadas = f"lotofacil_premiadas_{tot_prem}j.txt"
                    st.download_button("📥 BAIXAR APOSTAS PREMIADAS (11+ PONTOS) (.TXT)", data=jogos_premiados_txt, file_name=nome_arquivo_premiadas, mime="text/plain", use_container_width=True)
                else:
                    st.warning("Nenhuma aposta alcançou pontuação de 11 a 15 acertos.")

                jogos_com_acerto = [it for it in relatorio_conf if it["qtd_acertos"] >= 11] or relatorio_conf
                opcoes_map = {it["num_aposta"]: f"Aposta #{it['num_aposta']:04d} — {it['qtd_acertos']} acertos" for it in jogos_com_acerto[:50]}
                if opcoes_map:
                    idx_escolhido = st.selectbox("Inspecionar no Volante:", list(opcoes_map.keys()), format_func=lambda x: opcoes_map[x])
                    if idx_escolhido is not None:
                        item_ativo = next(it for it in relatorio_conf if "num_aposta" in it and it["num_aposta"] == idx_escolhido)
                        render_volante_conferencia(item_ativo["jogo"], dezenas_conf, titulo=f"Aposta #{item_ativo['num_aposta']:04d} ({item_ativo['qtd_acertos']} Acertos)")
    else:
        st.info("Carregue um arquivo .txt ou .csv na parte superior para ativar o painel de conferência.")

# ------------------------------------------------------------------------------
# ABA 5: HISTÓRICO, CAIXA & CICLO
# ------------------------------------------------------------------------------
with tab_historico:
    st.subheader("📊 HISTÓRICO DE CONCURSOS & ANÁLISE DE CICLO")
    
    col_sync1, col_sync2 = st.columns([1, 2])
    with col_sync1:
        if st.button("🌐 SINCRONIZAR COM A CAIXA AGORA", type="primary", use_container_width=True):
            try:
                r = requests.get("https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil", headers=HEADERS_CAIXA, timeout=10, verify=False)
                if r.status_code == 200:
                    ult = r.json()
                    dezenas_sorteadas = sorted([int(x) for x in ult.get("listaDezenas", [])])
                    if len(dezenas_sorteadas) == 15 and dezenas_sorteadas not in st.session_state.historico:
                        st.session_state.historico.append(dezenas_sorteadas)
                        st.success(f"Concurso #{ult.get('numero')} sincronizado com sucesso!")
                        st.rerun()
                    elif dezenas_sorteadas in st.session_state.historico:
                        st.info(f"O concurso #{ult.get('numero')} já está presente no histórico.")
                else:
                    st.error(f"Erro ao consultar a Caixa: Status {r.status_code}")
            except Exception as e:
                st.error(f"Falha de conexão com a API da Caixa: {e}")

    st.divider()

    ciclo_dados = calcular_ciclo_lotofacil(st.session_state.historico)
    
    st.markdown("### 🔄 ANÁLISE DO CICLO ATUAL DA LOTOFÁCIL")
    st.markdown(f"**Concursos decorridos neste ciclo:** `{ciclo_dados['concursos_no_ciclo']}` concurso(s)")
    
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.markdown("#### ✅ Dezenas que já saíram no ciclo:")
        ja_deram_str = " • ".join([f"{n:02d}" for n in ciclo_dados['ja_deram']]) if ciclo_dados['ja_deram'] else "Nenhuma dezena registrada"
        st.markdown(f"<div style='background:#facc15;color:#000;padding:12px;border:3px solid #000;border-radius:8px;font-size:1.3rem;font-weight:900;'>{ja_deram_str}</div>", unsafe_allow_html=True)
        st.markdown(f"**Total já sorteadas:** `{len(ciclo_dados['ja_deram'])} / 25`")

    with col_c2:
        st.markdown("#### ⏳ Dezenas que FALTAM (Ausentes no ciclo):")
        faltam_str = " • ".join([f"{n:02d}" for n in ciclo_dados['faltam']]) if ciclo_dados['faltam'] else "🎉 CICLO FECHADO!"
        bg_faltam = "#fef08a" if ciclo_dados['faltam'] else "#38bdf8"
        st.markdown(f"<div style='background:{bg_faltam};color:#000;padding:12px;border:3px solid #000;border-radius:8px;font-size:1.4rem;font-weight:900;'>{faltam_str}</div>", unsafe_allow_html=True)
        st.markdown(f"**Total que faltam:** `{len(ciclo_dados['faltam'])} dezenas`")

    if ciclo_dados['ciclo_fechado']:
        st.success("🌟 O ciclo atual completou todas as 25 dezenas e foi encerrado! O próximo sorteio iniciará um novo ciclo.")

# ------------------------------------------------------------------------------
# ABA 6: BLOCO DE NOTAS
# ------------------------------------------------------------------------------
with tab_notas:
    st.subheader("📝 BLOCO DE NOTAS AUTOMÁTICO")
    st.markdown("Use este espaço para apontar palpites, estratégias ou matrizes. **O conteúdo é gravado instantaneamente no disco.**")
    
    conteudo_atual = carregar_notas_salvas()
    
    novas_notas = st.text_area(
        "Escreva as suas anotações aqui:",
        value=conteudo_atual,
        height=400,
        key="bloco_notas_input"
    )
    
    if novas_notas != conteudo_atual:
        salvar_notas_automaticamente(novas_notas)
    
    c_n1, c_n2 = st.columns(2)
    with c_n1:
        if st.button("💾 FORÇAR GRAVAÇÃO", use_container_width=True, type="primary"):
            bar_nota = st.progress(0, text="Salvando notas no disco...")
            time.sleep(0.2)
            salvar_notas_automaticamente(novas_notas)
            bar_nota.progress(100, text="Notas salvas com sucesso!")
            time.sleep(0.3)
            bar_nota.empty()
            st.success("✅ Anotações gravadas com sucesso no arquivo `meu_bloco_de_notas.txt`!")
    with c_n2:
        st.download_button(
            "📥 BAIXAR NOTAS (.TXT)",
            data=novas_notas,
            file_name="lotofacil_minhas_notas.txt",
            mime="text/plain",
            use_container_width=True
        )
