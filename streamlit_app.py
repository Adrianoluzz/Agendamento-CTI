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

# --- 2. CONEXÃO E DADOS ---
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

# --- 3. LÓGICA DE SEMESTRE ---
hoje = datetime.now().date()
ano_atual = hoje.year

# Define o fim do semestre atual
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
    if pagina == "🔐 Administração":
        senha = st.text_input("Senha Admin:", type="password")
    else: senha = ""

# --- 5. CONTEÚDO PRINCIPAL ---
if pagina == "📅 Consulta de Agenda":
    st.title(f"📋 Agenda de Laboratórios - Semestre {nome_semestre}")
    df_raw = carregar_dados()
    
    f_labs = st.multiselect("Filtrar por Laboratório", LABS, default=LABS)

    # Gera o intervalo exato do dia atual até o último dia do semestre
    dias_restantes = (fim_periodo - hoje).days + 1
    
    intervalo_datas = []
    for i in range(dias_restantes):
        d = hoje + timedelta(days=i)
        if d.weekday() != 6:  # Pula Domingos
            intervalo_datas.append(d)
    
    if not intervalo_datas:
        st.info("O semestre atual encerrou. Aguarde o início do próximo período.")
    else:
        df_cal = pd.DataFrame({'Data': intervalo_datas})
        df_cal['Mes_Ano'] = pd.to_datetime(df_cal['Data']).dt.strftime('%B %Y')
        df_cal['Semana_ID'] = pd.to_datetime(df_cal['Data']).dt.strftime('%Y-%U') 

        for m_en in df_cal['Mes_Ano'].unique():
            m_pt = m_en
            for en, pt in MESES_PT.items(): m_pt = m_pt.replace(en, pt)
            st.markdown(f'<h2 class="mes-titulo">📅 {m_pt}</h2>', unsafe_allow_html=True)
            
            df_mes = df_cal[df_cal['Mes_Ano'] == m_en]
            
            for sem_id in df_mes['Semana_ID'].unique():
                df_sem = df_mes[df_sem['Semana_ID'] == sem_id]
                inicio_sem = df_sem['Data'].min().strftime('%d/%m')
                fim_sem = df_sem['Data'].max().strftime('%d/%m')
                num_semana = pd.to_datetime(df_sem['Data'].min()).isocalendar()[1]
                
                st.markdown(f'<div class="semana-header">Semana {num_semana} ({inicio_sem} a {fim_sem})</div>', unsafe_allow_html=True)
                
                for d_dt in sorted(df_sem['Data'].unique()):
                    d_s = d_dt.strftime('%d/%m/%Y')
                    s_pt = DIAS_PT.get(d_dt.strftime('%A'))
                    reserva_dia = df_raw[(df_raw['Data'] == d_dt) & (df_raw['Laboratorio'].isin(f_labs))]
                    
                    label_dia = f"{d_s} ({s_pt})"
                    if not reserva_dia.empty:
                        with st.expander(f"🔵 {label_dia} - {len(reserva_dia)} reserva(s)"):
                            st.table(reserva_dia[["Horario", "Laboratorio", "Professor"]].sort_values(by="Horario"))
                    else:
                        with st.expander(f"⚪ {label_dia} - Disponível"):
                            st.markdown('<p class="dia-vazio">Nenhum agendamento registrado.</p>', unsafe_allow_html=True)

elif pagina == "🔐 Administração":
    st.title("🔐 Painel Administrativo")
    if senha == SENHA_ADMIN:
        st.success("Acesso Liberado")
        prof_n = st.text_input("Professor")
        lab_n = st.selectbox("Laboratório", LABS)
        modo = st.selectbox("Modo", ["Recorrência Semestral", "Datas Específicas"])
        
        st.markdown("---")
        datas_finais = []
        
        # Limita o calendário de escolha ao fim do semestre atual para evitar erros
        max_data_pick = fim_periodo
        
        if modo == "Recorrência Semestral":
            ca, cb = st.columns(2)
            with ca:
                d_ini = st.date_input("Início", hoje, min_value=hoje, max_value=max_data_pick)
                # Calcula quantas semanas faltam para o fim do semestre
                semanas_restantes = max(1, (max_data_pick - d_ini).days // 7)
                qtd = st.number_input("Quantidade de semanas", min_value=1, max_value=semanas_restantes + 1, value=semanas_restantes)
            with cb:
                freq = st.selectbox("Frequência", ["Semanal", "Quinzenal"])
                extras = st.multiselect("Datas Extras:", pd.date_range(start=hoje, end=max_data_pick).date, format_func=lambda x: x.strftime('%d/%m/%Y'))
            
            pulo = 2 if freq == "Quinzenal" else 1
            for i in range(qtd):
                d_calc = d_ini + timedelta(weeks=i * pulo)
                if d_calc <= max_data_pick and d_calc.weekday() != 6:
                    datas_finais.append(d_calc)
            datas_finais.extend(extras)
        else:
            datas_finais = st.multiselect("Selecione os dias:", pd.date_range(start=hoje, end=max_data_pick).date, format_func=lambda x: x.strftime('%d/%m/%Y'))
        
        datas_finais = sorted(list(set(datas_finais)))
        turno_n = st.radio("Turno", list(OPCOES_POR_TURNO.keys()), horizontal=True)
        horario_n = st.radio("Horário", OPCOES_POR_TURNO[turno_n], horizontal=True)

        if st.button("🚀 Gravar Agendamentos", use_container_width=True, type="primary"):
            if not prof_n or not datas_finais: st.warning("Preencha os campos obrigatórios.")
            else:
                df_at = carregar_dados()
                novos = [{"Professor": prof_n, "Laboratorio": lab_n, "Data": d.strftime('%Y-%m-%d'), "Turno": turno_n, "Horario": horario_n} for d in datas_finais]
                conn.update(data=pd.concat([df_at, pd.DataFrame(novos)], ignore_index=True))
                st.success(f"✅ Agendamentos para o semestre {nome_semestre} gravados!"); st.balloons()
    else: st.info("Insira a senha na barra lateral.")
