import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÕES DO CTI ---
LABS = [
    "Automação", "Química", "Desenho", "Predial", "Hidráulica", 
    "Civil", "Maquete", "Eletrônica", "Física", "Mecânica"
]

# Grade de horários oficial vinculada aos turnos
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

# --- 2. CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        # ttl=0 evita que o Streamlit use dados antigos do cache
        data = conn.read(ttl=0)
        if data is None or data.empty:
            return pd.DataFrame(columns=["Professor", "Laboratorio", "Data", "Turno", "Horario", "Semanas"])
        return data
    except Exception:
        return pd.DataFrame(columns=["Professor", "Laboratorio", "Data", "Turno", "Horario", "Semanas"])

# --- 3. INTERFACE DE NAVEGAÇÃO ---
aba_reserva, aba_agenda = st.tabs(["🆕 Novo Agendamento", "📋 Visualizar Agenda"])

# --- ABA 1: FORMULÁRIO DE RESERVA (COM ATUALIZAÇÃO EM TEMPO REAL) ---
with aba_reserva:
    st.subheader("Configurar Nova Reserva")
    
    # Criamos colunas para organizar os pontos de seleção
    col1, col2, col3 = st.columns([1, 1, 1.2])
    
    with col1:
        prof = st.text_input("Nome do Professor", placeholder="Digite o nome...")
        lab = st.selectbox("Selecionar Laboratório", LABS)
        data_ini = st.date_input("Data de Início", datetime.now())

    with col2:
        # PONTOS DE SELEÇÃO PARA O TURNO
        turno_sel = st.radio(
            "Selecione o Turno:", 
            list(OPCOES_POR_TURNO.keys()),
            help="Clique para atualizar os horários ao lado."
        )

    with col3:
        # PONTOS DE SELEÇÃO PARA O HORÁRIO (Atualiza baseado no turno_sel)
        horario_sel = st.radio(
            "Selecione o Horário de Aula:", 
            OPCOES_POR_TURNO[turno_sel]
        )
        
        st.markdown("---")
        qtd_semanas = st.number_input("Repetir por quantas semanas?", min_value=1, max_value=20, value=1)

    # Botão de ação principal
    if st.button("🚀 Confirmar e Salvar Agendamento", use_container_width=True, type="primary"):
        if not prof:
            st.warning("⚠️ Por favor, insira o nome do professor antes de salvar.")
        else:
            novos_registros = []
            for i in range(qtd_semanas):
                data_aula = data_ini + timedelta(weeks=i)
                novos_registros.append({
                    "Professor": prof,
                    "Laboratorio": lab,
                    "Data": data_aula.strftime('%Y-%m-%d'),
                    "Turno": turno_sel,
                    "Horario": horario_sel,
                    "Semanas": i + 1
                })
            
            # Processo de salvamento
            with st.spinner("Salvando na planilha..."):
                df_atual = carregar_dados()
                df_novo = pd.DataFrame(novos_registros)
                df_final = pd.concat([df_atual, df_novo], ignore_index=True)
                
                try:
                    conn.update(data=df_final)
                    st.success(f"✅ Sucesso! {qtd_semanas} reserva(s) adicionada(s) à agenda.")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro técnico ao salvar: {e}")

# --- ABA 2: VISUALIZAÇÃO DA AGENDA ---
with aba_agenda:
    st.subheader("Consulta de Ocupação")
    df_raw = carregar_dados()
    
    filtro_lab = st.multiselect("Filtrar Laboratórios", LABS, default=LABS)
    
    if not df_raw.empty:
        # Tratamento de dados para garantir que a data seja lida corretamente
        df_raw['Data'] = pd.to_datetime(df_raw['Data'], errors='coerce')
        df_view = df_raw.dropna(subset=['Data']).copy()
        
        # Ordenação cronológica (do dia mais próximo para o mais distante)
        datas_disponiveis = sorted(df_view['Data'].unique())
        
        if not datas_disponiveis:
            st.info("Nenhum agendamento encontrado para os filtros selecionados.")
        
        for data_dt in datas_disponiveis:
            df_dia = df_view[
                (df_view['Data'] == data_dt) & 
                (df_view['Laboratorio'].isin(filtro_lab))
            ]
            
            if not df_dia.empty:
                # Título do card formatado (Ex: 23/03/2026 - Monday)
                label_dia = f"📅 {data_dt.strftime('%d/%m/%Y')} - {data_dt.strftime('%A')}"
                with st.expander(label_dia):
                    st.table(df_dia[["Horario", "Laboratorio", "Professor"]].sort_values(by="Horario"))
    else:
        st.info("ℹ️ A agenda está vazia. Realize um novo agendamento para visualizar os dados.")
