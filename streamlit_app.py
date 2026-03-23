import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÕES E ESTILO ---
st.set_page_config(page_title="Sistema CTI - Semestral", layout="wide", page_icon="📅")

hide_elements_style = """
    <style>
    header[data-testid="stHeader"] { visibility: hidden; height: 0px; }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }
    footer {visibility: hidden;}
    .block-container { padding-top: 1rem !important; }
    
    /* TARJA DA SEMANA */
    .semana-header {
        background-color: #004a99;
        color: white !important;
        padding: 8px 20px;
        border-radius: 8px;
        margin-top: 25px;
        margin-bottom: 10px;
        font-weight: bold;
        font-size: 1.1rem;
    }
    
    .dia-vazio {
        color: #888;
        font-style: italic;
        padding: 5px 0px;
    }
    
    /* Destaque para o nome do Mês */
    .mes-titulo {
        color: #004a99;
        border-bottom: 2px solid #004a99;
        padding-bottom: 5px;
        margin-top: 40px;
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
        if data is not None:
            data['Data'] = pd.to_datetime(data['Data'], errors='coerce').dt.date
            return data
        return pd.DataFrame(columns=["Professor", "Laboratorio", "Data", "Turno", "Horario"])
    except:
        return pd.DataFrame(columns=["Professor", "Laboratorio", "Data", "Turno", "Horario"])

# --- 3. BARRA LATERAL ---
with st.sidebar:
    st.title("📌 Sistema CTI")
    st.info("Planejamento Semestral (5 meses)")
    pagina = st.radio("Navegação:", ["📅 Consulta de Agenda", "🔐 Administração"])
    if pagina == "🔐 Administração":
        senha = st.text_input("Senha Admin:", type="password")
    else: senha = ""

# --- 4. CONTEÚDO PRINCIPAL ---
if pagina == "📅 Consulta de Agenda":
    st.title("📋 Agenda de Laboratórios - Visão 5 Meses")
    df_raw = carregar_dados()
    
    f_labs = st.multiselect("Filtrar por Laboratório", LABS, default=LABS)

    # Lógica para 5 meses (aprox. 150 dias)
    hoje = datetime.now().date()
    # Calculamos o fim do período de 5 meses
    qtd_dias = 150 
    
    intervalo_datas = []
    for i in range(qtd_dias):
        d = hoje + timedelta(days=i)
        if d.weekday() != 6:  # Pula Domingos
            intervalo_datas.append(d)
    
    df_cal = pd.DataFrame({'Data': intervalo_datas})
    df_cal['Mes_Ano'] = pd.to_datetime(df_cal['Data']).dt.strftime('%B %Y')
    # Usamos uma combinação de Ano + Semana para o agrupamento não bugar na virada de ano
    df_cal['Semana_ID'] = pd.to_datetime(df_cal['Data']).dt.strftime('%Y-%U') 

    # Loop de Meses
    for m_en in df_cal['Mes_Ano'].unique():
        m_pt = m_en
        for en, pt in MESES_PT.items(): m_pt = m_pt.replace(en, pt)
        st.markdown(f'<h2 class="mes-titulo">📅 {m_pt}</h2>', unsafe_allow_html=True)
        
        df_mes = df_cal[df_cal['Mes_Ano'] == m_en]
        
        # Loop de Semanas dentro do Mês
        for sem_id in df_mes['Semana_ID'].unique():
            df_sem = df_mes[df_mes['Semana_ID'] == sem_id]
            
            # Formatação do cabeçalho da semana
            inicio_sem = df_sem['Data'].min().strftime('%d/%m')
            fim_sem = df_sem['Data'].max().strftime('%d/%m')
            num_semana = pd.to_datetime(df_sem['Data'].min()).isocalendar()[1]
            
            st.markdown(f'<div class="semana-header">Semana {num_semana} ({inicio_sem} a {fim_sem})</div>', unsafe_allow_html=True)
            
            # Mostrar os dias daquela semana
            for d_dt in sorted(df_sem['Data'].unique()):
                d_s = d_dt.strftime('%d/%m/%Y')
                s_pt = DIAS_PT.get(d_dt.strftime('%A'))
                
                reserva_dia = df_raw[(df_raw['Data'] == d_dt) & (df_raw['Laboratorio'].isin(f_labs))]
                
                # Expander para cada dia
                label_dia = f"{d_s} ({s_pt})"
                if not reserva_dia.empty:
                    with st.expander(f"🔵 {label_dia} - {len(reserva_dia)} reserva(s)"):
                        st.table(reserva_dia[["Horario", "Laboratorio", "Professor"]].sort_values(by="Horario"))
                else:
                    with st.expander(f"⚪ {label_dia} - Disponível"):
                        st.markdown('<p class="dia-vazio">Nenhum agendamento. Laboratórios liberados.</p>', unsafe_allow_html=True)

elif pagina == "🔐 Administração":
    st.title("🔐 Painel Administrativo")
    if senha == SENHA_ADMIN:
        st.success("Acesso Liberado")
        prof_n = st.text_input("Professor")
        lab_n = st.selectbox("Laboratório", LABS)
        modo = st.selectbox("Modo", ["Recorrência Semestral", "Datas Específicas"])
        
        st.markdown("---")
        datas_finais = []
        if modo == "Recorrência Semestral":
            ca, cb = st.columns(2)
            with ca:
                d_ini = st.date_input("Data de Início", datetime.now().date())
                qtd = st.number_input("Quantidade de semanas (ex: 20 para o semestre)", min_value=1, value=18)
            with cb:
                freq = st.selectbox("Frequência", ["Semanal", "Quinzenal"])
                extras = st.multiselect("Datas Extras (ex: Sábados letivos):", pd.date_range(start=datetime.now(), periods=180).date, format_func=lambda x: x.strftime('%d/%m/%Y'))
            
            pulo = 2 if freq == "Quinzenal" else 1
            for i in range(qtd):
                d_calc = d_ini + timedelta(weeks=i * pulo)
                if d_calc.weekday() != 6: datas_finais.append(d_calc)
            datas_finais.extend(extras)
        else:
            datas_finais = st.multiselect("Selecione os dias:", pd.date_range(start=datetime.now(), periods=180).date, format_func=lambda x: x.strftime('%d/%m/%Y'))
        
        datas_finais = sorted(list(set(datas_finais)))
        turno_n = st.radio("Turno", list(OPCOES_POR_TURNO.keys()), horizontal=True)
        horario_n = st.radio("Horário", OPCOES_POR_TURNO[turno_n], horizontal=True)

        if st.button("🚀 Gravar Agendamentos Semestrais", use_container_width=True, type="primary"):
            if not prof_n or not datas_finais: st.warning("Preencha o nome e selecione as datas.")
            else:
                df_at = carregar_dados()
                novos = [{"Professor": prof_n, "Laboratorio": lab_n, "Data": d.strftime('%Y-%m-%d'), "Turno": turno_n, "Horario": horario_n} for d in datas_finais]
                try:
                    conn.update(data=pd.concat([df_at, pd.DataFrame(novos)], ignore_index=True))
                    st.success(f"✅ {len(datas_finais)} datas agendadas com sucesso!"); st.balloons()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
    else: st.info("Insira a senha na barra lateral.")
