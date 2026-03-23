import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÕES E ESTILO ---
st.set_page_config(page_title="Sistema CTI - Gestão de Labs", layout="wide", page_icon="📅")

hide_elements_style = """
    <style>
    header[data-testid="stHeader"] { visibility: hidden; height: 0px; }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }
    footer {visibility: hidden;}
    .block-container { padding-top: 1rem !important; }
    
    .hoje-container {
        background-color: #fff3cd;
        border: 2px solid #ffeeba;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 30px;
        color: #212529 !important;
    }
    
    .semana-header {
        background-color: #004a99;
        color: white !important;
        padding: 8px 20px;
        border-radius: 8px;
        margin-top: 25px;
        margin-bottom: 10px;
        font-weight: bold;
    }
    
    .mes-titulo { color: #004a99; border-bottom: 2px solid #004a99; padding-bottom: 5px; margin-top: 40px; }
    </style>
"""
st.markdown(hide_elements_style, unsafe_allow_html=True)

# --- CONFIGURAÇÕES TÉCNICAS (SALA DE TOPOGRAFIA ADICIONADA) ---
LABS = sorted([
    "Automação", "Química", "Desenho", "Predial", "Hidráulica", 
    "Civil", "Maquete", "Eletrônica", "Física", "Mecânica", 
    "Equipamentos Topografia"
])

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
        colunas = ["Professor", "Disciplina", "Laboratorio", "Data", "Turno", "Horario"]
        if data is not None and not data.empty:
            if "Disciplina" not in data.columns: data["Disciplina"] = "-"
            data['Data'] = pd.to_datetime(data['Data'], errors='coerce').dt.date
            return data[colunas]
        return pd.DataFrame(columns=colunas)
    except:
        return pd.DataFrame(columns=["Professor", "Disciplina", "Laboratorio", "Data", "Turno", "Horario"])

# --- 3. LÓGICA DE SEMESTRE ---
hoje = datetime.now().date()
ano_atual = hoje.year
fim_periodo = datetime(ano_atual, 6, 30).date() if hoje <= datetime(ano_atual, 6, 30).date() else datetime(ano_atual, 12, 31).date()
nome_semestre = f"{ano_atual}.1" if hoje <= datetime(ano_atual, 6, 30).date() else f"{ano_atual}.2"

# --- 4. BARRA LATERAL ---
with st.sidebar:
    st.title("📌 Sistema CTI")
    st.success(f"📅 Semestre: {nome_semestre}")
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
            st.table(reserva_hoje[["Horario", "Laboratorio", "Professor", "Disciplina"]].sort_values(by="Horario"))
        else:
            st.markdown("✅ <b>Laboratórios disponíveis para hoje.</b>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    st.title(f"📋 Cronograma {nome_semestre}")
    f_labs = st.multiselect("Filtrar Laboratórios:", LABS, default=LABS)

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
                df_sem_atual = df_mes[df_mes['Semana_ID'] == sem_id]
                st.markdown(f'<div class="semana-header">Semana {pd.to_datetime(df_sem_atual["Data"].min()).isocalendar()[1]}</div>', unsafe_allow_html=True)
                for d_dt in sorted(df_sem_atual['Data'].unique()):
                    reserva_dia = df_raw[(df_raw['Data'] == d_dt) & (df_raw['Laboratorio'].isin(f_labs))]
                    label = f"{d_dt.strftime('%d/%m/%Y')} ({DIAS_PT.get(d_dt.strftime('%A'))})"
                    with st.expander(f"{'🔵' if not reserva_dia.empty else '⚪'} {label}"):
                        if not reserva_dia.empty: st.table(reserva_dia[["Horario", "Laboratorio", "Professor", "Disciplina"]].sort_values(by="Horario"))
                        else: st.write("Disponível.")

elif pagina == "🔐 Administração":
    st.title("🔐 Painel Administrativo")
    if senha == SENHA_ADMIN:
        tab_add, tab_del = st.tabs(["➕ Novo Agendamento", "🗑️ Gerenciar/Excluir"])
        
        with tab_add:
            df_db = carregar_dados()
            c1, c2 = st.columns(2)
            prof_n = c1.text_input("Professor")
            disc_n = c2.text_input("Disciplina")
            lab_n = st.selectbox("Laboratório", LABS)
            modo = st.selectbox("Modo", ["Recorrência Semanal", "Datas Específicas"])
            
            datas_finais = []
            if modo == "Recorrência Semanal":
                ca, cb = st.columns(2)
                d_ini = ca.date_input("Início", hoje, min_value=hoje, max_value=fim_periodo)
                qtd = cb.number_input("Semanas", 1, 22, 1)
                datas_finais = [d_ini + timedelta(weeks=i) for i in range(qtd) if (d_ini + timedelta(weeks=i)) <= fim_periodo and (d_ini + timedelta(weeks=i)).weekday() != 6]
            else:
                datas_finais = st.multiselect("Datas:", pd.date_range(hoje, fim_periodo).date, format_func=lambda x: x.strftime('%d/%m/%Y'))

            turno_n = st.radio("Turno", list(OPCOES_POR_TURNO.keys()), horizontal=True)
            horario_n = st.radio("Horário", OPCOES_POR_TURNO[turno_n], horizontal=True)

            if st.button("🚀 Gravar Agendamentos", use_container_width=True, type="primary"):
                if not prof_n or not disc_n or not datas_finais:
                    st.warning("Preencha todos os campos.")
                else:
                    conflitos = []
                    for data_alvo in datas_finais:
                        check = df_db[(df_db['Laboratorio'] == lab_n) & 
                                      (df_db['Data'] == data_alvo) & 
                                      (df_db['Horario'] == horario_n)]
                        if not check.empty:
                            conflitos.append(f"{data_alvo.strftime('%d/%m')} ({check['Professor'].iloc[0]})")
                    
                    if conflitos:
                        st.error(f"❌ CONFLITO! O {lab_n} já está ocupado em: {', '.join(conflitos)}. Nada foi gravado.")
                    else:
                        novos = pd.DataFrame([{"Professor": prof_n, "Disciplina": disc_n, "Laboratorio": lab_n, "Data": d, "Turno": turno_n, "Horario": horario_n} for d in datas_finais])
                        conn.update(data=pd.concat([df_db, novos], ignore_index=True))
                        st.success(f"✅ Agendamentos realizados!"); st.rerun()

        with tab_del:
            df_del = carregar_dados()
            if not df_del.empty:
                f_p = st.selectbox("Filtrar Professor", ["Todos"] + list(df_del['Professor'].unique()))
                df_f = df_del if f_p == "Todos" else df_del[df_del['Professor'] == f_p]
                df_f['Selecionar'] = False
                edited = st.data_editor(df_f, hide_index=True, use_container_width=True)
                if st.button("Confirmar Exclusão"):
                    indices = edited[edited['Selecionar'] == False].index
                    conn.update(data=df_del.loc[indices].drop(columns=['Selecionar'], errors='ignore'))
                    st.warning("Removido!"); st.rerun()
    else:
        st.info("Insira a senha.")
