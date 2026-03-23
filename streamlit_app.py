import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÕES E ESTILIZAÇÃO ---
st.set_page_config(page_title="Sistema de Laboratórios CTI", layout="wide", page_icon="📅")

# CSS "NINJA": Esconde os controles nativos e isola a seta de navegação
hide_style = """
    <style>
    /* Esconde o Header e o Rodapé nativos */
    header[data-testid="stHeader"] {
        visibility: hidden;
        height: 0px;
    }
    footer {visibility: hidden !important;}
    
    /* Esconde botões de Deploy e Menu que possam sobrar */
    .stAppDeployButton, #MainMenu {display: none !important;}

    /* RECRIA O BOTÃO DA BARRA LATERAL (A SETINHA) */
    /* Garante que ela apareça mesmo com o header escondido */
    [data-testid="stSidebarCollapseButton"] {
        visibility: visible !important;
        display: flex !important;
        position: fixed !important;
        top: 15px !important;
        left: 15px !important;
        z-index: 999999;
        background-color: #ffffff;
        border: 1px solid #ddd;
        border-radius: 5px;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.1);
    }
    
    /* Ajuste de margem interna para o conteúdo não colar no topo */
    .block-container {
        padding-top: 3rem !important;
    }
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# --- CONFIGURAÇÕES DO CTI ---
LABS = ["Automação", "Química", "Desenho", "Predial", "Hidráulica", 
        "Civil", "Maquete", "Eletrônica", "Física", "Mecânica"]

OPCOES_POR_TURNO = {
    "Matutino": ["08:00 - 11:00 (Completo)", "08:00 - 09:30 (1º Horário)", "09:45 - 11:00 (2º Horário)"],
    "Vespertino": ["14:00 - 17:00 (Completo)"],
    "Noturno": ["19:00 - 22:00 (Completo)", "19:00 - 20:30 (1º Horário)", "20:45 - 22:00 (2º Horário)"]
}

MESES_PT = {'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março', 'April': 'Abril', 'May': 'Maio', 'June': 'Junho', 'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro', 'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'}
DIAS_PT = {'Monday': 'Segunda-feira', 'Tuesday': 'Terça-feira', 'Wednesday': 'Quarta-feira', 'Thursday': 'Quinta-feira', 'Friday': 'Sexta-feira', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}

# SENHA DE ACESSO ADMINISTRATIVO
SENHA_ADMIN = "cti123" 

# --- 2. CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        data = conn.read(ttl=0)
        return data if data is not None else pd.DataFrame(columns=["Professor", "Laboratorio", "Data", "Turno", "Horario"])
    except:
        return pd.DataFrame(columns=["Professor", "Laboratorio", "Data", "Turno", "Horario"])

def analisar_disponibilidade(df, lab, data, turno):
    df_temp = df.copy()
    df_temp['Data'] = pd.to_datetime(df_temp['Data'], errors='coerce').dt.date
    reservas = df_temp[(df_temp['Laboratorio'] == lab) & (df_temp['Data'] == data) & (df_temp['Turno'] == turno)]
    
    status = {"1º": "Livre", "2º": "Livre", "Completo": "Livre"}
    for _, r in reservas.iterrows():
        h, prof = r['Horario'], r['Professor']
        if "(1º Horário)" in h:
            status["1º"] = f"Ocupado (1º H) - Prof. {prof}"
            status["Completo"] = f"Ocupado (1º H) - Prof. {prof}"
        elif "(2º Horário)" in h:
            status["2º"] = f"Ocupado (2º H) - Prof. {prof}"
            status["Completo"] = f"Ocupado (2º H) - Prof. {prof}"
        elif "(Completo)" in h:
            status["1º"] = f"Ocupado - Prof. {prof}"
            status["2º"] = f"Ocupado - Prof. {prof}"
            status["Completo"] = f"Ocupado - Prof. {prof}"
    return status

# --- 3. NAVEGAÇÃO LATERAL ---
st.sidebar.title("📌 Sistema CTI")
pagina = st.sidebar.radio("Navegação:", ["📅 Consulta de Agenda", "🔐 Administração"])

if pagina == "📅 Consulta de Agenda":
    st.title("📋 Agenda de Laboratórios")
    df_raw = carregar_dados()
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_lab = st.multiselect("Filtrar por Laboratório", LABS, default=LABS)
    with col_f2:
        ver_historico = st.checkbox("Exibir agendamentos passados")

    if not df_raw.empty:
        df_raw['Data'] = pd.to_datetime(df_raw['Data'], errors='coerce')
        hoje = datetime.now().date()
        df_view = df_raw.copy() if ver_historico else df_raw[df_raw['Data'].dt.date >= hoje].copy()
        df_view = df_view[df_view['Laboratorio'].isin(filtro_lab)].sort_values(by="Data")

        if not df_view.empty:
            df_view['Mes_Ano'] = df_view['Data'].dt.strftime('%B %Y')
            for m_en in df_view['Mes_Ano'].unique():
                m_pt = m_en
                for en, pt in MESES_PT.items(): m_pt = m_pt.replace(en, pt)
                st.markdown(f"### 📅 {m_pt}")
                df_mes = df_view[df_view['Mes_Ano'] == m_en]
                for d_dt in sorted(df_mes['Data'].unique()):
                    df_dia = df_mes[df_mes['Data'] == d_dt]
                    d_s = pd.to_datetime(d_dt).strftime('%d/%m/%Y')
                    s_pt = DIAS_PT.get(pd.to_datetime(d_dt).strftime('%A'))
                    with st.expander(f"{d_s} ({s_pt}) - {len(df_dia)} reserva(s)"):
                        st.table(df_dia[["Horario", "Laboratorio", "Professor"]].sort_values(by="Horario"))
        else: st.warning("Nenhum agendamento encontrado para os filtros atuais.")
    else: st.info("A base de dados está vazia.")

elif pagina == "🔐 Administração":
    st.title("🔐 Painel Administrativo")
    senha_input = st.sidebar.text_input("Senha de Acesso:", type="password")
    
    if senha_input == SENHA_ADMIN:
        st.success("Acesso Liberado!")
        st.subheader("Novo Agendamento")
        
        c1, c2, c3 = st.columns([1, 1, 1.2])
        with c1:
            prof = st.text_input("Nome do Professor")
            lab = st.selectbox("Laboratório", LABS)
            tipo = st.selectbox("Modo de Agendamento", ["Recorrência + Extras", "Apenas Dias Específicos"])
        with c2:
            turno = st.radio("Turno", list(OPCOES_POR_TURNO.keys()))
            freq = st.selectbox("Frequência", ["Semanal", "Quinzenal"]) if tipo == "Recorrência + Extras" else None
        with c3:
            horario = st.radio("Horário", OPCOES_POR_TURNO[turno])

        st.markdown("---")
        datas_finais = []
        cd1, cd2 = st.columns(2)
        with cd1:
            if tipo == "Recorrência + Extras":
                d_ini = st.date_input("Data Inicial", datetime.now().date())
                qtd = st.number_input("Número de aulas na série", min_value=1, value=1)
                pulo = 2 if freq == "Quinzenal" else 1
                for i in range(qtd): datas_finais.append(d_ini + timedelta(weeks=i * pulo))
            else:
                datas_finais = st.multiselect("Selecione as datas:", pd.date_range(start=datetime.now(), periods=120).date, format_func=lambda x: x.strftime('%d/%m/%Y'))
        with cd2:
            if tipo == "Recorrência + Extras":
                extras = st.multiselect("Adicionar dias extras (Ex: Sábado letivo):", pd.date_range(start=datetime.now(), periods=120).date, format_func=lambda x: x.strftime('%d/%m/%Y'))
                datas_finais.extend(extras)
                datas_finais = sorted(list(set(datas_finais)))

        st.markdown("---")
        chave = "Completo" if "Completo" in horario else ("1º" if "1º" in horario else "2º")

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("🔍 Verificar Disponibilidade", use_container_width=True):
                if not datas_finais: st.warning("Selecione ao menos uma data.")
                else:
                    df_at = carregar_dados()
                    for d in datas_finais:
                        st_dia = analisar_disponibilidade(df_at, lab, d, turno)
                        if st_dia[chave] == "Livre": st.success(f"✅ {d.strftime('%d/%m/%Y')}: Disponível")
                        else: st.error(f"❌ {d.strftime('%d/%m/%Y')}: {st_dia[chave]}")

        with col_b2:
            if st.button("🚀 Confirmar Reserva", use_container_width=True, type="primary"):
                if not prof or not datas_finais: st.warning("Preencha o nome do professor e as datas.")
                else:
                    df_at = carregar_dados()
                    if any(analisar_disponibilidade(df_at, lab, d, turno)[chave] != "Livre" for d in datas_finais):
                        st.error("Erro: Uma ou mais datas possuem conflitos de horário.")
                    else:
                        novos = [{"Professor": prof, "Laboratorio": lab, "Data": d.strftime('%Y-%m-%d'), "Turno": turno, "Horario": horario} for d in datas_finais]
                        try:
                            conn.update(data=pd.concat([df_at, pd.DataFrame(novos)], ignore_index=True))
                            st.success(f"✅ {len(datas_finais)} agendamentos realizados!"); st.balloons()
                        except Exception as e: st.error(f"Erro ao salvar na planilha: {e}")
    else:
        if senha_input: st.sidebar.error("Senha Incorreta")
        st.info("💡 Digite a senha administrativa na barra lateral para realizar novos agendamentos.")
