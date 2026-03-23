import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

# Configuração dos Labs do CTI
LABS = ["Automação", "Química", "Desenho", "Predial", "Hidráulica", 
        "Civil", "Maquete", "Eletrônica", "Física", "Mecânica"]

st.title("🚀 Sistema de Agendamento Automático - CTI")

# --- FORMULÁRIO DE AGENDAMENTO ---
with st.expander("Novo Agendamento Recorrente", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        prof = st.text_input("Nome do Professor")
        lab = st.selectbox("Selecionar Laboratório", LABS)
        data_inicio = st.date_input("Data da Primeira Aula", datetime.now())
    
    with col2:
        turno = st.radio("Turno Padrão", ["Matutino", "Vespertino", "Noturno"])
        h_inicio = st.time_input("Horário de Início", datetime.strptime("19:00", "%H:%M"))
        h_fim = st.time_input("Horário de Término", datetime.strptime("22:30", "%H:%M"))

    semanas = st.number_input("Repetir por quantas semanas?", min_value=1, max_value=20, value=1)
    
    if st.button("Gerar Agenda Automática"):
        agendamentos = []
        for i in range(semanas):
            nova_data = data_inicio + timedelta(weeks=i)
            # Aqui adicionamos a lógica de pular feriados/provas se necessário
            agendamentos.append({
                "Professor": prof,
                "Lab": lab,
                "Data": nova_data,
                "Hora": f"{h_inicio} - {h_fim}"
            })
        
        st.write("### Prévia do Cronograma:")
        st.table(pd.DataFrame(agendamentos))
        
        if st.button("Confirmar e Salvar no Google Sheets"):
            # Função para disparar os dados para a planilha
            st.success("Agenda salva com sucesso!")

# --- VISUALIZAÇÃO DE CONFLITOS ---
st.divider()
st.subheader("🔍 Mapa de Ocupação Real")
# Aqui o Streamlit filtraria a planilha e mostraria quem está em qual lab hoje.
