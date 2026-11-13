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
    page_title="LOTOFÁCIL25 - Alto Contraste & Filtro Direto",
    page_icon="🍀",
    layout="wide"
)

# ESTILIZAÇÃO CSS ENXUTA E DE ALTO CONTRASTE (VISUAL CLÁSSICO)
st.markdown('''
<style>
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    html, body, [class*="css"], .stMarkdown, p, span, label, div, input, textarea, select {
        color: #000000 !important;
        font-weight: 800 !important;
        font-family: Arial, sans-serif !important;
    }
    h1, h2, h3 { color: #000000 !important; font-weight: 900 !important; }
    
    [data-testid="stVerticalBlock"] > div[style*="border"] {
        background-color: #f8fafc !important;
        border: 3px solid #000000 !important;
        border-radius: 8px !important;
    }

    .stButton > button {
        color: #000000 !important;
        font-size: 1.2rem !important;
        font-weight: 900 !important;
        border: 3px solid #000000 !important;
        background-color: #ffffff !important;
        border-radius: 6px !important;
    }
    .stButton > button[kind="primary"] {
        background-color: #facc15 !important;
        color: #000000 !important;
        border: 3px solid #000000 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 900 !important;
        color: #000000 !important;
    }
    .progresso-gigante {
        font-size: 1.3rem !important;
        font-weight: 900 !important;
        color: #000000 !important;
        background-color: #fef08a !important;
        padding: 10px;
        border: 3px solid #000000;
        border-radius: 6px;
        text-align: center;
        margin: 10px 0;
    }
</style>
''', unsafe_allow_html=True)

# ==============================================================================
# CONSTANTES E LOOKUPS MATRICIAIS 5x5
# ==============================================================================
TOTAL_NUMS = 25
FIBONACCI_LOTOFACIL = {1, 2, 3, 5, 8, 13, 21}
PRIMOS_LOTOFACIL = {2, 3, 5, 7, 11, 13, 17, 19, 23}

PAR_LOOKUP = [False] + [(n % 2 == 0) for n in range(1, 26)]
PRIMO_LOOKUP = [False] + [(n in PRIMOS_LOTOFACIL) for n in range(1, 26)]
MOLDURA_SET = set(range(1, 6)) | set(range(21, 26)) | {r * 5 + 1 for r in range(5)} | {r * 5 + 5 for r in range(5)}
MOLDURA_LOOKUP = [False] + [(n in MOLDURA_SET) for n in range(1, 26)]
CRUZ_CENTRAL_SET = {3, 8, 11, 12, 13, 14, 15, 18, 23}
CRUZ_LOOKUP = [False] + [(n in CRUZ_CENTRAL_SET) for n in range(1, 26)]

ROW_LOOKUP = [0] + [(n - 1) // 5 for n in range(1, 26)]
COL_LOOKUP = [0] + [(n - 1) % 5 for n in range(1, 26)]
DC_LOOKUP = [0] + [(((n - 1) % 5) + ((n - 1) // 5)) % 5 for n in range(1, 26)]
DD_LOOKUP = [0] + [(((n - 1) % 5) - ((n - 1) // 5)) % 5 for n in range(1, 26)]

JOGO_BASE_PADRAO = [3, 5, 7, 8, 11, 13, 14, 15, 18, 19, 20, 21, 22, 23, 25]

HEADERS_CAIXA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
}

# ==============================================================================
# ESTADO DA SESSÃO
# ==============================================================================
if "historico" not in st.session_state:
    st.session_state.historico = [JOGO_BASE_PADRAO]

if "jogos_aprovados" not in st.session_state:
    st.session_state.jogos_aprovados = []

if "pool_trabalho" not in st.session_state:
    st.session_state.pool_trabalho = set(JOGO_BASE_PADRAO)

if "input_dezenas_texto" not in st.session_state:
    st.session_state.input_dezenas_texto = " ".join([f"{n:02d}" for n in JOGO_BASE_PADRAO])

# ==============================================================================
# FUNÇÕES DE ENGENHARIA REVERSA E VALIDAÇÃO
# ==============================================================================
def extrair_filtros_precisos(dezenas):
    dezenas = sorted(list(set(dezenas)))
    if len(dezenas) < 15:
        dezenas = JOGO_BASE_PADRAO

    l_cnt, c_cnt, dc_cnt, dd_cnt = [0]*5, [0]*5, [0]*5, [0]*5
    for n in dezenas:
        l_cnt[ROW_LOOKUP[n]] += 1
        c_cnt[COL_LOOKUP[n]] += 1
        dc_cnt[DC_LOOKUP[n]] += 1
        dd_cnt[DD_LOOKUP[n]] += 1

    def folga(v):
        return [max(0, v - 2), min(5, v + 2)]

    pares_jogo = sum(1 for n in dezenas if PAR_LOOKUP[n])
    primos_total = sum(1 for n in dezenas if PRIMO_LOOKUP[n])
    moldura_total = sum(1 for n in dezenas if MOLDURA_LOOKUP[n])
    cruz_total = sum(1 for n in dezenas if CRUZ_LOOKUP[n])
    soma_total = sum(dezenas[:15])

    return {
        "linhas": [folga(q) for q in l_cnt],
        "colunas": [folga(q) for q in c_cnt],
        "diag_cresc": [folga(q) for q in dc_cnt],
        "diag_decresc": [folga(q) for q in dd_cnt],
        "primos": list(range(max(1, primos_total - 2), min(10, primos_total + 3))),
        "pares": list(range(max(4, pares_jogo - 2), min(12, pares_jogo + 3))),
        "moldura": list(range(max(5, moldura_total - 3), min(16, moldura_total + 4))),
        "cruz": list(range(max(1, cruz_total - 3), min(10, cruz_total + 4))),
        "soma": [max(130, soma_total - 50), min(260, soma_total + 50)]
    }

def validar_aposta(jogo, cfg):
    soma_j = sum(jogo)
    faixa_soma = cfg.get("soma", [130, 260])
    if not (faixa_soma[0] <= soma_j <= faixa_soma[1]):
        return False
    
    if sum(1 for n in jogo if PAR_LOOKUP[n]) not in cfg.get("pares", []):
        return False
    if sum(1 for n in jogo if PRIMO_LOOKUP[n]) not in cfg.get("primos", []):
        return False
    if sum(1 for n in jogo if MOLDURA_LOOKUP[n]) not in cfg.get("moldura", []):
        return False

    l_cnt, c_cnt, dc_cnt, dd_cnt = [0]*5, [0]*5, [0]*5, [0]*5
    for n in jogo:
        l_cnt[ROW_LOOKUP[n]] += 1
        c_cnt[COL_LOOKUP[n]] += 1
        dc_cnt[DC_LOOKUP[n]] += 1
        dd_cnt[DD_LOOKUP[n]] += 1

    def check(cnt, limits):
        for i, val in enumerate(cnt):
            mn, mx = limits[i]
            if not (mn <= val <= mx):
                return False
        return True

    if not check(l_cnt, cfg["linhas"]): return False
    if not check(c_cnt, cfg["colunas"]): return False
    if not check(dc_cnt, cfg["diag_cresc"]): return False
    if not check(dd_cnt, cfg["diag_decresc"]): return False

    return True

# ==============================================================================
# INTERFACE PRINCIPAL
# ==============================================================================
st.title("🍀 LOTOFÁCIL 25 - PAINEL DIRETO")
st.caption("MATRIZ 5x5 • ALTO CONTRASTE • MOTOR DE RESTRIÇÃO ENXUTO")

tab_principal, tab_conferencia = st.tabs(["🎯 Configuração & Geração", "📊 Conferência de Resultados"])

with tab_principal:
    with st.container(border=True):
        st.markdown("### ⚡ SUAS 15 DEZENAS DE BASE")
        st.caption("Insira seu jogo base abaixo. O sistema criará automaticamente a restrição com margem de segurança ajustada para gerar os jogos.")
        
        txt_input = st.text_area("Dezenas:", value=st.session_state.input_dezenas_texto, height=70)
        st.session_state.input_dezenas_texto = txt_input

        if st.button("🚀 CALIBRAR FILTRO E GERAR JOGOS", type="primary", use_container_width=True):
            nums = [int(x) for x in re.findall(r"\b\d+\b", txt_input)]
            nums_limpos = sorted(list(set([n for n in nums if 1 <= n <= 25])))
            
            if len(nums_limpos) < 15:
                st.error("⚠️ Insira exatamente ou pelo menos 15 dezenas válidas (entre 01 e 25).")
            else:
                st.session_state.pool_trabalho = set(nums_limpos[:15])
                cfg_gerada = extrair_filtros_precisos(nums_limpos[:15])
                st.session_state["cfg_ativa"] = cfg_gerada
                
                # Executa a varredura combinatória
                pool = sorted(list(st.session_state.pool_trabalho))
                aprovados = []
                bar = st.progress(0.0)
                txt_status = st.empty()
                
                total_comb = math.comb(len(pool), 15) if len(pool) >= 15 else 1
                testadas = 0
                
                for comb in combinations(pool, 15):
                    testadas += 1
                    if validar_aposta(comb, cfg_gerada):
                        aprovados.append(sorted(list(comb)))
                    if testadas % 100 == 0:
                        bar.progress(min(1.0, testadas / total_comb))
                
                bar.progress(1.0)
                st.session_state.jogos_aprovados = aprovados
                st.success(f"✅ Processo concluído! {len(aprovados):,} apostas geradas com sucesso.")
                st.rerun()

    if st.session_state.jogos_aprovados:
        st.markdown(f"<div class='progresso-gigante'>TOTAL GERADO: {len(st.session_state.jogos_aprovados):,} APOSTAS</div>", unsafe_allow_html=True)
        txt_download = "\n".join([" ".join([f"{n:02d}" for n in j]) for j in st.session_state.jogos_aprovados])
        st.download_button("📥 BAIXAR JOGOS (.TXT)", data=txt_download, file_name="lotofacil_jogos.txt", mime="text/plain", use_container_width=True)

with tab_conferencia:
    st.markdown("### 🎯 CONFERÊNCIA RÁPIDA")
    if st.session_state.jogos_aprovados:
        st.info(f"Você tem {len(st.session_state.jogos_aprovados):,} jogos em memória prontos para conferir.")
        sorteio_str = st.text_input("Digite as 15 dezenas do sorteio:", "01 02 03 04 05 06 07 08 09 10 11 12 13 14 15")
        sorteio_nums = [int(x) for x in re.findall(r"\b\d+\b", sorteio_str)]
        
        if len(sorteio_nums) == 15 and st.button("Conferir Jogos", type="primary"):
            sort_set = set(sorteio_nums)
            premios = {15: 0, 14: 0, 13: 0, 12: 0, 11: 0}
            for j in st.session_state.jogos_aprovados:
                acertos = len(set(j) & sort_set)
                if acertos in premios:
                    premios[acertos] += 1
            st.metric("Jogos com 14 Pontos", premios[14])
            st.metric("Jogos com 13 Pontos", premios[13])
            st.metric("Jogos com 12 Pontos", premios[12])
            st.metric("Jogos com 11 Pontos", premios[11])
    else:
        st.warning("Gere os jogos na aba anterior para habilitar a conferência.")
