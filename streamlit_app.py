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

MESES_PT = {'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março', 'April': 'Abril', 'May': 'Maio', 'June': 'Junho', 'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro', 'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'}
DIAS_PT = {'Monday': 'Segunda-feira', 'Tuesday': 'Terça-feira', 'Wednesday': 'Quarta-feira', 'Thursday': 'Quinta-feira', 'Friday': 'Sexta-feira', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}

st.set_page_config(page_title="Gestão de Labs CTI", layout="wide", page_icon="📅")
st.title("📅 Gestão de Laboratórios - CTI")

# --- 2. CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        data = conn.read(ttl=0)
        return data if data is not None else pd.DataFrame(columns=["Professor", "Laboratorio", "Data", "Turno", "Horario"])
    except:
        return pd.DataFrame(columns=["Professor", "Laboratorio", "Data", "Turno", "Horario"])

def analisar_disponibilidade(df, lab, data, turno):
    df_temp = df.copy()
    df_temp['Data'] = pd.to_datetime(df_temp['Data'], errors='coerce').dt.date
    reservas = df_temp[(df_temp['Laboratorio'] == lab) & (df_temp['Data'] == data) & (df_temp['Turno'] == turno)]
    status = {"1º": "Livre", "2º": "Livre", "Completo": "Livre"}
    for _, r in reservas.iterrows():
        h, prof = r['Horario'], r['Professor']
        if "(1º Horário)" in h:
            status["1º"] = f"Agendamento (1 horario) indisponivel - Prof. {prof}"
            status["Completo"] = f"Agendamento (completo) indisponivel - Prof. {prof}"
        elif "(2º Horário)" in h:
            status["2º"] = f"Agendamento (2 horario) indisponivel - Prof. {prof}"
            status["Completo"] = f"Agendamento (completo) indisponivel - Prof. {prof}"
        elif "(Completo)" in h:
            status["1º"] = f"Agendamento (1 horario) indisponivel - Prof. {prof}"
            status["2º"] = f"Agendamento (2 horario) indisponivel - Prof. {prof}"
            status["Completo"] = f"Agendamento (completo) indisponivel - Prof. {prof}"
    return status

# --- 3. INTERFACE ---
aba_reserva, aba_agenda = st.tabs(["🆕 Novo Agendamento", "📋 Visualizar Agenda"])

with aba_reserva:
    st.subheader("Configurar Agendamento Múltiplo")
    
    col1, col2, col3 = st.columns([1, 1, 1.2])
    
    with col1:
        prof = st.text_input("Nome do Professor")
        lab = st.selectbox("Selecionar Laboratório", LABS)
        tipo_agenda = st.selectbox("Tipo de Agendamento", ["Apenas Dias Específicos", "Recorrência + Extras"])

    with col2:
        turno_sel = st.radio("Selecione o Turno:", list(OPCOES_POR_TURNO.keys()))
        if tipo_agenda == "Recorrência + Extras":
            freq = st.selectbox("Frequência da Recorrência", ["Semanal", "Quinzenal"])

    with col3:
        horario_sel = st.radio("Selecione o Horário:", OPCOES_POR_TURNO[turno_sel])

    st.markdown("---")
    col_data1, col_data2 = st.columns(2)

    datas_finais = []

    with col_data1:
        if tipo_agenda == "Recorrência + Extras":
            st.write("**Configurar Recorrência**")
            d_ini = st.date_input("Data de Início da Série", datetime.now())
            qtd = st.number_input("Número de semanas/quatorzenas:", min_value=1, max_value=20, value=1)
            pulo = 2 if freq == "Quinzenal" else 1
            for i in range(qtd):
                datas_finais.append(d_ini + timedelta(weeks=i * pulo))
        else:
            st.write("**Seleção Manual**")
            datas_manuais = st.multiselect("Selecione os dias:", 
                                           pd.date_range(start=datetime.now(), periods=120).date,
                                           format_func=lambda x: x.strftime('%d/%m/%Y'))
            datas_finais.extend(datas_manuais)

    with col_data2:
        if tipo_agenda == "Recorrência + Extras":
            st.write("**Adicionar Dias Extras (Opcional)**")
            extras = st.multiselect("Selecione dias fora da recorrência:", 
                                     pd.date_range(start=datetime.now(), periods=120).date,
                                     format_func=lambda x: x.strftime('%d/%m/%Y'))
            datas_finais.extend(extras)
            # Remover duplicatas caso o usuário selecione um dia que já cairia na recorrência
            datas_finais = sorted(list(set(datas_finais)))

    st.markdown("---")
    chave_busca = "Completo" if "Completo" in horario_sel else ("1º" if "1º" in horario_sel else "2º")

    # BOTÃO VERIFICAR
    if st.button("🔍 Verificar Tudo", use_container_width=True):
        if not datas_finais:
            st.warning("Nenhuma data selecionada.")
        else:
            df_atual = carregar_dados()
            for d in datas_finais:
                status = analisar_disponibilidade(df_atual, lab, d, turno_sel)
                if status[chave_busca] == "Livre":
                    st.success(f"✅ {d.strftime('%d/%m/%Y')}: Disponível")
                else:
                    st.error(f"❌ {d.strftime('%d/%m/%Y')}: {status[chave_busca]}")

    # BOTÃO SALVAR
    if st.button("🚀 Gravar Agendamentos", use_container_width=True, type="primary"):
        if not prof or not datas_finais:
            st.warning("Preencha o professor e selecione as datas.")
        else:
            df_atual = carregar_dados()
            conflito = False
            for d in datas_finais:
                if analisar_disponibilidade(df_atual, lab, d, turno_sel)[chave_busca] != "Livre":
                    conflito = True; break
            
            if conflito:
                st.error("Conflito detectado. Corrija as datas antes de salvar.")
            else:
                novos_dados = []
                for d in datas_finais:
                    novos_dados.append({
                        "Professor": prof, "Laboratorio": lab, 
                        "Data": d.strftime('%Y-%m-%d'),
                        "Turno": turno_sel, "Horario": horario_sel
                    })
                df_final = pd.concat([df_atual, pd.DataFrame(novos_dados)], ignore_index=True)
                try:
                    conn.update(data=df_final)
                    st.success(f"✅ {len(datas_finais)} agendamentos salvos com sucesso!")
                    st.balloons()
                except Exception as e: st.error(f"Erro na planilha: {e}")

# --- ABA 2: VISUALIZAÇÃO ---
with aba_agenda:
    st.subheader("Agenda Futura")
    df_raw = carregar_dados()
    filtro_lab = st.multiselect("Filtrar Laboratórios", LABS, default=LABS)
    if not df_raw.empty:
        df_raw['Data'] = pd.to_datetime(df_raw['Data'], errors='coerce')
        df_view = df_raw[df_raw['Data'].dt.date >= datetime.now().date()].copy()
        df_view = df_view[df_view['Laboratorio'].isin(filtro_lab)].sort_values(by="Data")
        if not df_view.empty:
            df_view['Mes_Ano'] = df_view['Data'].dt.strftime('%B %Y')
            for mes_en in df_view['Mes_Ano'].unique():
                mes_pt = mes_en
                for en, pt in MESES_PT.items(): mes_pt = mes_pt.replace(en, pt)
                st.markdown(f"#### 📅 {mes_pt}")
                df_mes = df_view[df_view['Mes_Ano'] == mes_en]
                for d_dt in sorted(df_mes['Data'].unique()):
                    df_dia = df_mes[df_mes['Data'] == d_dt]
                    d_str = pd.to_datetime(d_dt).strftime('%d/%m/%Y')
                    sem_pt = DIAS_PT.get(pd.to_datetime(d_dt).strftime('%A'))
                    with st.expander(f"{d_str} ({sem_pt})"):
                        st.table(df_dia[["Horario", "Laboratorio", "Professor"]].sort_values(by="Horario"))
        else: st.info("Sem agendamentos.")
    else: st.info("Planilha vazia.")
