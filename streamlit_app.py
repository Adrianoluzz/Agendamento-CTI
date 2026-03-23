import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÕES DO CTI ---
LABS = ["Automação", "Química", "Desenho", "Predial", "Hidráulica", 
        "Civil", "Maquete", "Eletrônica", "Física", "Mecânica"]

OPCOES_POR_TURNO = {
    "Matutino": ["08:00 - 11:00 (Completo)", "08:00 - 09:30 (1º Horário)", "09:45 - 11:00 (2º Horário)"],
    "Vespertino": ["14:00 - 17:00 (Completo)"],
    "Noturno": ["19:00 - 22:00 (Completo)", "19:00 - 20:30 (1º Horário)", "20:45 - 22:00 (2º Horário)"]
}

st.set_page_config(page_title="Gestão de Labs CTI", layout="wide", page_icon="📅")
st.title("📅 Gestão de Laboratórios - CTI")

# --- 2. CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        data = conn.read(ttl=0)
        return data if data is not None else pd.DataFrame(columns=["Professor", "Laboratorio", "Data", "Turno", "Horario", "Semanas"])
    except Exception:
        return pd.DataFrame(columns=["Professor", "Laboratorio", "Data", "Turno", "Horario", "Semanas"])

# --- 3. LÓGICA DE ANÁLISE DE DISPONIBILIDADE ---
def analisar_disponibilidade(df, lab, data, turno):
    df_temp = df.copy()
    df_temp['Data'] = pd.to_datetime(df_temp['Data'], errors='coerce').dt.date
    
    reservas = df_temp[(df_temp['Laboratorio'] == lab) & 
                       (df_temp['Data'] == data) & 
                       (df_temp['Turno'] == turno)]
    
    # Dicionário para rastrear o que está livre ou quem ocupa
    status = {"1º": "Livre", "2º": "Livre", "Completo": "Livre"}
    
    for _, r in reservas.iterrows():
        h = r['Horario']
        prof = r['Professor']
        
        if "(1º Horário)" in h:
            status["1º"] = f"Agendamento (1 horario) indisponivel - Prof. {prof}"
            status["Completo"] = f"Agendamento (completo) indisponivel - Prof. {prof} (No 1º Horário)"
        elif "(2º Horário)" in h:
            status["2º"] = f"Agendamento (2 horario) indisponivel - Prof. {prof}"
            status["Completo"] = f"Agendamento (completo) indisponivel - Prof. {prof} (No 2º Horário)"
        elif "(Completo)" in h:
            status["1º"] = f"Agendamento (1 horario) indisponivel - Prof. {prof}"
            status["2º"] = f"Agendamento (2 horario) indisponivel - Prof. {prof}"
            status["Completo"] = f"Agendamento (completo) indisponivel - Prof. {prof}"
            
    return status

# --- 4. INTERFACE ---
aba_reserva, aba_agenda = st.tabs(["🆕 Novo Agendamento", "📋 Visualizar Agenda"])

with aba_reserva:
    st.subheader("Configurar Nova Reserva")
    col1, col2, col3 = st.columns([1, 1, 1.2])
    
    with col1:
        prof = st.text_input("Nome do Professor")
        lab = st.selectbox("Selecionar Laboratório", LABS)
        data_ini = st.date_input("Data de Início", datetime.now())

    with col2:
        turno_sel = st.radio("Selecione o Turno:", list(OPCOES_POR_TURNO.keys()))

    with col3:
        horario_sel = st.radio("Selecione o Horário:", OPCOES_POR_TURNO[turno_sel])
        qtd_semanas = st.number_input("Repetir por quantas semanas?", min_value=1, max_value=20, value=1)

    st.markdown("---")
    
    chave_busca = "Completo" if "Completo" in horario_sel else ("1º" if "1º" in horario_sel else "2º")

    # BOTÃO: VERIFICAR DISPONIBILIDADE
    if st.button("🔍 Verificar Disponibilidade", use_container_width=True):
        df_atual = carregar_dados()
        for i in range(qtd_semanas):
            d_alvo = data_ini + timedelta(weeks=i)
            status_dia = analisar_disponibilidade(df_atual, lab, d_alvo, turno_sel)
            
            if status_dia[chave_busca] == "Livre":
                st.success(f"✅ {d_alvo.strftime('%d/%m/%Y')}: Disponível")
            else:
                st.error(f"❌ {d_alvo.strftime('%d/%m/%Y')}: {status_dia[chave_busca]}")
                
                # INFORMAR SE O OUTRO HORÁRIO ESTÁ DISPONÍVEL (Caso tenha tentado Completo ou um específico)
                disponiveis = []
                if status_dia["1º"] == "Livre": disponiveis.append("1º Horário")
                if status_dia["2º"] == "Livre": disponiveis.append("2º Horário")
                
                if disponiveis:
                    st.info(f"ℹ️ Informação: O { ' e o '.join(disponiveis) } está disponível nesta data.")

    # BOTÃO: SALVAR
    if st.button("🚀 Confirmar e Salvar", use_container_width=True, type="primary"):
        if not prof:
            st.warning("⚠️ Digite o nome do professor.")
        else:
            df_atual = carregar_dados()
            pode_gravar = True
            for i in range(qtd_semanas):
                d_check = data_ini + timedelta(weeks=i)
                status = analisar_disponibilidade(df_atual, lab, d_check, turno_sel)
                if status[chave_busca] != "Livre":
                    pode_gravar = False
                    break
            
            if not pode_gravar:
                st.error("⚠️ Conflito detectado! Verifique a disponibilidade antes de salvar.")
            else:
                novos = []
                for i in range(qtd_semanas):
                    novos.append({
                        "Professor": prof, "Laboratorio": lab, 
                        "Data": (data_ini + timedelta(weeks=i)).strftime('%Y-%m-%d'),
                        "Turno": turno_sel, "Horario": horario_sel, "Semanas": i + 1
                    })
                df_final = pd.concat([df_atual, pd.DataFrame(novos)], ignore_index=True)
                try:
                    conn.update(data=df_final)
                    st.success("✅ Agendamento realizado!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

with aba_agenda:
    # Código de visualização
    df_raw = carregar_dados()
    filtro_lab = st.multiselect("Filtrar Laboratórios", LABS, default=LABS)
    if not df_raw.empty:
        df_raw['Data'] = pd.to_datetime(df_raw['Data'], errors='coerce')
        df_view = df_raw.dropna(subset=['Data']).copy()
        for data_dt in sorted(df_view['Data'].unique()):
            df_dia = df_view[(df_view['Data'] == data_dt) & (df_view['Laboratorio'].isin(filtro_lab))]
            if not df_dia.empty:
                with st.expander(f"📅 {data_dt.strftime('%d/%m/%Y')} - {data_dt.strftime('%A')}"):
                    st.table(df_dia[["Horario", "Laboratorio", "Professor"]].sort_values(by="Horario"))
    else:
        st.info("Agenda vazia.")
