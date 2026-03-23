import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÕES E ESTILO ---
st.set_page_config(page_title="Sistema CTI", layout="wide", page_icon="📅")

# CSS: Customização das cores, tarjas e remoção da seta lateral
hide_elements_style = """
    <style>
    header[data-testid="stHeader"] { visibility: hidden; height: 0px; }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }
    footer {visibility: hidden;}
    .block-container { padding-top: 1rem !important; }
    
    /* ESTILO DA TARJA DA SEMANA */
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
    
    /* Estilo para dias sem agendamento */
    .dia-vazio {
        color: #888;
        font-style: italic;
        padding: 5px 0px;
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
    pagina = st.radio("Navegação:", ["📅 Consulta de Agenda", "🔐 Administração"])
    if pagina == "🔐 Administração":
        senha = st.text_input("Senha Admin:", type="password")
    else: senha = ""

# --- 4. CONTEÚDO PRINCIPAL ---
if pagina == "📅 Consulta de Agenda":
    st.title("📋 Agenda de Laboratórios")
    df_raw = carregar_dados()
    
    col_f1, col_f2 = st.columns(2)
    with col_f1: 
        f_labs = st.multiselect("Filtrar por Laboratório", LABS, default=LABS)
    with col_f2: 
        dias_a_frente = st.slider("Mostrar próximos quantos dias?", 7, 90, 30)

    # Gerar intervalo de datas completo (Hoje até X dias a frente)
    hoje = datetime.now().date()
    intervalo_datas = [hoje + timedelta(days=i) for i in range(dias_a_frente)]
    
    # Criar um DataFrame base com todas as datas para garantir que todas apareçam
    df_calendario = pd.DataFrame({'Data': intervalo_datas})
    df_calendario['Mes_Ano'] = pd.to_datetime(df_calendario['Data']).dt.strftime('%B %Y')
    df_calendario['Semana'] = pd.to_datetime(df_calendario['Data']).dt.isocalendar().week

    for m_en in df_calendario['Mes_Ano'].unique():
        m_pt = m_en
        for en, pt in MESES_PT.items(): m_pt = m_pt.replace(en, pt)
        st.markdown(f"## 📅 {m_pt}")
        
        df_mes = df_calendario[df_calendario['Mes_Ano'] == m_en]
        
        for sem_num in sorted(df_mes['Semana'].unique()):
            df_semana = df_mes[df_mes['Semana'] == sem_num]
            inicio_sem = df_semana['Data'].min().strftime('%d/%m')
            fim_sem = df_semana['Data'].max().strftime('%d/%m')
            
            st.markdown(f'<div class="semana-header">Semana {sem_num} ({inicio_sem} a {fim_sem})</div>', unsafe_allow_html=True)
            
            for d_dt in sorted(df_semana['Data'].unique()):
                d_s = d_dt.strftime('%d/%m/%Y')
                s_pt = DIAS_PT.get(d_dt.strftime('%A'))
                
                # Filtrar agendamentos reais para este dia e laboratórios selecionados
                agendamentos_dia = df_raw[(df_raw['Data'] == d_dt) & (df_raw['Laboratorio'].isin(f_labs))]
                
                with st.expander(f"{d_s} ({s_pt})"):
                    if not agendamentos_dia.empty:
                        st.table(agendamentos_dia[["Horario", "Laboratorio", "Professor"]].sort_values(by="Horario"))
                    else:
                        st.markdown('<p class="dia-vazio">Nenhum agendamento para esta data.</p>', unsafe_allow_html=True)

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
                # Lógica simplificada de gravação (mantendo a mesma das versões anteriores)
                df_at = carregar_dados()
                # (Aqui entraria a função analisar_disponibilidade se necessário)
                novos = [{"Professor": prof_n, "Laboratorio": lab_n, "Data": d.strftime('%Y-%m-%d'), "Turno": turno_n, "Horario": horario_n} for d in datas_finais]
                conn.update(data=pd.concat([df_at, pd.DataFrame(novos)], ignore_index=True))
                st.success("Salvo!"); st.balloons()
    else: st.info("Digite a senha na barra lateral.")
