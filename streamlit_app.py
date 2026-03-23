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

# Dicionários de tradução para exibição organizada
MESES_PT = {
    'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março', 'April': 'Abril',
    'May': 'Maio', 'June': 'Junho', 'July': 'Julho', 'August': 'Agosto',
    'September': 'Setembro', 'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
}

DIAS_PT = {
    'Monday': 'Segunda-feira', 'Tuesday': 'Terça-feira', 'Wednesday': 'Quarta-feira', 
    'Thursday': 'Quinta-feira', 'Friday': 'Sexta-feira', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
}

st.set_page_config(page_title="Gestão de Labs CTI", layout="wide", page_icon="📅")
st.title("📅 Gestão de Laboratórios - CTI")

# --- 2. CONEXÃO COM O GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        data = conn.read(ttl=0)
        if data is None or data.empty:
            return pd.DataFrame(columns=["Professor", "Laboratorio", "Data", "Turno", "Horario", "Semanas"])
        return data
    except Exception:
        return pd.DataFrame(columns=["Professor", "Laboratorio", "Data", "Turno", "Horario", "Semanas"])

# --- 3. LÓGICA DE DISPONIBILIDADE E CONFLITOS ---
def analisar_disponibilidade(df, lab, data, turno):
    df_temp = df.copy()
    df_temp['Data'] = pd.to_datetime(df_temp['Data'], errors='coerce').dt.date
    
    reservas = df_temp[(df_temp['Laboratorio'] == lab) & 
                       (df_temp['Data'] == data) & 
                       (df_temp['Turno'] == turno)]
    
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

# --- ABA 1: FORMULÁRIO DE RESERVA ---
with aba_reserva:
    st.subheader("Configurar Nova Reserva")
    col1, col2, col3 = st.columns([1, 1, 1.2])
    
    with col1:
        prof = st.text_input("Nome do Professor")
        lab = st.selectbox("Selecionar Laboratório", LABS)
        data_ini = st.date_input("Data de Início", datetime.now())

    with col2:
        turno_sel = st.radio("Selecione o Turno:", list(OPCOES_POR_TURNO.keys()))
        quinzenal = st.checkbox("Agendamento Quinzenal (Semana sim / Semana não)")

    with col3:
        horario_sel = st.radio("Selecione o Horário:", OPCOES_POR_TURNO[turno_sel])
        qtd_repeticoes = st.number_input("Número de aulas (ocorrências):", min_value=1, max_value=20, value=1)

    st.markdown("---")
    chave_busca = "Completo" if "Completo" in horario_sel else ("1º" if "1º" in horario_sel else "2º")
    intervalo_semanas = 2 if quinzenal else 1

    # BOTÃO: VERIFICAR
    if st.button("🔍 Verificar Disponibilidade", use_container_width=True):
        df_atual = carregar_dados()
        for i in range(qtd_repeticoes):
            d_alvo = data_ini + timedelta(weeks=i * intervalo_semanas)
            status_dia = analisar_disponibilidade(df_atual, lab, d_alvo, turno_sel)
            
            if status_dia[chave_busca] == "Livre":
                st.success(f"✅ {d_alvo.strftime('%d/%m/%Y')}: Disponível")
            else:
                st.error(f"❌ {d_alvo.strftime('%d/%m/%Y')}: {status_dia[chave_busca]}")
                # Informar brechas
                disponiveis = [f"{k} Horário" for k, v in status_dia.items() if v == "Livre" and k != "Completo"]
                if disponiveis:
                    st.info(f"ℹ️ Informação: O { ' e o '.join(disponiveis) } está disponível nesta data.")

    # BOTÃO: SALVAR
    if st.button("🚀 Confirmar e Salvar", use_container_width=True, type="primary"):
        if not prof:
            st.warning("⚠️ Informe o nome do professor.")
        else:
            df_atual = carregar_dados()
            pode_gravar = True
            for i in range(qtd_repeticoes):
                d_check = data_ini + timedelta(weeks=i * intervalo_semanas)
                if analisar_disponibilidade(df_atual, lab, d_check, turno_sel)[chave_busca] != "Livre":
                    pode_gravar = False
                    break
            
            if not pode_gravar:
                st.error("⚠️ Conflito de horário! Verifique a disponibilidade antes de salvar.")
            else:
                novos = []
                for i in range(qtd_repeticoes):
                    d_save = data_ini + timedelta(weeks=i * intervalo_semanas)
                    novos.append({
                        "Professor": prof, "Laboratorio": lab, 
                        "Data": d_save.strftime('%Y-%m-%d'),
                        "Turno": turno_sel, "Horario": horario_sel, "Semanas": i + 1
                    })
                df_final = pd.concat([df_atual, pd.DataFrame(novos)], ignore_index=True)
                try:
                    conn.update(data=df_final)
                    st.success("✅ Agendamento(s) realizado(s) com sucesso!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# --- ABA 2: VISUALIZAR AGENDA ---
with aba_agenda:
    st.subheader("Agenda Futura dos Laboratórios")
    df_raw = carregar_dados()
    filtro_lab = st.multiselect("Filtrar Laboratórios", LABS, default=LABS)
    
    if not df_raw.empty:
        df_raw['Data'] = pd.to_datetime(df_raw['Data'], errors='coerce')
        hoje = datetime.now().date()
        
        # Filtros: Apenas hoje/futuro e laboratórios selecionados
        df_view = df_raw[df_raw['Data'].dt.date >= hoje].copy()
        df_view = df_view[df_view['Laboratorio'].isin(filtro_lab)].sort_values(by="Data")

        if not df_view.empty:
            df_view['Mes_Ano'] = df_view['Data'].dt.strftime('%B %Y')
            
            for mes_en in df_view['Mes_Ano'].unique():
                mes_pt = mes_en
                for en, pt in MESES_PT.items():
                    mes_pt = mes_pt.replace(en, pt)
                
                st.markdown(f"#### 📅 {mes_pt}")
                df_mes = df_view[df_view['Mes_Ano'] == mes_en]
                
                for d_dt in sorted(df_mes['Data'].unique()):
                    df_dia = df_mes[df_mes['Data'] == d_dt]
                    d_str = pd.to_datetime(d_dt).strftime('%d/%m/%Y')
                    sem_en = pd.to_datetime(d_dt).strftime('%A')
                    sem_pt = DIAS_PT.get(sem_en, sem_en)

                    with st.expander(f"{d_str} ({sem_pt})"):
                        st.table(df_dia[["Horario", "Laboratorio", "Professor"]].sort_values(by="Horario"))
        else:
            st.info("Não há agendamentos futuros para estes filtros.")
    else:
        st.info("A base de dados está vazia.")
