def render_volante_5x5_nativo(dezenas_jogo, dezenas_sorteadas, titulo="VOLANTE DA APOSTA"):
    """Renderiza a matriz 5x5 usando colunas nativas do Streamlit (Sem risco de corte HTML)"""
    jogo_set = set(dezenas_jogo)
    sorteio_set = set(dezenas_sorteadas)
    
    st.markdown(f"<div style='text-align:center; font-weight:900; font-size:16px; margin-bottom:8px; text-transform:uppercase;'>{titulo}</div>", unsafe_allow_html=True)
    
    for r in range(5):
        cols = st.columns(5)
        for c in range(5):
            n = r * 5 + c + 1
            acertou = (n in jogo_set) and (n in sorteio_set)
            presente_jogo = n in jogo_set
            
            # Cores idênticas ao modelo da foto
            if acertou:
                bg = "#facc15" # Amarelo forte
                color = "#000000"
                txt_bola = f"{n:02d}<br><span style='font-size:11px;'>★</span>"
            elif presente_jogo:
                bg = "#d4d4d8" # Cinza intermediário (jogo selecionado)
                color = "#000000"
                txt_bola = f"{n:02d}<br><span style='font-size:11px;'>&nbsp;</span>"
            else:
                bg = "#f4f4f5" # Cinza claro limpo
                color = "#71717a"
                txt_bola = f"{n:02d}<br><span style='font-size:11px;'>&nbsp;</span>"
                
            with cols[c]:
                st.markdown(f"""
                <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;width:100%;height:46px;background:{bg};color:{color};font-weight:900;font-size:17px;border:3px solid #000000;border-radius:8px;font-family:monospace;text-align:center;line-height:1.1;margin-bottom:4px;">
                    {txt_bola}
                </div>
                """, unsafe_allow_html=True)
