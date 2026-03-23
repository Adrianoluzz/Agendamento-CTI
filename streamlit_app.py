import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURAÇÕES DE ENGENHARIA DO CTI ---
LABS = ["Automação", "Química", "Desenho", "Predial", "Hidráulica", 
        "Civil", "Maquete", "Eletrônica", "Física", "Mecânica"]

TURNOS_PADRAO = {
    "Matutino": "08:00 - 11:00",
    "Vespertino": "14:00 - 17:00",
    "Noturno": "19:00 - 22:00"
}

# Configuração da Interface
st.set_page_config(page_title="Gestão de Labs CTI", layout="wide")
st.title("📅 Sistema de Gestão de Laboratórios - CTI")

# --- CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        # Tenta ler os dados. Se a planilha estiver vazia ou link errado, cairá no except.
        data = conn.read(ttl=0)
        if data is None or data.empty:
            return pd.DataFrame(columns=["Professor", "Laboratorio", "Data", "Turno", "Horario", "Semanas"])
        return data
    except Exception as e:
        # Retorna estrutura vazia para não quebrar a interface do App
        return pd.DataFrame(columns=["Professor", "Laboratorio", "Data", "Turno", "Horario", "Semanas"])

# --- INTERFACE DE NAVEGAÇÃO ---
aba_reserva, aba_agenda = st.tabs(["🆕 Novo Agendamento", "📋 Visualizar Agenda"])

# --- ABA 1: RESERVA AUTOMÁTICA (RECORRENTE) ---
with aba_reserva:
    with st.form("form_agendamento"):
        st.subheader("Configurar Reserva Recorrente")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            prof = st.text_input("Nome do Professor")
            lab = st.selectbox("Selecionar Laboratório", LABS)
        with col2:
            data_ini = st.date_input("Data da Primeira Aula", datetime.now())
            turno = st.selectbox("Turno Padrão", list(TURNOS_PADRAO.keys()))
        with col3:
            horario_custom = st.text_input("Horário Específico", value=TURNOS_PADRAO[turno])
            qtd_semanas = st.number_input("Repetir por quantas semanas?", min_value=1, max_value=20, value=1)
        
        submit = st.form_submit_button("Gerar e Salvar no Banco de Dados")

    if submit:
        if not prof:
            st.error("Por favor, insira o nome do professor.")
        else:
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
            
            # Processo de Salvamento
            df_atual = carregar_dados()
            df_novo = pd.DataFrame(novos_dados)
            df_final = pd.concat([df_atual, df_novo], ignore_index=True)
            
            try:
                conn.update(data=df_final)
                st.success(f"✅ Sucesso! {qtd_semanas} agendamentos criados para o Lab {lab}.")
                st.balloons()
            except Exception as e:
                st.error(f"Erro ao salvar na planilha. Verifique se ela está como 'Editor'. Detalhe: {e}")

# --- ABA 2: VISUALIZAÇÃO POR DIA (AGENDA) ---
with aba_agenda:
    st.subheader("Consulta de Ocupação por Data")
    df_visualizacao = carregar_dados()
    
    # Filtro de Laboratórios para limpar a visão
    filtro_lab = st.multiselect("Filtrar Laboratórios na Visualização", LABS, default=LABS)
    
    if not df_visualizacao.empty:
        # Garantir que a coluna Data é tratada como data real
        df_visualizacao['Data'] = pd.to_datetime(df_visualizacao['Data'])
        
        # Ordenar datas únicas para criar os expansores
        datas_disponiveis = sorted(df_visualizacao['Data'].unique())
        
        for data_dt in datas_disponiveis:
            # Filtrar apenas o que o usuário quer ver (Labs selecionados)
            df_dia = df_visualizacao[
                (df_visualizacao['Data'] == data_dt) & 
                (df_visualizacao['Laboratorio'].isin(filtro_lab))
            ]
            
            if not df_dia.empty:
                # Criar um "card" expansível para cada dia
                label_dia = f"📅 {data_dt.strftime('%d/%m/%Y')} - {data_dt.strftime('%A')}"
                with st.expander(label_dia):
                    st.dataframe(
                        df_dia[["Horario", "Laboratorio", "Professor"]].sort_values(by="Horario"),
                        use_container_width=True,
                        hide_index=True
                    )
    else:
        st.info("Nenhum agendamento encontrado. Vá na aba 'Novo Agendamento' para começar.")
