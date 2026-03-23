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
    st.title(f"📋 Agenda de Laboratórios - {nome_semestre}")
    df_raw = carregar_dados()
    f_labs = st.multiselect("Filtrar por Laboratório", LABS, default=LABS)

    dias_restantes = (fim_periodo - hoje).days + 1
    intervalo_datas = [hoje + timedelta(days=i) for i in range(dias_restantes) if (hoje + timedelta(days=i)).weekday() != 6]
    
    if not intervalo_datas:
        st.info("Semestre encerrado.")
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
                # --- CORREÇÃO DO ERRO AQUI ---
                df_sem_atual = df_mes[df_mes['Semana_ID'] == sem_id]
                
                inicio_sem = df_sem_atual['Data'].min().strftime('%d/%m')
                fim_sem = df_sem_atual['Data'].max().strftime('%d/%m')
                num_semana = pd.to_datetime(df_sem_atual['Data'].min()).isocalendar()[1]
                
                st.markdown(f'<div class="semana-header">Semana {num_semana} ({inicio_sem} a {fim_sem})</div>', unsafe_allow_html=True)
                
                for d_dt in sorted(df_sem_atual['Data'].unique()):
                    d_s, s_pt = d_dt.strftime('%d/%m/%Y'), DIAS_PT.get(d_dt.strftime('%A'))
                    reserva_dia = df_raw[(df_raw['Data'] == d_dt) & (df_raw['Laboratorio'].isin(f_labs))]
                    
                    if not reserva_dia.empty:
                        with st.expander(f"🔵 {d_s} ({s_pt}) - {len(reserva_dia)} reserva(s)"):
                            st.table(reserva_dia[["Horario", "Laboratorio", "Professor"]].sort_values(by="Horario"))
                    else:
                        with st.expander(f"⚪ {d_s} ({s_pt}) - Disponível"):
                            st.markdown('<p class="dia-vazio">Nenhum agendamento registrado.</p>', unsafe_allow_html=True)

elif pagina == "🔐 Administração":
    st.title("🔐 Painel Administrativo")
    if senha == SENHA_ADMIN:
        tab_add, tab_del = st.tabs(["➕ Novo Agendamento", "🗑️ Gerenciar/Excluir"])
        
        with tab_add:
            prof_n = st.text_input("Professor")
            lab_n = st.selectbox("Laboratório", LABS)
            modo = st.selectbox("Modo", ["Recorrência", "Datas Específicas"])
            
            datas_finais = []
            if modo == "Recorrência":
                c1, c2 = st.columns(2)
                d_ini = c1.date_input("Início", hoje, min_value=hoje, max_value=fim_periodo)
                qtd = c2.number_input("Semanas", 1, 20, 1)
                for i in range(qtd):
                    d_c = d_ini + timedelta(weeks=i)
                    if d_c <= fim_periodo and d_c.weekday() != 6: datas_finais.append(d_c)
            else:
                datas_finais = st.multiselect("Datas:", pd.date_range(hoje, fim_periodo).date, format_func=lambda x: x.strftime('%d/%m/%Y'))

            turno_n = st.radio("Turno", list(OPCOES_POR_TURNO.keys()), horizontal=True)
            horario_n = st.radio("Horário", OPCOES_POR_TURNO[turno_n], horizontal=True)

            if st.button("🚀 Gravar", use_container_width=True):
                df_at = carregar_dados()
                novos = pd.DataFrame([{"Professor": prof_n, "Laboratorio": lab_n, "Data": d, "Turno": turno_n, "Horario": horario_n} for d in datas_finais])
                conn.update(data=pd.concat([df_at, novos], ignore_index=True))
                st.success("Salvo!"); st.rerun()

        with tab_del:
            st.subheader("Excluir Agendamentos")
            df_del = carregar_dados()
            if not df_del.empty:
                # Filtro para facilitar a busca do que deletar
                f_prof = st.selectbox("Filtrar por Professor para deletar", ["Todos"] + list(df_del['Professor'].unique()))
                df_filtrado_del = df_del if f_prof == "Todos" else df_del[df_del['Professor'] == f_prof]
                
                # Exibe a tabela com opção de seleção
                df_filtrado_del['Selecionar'] = False
                edited_df = st.data_editor(df_filtrado_del, hide_index=True, use_container_width=True)
                
                if st.button("🗑️ Excluir Selecionados", type="secondary"):
                    indices_para_manter = edited_df[edited_df['Selecionar'] == False].index
                    # Reatribui o DataFrame original apenas com os itens não selecionados
                    df_final = df_del.loc[indices_para_manter].drop(columns=['Selecionar'], errors='ignore')
                    conn.update(data=df_final)
                    st.warning("Agendamentos removidos!"); st.rerun()
            else:
                st.info("Nenhum dado para excluir.")
    else:
        st.info("Aguardando senha...")
