import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÕES E ESTILIZAÇÃO ---
st.set_page_config(page_title="Sistema de Laboratórios CTI", layout="wide", page_icon="📅")

# CSS CIRÚRGICO: Esconde apenas o Deploy e o Menu, mantendo a Seta da Barra Lateral
hide_style = """
    <style>
    /* Esconde o botão de Deploy (canto superior direito) */
    .stAppDeployButton {display:none !important;}
    
    /* Esconde o menu de hambúrguer (três linhas) */
    #MainMenu {visibility: hidden !important;}
    
    /* Esconde o rodapé 'Made with Streamlit' */
    footer {visibility: hidden !important;}
    
    /* REMOVE ESPECIFICAMENTE o ícone de código/GitHub do cabeçalho */
    [data-testid="stActionButtonIcon"] {display: none !important;}
    
    /* Garante que a seta de abrir/fechar a barra lateral continue visível e funcional */
    [data-testid="stSidebarCollapseButton"] {
        visibility: visible !important;
        display: flex !important;
    }
    
    /* Ajusta a margem do topo para não ficar um buraco vazio mas manter a seta */
    .st-emotion-cache-12fmjuu {top: 0px !important;}
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
            status["1º"] = f"Ocupado - Prof. {prof}"
            status["Completo"] = f"Ocupado (1º Horário) - Prof. {prof}"
        elif "(2º Horário)" in h:
            status["2º"] = f"Ocupado - Prof. {prof}"
            status["Completo"] = f"Ocupado (2º Horário) - Prof. {prof}"
        elif "(Completo)" in h:
            status["1º"] = f"Ocupado - Prof. {prof}"; status["2º"] = f"Ocupado - Prof. {prof}"; status["Completo"] = f"Ocupado - Prof. {prof}"
    return status

# --- 3. NAVEGAÇÃO ---
st.sidebar.title("📌 Sistema CTI")
pagina = st.sidebar.radio("Navegação:", ["📅 Consulta de Agenda", "🔐 Administração"])

if pagina == "📅 Consulta de Agenda":
    st.title("📋 Agenda de Laboratórios")
    df_raw = carregar_dados()
    c_f1, c_f2 = st.columns(2)
    with c_f1: flt_lab = st.multiselect("Filtrar Laboratório", LABS, default=LABS)
    with c_f2: ver_hist = st.checkbox("Ver passados")

    if not df_raw.empty:
        df_raw['Data'] = pd.to_datetime(df_raw['Data'], errors='coerce')
        hoje = datetime.now().date()
        df_view = df_raw.copy() if ver_hist else df_raw[df_raw['Data'].dt.date >= hoje].copy()
        df_view = df_view[df_view['Laboratorio'].isin(flt_lab)].sort_values(by="Data")
        if not df_view.empty:
            df_view['Mes_Ano'] = df_view['Data'].dt.strftime('%B %Y')
            for m_en in df_view['Mes_Ano'].unique():
                m_pt = m_en
                for en, pt in MESES_PT.items(): m_pt = m_pt.replace(en, pt)
                st.markdown(f"#### 📅 {m_pt}")
                df_mes = df_view[df_view['Mes_Ano'] == m_en]
                for d_dt in sorted(df_mes['Data'].unique()):
                    df_dia = df_mes[df_mes['Data'] == d_dt]
                    d_s = pd.to_datetime(d_dt).strftime('%d/%m/%Y')
                    s_pt = DIAS_PT.get(pd.to_datetime(d_dt).strftime('%A'))
                    with st.expander(f"{d_s} ({s_pt})"):
                        st.table(df_dia[["Horario", "Laboratorio", "Professor"]].sort_values(by="Horario"))
        else: st.warning("Sem registros.")

elif pagina == "🔐 Administração":
    st.title("🔐 Painel Administrativo")
    senha = st.sidebar.text_input("Senha de Admin:", type="password")
    if senha == SENHA_ADMIN:
        st.success("Acesso Liberado")
        c1, c2, c3 = st.columns([1, 1, 1.2])
        with c1:
            prof_n = st.text_input("Professor")
            lab_n = st.selectbox("Laboratório", LABS)
            tipo_n = st.selectbox("Modo", ["Recorrência + Extras", "Apenas Dias Específicos"])
        with c2:
            turno_n = st.radio("Turno", list(OPCOES_POR_TURNO.keys()))
            freq_n = st.selectbox("Frequência", ["Semanal", "Quinzenal"]) if tipo_n == "Recorrência + Extras" else None
        with c3:
            horario_n = st.radio("Horário", OPCOES_POR_TURNO[turno_n])

        st.markdown("---")
        datas_finais = []
        cd1, cd2 = st.columns(2)
        with cd1:
            if tipo_n == "Recorrência + Extras":
                d_ini = st.date_input("Início", datetime.now().date())
                qtd = st.number_input("Total de aulas", min_value=1, value=1)
                for i in range(qtd): datas_finais.append(d_ini + timedelta(weeks=i * (2 if freq_n == "Quinzenal" else 1)))
            else:
                datas_finais = st.multiselect("Dias específicos:", pd.date_range(start=datetime.now(), periods=120).date, format_func=lambda x: x.strftime('%d/%m/%Y'))
        with cd2:
            if tipo_n == "Recorrência + Extras":
                extras = st.multiselect("Extras:", pd.date_range(start=datetime.now(), periods=120).date, format_func=lambda x: x.strftime('%d/%m/%Y'))
                datas_finais.extend(extras); datas_finais = sorted(list(set(datas_finais)))

        st.markdown("---")
        chave = "Completo" if "Completo" in horario_n else ("1º" if "1º" in horario_n else "2º")

        if st.button("🔍 Verificar Tudo", use_container_width=True):
            if not datas_finais: st.warning("Selecione as datas.")
            else:
                df_at = carregar_dados()
                for d in datas_finais:
                    st_d = analisar_disponibilidade(df_at, lab_n, d, turno_n)
                    if st_d[chave] == "Livre": st.success(f"✅ {d.strftime('%d/%m/%Y')}: Disponível")
                    else: st.error(f"❌ {d.strftime('%d/%m/%Y')}: {st_d[chave]}")

        if st.button("🚀 Gravar", use_container_width=True, type="primary"):
            if not prof_n or not datas_finais: st.warning("Preencha tudo.")
            else:
                df_at = carregar_dados()
                if any(analisar_disponibilidade(df_at, lab_n, d, turno_n)[chave] != "Livre" for d in datas_finais):
                    st.error("Conflito detectado!")
                else:
                    novos = [{"Professor": prof_n, "Laboratorio": lab_n, "Data": d.strftime('%Y-%m-%d'), "Turno": turno_n, "Horario": horario_n} for d in datas_finais]
                    try:
                        conn.update(data=pd.concat([df_at, pd.DataFrame(novos)], ignore_index=True))
                        st.success("Salvo!"); st.balloons()
                    except: st.error("Erro ao salvar.")
    else:
        if senha: st.sidebar.error("Senha incorreta")
        st.warning("⚠️ Insira a senha na lateral.")
