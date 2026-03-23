import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÕES E ESTILO ---
st.set_page_config(page_title="Sistema CTI", layout="wide", page_icon="📅")

# CSS: Customização das cores e remoção da seta lateral
hide_elements_style = """
    <style>
    header[data-testid="stHeader"] { visibility: hidden; height: 0px; }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }
    footer {visibility: hidden;}
    .block-container { padding-top: 1rem !important; }
    
    /* ESTILO DA TARJA DA SEMANA (AZUL COM TEXTO BRANCO) */
    .semana-header {
        background-color: #004a99; /* Azul escuro profissional */
        color: white !important;    /* Texto branco */
        padding: 8px 20px;
        border-radius: 8px;
        margin-top: 25px;
        margin-bottom: 10px;
        font-weight: bold;
        font-size: 1.1rem;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    </style>
"""
st.markdown(hide_elements_style, unsafe_allow_html=True)

# --- CONFIGURAÇÕES TÉCNICAS ---
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
            status["1º"] = f"Ocupado - Prof. {prof}"; status["Completo"] = f"Ocupado (1º H) - Prof. {prof}"
        elif "(2º Horário)" in h:
            status["2º"] = f"Ocupado - Prof. {prof}"; status["Completo"] = f"Ocupado (2º H) - Prof. {prof}"
        elif "(Completo)" in h:
            status["1º"] = f"Ocupado - Prof. {prof}"; status["2º"] = f"Ocupado - Prof. {prof}"; status["Completo"] = f"Ocupado - Prof. {prof}"
    return status

# --- 3. BARRA LATERAL ---
with st.sidebar:
    st.title("📌 Sistema CTI")
    pagina = st.radio("Navegação:", ["📅 Consulta de Agenda", "🔐 Administração"])
    if pagina == "🔐 Administração":
        senha = st.text_input("Senha Admin:", type="password")
    else: senha = ""

# --- 4. CONTEÚDO PRINCIPAL ---
if pagina == "📅 Consulta de Agenda":
    st.title("📋 Agenda de Laboratórios")
    df_raw = carregar_dados()
    
    col_f1, col_f2 = st.columns(2)
    with col_f1: f_labs = st.multiselect("Filtrar Lab", LABS, default=LABS)
    with col_f2: v_hist = st.checkbox("Ver agendamentos passados")

    if not df_raw.empty:
        df_raw['Data'] = pd.to_datetime(df_raw['Data'], errors='coerce')
        hoje = datetime.now().date()
        df_view = df_raw.copy() if v_hist else df_raw[df_raw['Data'].dt.date >= hoje].copy()
        df_view = df_view[df_view['Laboratorio'].isin(f_labs)].sort_values(by="Data")

        if not df_view.empty:
            df_view['Mes_Ano'] = df_view['Data'].dt.strftime('%B %Y')
            df_view['Semana'] = df_view['Data'].dt.isocalendar().week

            for m_en in df_view['Mes_Ano'].unique():
                m_pt = m_en
                for en, pt in MESES_PT.items(): m_pt = m_pt.replace(en, pt)
                st.markdown(f"## 📅 {m_pt}")
                
                df_mes = df_view[df_view['Mes_Ano'] == m_en]
                
                for sem_num in sorted(df_mes['Semana'].unique()):
                    df_semana = df_mes[df_mes['Semana'] == sem_num]
                    inicio_sem = df_semana['Data'].min().strftime('%d/%m')
                    fim_sem = df_semana['Data'].max().strftime('%d/%m')
                    
                    # APLICANDO A TARJA COLORIDA
                    st.markdown(f'<div class="semana-header">Semana {sem_num} ({inicio_sem} a {fim_sem})</div>', unsafe_allow_html=True)
                    
                    for d_dt in sorted(df_semana['Data'].unique()):
                        df_dia = df_semana[df_semana['Data'] == d_dt]
                        d_s = pd.to_datetime(d_dt).strftime('%d/%m/%Y')
                        s_pt = DIAS_PT.get(pd.to_datetime(d_dt).strftime('%A'))
                        
                        with st.expander(f"{d_s} ({s_pt})"):
                            st.table(df_dia[["Horario", "Laboratorio", "Professor"]].sort_values(by="Horario"))
        else: st.warning("Nenhum agendamento encontrado.")

elif pagina == "🔐 Administração":
    st.title("🔐 Painel Administrativo")
    if senha == SENHA_ADMIN:
        st.success("Acesso Liberado")
        prof_n = st.text_input("Professor")
        lab_n = st.selectbox("Laboratório", LABS)
        modo = st.selectbox("Modo", ["Recorrência", "Datas Avulsas"])
        
        st.markdown("---")
        datas_finais = []
        if modo == "Recorrência":
            ca, cb = st.columns(2)
            with ca:
                d_ini = st.date_input("Início", datetime.now().date())
                qtd = st.number_input("Total aulas", min_value=1, value=1)
                freq = st.selectbox("Frequência", ["Semanal", "Quinzenal"])
            with cb:
                extras = st.multiselect("Extras:", pd.date_range(start=datetime.now(), periods=90).date, format_func=lambda x: x.strftime('%d/%m/%Y'))
            for i in range(qtd): datas_finais.append(d_ini + timedelta(weeks=i * (2 if freq == "Quinzenal" else 1)))
            datas_finais.extend(extras)
        else:
            datas_finais = st.multiselect("Datas:", pd.date_range(start=datetime.now(), periods=120).date, format_func=lambda x: x.strftime('%d/%m/%Y'))
        
        datas_finais = sorted(list(set(datas_finais)))
        turno_n = st.radio("Turno", list(OPCOES_POR_TURNO.keys()), horizontal=True)
        horario_n = st.radio("Horário", OPCOES_POR_TURNO[turno_n], horizontal=True)

        if st.button("🚀 Gravar Agendamentos", use_container_width=True, type="primary"):
            if not prof_n or not datas_finais: st.warning("Preencha os campos.")
            else:
                df_at = carregar_dados()
                chave = "Completo" if "Completo" in horario_n else ("1º" if "1º" in horario_n else "2º")
                if any(analisar_disponibilidade(df_at, lab_n, d, turno_n)[chave] != "Livre" for d in datas_finais):
                    st.error("Conflito detectado!")
                else:
                    novos = [{"Professor": prof_n, "Laboratorio": lab_n, "Data": d.strftime('%Y-%m-%d'), "Turno": turno_n, "Horario": horario_n} for d in datas_finais]
                    conn.update(data=pd.concat([df_at, pd.DataFrame(novos)], ignore_index=True))
                    st.success("Salvo com sucesso!"); st.balloons()
    else: st.info("Digite a senha administrativa na barra lateral.")
