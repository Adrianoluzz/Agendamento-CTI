import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import dateutil.relativedelta as rd # Biblioteca padrão para lidar com meses/semanas complexos

# --- 1. CONFIGURAÇÕES ---
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

conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        data = conn.read(ttl=0)
        return data if data is not None else pd.DataFrame(columns=["Professor", "Laboratorio", "Data", "Turno", "Horario"])
    except:
        return pd.DataFrame(columns=["Professor", "Laboratorio", "Data", "Turno", "Horario"])

def analisar_disponibilidade(df, lab, data, turno):
    df_temp = df.copy()
    # Forçar a coluna Data a ser apenas o dia, sem horas
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

# --- INTERFACE ---
aba_reserva, aba_agenda = st.tabs(["🆕 Novo Agendamento", "📋 Visualizar Agenda"])

with aba_reserva:
    st.subheader("Configurar Agendamento Inteligente")
    col1, col2, col3 = st.columns([1, 1, 1.2])
    
    with col1:
        prof = st.text_input("Nome do Professor")
        lab = st.selectbox("Selecionar Laboratório", LABS)
        tipo_agenda = st.selectbox("Tipo de Agendamento", ["Recorrência + Extras", "Apenas Dias Específicos"])

    with col2:
        turno_sel = st.radio("Selecione o Turno:", list(OPCOES_POR_TURNO.keys()))
        if tipo_agenda == "Recorrência + Extras":
            freq = st.selectbox("Frequência", ["Semanal", "Quinzenal"])

    with col3:
        horario_sel = st.radio("Selecione o Horário:", OPCOES_POR_TURNO[turno_sel])

    st.markdown("---")
    
    datas_finais = []
    c1, c2 = st.columns(2)

    with c1:
        if tipo_agenda == "Recorrência + Extras":
            st.write("**Série de Aulas**")
            d_ini = st.date_input("Data de Início", datetime.now().date())
            qtd = st.number_input("Total de aulas na série:", min_value=1, max_value=30, value=1)
            
            # LÓGICA DE CALENDÁRIO PRECISA
            semanas_adicionar = 2 if freq == "Quinzenal" else 1
            for i in range(qtd):
                # Usamos semanas fixas que o Python converte corretamente para o dia do mês
                nova_data = d_ini + timedelta(weeks=i * semanas_adicionar)
                datas_finais.append(nova_data)
        else:
            datas_manuais = st.multiselect("Datas avulsas:", pd.date_range(start=datetime.now(), periods=180).date, format_func=lambda x: x.strftime('%d/%m/%Y'))
            datas_finais.extend(datas_manuais)

    with c2:
        if tipo_agenda == "Recorrência + Extras":
            st.write("**Dias Adicionais (Ex: Sábados letivos)**")
            extras = st.multiselect("Selecione dias extras:", pd.date_range(start=datetime.now(), periods=180).date, format_func=lambda x: x.strftime('%d/%m/%Y'))
            datas_finais.extend(extras)
            datas_finais = sorted(list(set(datas_finais)))

    st.markdown("---")
    chave_busca = "Completo" if "Completo" in horario_sel else ("1º" if "1º" in horario_sel else "2º")

    if st.button("🔍 Verificar Disponibilidade das Datas", use_container_width=True):
        if not datas_finais: st.warning("Selecione as datas.")
        else:
            df_atual = carregar_dados()
            for d in datas_finais:
                st_dia = analisar_disponibilidade(df_atual, lab, d, turno_sel)
                if st_dia[chave_busca] == "Livre":
                    st.success(f"✅ {d.strftime('%d/%m/%Y')} ({DIAS_PT.get(d.strftime('%A'))}): Disponível")
                else:
                    st.error(f"❌ {d.strftime('%d/%m/%Y')}: {st_dia[chave_busca]}")

    if st.button("🚀 Confirmar Agendamentos no CTI", use_container_width=True, type="primary"):
        if not prof or not datas_finais:
            st.warning("Preencha todos os campos.")
        else:
            df_atual = carregar_dados()
            pode_ir = True
            for d in datas_finais:
                if analisar_disponibilidade(df_atual, lab, d, turno_sel)[chave_busca] != "Livre":
                    pode_ir = False; break
            
            if not pode_ir:
                st.error("Conflito detectado. Verifique as datas individualmente.")
            else:
                novos = []
                for d in datas_finais:
                    novos.append({"Professor": prof, "Laboratorio": lab, "Data": d.strftime('%Y-%m-%d'), "Turno": turno_sel, "Horario": horario_sel})
                df_final = pd.concat([df_atual, pd.DataFrame(novos)], ignore_index=True)
                try:
                    conn.update(data=df_final)
                    st.success(f"✅ {len(datas_finais)} datas agendadas!")
                    st.balloons()
                except Exception as e: st.error(f"Erro: {e}")

# --- ABA 2: AGENDA ---
with aba_agenda:
    st.subheader("Agenda Atualizada CTI")
    df_raw = carregar_dados()
    if not df_raw.empty:
        df_raw['Data'] = pd.to_datetime(df_raw['Data'], errors='coerce')
        df_view = df_raw[df_raw['Data'].dt.date >= datetime.now().date()].copy().sort_values(by="Data")
        if not df_view.empty:
            df_view['Mes_Ano'] = df_view['Data'].dt.strftime('%B %Y')
            for m_en in df_view['Mes_Ano'].unique():
                m_pt = m_en
                for en, pt in MESES_PT.items(): m_pt = m_pt.replace(en, pt)
                st.markdown(f"#### 📅 {m_pt}")
                df_mes = df_view[df_view['Mes_Ano'] == m_en]
                for d_dt in sorted(df_mes['Data'].unique()):
                    df_dia = df_mes[df_mes['Data'] == d_dt]
                    d_s = pd.to_datetime(d_dt).strftime('%d/%m/%Y')
                    s_pt = DIAS_PT.get(pd.to_datetime(d_dt).strftime('%A'))
                    with st.expander(f"{d_s} ({s_pt})"):
                        st.table(df_dia[["Horario", "Laboratorio", "Professor"]].sort_values(by="Horario"))
        else: st.info("Sem agendamentos futuros.")
    else: st.info("Planilha vazia.")
