import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÕES E ESTILO ---
st.set_page_config(page_title="Sistema CTI - Gestão de Labs", layout="wide", page_icon="📅")

# CSS para esconder elementos do Streamlit e personalizar as cores
hide_elements_style = """
    <style>
    header[data-testid="stHeader"] { visibility: hidden; height: 0px; }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }
    footer {visibility: hidden;}
    .block-container { padding-top: 1rem !important; }
    
    /* QUADRO DE HOJE EM EVIDÊNCIA - CORREÇÃO DE CONTRASTE */
    .hoje-container {
        background-color: #fff3cd;
        border: 2px solid #ffeeba;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 30px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        color: #212529 !important; /* Texto escuro para leitura no fundo amarelo */
    }
    
    .hoje-container b, .hoje-container p {
        color: #856404 !important; /* Tom marrom escuro para destaque */
    }
    
    /* CABEÇALHO DA SEMANA (AZUL CTI) */
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
    
    # --- SEÇÃO EM EVIDÊNCIA: HOJE ---
    st.markdown(f'### 📍 Hoje: {hoje.strftime("%d/%m/%Y")} ({DIAS_PT.get(hoje.strftime("%A"))})')
    reserva_hoje = df_raw[df_raw['Data'] == hoje]
    
    with st.container():
        st.markdown('<div class="hoje-container">', unsafe_allow_html=True)
        if not reserva_hoje.empty:
            st.markdown(f"<b>Status:</b> {len(reserva_hoje)} reserva(s) encontrada(s) para hoje.", unsafe_allow_html=True)
            st.table(reserva_hoje[["Horario", "Laboratorio", "Professor", "Disciplina"]].sort_values(by="Horario"))
        else:
            st.markdown("✅ <b>Todos os laboratórios estão disponíveis para hoje.</b>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    
    # --- CRONOGRAMA SEMESTRAL ---
    st.title(f"📋 Cronograma {nome_semestre}")
    f_labs = st.multiselect("Filtrar por Laboratório no cronograma:", LABS, default=LABS)

    dias_restantes = (fim_periodo - hoje).days + 1
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
                # Filtro da semana atual para o loop
                df_sem_atual = df_mes[df_mes['Semana_ID'] == sem_id]
                
                inicio_sem = df_sem_atual['Data'].min().strftime('%d/%m')
                fim_sem = df_sem_atual['Data'].max().strftime('%d/%m')
                num_semana = pd.to_datetime(df_sem_atual['Data'].min()).isocalendar()[1]
                
                st.markdown(f'<div class="semana-header">Semana {num_semana} ({inicio_sem} a {fim_sem})</div>', unsafe_allow_html=True)
                
                for d_dt in sorted(df_sem_atual['Data'].unique()):
                    d_s, s_pt = d_dt.strftime('%d/%m/%Y'), DIAS_PT.get(d_dt.strftime('%A'))
                    reserva_dia = df_raw[(df_raw['Data'] == d_dt) & (df_raw['Laboratorio'].isin(f_labs))]
                    
                    label_dia = f"{d_s} ({s_pt})"
                    if d_dt == hoje: label_dia += " (HOJE)"
                    
                    if not reserva_dia.empty:
                        with st.expander(f"🔵 {label_dia} - {len(reserva_dia)} reserva(s)"):
                            st.table(reserva_dia[["Horario", "Laboratorio", "Professor", "Disciplina"]].sort_values(by="Horario"))
                    else:
                        with st.expander(f"⚪ {label_dia} - Disponível"):
                            st.markdown('<p class="dia-vazio">Nenhum agendamento registrado.</p>', unsafe_allow_html=True)

elif pagina == "🔐 Administração":
    st.title("🔐 Painel Administrativo")
    if senha == SENHA_ADMIN:
        tab_add, tab_del = st.tabs(["➕ Novo Agendamento", "🗑️ Gerenciar/Excluir"])
        
        with tab_add:
            c1, c2 = st.columns(2)
            prof_n = c1.text_input("Nome do Professor")
            disc_n = c2.text_input("Nome da Disciplina")
            
            lab_n = st.selectbox("Laboratório", LABS)
            modo = st.selectbox("Modo", ["Recorrência Semanal", "Datas Específicas"])
            
            datas_finais = []
            if modo == "Recorrência Semanal":
                ca, cb = st.columns(2)
                d_ini = ca.date_input("Data Inicial", hoje, min_value=hoje, max_value=fim_periodo)
                qtd = cb.number_input("Número de Semanas", 1, 22, 1)
                for i in range(qtd):
                    d_calc = d_ini + timedelta(weeks=i)
                    if d_calc <= fim_periodo and d_calc.weekday() != 6:
                        datas_finais.append(d_calc)
            else:
                datas_finais = st.multiselect("Selecione as Datas:", pd.date_range(hoje, fim_periodo).date, format_func=lambda x: x.strftime('%d/%m/%Y'))

            turno_n = st.radio("Turno", list(OPCOES_POR_TURNO.keys()), horizontal=True)
            horario_n = st.radio("Horário", OPCOES_POR_TURNO[turno_n], horizontal=True)

            if st.button("🚀 Gravar Agendamentos", use_container_width=True, type="primary"):
                if not prof_n or not disc_n or not datas_finais:
                    st.warning("Preencha todos os campos obrigatórios.")
                else:
                    df_at = carregar_dados()
                    novos = pd.DataFrame([{"Professor": prof_n, "Disciplina": disc_n, "Laboratorio": lab_n, "Data": d, "Turno": turno_n, "Horario": horario_n} for d in datas_finais])
                    conn.update(data=pd.concat([df_at, novos], ignore_index=True))
                    st.success(f"✅ {len(datas_finais)} agendamentos realizados!"); st.rerun()

        with tab_del:
            st.subheader("🗑️ Gerenciar Agendamentos")
            df_del = carregar_dados()
            if not df_del.empty:
                f_p = st.selectbox("Filtrar por Professor para exclusão", ["Todos"] + list(df_del['Professor'].unique()))
                df_f = df_del if f_p == "Todos" else df_del[df_del['Professor'] == f_p]
                
                df_f['Selecionar'] = False
                edited_df = st.data_editor(df_f, hide_index=True, use_container_width=True)
                
                if st.button("Confirmar Exclusão Selecionada", type="secondary"):
                    indices_manter = edited_df[edited_df['Selecionar'] == False].index
                    df_final = df_del.loc[indices_manter].drop(columns=['Selecionar'], errors='ignore')
                    conn.update(data=df_final)
                    st.warning("Agendamentos removidos!"); st.rerun()
            else:
                st.info("Nenhuma reserva encontrada para gerenciar.")
    else:
        st.info("Digite a senha administrativa na barra lateral para acessar as ferramentas.")
