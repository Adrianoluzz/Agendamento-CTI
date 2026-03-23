import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURAÇÕES DO CTI ---
LABS = ["Automação", "Química", "Desenho", "Predial", "Hidráulica", 
        "Civil", "Maquete", "Eletrônica", "Física", "Mecânica"]

# Dicionário de horários sugeridos por turno
OPCOES_POR_TURNO = {
    "Matutino": ["08:00 - 11:00", "07:30 - 11:30", "08:00 - 12:00"],
    "Vespertino": ["14:00 - 17:00", "13:30 - 17:30", "13:00 - 17:00"],
    "Noturno": ["19:00 - 22:00", "18:30 - 22:30", "19:00 - 21:00"]
}

# Configuração da Interface
st.set_page_config(page_title="Gestão de Labs CTI", layout="wide", page_icon="📅")
st.title("📅 Sistema de Gestão de Laboratórios - CTI")

# --- CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        data = conn.read(ttl=0)
        if data is None or data.empty:
            return pd.DataFrame(columns=["Professor", "Laboratorio", "Data", "Turno", "Horario", "Semanas"])
        return data
    except Exception:
        return pd.DataFrame(columns=["Professor", "Laboratorio", "Data", "Turno", "Horario", "Semanas"])

# --- NAVEGAÇÃO ---
aba_reserva, aba_agenda = st.tabs(["🆕 Novo Agendamento", "📋 Visualizar Agenda"])

# --- ABA 1: NOVO AGENDAMENTO ---
with aba_reserva:
    with st.form("form_agendamento"):
        st.subheader("Configurar Reserva")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            prof = st.text_input("Nome do Professor")
            lab = st.selectbox("Selecionar Laboratório", LABS)
        
        with col2:
            data_ini = st.date_input("Data de Início", datetime.now())
            turno_sel = st.selectbox("Turno", list(OPCOES_POR_TURNO.keys()))
        
        with col3:
            # Lista de horários baseada no turno + opção de personalizar
            lista_horarios = OPCOES_POR_TURNO[turno_sel] + ["Outro (Digitar)"]
            horario_sel = st.selectbox("Horário", lista_horarios)
            
            # Se escolher 'Outro', aparece campo para digitar
            if horario_sel == "Outro (Digitar)":
                horario_final = st.text_input("Digite o horário (ex: 09:00 - 11:00)")
            else:
                horario_final = horario_sel
                
            qtd_semanas = st.number_input("Repetir por quantas semanas?", min_value=1, max_value=20, value=1)
        
        submit = st.form_submit_button("Salvar Agendamento")

    if submit:
        if not prof or not horario_final:
            st.error("Por favor, preencha o nome do professor e o horário.")
        else:
            novos_dados = []
            for i in range(qtd_semanas):
                data_aula = data_ini + timedelta(weeks=i)
                novos_dados.append({
                    "Professor": prof,
                    "Laboratorio": lab,
                    "Data": data_aula.strftime('%Y-%m-%d'),
                    "Turno": turno_sel,
                    "Horario": horario_final,
                    "Semanas": i + 1
                })
            
            df_atual = carregar_dados()
            df_novo = pd.DataFrame(novos_dados)
            df_final = pd.concat([df_atual, df_novo], ignore_index=True)
            
            try:
                conn.update(data=df_final)
                st.success(f"✅ Sucesso! {qtd_semanas} reserva(s) salva(s) na planilha.")
                st.balloons()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

# --- ABA 2: VISUALIZAÇÃO ---
with aba_agenda:
    st.subheader("Ocupação dos Laboratórios")
    df_raw = carregar_dados()
    
    filtro_lab = st.multiselect("Filtrar por Laboratório", LABS, default=LABS)
    
    if not df_raw.empty:
        df_raw['Data'] = pd.to_datetime(df_raw['Data'], errors='coerce')
        df_view = df_raw.dropna(subset=['Data']).copy()
        
        datas_disponiveis = sorted(df_view['Data'].unique())
        
        if not datas_disponiveis:
            st.warning("Nenhum agendamento válido encontrado.")
        
        for data_dt in datas_disponiveis:
            df_dia = df_view[
                (df_view['Data'] == data_dt) & 
                (df_view['Laboratorio'].isin(filtro_lab))
            ]
            
            if not df_dia.empty:
                label_dia = f"📅 {data_dt.strftime('%d/%m/%Y')} - {data_dt.strftime('%A')}"
                with st.expander(label_dia):
                    st.table(df_dia[["Horario", "Laboratorio", "Professor"]].sort_values(by="Horario"))
    else:
        st.info("A agenda está vazia.")
