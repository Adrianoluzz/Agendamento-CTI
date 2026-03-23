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
    
    /* QUADRO DE HOJE EM EVIDÊNCIA - AJUSTE DE CONTRASTE */
    .hoje-container {
        background-color: #fff3cd;
        border: 2px solid #ffeeba;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 30px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        color: #212529 !important; /* Cor de texto escura para leitura clara */
    }
    
    .hoje-container h3, .hoje-container p, .hoje-container b {
        color: #856404 !important; /* Tom de marrom escuro para títulos dentro do amarelo */
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

# --- (O restante das configurações técnicas permanece o mesmo) ---
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
        colunas_esperadas = ["Professor", "Disciplina", "Laboratorio", "Data", "Turno", "Horario"]
        if data is not None and not data.empty:
            if "Disciplina" not in data.columns:
                data["Disciplina"] = "-"
            data['Data'] = pd.to_datetime(data['Data'], errors='coerce').dt.date
            return data[colunas_esperadas]
        return pd.DataFrame(columns=colunas_esperadas)
    except:
        return pd.DataFrame(columns=["Professor", "Disciplina", "Laboratorio", "Data", "Turno", "Horario"])

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
    
    st.markdown(f'### 📍 Hoje: {hoje.strftime("%d/%m/%Y")} ({DIAS_PT.get(hoje.strftime("%A"))})')
    reserva_hoje = df_raw[df_raw['Data'] == hoje]
    
    with st.container():
        st.markdown('<div class="hoje-container">', unsafe_allow_html=True)
        if not reserva_hoje.empty:
            st.markdown(f"<b>Atenção:</b> Existem {len(reserva_hoje)} laboratórios ocupados agora.", unsafe_allow_html=True)
            # Tabela forçada com estilo para visibilidade
            st.table(reserva_hoje[["Horario", "Laboratorio", "Professor", "Disciplina"]].sort_values(by="Horario"))
        else:
            st.markdown("✅ <b>Todos os laboratórios estão disponíveis para hoje.</b>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    # ... (O restante do código de Cronograma e Administração permanece igual)
