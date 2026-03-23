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
    
    /* QUADRO DE HOJE EM EVIDÊNCIA */
    .hoje-container {
        background-color: #fff3cd;
        border: 2px solid #ffeeba;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 30px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    
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
    
    .dia-vazio { color: #888; font-style: italic; padding: 5px 0px; }
    .mes-titulo { color: #004a99; border-bottom: 2px solid #004a99; padding-bottom: 5px; margin-top: 40px; }
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

# --- 2. CONEXÃO E DADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        data = conn.read(ttl=0)
        if data is not None and not data.empty:
            data['Data'] = pd.to_datetime(data['Data'], errors='coerce').dt.date
            return data
        return pd.DataFrame(columns=["Professor", "Laboratorio", "Data", "Turno", "Horario"])
    except:
        return pd.DataFrame(columns=["Professor", "Laboratorio", "Data", "Turno", "Horario"])

# --- 3. LÓGICA DE SEMESTRE ---
hoje = datetime.now().date()
ano_atual = hoje.year

if hoje <= datetime(ano_atual, 6, 30).date():
    fim_periodo = datetime(ano_atual, 6, 30).date()
    nome_semestre = f"{ano_atual}.1"
else:
    fim_periodo = datetime(ano_atual, 12, 31).date()
    nome_semestre = f"{ano_atual}.2"

# --- 4. BARRA LATERAL ---
with st.sidebar:
    st.title("📌 Sistema CTI")
    st.success(f"📅 Semestre Ativo: {nome_semestre}")
    pagina = st.radio("Navegação:", ["📅 Consulta de Agenda", "🔐 Administração"])
    senha = st.text_input("Senha Admin:", type="password") if pagina == "🔐 Administração" else ""

# --- 5. CONTEÚDO PRINCIPAL ---
if pagina == "📅 Consulta de Agenda":
    df_raw = carregar_dados()
    
    # --- SEÇÃO EM EVIDÊNCIA: HOJE ---
    st.markdown(f'### 📍 Hoje: {hoje.strftime("%d/%m/%Y")} ({DIAS_PT.get(hoje.strftime("%A"))})')
    
    reserva_hoje = df_raw[df_raw['Data'] == hoje]
    
    with st.container():
        st.markdown('<div class="hoje-container">', unsafe_allow_html=True)
        if not reserva_hoje.empty:
            st.info(f"Existem {len(reserva_hoje)} agendamentos para hoje.")
            st.table(reserva_hoje[["Horario", "Laboratorio", "Professor"]].sort_values(by="Horario"))
        else:
            st.write("✅ Todos os laboratórios estão **disponíveis** para hoje (até o momento).")
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    
    # --- FILTROS E CALENDÁRIO SEMESTRAL ---
    st.title(f"📋 Cronograma {nome_semestre}")
    f_labs = st.multiselect("Filtrar por Laboratório no histórico abaixo:", LABS, default=LABS)

    dias_restantes = (fim_periodo - hoje).days + 1
    # Começa de amanhã para não repetir o "Hoje" que já está no topo (opcional, mas fica mais limpo)
    intervalo_datas = [hoje + timedelta(days=i) for i in range(dias_restantes) if (hoje + timedelta(days=i)).weekday() != 6]
    
    if intervalo_datas:
        df_cal = pd.DataFrame({'Data': intervalo_datas})
        df_cal['Mes_Ano'] = pd.to_datetime(df_cal['Data']).dt.strftime('%B %Y')
        df_cal['Semana_ID'] = pd.to_datetime(df_cal['Data']).dt.strftime('%Y-%U') 

        for m_en in df_cal['Mes_Ano'].unique():
            m_pt = m_en
            for en, pt in MESES_PT.items(): m_pt = m_pt.replace(en, pt)
            st.markdown(f'<h2 class="mes-titulo">📅 {m_pt}</h2>', unsafe_allow_html=True)
            
            df_mes = df_cal[df_cal['Mes_Ano'] == m_en]
            for sem_id in df_mes['Semana_ID'].unique():
                df_sem_atual = df_mes[df_mes['Semana_ID'] == sem_id]
                
                inicio_sem = df_sem_atual['Data'].min().strftime('%d/%m')
                fim_sem = df_sem_atual['Data'].max().strftime('%d/%m')
                num_semana = pd.to_datetime(df_sem_atual['Data'].min()).isocalendar()[1]
                
                st.markdown(f'<div class="semana-header">Semana {num_semana} ({inicio_sem} a {fim_sem})</div>', unsafe_allow_html=True)
                
                for d_dt in sorted(df_sem_atual['Data'].unique()):
                    d_s, s_pt = d_dt.strftime('%d/%m/%Y'), DIAS_PT.get(d_dt.strftime('%A'))
                    reserva_dia = df_raw[(df_raw['Data'] == d_dt) & (df_raw['Laboratorio'].isin(f_labs))]
                    
                    # Estilização diferente se for o dia de hoje dentro da lista (opcional)
                    label_extra = " (HOJE)" if d_dt == hoje else ""
                    
                    if not reserva_dia.empty:
                        with st.expander(f"🔵 {d_s} ({s_pt}){label_extra} - {len(reserva_dia)} reserva(s)"):
                            st.table(reserva_dia[["Horario", "Laboratorio", "Professor"]].sort_values(by="Horario"))
                    else:
                        with st.expander(f"⚪ {d_s} ({s_pt}){label_extra} - Disponível"):
                            st.markdown('<p class="dia-vazio">Nenhum agendamento registrado.</p>', unsafe_allow_html=True)

elif pagina == "🔐 Administração":
    # (Mantém a mesma lógica de administração anterior com Novo Agendamento e Excluir)
    st.title("🔐 Painel Administrativo")
    if senha == SENHA_ADMIN:
        tab_add, tab_del = st.tabs(["➕ Novo Agendamento", "🗑️ Gerenciar/Excluir"])
        # ... (resto do código de administração permanece igual)
