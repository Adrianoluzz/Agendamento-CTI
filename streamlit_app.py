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

# --- 3. FUNÇÃO DE CHECAGEM DE CONFLITO (LÓGICA CRUZADA) ---
def verificar_conflito(df, lab, data, horario_desejado):
    # Filtra apenas o laboratório e a data específica
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce').dt.date
    reservas_dia = df[(df['Laboratorio'] == lab) & (df['Data'] == data)]
    
    if reservas_dia.empty:
        return None # Livre

    for _, reserva in reservas_dia.iterrows():
        h_existente = reserva['Horario']
        
        # Regra 1: Se o desejado for COMPLETO, qualquer reserva no turno bloqueia
        if "(Completo)" in horario_desejado:
            return f"Ocupado por {reserva['Professor']} ({h_existente})"
        
        # Regra 2: Se já existe um COMPLETO, bloqueia qualquer tentativa (1º, 2º ou Completo)
        if "(Completo)" in h_existente:
            return f"Ocupado por {reserva['Professor']} (Horário Completo)"
            
        # Regra 3: Conflito direto (1º com 1º, ou 2º com 2º)
        if horario_desejado == h_existente:
            return f"Ocupado por {reserva['Professor']} ({h_existente})"
            
    return None

# --- 4. INTERFACE ---
aba_reserva, aba_agenda = st.tabs(["🆕 Novo Agendamento", "📋 Visualizar Agenda"])

with aba_reserva:
    st.subheader("Nova Reserva")
    col1, col2, col3 = st.columns([1, 1, 1.2])
    
    with col1:
        prof = st.text_input("Nome do Professor")
        lab = st.selectbox("Laboratório", LABS)
        data_ini = st.date_input("Data de Início", datetime.now())

    with col2:
        turno_sel = st.radio("Selecione o Turno:", list(OPCOES_POR_TURNO.keys()))

    with col3:
        horario_sel = st.radio("Selecione o Horário:", OPCOES_POR_TURNO[turno_sel])
        qtd_semanas = st.number_input("Repetir por quantas semanas?", min_value=1, max_value=20, value=1)

    st.markdown("---")
    
    # --- BOTÃO VERIFICAR ---
    if st.button("🔍 Verificar Disponibilidade", use_container_width=True):
        df_atual = carregar_dados()
        conflitos = []
        for i in range(qtd_semanas):
            d = data_ini + timedelta(weeks=i)
            resultado = verificar_conflito(df_atual, lab, d, horario_sel)
            if resultado:
                conflitos.append(f"{d.strftime('%d/%m/%Y')}: {resultado}")
        
        if conflitos:
            for c in conflitos: st.error(c)
        else:
            st.success("✅ Laboratório disponível para todas as datas!")

    # --- BOTÃO SALVAR (Com checagem automática antes de gravar) ---
    if st.button("🚀 Confirmar Agendamento", use_container_width=True, type="primary"):
        if not prof:
            st.warning("Informe o nome do professor.")
        else:
            df_atual = carregar_dados()
            conflitos_finais = []
            
            # Checagem de segurança de última hora
            for i in range(qtd_semanas):
                d = data_ini + timedelta(weeks=i)
                if verificar_conflito(df_atual, lab, d, horario_sel):
                    conflitos_finais.append(d.strftime('%d/%m/%Y'))
            
            if conflitos_finais:
                st.error(f"Não foi possível salvar. Conflito nas datas: {', '.join(conflitos_finais)}")
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
    # (Mantém o mesmo código de visualização anterior)
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
