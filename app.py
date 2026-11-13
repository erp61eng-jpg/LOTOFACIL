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
    page_title="LOTOFÁCIL25 - Painel Blindado Completo",
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
# 🛠️ CONSTANTES & BANCO DE DADOS LOCAL
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
FIBONACCI_LOTOFACIL = {1, 2, 3, 5, 8, 13, 21}
PRIMOS_LOTOFACIL = {2, 3, 5, 7, 11, 13, 17, 19, 23}

MOLDURA_SET = (
    set(range(1, 6)) |
    set(range(21, 26)) |
    {r * 5 + 1 for r in range(5)} |
    {r * 5 + 5 for r in range(5)}
)
CRUZ_CENTRAL_SET = {3, 8, 11, 12, 13, 14, 15, 18, 23}

JOGO_BASE_PADRAO = [3, 5, 7, 8, 11, 13, 14, 15, 18, 19, 20, 21, 22, 23, 25]

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
    "Livre (0 a 5)": [0, 5], "0 (Nenhuma)": [0, 0], "Exatamente 1": [1, 1],
    "Exatamente 2": [2, 2], "Exatamente 3": [3, 3], "Exatamente 4": [4, 4], "Exatamente 5": [5, 5],
    "0 a 2": [0, 2], "0 a 3": [0, 3], "0 a 4": [0, 4], "0 a 5": [0, 5],
    "1 a 3": [1, 3], "1 a 4": [1, 4], "1 a 5": [1, 5],
    "2 a 3": [2, 3], "2 a 4": [2, 4], "2 a 5": [2, 5],
    "3 a 4": [3, 4], "3 a 5": [3, 5]
}

PRESETS_PADRAO = {
    "JOGO_BASE_COM_FOLGA": {
        "linhas": [[0, 5], [0, 5], [0, 5], [0, 5], [0, 5]],
        "colunas": [[0, 5], [0, 5], [0, 5], [0, 5], [0, 5]],
        "diag_cresc": [[0, 5], [0, 5], [0, 5], [0, 5], [0, 5]],
        "diag_decresc": [[0, 5], [0, 5], [0, 5], [0, 5], [0, 5]],
        "primos": list(range(3, 9)),
        "pares": [7, 8, 9, 6, 10],
        "moldura": list(range(7, 16)),
        "cruz": list(range(2, 9)),
        "soma": [130, 260]
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

def extrair_filtros_de_jogo(dezenas, margem_soma=50):
    dezenas = sorted(list(set(dezenas)))
    if len(dezenas) < 15: dezenas = JOGO_BASE_PADRAO

    l_cnt, c_cnt, dc_cnt, dd_cnt = [0]*5, [0]*5, [0]*5, [0]*5
    for n in dezenas:
        l_cnt[ROW_LOOKUP[n]] += 1
        c_cnt[COL_LOOKUP[n]] += 1
        dc_cnt[DC_LOOKUP[n]] += 1
        dd_cnt[DD_LOOKUP[n]] += 1

    def faixa_folga(val):
        return [max(0, val - 2), min(5, val + 2)]

    pares_jogo = sum(1 for n in dezenas if PAR_LOOKUP[n])
    primos_total = sum(1 for n in dezenas if PRIMO_LOOKUP[n])
    moldura_total = sum(1 for n in dezenas if MOLDURA_LOOKUP[n])
    cruz_total = sum(1 for n in dezenas if CRUZ_LOOKUP[n])
    soma_total = sum(dezenas[:15])

    return {
        "linhas": [faixa_folga(q) for q in l_cnt],
        "colunas": [faixa_folga(q) for q in c_cnt],
        "diag_cresc": [faixa_folga(q) for q in dc_cnt],
        "diag_decresc": [faixa_folga(q) for q in dd_cnt],
        "primos": list(range(max(1, primos_total - 2), min(10, primos_total + 3))),
        "pares": [7, 8, 9, 6, 10],
        "moldura": list(range(max(5, moldura_total - 3), min(16, moldura_total + 4))),
        "cruz": list(range(max(1, cruz_total - 3), min(10, cruz_total + 4))),
        "soma": [max(130, soma_total - margem_soma), min(260, soma_total + margem_soma)]
    }

def validar_aposta_final_15(jogo, cfg):
    soma_j = sum(jogo)
    faixa_soma = cfg.get("soma", [130, 260])
    if not (faixa_soma[0] <= soma_j <= faixa_soma[1]): return False
    
    if sum(1 for n in jogo if PAR_LOOKUP[n]) not in cfg.get("pares", []): return False
    if sum(1 for n in jogo if PRIMO_LOOKUP[n]) not in cfg.get("primos", []): return False
    if sum(1 for n in jogo if MOLDURA_LOOKUP[n]) not in cfg.get("moldura", []): return False

    l_cnt, c_cnt, dc_cnt, dd_cnt = [0]*5, [0]*5, [0]*5, [0]*5
    for n in jogo:
        l_cnt[ROW_LOOKUP[n]] += 1
        c_cnt[COL_LOOKUP[n]] += 1
        dc_cnt[DC_LOOKUP[n]] += 1
        dd_cnt[DD_LOOKUP[n]] += 1

    def verificar_limites(contador, lista_limites):
        for idx, qtd in enumerate(contador):
            limite = lista_limites[idx]
            min_v, max_v = limite if isinstance(limite, (list, tuple)) and len(limite) == 2 else (0, 5)
            if not (min_v <= qtd <= max_v): return False
        return True

    if not verificar_limites(l_cnt, cfg.get("linhas", [[0, 5]]*5)): return False
    if not verificar_limites(c_cnt, cfg.get("colunas", [[0, 5]]*5)): return False
    if not verificar_limites(dc_cnt, cfg.get("diag_cresc", [[0, 5]]*5)): return False
    if not verificar_limites(dd_cnt, cfg.get("diag_decresc", [[0, 5]]*5)): return False
        
    return True

def executar_varredura_pool(pool_dezenas, cfg, bar_progresso, ticker_metricas):
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
        t_agora = time.time()
        if t_agora - t_ultimo_update >= 0.25:
            t_ultimo_update = t_agora
            prog = min(1.0, testadas / total_combinacoes)
            bar_progresso.progress(prog)
            ticker_metricas.markdown(f"<div class='progresso-gigante'>PROCESSANDO: {testadas:,} / {total_combinacoes:,} ({prog*100:.1f}%) | APROVADAS: {len(jogos_aprovados):,}</div>", unsafe_allow_html=True)
    bar_progresso.progress(1.0)
    return jogos_aprovados

def conferir_apostas_contra_sorteio(lista_jogos, dezenas_sorteadas):
    sorteio_set = set(dezenas_sorteadas)
    placar = {15: [], 14: [], 13: [], 12: [], 11: [], 10: []}
    relatorio = []
    for idx, jogo in enumerate(lista_jogos):
        acertos = sorted(list(set(jogo) & sorteio_set))
        qtd = len(acertos)
        if qtd in placar: placar[qtd].append(idx + 1)
        relatorio.append({"num_aposta": idx + 1, "jogo": sorted(jogo), "qtd_acertos": qtd, "acertos": acertos})
    return relatorio, placar

def render_html_seguro(conteudo_html, altura=380):
    try:
        if hasattr(st, "html"): st.html(conteudo_html)
        else: components.html(conteudo_html, height=altura, scrolling=False)
    except Exception:
        components.html(conteudo_html, height=altura, scrolling=False)

def render_cartao_sorteio_html(dezenas, titulo="CARTÃO OFICIAL DO SORTEIO"):
    bolas_html = "".join([f"<span style='display:inline-flex;align-items:center;justify-content:center;width:48px;height:48px;background:#facc15;color:#000000;font-weight:900;font-size:22px;border-radius:50%;margin:0 4px;border:3px solid #000000;font-family:monospace;'>{n:02d}</span>" for n in dezenas])
    st.markdown(f'''<div style="background:#ffffff;border:4px solid #000000;border-radius:12px;padding:14px;margin:8px 0;text-align:center;"><div style="font-weight:900;color:#000000;font-size:18px;margin-bottom:8px;text-transform:uppercase;">🏆 {titulo}</div><div style="display:flex;justify-content:center;align-items:center;flex-wrap:wrap;gap:6px;">{bolas_html}</div></div>''', unsafe_allow_html=True)


# ==============================================================================
# ESTADO DA SESSÃO
# ==============================================================================
if "historico" not in st.session_state:
    st.session_state.historico = [JOGO_BASE_PADRAO]

if "jogos_aprovados" not in st.session_state: st.session_state.jogos_aprovados = []
if "presets_filtros" not in st.session_state: st.session_state.presets_filtros = carregar_presets_persistidos()

if "input_dezenas_texto" not in st.session_state:
    st.session_state.input_dezenas_texto = " ".join([f"{n:02d}" for n in JOGO_BASE_PADRAO])

dados_calor = calcular_metricas_elliott(st.session_state.historico)
ranking_elliott = sorted(dados_calor.values(), key=lambda x: x["score"], reverse=True)
top_20 = {item["numero"] for item in ranking_elliott[:20]}
analise_elite = extrair_analise_elite(dados_calor)

if "pool_trabalho" not in st.session_state or not isinstance(st.session_state.pool_trabalho, set):
    st.session_state.pool_trabalho = set(JOGO_BASE_PADRAO)


# ==============================================================================
# INTERFACE PRINCIPAL (ABAS)
# ==============================================================================
st.title("🍀 LOTOFÁCIL 25 - PAINEL BLINDADO")
st.caption("MATRIZ 5x5 • ALTO CONTRASTE PRETO E BRANCO • ENGENHARIA REVERSA PRECISA")

tab_cartela, tab_config, tab_upload, tab_historico, tab_notas = st.tabs([
    "🎟️ Cartela & Seleção Elite",
    "🎛️ Filtros & Engenharia Reversa",
    "📥 Upload & Conferência",
    "📊 Histórico & Ciclo",
    "📝 Bloco de Notas"
])

# ------------------------------------------------------------------------------
# ABA 1: CARTELA & SELEÇÃO ELITE
# ------------------------------------------------------------------------------
with tab_cartela:
    with st.container(border=True):
        st.markdown("### 🏆 DESTAQUES DE ELITE")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("#### 💎 MELHORES PRIMOS")
            st.markdown(f"<div style='font-size:1.4rem;'>{' • '.join([f'{n:02d}' for n in analise_elite['primos']])}</div>", unsafe_allow_html=True)
        with c2:
            st.markdown("#### ⚖️ MELHORES PARES")
            st.markdown(f"<div style='font-size:1.4rem;'>{' • '.join([f'{n:02d}' for n in analise_elite['pares']])}</div>", unsafe_allow_html=True)
        with c3:
            st.markdown("#### 📊 COLUNAS DESTAQUE")
            col_badges = "".join([f"<span style='background:#facc15;padding:4px 8px;margin:2px;border:2px solid #000;border-radius:4px;'>C{c+1}</span>" for c in analise_elite["colunas"]])
            st.markdown(f"<div>{col_badges}</div>", unsafe_allow_html=True)

    st.subheader("🎟️ CARTELA DE 25 NÚMEROS (MATRIZ 5x5)")
    c_b1, c_b2, c_b3 = st.columns(3)
    with c_b1:
        if st.button("⭐ Carregar Seu Jogo Base", use_container_width=True):
            st.session_state.pool_trabalho = set(JOGO_BASE_PADRAO)
            st.rerun()
    with c_b2:
        if st.button("✅ Marcar Todas", use_container_width=True):
            st.session_state.pool_trabalho = set(range(1, 26))
            st.rerun()
    with c_b3:
        if st.button("🧹 Limpar Cartela", use_container_width=True):
            st.session_state.pool_trabalho = set()
            st.rerun()

    for r in range(5):
        cols = st.columns(5)
        for c in range(5):
            n = r * 5 + c + 1
            ativa = n in st.session_state.pool_trabalho
            with cols[c]:
                if st.button(f"{n:02d}\n({dados_calor[n]['score']:.0f}p)", key=f"btn_n_{n}", type="primary" if ativa else "secondary", use_container_width=True):
                    if ativa: st.session_state.pool_trabalho.remove(n)
                    else: st.session_state.pool_trabalho.add(n)
                    st.rerun()

# ------------------------------------------------------------------------------
# ABA 2: CONFIGURAÇÃO DE FILTROS & ENGENHARIA REVERSA
# ------------------------------------------------------------------------------
with tab_config:
    st.markdown("### 🎛️ ENGENHARIA REVERSA E RESTRIÇÕES")
    with st.container(border=True):
        st.caption("Insira suas 15 dezenas de base. O sistema extrairá a estrutura e calibrará os seletores.")
        txt_base = st.text_area("Suas 15 Dezenas:", value=st.session_state.input_dezenas_texto, height=75)
        st.session_state.input_dezenas_texto = txt_base

        if st.button("⚡ EXTRAIR E CALIBRAR FILTROS", type="primary", use_container_width=True):
            nums = [int(x) for x in re.findall(r"\b\d+\b", txt_base)]
            nums_limpos = sorted(list(set([n for n in nums if 1 <= n <= 25])))
            if len(nums_limpos) < 15:
                st.error("⚠️ Insira pelo menos 15 dezenas válidas.")
            else:
                cfg_gerada = extrair_filtros_de_jogo(nums_limpos[:15])
                st.session_state["cfg_ativa"] = cfg_gerada
                st.session_state.pool_trabalho = set(nums_limpos[:15])
                st.success("✅ Filtros extraídos e calibrados com sucesso!")
                st.rerun()

    cfg_ativo = st.session_state.get("cfg_ativa", extrair_filtros_de_jogo(JOGO_BASE_PADRAO))

    with st.container(border=True):
        st.markdown("#### ⚙️ AJUSTE MANUAL DE RESTRIÇÕES")
        
        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1:
            primos_sel = st.multiselect("Quantidade de Primos:", list(range(10)), default=cfg_ativo["primos"], key="sel_primos")
        with c_p2:
            pares_sel = st.multiselect("Quantidade de Pares:", list(range(16)), default=cfg_ativo["pares"], key="sel_pares")
        with c_p3:
            moldura_sel = st.multiselect("Quantidade na Moldura:", list(range(16)), default=cfg_ativo["moldura"], key="sel_moldura")

        faixa_soma_cfg = st.slider("Faixa de Soma Total:", 100, 300, tuple(cfg_ativo["soma"]), key="sel_soma")

    if st.button("🚀 GERAR JOGOS COM ESTAS RESTRIÇÕES", type="primary", use_container_width=True):
        cfg_atualizado = cfg_ativo.copy()
        cfg_atualizado["primos"] = primos_sel
        cfg_atualizado["pares"] = pares_sel
        cfg_atualizado["moldura"] = moldura_sel
        cfg_atualizado["soma"] = list(faixa_soma_cfg)
        
        with st.spinner("🛠️ Processando combinações..."):
            aprovados = executar_varredura_pool(st.session_state.pool_trabalho, cfg_atualizado, st.empty(), st.empty())
            st.session_state.jogos_aprovados = aprovados
            st.success(f"✅ Sucesso! {len(aprovados):,} apostas geradas.")
            st.rerun()

    if st.session_state.jogos_aprovados:
        st.markdown(f"<div class='progresso-gigante'>TOTAL APROVADO: {len(st.session_state.jogos_aprovados):,} APOSTAS</div>", unsafe_allow_html=True)
        st.download_button("📥 BAIXAR JOGOS APROVADOS (.TXT)", data="\n".join([" ".join([f"{n:02d}" for n in j]) for j in st.session_state.jogos_aprovados]), file_name="lotofacil_filtradas.txt", mime="text/plain", use_container_width=True)

# ------------------------------------------------------------------------------
# ABA 3: UPLOAD & CONFERÊNCIA
# ------------------------------------------------------------------------------
with tab_upload:
    st.markdown("### 🎯 CONFERÊNCIA DE RESULTADOS")
    if st.session_state.jogos_aprovados:
        st.info(f"Há {len(st.session_state.jogos_aprovados):,} apostas na memória.")
        sorteio_str = st.text_input("15 Dezenas do Sorteio (espaços):", "03 05 07 08 11 13 14 15 18 19 20 21 22 23 25")
        sorteio_nums = [int(x) for x in re.findall(r"\b\d+\b", sorteio_str)]
        
        if len(sorteio_nums) == 15 and st.button("Conferir Jogos Agora", type="primary"):
            render_cartao_sorteio_html(sorteio_nums, titulo="CONCURSO CONFERIDO")
            relatorio, placar = conferir_apostas_contra_sorteio(st.session_state.jogos_aprovados, sorteio_nums)
            
            c15, c14, c13, c12, c11 = st.columns(5)
            c15.metric("15 P", f"{len(placar[15])}")
            c14.metric("14 P", f"{len(placar[14])}")
            c13.metric("13 P", f"{len(placar[13])}")
            c12.metric("12 P", f"{len(placar[12])}")
            c11.metric("11 P", f"{len(placar[11])}")
    else:
        st.warning("Gere seus jogos na aba anterior para habilitar a conferência.")

# ------------------------------------------------------------------------------
# ABA 4: HISTÓRICO & CICLO
# ------------------------------------------------------------------------------
with tab_historico:
    st.markdown("### 📊 HISTÓRICO & CICLO DA LOTOFÁCIL")
    if st.button("🌐 SINCRONIZAR COM A CAIXA", type="primary", use_container_width=True):
        try:
            r = requests.get("https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil", headers=HEADERS_CAIXA, timeout=10, verify=False)
            if r.status_code == 200:
                ult = r.json()
                dezenas = sorted([int(x) for x in ult.get("listaDezenas", [])])
                if len(dezenas) == 15 and dezenas not in st.session_state.historico:
                    st.session_state.historico.append(dezenas)
                    st.success(f"Concurso #{ult.get('numero')} sincronizado!")
                    st.rerun()
        except Exception as e:
            st.error(f"Erro: {e}")

# ------------------------------------------------------------------------------
# ABA 5: BLOCO DE NOTAS
# ------------------------------------------------------------------------------
with tab_notas:
    st.markdown("### 📝 BLOCO DE NOTAS AUTOMÁTICO")
    notas_atuais = carregar_notas_salvas()
    novas_notas = st.text_area("Rascunho:", value=notas_atuais, height=350)
    if novas_notas != notas_atuais:
        salvar_notas_automaticamente(novas_notas)
