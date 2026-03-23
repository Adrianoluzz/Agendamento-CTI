import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÕES TÉCNICAS DO CTI ---
LABS = [
    "Automação", "Química", "Desenho", "Predial", "Hidráulica", 
    "Civil", "Maquete", "Eletrônica", "Física", "Mecânica"
]

# Grade de horários oficial conforme sua especificação
OPCOES_POR_TURNO = {
    "Matutino": [
        "08:00 - 11:00 (Completo)", 
        "08:00 - 09:30 (1º Horário)", 
        "09:45 - 11:00 (2º Horário)"
    ],
    "Vespertino": [
        "14:00 - 17:00 (Completo)"
    ],
    "Noturno": [
        "19:00 - 22:00 (Completo)", 
        "19:00 - 20:30 (1º Horário)", 
        "20:45 - 22:00 (2º Horário)"
    ]
}

# Configuração da Página
st.set_page_config(page_title="Gestão de Labs CTI", layout="wide", page_icon="📅")
st.title("📅 Sistema de Gestão de Laboratórios - CTI")

# --- 2. FUNÇÕES DE CONEXÃO (GOOGLE SHEETS) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        # ttl=0 força a atualização em tempo real sem cache
        data = conn.read(ttl=0)
        if data is None or data.empty:
            return pd.DataFrame(columns=["Professor", "Laboratorio", "Data", "Turno", "Horario", "Semanas"])
        return data
    except Exception:
        # Retorna DataFrame vazio se houver erro na leitura ou planilha inexistente
        return pd.DataFrame(columns=["Professor", "Laboratorio", "Data", "Turno", "Horario", "Semanas"])

# --- 3. INTERFACE DE NAVEGAÇÃO ---
aba_reserva, aba_agenda = st.tabs(["🆕 Novo Agendamento", "📋 Visualizar Agenda"])

# --- ABA 1: FORMULÁRIO DE RESERVA ---
with aba_reserva:
    with st.form("form_agendamento"):
        st.subheader("Cadastrar Nova Reserva")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            prof = st.text_input("Nome do Professor")
            lab = st.selectbox("Selecionar Laboratório", LABS)
        
        with col2:
            data_ini = st.date_input("Data de Início", datetime.now())
            turno_sel = st.selectbox("Turno", list(OPCOES_POR_TURNO.keys()))
        
        with col3:
            # Lista dinâmica baseada no turno selecionado
            lista_h = OPCOES_POR_TURNO[turno_sel] + ["Outro (Personalizado)"]
            horario_sel = st.selectbox("Horário de Aula", lista_h)
            
            if horario_sel == "Outro (Personalizado)":
                horario_final = st.text_input("Digite o horário (ex: 10:00 - 11:30)")
            else:
                horario_final = horario_sel
                
            qtd_semanas = st.number_input("Repetir por quantas semanas?", min_value=1, max_value=20, value=1)
        
        submit = st.form_submit_button("Confirmar e Salvar")

    if submit:
        if not prof or not horario_final:
            st.error("⚠️ Por favor, preencha todos os campos obrigatórios.")
        else:
            novos_registros = []
            for i in range(qtd_semanas):
                data_aula = data_ini + timedelta(weeks=i)
                novos_registros.append({
                    "Professor": prof,
                    "Laboratorio": lab,
                    "Data": data_aula.strftime('%Y-%m-%d'),
                    "Turno": turno_sel,
                    "Horario": horario_final,
                    "Semanas": i + 1
                })
            
            df_atual = carregar_dados()
            df_novo = pd.DataFrame(novos_registros)
            df_final = pd.concat([df_atual, df_novo], ignore_index=True)
            
            try:
                # O comando update sincroniza o DataFrame com a Google Sheets
                conn.update(data=df_final)
                st.success(f"✅ Sucesso! {qtd_semanas} agendamento(s) realizado(s).")
                st.balloons()
            except Exception as e:
                st.error(f"❌ Erro de permissão: Verifique se a planilha está compartilhada com o e-mail da Service Account. Detalhe: {e}")

# --- ABA 2: VISUALIZAÇÃO DA AGENDA ---
with aba_agenda:
    st.subheader("Consulta de Ocupação")
    df_raw = carregar_dados()
    
    # Filtro multiselect para facilitar a busca por lab específico
    filtro_lab = st.multiselect("Filtrar Laboratórios", LABS, default=LABS)
    
    if not df_raw.empty:
        # Tratamento de data para evitar erros de visualização
        df_raw['Data'] = pd.to_datetime(df_raw['Data'], errors='coerce')
        df_view = df_raw.dropna(subset=['Data']).copy()
        
        # Ordenação cronológica
        datas_disponiveis = sorted(df_view['Data'].unique())
        
        if not datas_disponiveis:
            st.warning("Nenhum dado válido encontrado na planilha.")
        
        for data_dt in datas_disponiveis:
            df_dia = df_view[
                (df_view['Data'] == data_dt) & 
                (df_view['Laboratorio'].isin(filtro_lab))
            ]
            
            if not df_dia.empty:
                # Título formatado: 📅 23/03/2026 - Monday
                label_dia = f"📅 {data_dt.strftime('%d/%m/%Y')} - {data_dt.strftime('%A')}"
                with st.expander(label_dia):
                    st.table(df_dia[["Horario", "Laboratorio", "Professor"]].sort_values(by="Horario"))
    else:
        st.info("ℹ️ A agenda está vazia no momento.")
