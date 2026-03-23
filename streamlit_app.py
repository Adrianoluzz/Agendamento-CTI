import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÕES E ESTILIZAÇÃO ---
st.set_page_config(page_title="Sistema de Laboratórios CTI", layout="wide", page_icon="📅")

# CSS REVISADO: Esconde o "View Source" e Menu, mas GARANTE que a seta lateral apareça
hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    /* Esconde o ícone de código/GitHub mas deixa o espaço da barra lateral livre */
    [data-testid="stActionButtonIcon"] {display: none;}
    
    /* Garante que o botão de abrir a barra lateral (setinha) seja visível */
    [data-testid="stSidebarCollapseButton"] {
        visibility: visible !important;
        display: block !important;
        left: 10px !important;
    }
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# --- RESTANTE DO CÓDIGO (IGUAL AO ANTERIOR) ---
LABS = ["Automação", "Química", "Desenho", "Predial", "Hidráulica", 
        "Civil", "Maquete", "Eletrônica", "Física", "Mecânica"]

OPCOES_POR_TURNO = {
    "Matutino": ["08:00 - 11:00 (Completo)", "08:00 - 09:30 (1º Horário)", "09:45 - 11:00 (2º Horário)"],
    "Vespertino": ["14:00 - 17:00 (Completo)"],
    "Noturno": ["19:00 - 22:00 (Completo)", "19:00 - 20:30 (1º Horário)", "20:45 - 22:00 (2º Horário)"]
}

MESES_PT = {'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março', 'April': 'Abril', 'May': 'Maio', 'June': 'Junho', 'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro', 'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'}
DIAS_PT = {'Monday': 'Segunda-feira', 'Tuesday': 'Terça-feira', 'Wednesday': 'Quarta-feira', 'Thursday': 'Quinta-feira', 'Friday': 'Sexta-feira', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}

SENHA_ADMIN = "cti123" 

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
            status["1º"] = f"Indisponível - Prof. {prof}"
            status["Completo"] = f"Indisponível - Prof. {prof} (1º Horário)"
        elif "(2º Horário)" in h:
            status["2º"] = f"Indisponível - Prof. {prof}"
            status["Completo"] = f"Indisponível - Prof. {prof} (2º Horário)"
        elif "(Completo)" in h:
            status["1º"] = f"Indisponível - Prof. {prof}"
            status["2º"] = f"Indisponível - Prof. {prof}"
            status["Completo"] = f"Indisponível - Prof. {prof}"
    return status

st.sidebar.title("📌 Sistema CTI")
pagina = st.sidebar.radio("Navegação:", ["📅 Consulta de Agenda", "🔐 Administração"])

if pagina == "📅 Consulta de Agenda":
    st.title("📋 Agenda de Laboratórios")
    df_raw = carregar_dados()
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_lab = st.multiselect("Filtrar por Laboratório", LABS, default=LABS)
    with col_f2:
        ver_historico = st.checkbox("Ver agendamentos passados")

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
                    with st.expander(f"{d_s} ({s_pt})"):
                        st.table(df_dia[["Horario", "Laboratorio", "Professor"]].sort_values(by="Horario"))
        else: st.warning("Nenhum agendamento encontrado.")

elif pagina == "🔐 Administração":
    st.title("🔐 Painel Administrativo")
    senha_input = st.sidebar.text_input("Digite a senha de Admin:", type="password")
    if senha_input == SENHA_ADMIN:
        st.success("Acesso Liberado")
        st.subheader("Nova Reserva")
        c1, c2, c3 = st.columns([1, 1, 1.2])
        with c1:
            prof = st.text_input("Professor")
            lab = st.selectbox("Laboratório", LABS)
            tipo = st.selectbox("Modo", ["Recorrência + Extras", "Apenas Dias Específicos"])
        with c2:
            turno = st.radio("Turno", list(OPCOES_POR_TURNO.keys()))
            freq = st.selectbox("Frequência", ["Semanal", "Quinzenal"]) if tipo == "Recorrência + Extras" else None
        with c3:
            horario = st.radio("Horário", OPCOES_POR_TURNO[turno])

        st.markdown("---")
        datas_finais = []
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            if tipo == "Recorrência + Extras":
                d_ini = st.date_input("Início", datetime.now().date())
                qtd = st.number_input("Total aulas", min_value=1, value=1)
                for i in range(qtd): datas_finais.append(d_ini + timedelta(weeks=i * (2 if freq == "Quinzenal" else 1)))
            else:
                datas_finais = st.multiselect("Dias específicos:", pd.date_range(start=datetime.now(), periods=120).date, format_func=lambda x: x.strftime('%d/%m/%Y'))
        with col_d2:
            if tipo == "Recorrência + Extras":
                extras = st.multiselect("Extras (opcional):", pd.date_range(start=datetime.now(), periods=120).date, format_func=lambda x: x.strftime('%d/%m/%Y'))
                datas_finais.extend(extras)
                datas_finais = sorted(list(set(datas_finais)))

        st.markdown("---")
        chave = "Completo" if "Completo" in horario else ("1º" if "1º" in horario else "2º")

        if st.button("🔍 Verificar Tudo", use_container_width=True):
            if not datas_finais: st.warning("Selecione as datas.")
            else:
                df_at = carregar_dados()
                for d in datas_finais:
                    st_d = analisar_disponibilidade(df_at, lab, d, turno)
                    if st_d[chave] == "Livre": st.success(f"✅ {d.strftime('%d/%m/%Y')}: Disponível")
                    else: st.error(f"❌ {d.strftime('%d/%m/%Y')}: {st_d[chave]}")

        if st.button("🚀 Gravar Agendamentos", use_container_width=True, type="primary"):
            if not prof or not datas_finais: st.warning("Dados incompletos.")
            else:
                df_at = carregar_dados()
                if any(analisar_disponibilidade(df_at, lab, d, turno)[chave] != "Livre" for d in datas_finais):
                    st.error("Conflito detectado!")
                else:
                    novos = [{"Professor": prof, "Laboratorio": lab, "Data": d.strftime('%Y-%m-%d'), "Turno": turno, "Horario": horario} for d in datas_finais]
                    try:
                        conn.update(data=pd.concat([df_at, pd.DataFrame(novos)], ignore_index=True))
                        st.success("Sucesso!"); st.balloons()
                    except Exception as e: st.error(f"Erro: {e}")
    else:
        if senha_input: st.sidebar.error("Senha incorreta")
        st.warning("⚠️ Insira a senha na barra lateral.")
