import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÕES E ESTILIZAÇÃO ---
st.set_page_config(page_title="Sistema de Laboratórios CTI", layout="wide", page_icon="📅")

# CSS REVISADO: Esconde apenas o lixo da direita, preservando a navegação da esquerda
hide_style = """
    <style>
    /* 1. Esconde o botão de Deploy (canto superior direito) */
    .stAppDeployButton {display:none !important;}
    
    /* 2. Esconde o menu de hambúrguer e o link de código */
    #MainMenu {visibility: hidden !important;}
    header [data-testid="stHeaderActionElements"] {display: none !important;}
    
    /* 3. Esconde o rodapé */
    footer {visibility: hidden !important;}

    /* 4. GARANTE que a seta da barra lateral esteja visível e clicável */
    /* Removemos as posições fixas para deixar o Streamlit gerenciar nativamente */
    [data-testid="stSidebarCollapseButton"] {
        visibility: visible !important;
        display: flex !important;
        opacity: 1 !important;
    }
    
    /* 5. Ajuste fino para o cabeçalho não cobrir a tela mas permitir a seta */
    header[data-testid="stHeader"] {
        background-color: rgba(0,0,0,0) !important;
        color: rgba(0,0,0,0) !important;
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

# SENHA DE ACESSO
SENHA_ADMIN = "cti123" 

# --- 2. CONEXÃO ---
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
            status["1º"] = f"Ocupado - Prof. {prof}"; status["2º"] = f"Ocupado - Prof. {prof}"; status["Completo"] = f"Ocupado - Prof. {prof}"
    return status

# --- 3. NAVEGAÇÃO ---
st.sidebar.title("📌 Sistema CTI")
pagina = st.sidebar.radio("Navegação:", ["📅 Consulta de Agenda", "🔐 Administração"])

if pagina == "📅 Consulta de Agenda":
    st.title("📋 Agenda de Laboratórios")
    df_raw = carregar_dados()
    c1, c2 = st.columns(2)
    with c1: f_lab = st.multiselect("Filtrar Lab", LABS, default=LABS)
    with c2: v_hist = st.checkbox("Ver passados")

    if not df_raw.empty:
        df_raw['Data'] = pd.to_datetime(df_raw['Data'], errors='coerce')
        hoje = datetime.now().date()
        df_view = df_raw.copy() if v_hist else df_raw[df_raw['Data'].dt.date >= hoje].copy()
        df_view = df_view[df_view['Laboratorio'].isin(f_lab)].sort_values(by="Data")
        
        if not df_view.empty:
            df_view['Mes_Ano'] = df_view['Data'].dt.strftime('%B %Y')
            for m_en in df_view['Mes_Ano'].unique():
                m_pt = m_en
                for en, pt in MESES_PT.items(): m_pt = m_pt.replace(en, pt)
                st.markdown(f"#### 📅 {m_pt}")
                df_mes = df_view[df_view['Mes_Ano'] == m_en]
                for d_dt in sorted(df_mes['Data'].unique()):
                    df_dia = df_mes[df_mes['Data'] == d_dt]
                    d_s, s_pt = pd.to_datetime(d_dt).strftime('%d/%m/%Y'), DIAS_PT.get(pd.to_datetime(d_dt).strftime('%A'))
                    with st.expander(f"{d_s} ({s_pt})"):
                        st.table(df_dia[["Horario", "Laboratorio", "Professor"]].sort_values(by="Horario"))
        else: st.warning("Sem agendamentos.")

elif pagina == "🔐 Administração":
    st.title("🔐 Painel Administrativo")
    senha = st.sidebar.text_input("Senha Admin:", type="password")
    if senha == SENHA_ADMIN:
        st.success("Acesso Liberado")
        prof_n = st.text_input("Nome do Professor")
        lab_n = st.selectbox("Laboratório", LABS)
        tipo_n = st.selectbox("Modo", ["Recorrência + Extras", "Apenas Dias Específicos"])
        
        st.markdown("---")
        datas_finais = []
        if tipo_n == "Recorrência + Extras":
            c_a, c_b = st.columns(2)
            with c_a:
                d_ini = st.date_input("Data de Início", datetime.now().date())
                qtd = st.number_input("Total de aulas", min_value=1, value=1)
                freq = st.selectbox("Frequência", ["Semanal", "Quinzenal"])
            with c_b:
                extras = st.multiselect("Dias Extras:", pd.date_range(start=datetime.now(), periods=120).date, format_func=lambda x: x.strftime('%d/%m/%Y'))
            pulo = 2 if freq == "Quinzenal" else 1
            for i in range(qtd): datas_finais.append(d_ini + timedelta(weeks=i * pulo))
            datas_finais.extend(extras)
        else:
            datas_finais = st.multiselect("Datas específicas:", pd.date_range(start=datetime.now(), periods=120).date, format_func=lambda x: x.strftime('%d/%m/%Y'))
        
        datas_finais = sorted(list(set(datas_finais)))
        turno_n = st.radio("Turno", list(OPCOES_POR_TURNO.keys()), horizontal=True)
        horario_n = st.radio("Horário", OPCOES_POR_TURNO[turno_n], horizontal=True)

        if st.button("🚀 Gravar Agendamentos", use_container_width=True, type="primary"):
            if not prof_n or not datas_finais: st.warning("Preencha tudo.")
            else:
                df_at = carregar_dados()
                chave = "Completo" if "Completo" in horario_n else ("1º" if "1º" in horario_n else "2º")
                if any(analisar_disponibilidade(df_at, lab_n, d, turno_n)[chave] != "Livre" for d in datas_finais):
                    st.error("Conflito detectado!")
                else:
                    novos = [{"Professor": prof_n, "Laboratorio": lab_n, "Data": d.strftime('%Y-%m-%d'), "Turno": turno_n, "Horario": horario_n} for d in datas_finais]
                    conn.update(data=pd.concat([df_at, pd.DataFrame(novos)], ignore_index=True))
                    st.success("Salvo com sucesso!"); st.balloons()
    else:
        if senha: st.sidebar.error("Senha incorreta")
        st.info("Insira a senha na lateral para agendar.")
