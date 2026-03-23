import streamlit as st
from library_gsheets_connection import GSheetsConnection # Tente esta se a anterior falhar
# OU MANTENHA A QUE FUNCIONA NO STREAMLIT ATUAL:
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# Configurações de Engenharia do CTI
LABS = ["Automação", "Química", "Desenho", "Predial", "Hidráulica", 
        "Civil", "Maquete", "Eletrônica", "Física", "Mecânica"]

TURNOS_PADRAO = {
    "Matutino": "08:00 - 11:00",
    "Vespertino": "14:00 - 17:00",
    "Noturno": "19:00 - 22:00"
}

# Configuração da Página
st.set_page_config(page_title="Gestão de Labs CTI", layout="wide")
st.title("📅 Sistema de Gestão de Laboratórios - CTI")

# Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Função para ler dados
def carregar_dados():
    return conn.read(ttl="0s") # ttl=0 força a atualização em tempo real

# --- INTERFACE DE NAVEGAÇÃO ---
aba_reserva, aba_agenda = st.tabs(["🆕 Novo Agendamento", "📋 Visualizar Agenda"])

# --- ABA 1: RESERVA AUTOMÁTICA ---
with aba_reserva:
    with st.form("form_agendamento"):
        st.subheader("Configurar Reserva Recorrente")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            prof = st.text_input("Nome do Professor")
            lab = st.selectbox("Laboratório", LABS)
        with col2:
            data_ini = st.date_input("Data de Início", datetime.now())
            turno = st.selectbox("Turno", list(TURNOS_PADRAO.keys()))
        with col3:
            horario_custom = st.text_input("Horário (Edite se necessário)", value=TURNOS_PADRAO[turno])
            qtd_semanas = st.number_input("Repetir por quantas semanas?", min_value=1, max_value=20, value=1)
        
        submit = st.form_submit_button("Gerar e Salvar Agenda")

    if submit:
        novos_dados = []
        for i in range(qtd_semanas):
            data_aula = data_ini + timedelta(weeks=i)
            novos_dados.append({
                "Professor": prof,
                "Laboratorio": lab,
                "Data": data_aula.strftime('%Y-%m-%d'),
                "Turno": turno,
                "Horario": horario_custom,
                "Semanas": i + 1
            })
        
        # Lógica para salvar: Lê o atual e anexa o novo
        df_atual = carregar_dados()
        df_novo = pd.DataFrame(novos_dados)
        df_final = pd.concat([df_atual, df_novo], ignore_index=True)
        
        conn.update(data=df_final)
        st.success(f"✅ Sucesso! {qtd_semanas} semanas agendadas para o Lab {lab}.")
        st.balloons()

# --- ABA 2: VISUALIZAÇÃO POR DIA ---
with aba_agenda:
    st.subheader("Consulta de Ocupação")
    df_visualizacao = carregar_dados()
    
    if not df_visualizacao.empty:
        # Filtros rápidos
        filtro_lab = st.multiselect("Filtrar Laboratórios", LABS, default=LABS)
        df_visualizacao['Data'] = pd.to_datetime(df_visualizacao['Data'])
        
        # Ordenar por data
        datas_disponiveis = sorted(df_visualizacao['Data'].unique())
        
        for data_dt in datas_disponiveis:
            data_str = data_dt.strftime('%Y-%m-%d')
            # Filtrar dados para o dia e labs selecionados
            df_dia = df_visualizacao[
                (df_visualizacao['Data'] == data_dt) & 
                (df_visualizacao['Laboratorio'].isin(filtro_lab))
            ]
            
            if not df_dia.empty:
                with st.expander(f"📅 {data_dt.strftime('%d/%m/%Y')} ({data_dt.strftime('%A')})"):
                    st.dataframe(
                        df_dia[["Horario", "Laboratorio", "Professor", "Turno"]],
                        use_container_width=True,
                        hide_index=True
                    )
    else:
        st.info("Nenhum agendamento encontrado na base de dados.")
