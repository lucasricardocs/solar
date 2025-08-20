# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import streamlit as st
import gspread
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
import warnings
import altair as alt
import locale

# Ignora avisos futuros do pandas
warnings.filterwarnings('ignore', category=FutureWarning, message='.*observed=False.*')

# Tenta configurar a localidade para português
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    pass

# --- Constantes de Configuração ---
SPREADSHEET_ID = '1WI2tZ94lVV9GfaaWerdSfuChFLzWfMbU4v2m6QrwTdY'
WORKSHEET_NAME = 'Solardaily'

# --- Configuração da Página ---
st.set_page_config(
    layout="wide",
    page_title="SolarAnalytics Pro | Dashboard Energia Solar",
    page_icon="⚡",
    initial_sidebar_state="collapsed"
)

# --- Estilo CSS Profissional ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --primary-color: #1f2937;
    --secondary-color: #3b82f6;
    --accent-color: #f59e0b;
    --success-color: #10b981;
    --background-color: #f8fafc;
    --card-background: #ffffff;
    --text-primary: #1f2937;
    --text-secondary: #6b7280;
    --border-color: #e5e7eb;
    --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

html, body, [class*="st-"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background-color: var(--background-color);
}

.main-container {
    background-color: var(--background-color);
    border-radius: 20px;
    padding: 2rem;
    margin: 1rem;
}

/* Header customizado */
.header-container {
    background: linear-gradient(135deg, var(--primary-color) 0%, #374151 100%);
    color: white;
    padding: 2rem;
    border-radius: 16px;
    margin-bottom: 2rem;
    box-shadow: var(--shadow-lg);
    position: relative;
    overflow: hidden;
}

.header-title {
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    background: linear-gradient(135deg, #fbbf24, #f59e0b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.header-subtitle {
    font-size: 1.1rem;
    opacity: 0.9;
    font-weight: 400;
}

/* Formulário */
.form-container {
    background: var(--card-background);
    padding: 2rem;
    border-radius: 16px;
    box-shadow: var(--shadow);
    border: 1px solid var(--border-color);
    margin-bottom: 2rem;
}

.stButton>button {
    background: linear-gradient(135deg, var(--secondary-color), #2563eb);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.75rem 1.5rem;
    font-weight: 600;
    box-shadow: var(--shadow);
    transition: all 0.2s ease;
}

.stButton>button:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow-lg);
}

/* Filtros */
.filters-container {
    background: var(--card-background);
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: var(--shadow);
    border: 1px solid var(--border-color);
    margin-bottom: 2rem;
}

/* Esconder elementos padrão do Streamlit */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Header Profissional ---
st.markdown("""
<div class="main-container">
    <div class="header-container">
        <div class="header-title">⚡ SolarAnalytics Pro</div>
        <div class="header-subtitle">Monitoramento Inteligente de Geração de Energia Solar</div>
    </div>
""", unsafe_allow_html=True)

# --- Conexão com Google Sheets ---
@st.cache_resource
def connect_to_gsheets():
    scopes = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    try:
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.worksheet(WORKSHEET_NAME)
        return sheet
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("📋 Planilha não encontrada. Verifique o SPREADSHEET_ID.")
        st.stop()
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"📊 Aba '{WORKSHEET_NAME}' não encontrada. Verifique o WORKSHEET_NAME.")
        st.stop()

sheet = connect_to_gsheets()

# --- Funções de Dados ---
@st.cache_data(ttl=600)
def load_data():
    try:
        values = sheet.get_all_values()
        if len(values) < 2: return pd.DataFrame()
        
        df = pd.DataFrame(values[1:], columns=values[0])
        df.columns = [col.lower().strip() for col in df.columns]

        if 'data' not in df.columns or 'gerado' not in df.columns:
            st.error("⚠️ **Erro de Configuração**: A planilha deve conter as colunas 'data' e 'gerado'.")
            return pd.DataFrame()

        df.rename(columns={'data': 'Data', 'gerado': 'Energia Gerada (kWh)'}, inplace=True)
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        df['Energia Gerada (kWh)'] = df['Energia Gerada (kWh)'].astype(str).str.replace(',', '.', regex=False)
        df['Energia Gerada (kWh)'] = pd.to_numeric(df['Energia Gerada (kWh)'], errors='coerce')
        df.dropna(subset=['Data', 'Energia Gerada (kWh)'], inplace=True)
        return df.sort_values(by='Data')
    except Exception as e:
        st.error(f"🚨 **Erro ao carregar dados**: {str(e)}")
        return pd.DataFrame()

def append_data(date, energy):
    try:
        formatted_date = date.strftime('%d/%m/%Y')
        sheet.append_row([formatted_date, energy], value_input_option='USER_ENTERED')
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"🚨 **Erro ao salvar**: {str(e)}")
        return False

# --- Formulário de Cadastro ---
st.header("☀️ Registro de Geração")
with st.container(border=True):
    with st.form("entry_form", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            input_date = st.date_input("📅 Data da Geração", value=datetime.today(), format="DD/MM/YYYY")
        with col2:
            input_energy_str = st.text_input("⚡ Energia Gerada (kWh)", placeholder="Ex: 25,75")
        with col3:
            st.write("")
            st.write("")
            submitted = st.form_submit_button("💾 Salvar", use_container_width=True)

        if submitted:
            if input_energy_str:
                try:
                    energy_value = float(input_energy_str.replace(',', '.'))
                    if append_data(input_date, energy_value):
                        st.success("✅ Dados salvos com sucesso!")
                except ValueError:
                    st.error("⚠️ Formato inválido! Digite um número.")
            else:
                st.warning("💡 Preencha o valor da energia.")

# --- Análise de Dados ---
df = load_data()

if df.empty:
    st.info("📊 Nenhum dado encontrado. Comece registrando sua primeira geração.")
else:
    # --- Filtros ---
    st.header("🔍 Filtros de Análise")
    with st.container(border=True):
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            years = sorted(df['Data'].dt.year.unique(), reverse=True)
            selected_year = st.selectbox("📅 Ano", options=years)
        with filter_col2:
            months = sorted(df[df['Data'].dt.year == selected_year]['Data'].dt.month.unique())
            month_names = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
            selected_month_num = st.selectbox("📊 Mês", options=months, format_func=lambda x: month_names.get(x, ''))

    filtered_df = df[(df['Data'].dt.year == selected_year) & (df['Data'].dt.month == selected_month_num)]
    
    if not filtered_df.empty:
        # --- Métricas ---
        total = filtered_df['Energia Gerada (kWh)'].sum()
        avg = filtered_df['Energia Gerada (kWh)'].mean()
        best = filtered_df.loc[filtered_df['Energia Gerada (kWh)'].idxmax()]
        worst = filtered_df.loc[filtered_df['Energia Gerada (kWh)'].idxmin()]
        
        st.header(f"Análise de {month_names.get(selected_month_num, '')} de {selected_year}")
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        with metric_col1:
            st.metric("Total no Mês", f"{total:,.2f} kWh".replace(",", "X").replace(".", ",").replace("X", "."))
        with metric_col2:
            st.metric("Média Diária", f"{avg:,.2f} kWh".replace(",", "X").replace(".", ",").replace("X", "."))
        with metric_col3:
            st.metric("Melhor Dia", f"{best['Energia Gerada (kWh)']:,.2f} kWh".replace(",", "X").replace(".", ",").replace("X", "."), delta=best['Data'].strftime('%d/%m'))
        with metric_col4:
            st.metric("Pior Dia", f"{worst['Energia Gerada (kWh)']:,.2f} kWh".replace(",", "X").replace(".", ",").replace("X", "."), delta=worst['Data'].strftime('%d/%m'), delta_color="inverse")

        # --- Gráficos do Mês ---
        st.subheader("Produção Diária")
        bar_chart = alt.Chart(filtered_df).mark_bar(
            color="#3b82f6"
        ).encode(
            x=alt.X('Data:T', title='Dia', scale=alt.Scale(paddingInner=0.2)), # DICA: Altere paddingInner (0 a 1) para o espaçamento. 0.1 é bem próximo.
            y=alt.Y('Energia Gerada (kWh):Q', title='Energia (kWh)'),
            tooltip=[alt.Tooltip('Data:T', title='Data'), alt.Tooltip('Energia Gerada (kWh):Q', title='Gerado')]
        ).properties(height=350).configure(background='transparent')
        st.altair_chart(bar_chart, use_container_width=True)

        st.subheader("Geração Acumulada no Mês")
        base = alt.Chart(filtered_df).encode(
            x=alt.X('Data:T', title='Dia'),
            tooltip=[alt.Tooltip('Data:T', title='Data'), alt.Tooltip('Acumulado:Q', title='Acumulado')]
        ).transform_window(
            Acumulado='sum(`Energia Gerada (kWh)`)',
            frame=[None, 0]
        )

        area = base.mark_area(
            line={'color':'#10b981'}, 
            color=alt.Gradient(
                gradient='linear', 
                stops=[alt.GradientStop(color='#10b981', offset=0), alt.GradientStop(color='rgba(16, 185, 129, 0)', offset=1)],
                x1=1, x2=1, y1=1, y2=0
            )
        ).encode(y=alt.Y('Acumulado:Q', title='Energia Acumulada (kWh)'))
        
        points = base.mark_point(
            size=40,
            color='#10b981',
            opacity=0.7,
            filled=True
        ).encode(y=alt.Y('Acumulado:Q'))

        st.altair_chart((area + points).properties(height=350).configure(background='transparent'), use_container_width=True)

    # --- Análise Anual ---
    year_df_filtered = df[df['Data'].dt.year == selected_year].copy()
    if not year_df_filtered.empty:
        st.divider()
        st.header(f"Resumo Anual de {selected_year}")
        
        # Gráfico Mensal
        monthly_summary = year_df_filtered.groupby(year_df_filtered['Data'].dt.month)['Energia Gerada (kWh)'].sum().reset_index()
        monthly_summary.rename(columns={'Data': 'Mês'}, inplace=True)
        monthly_summary['Nome Mês'] = monthly_summary['Mês'].apply(lambda m: month_names[m][:3])
        monthly_chart = alt.Chart(monthly_summary).mark_bar(
            color="#f59e0b"
        ).encode(
            x=alt.X('Nome Mês:N', title='Mês', sort=[m[:3] for m in month_names.values()], scale=alt.Scale(paddingInner=0.3)),
            y=alt.Y('Energia Gerada (kWh):Q', title='Total (kWh)'),
            tooltip=[alt.Tooltip('Nome Mês', title='Mês'), alt.Tooltip('Energia Gerada (kWh):Q', title='Total Gerado')]
        ).properties(height=350).configure(background='transparent')
        st.altair_chart(monthly_chart, use_container_width=True)
        
        # --- HEATMAP ESTILO GITHUB ---
        st.subheader(f"Calendário de Geração - {selected_year}")
        
        all_days_of_year = pd.date_range(start=f'{selected_year}-01-01', end=f'{selected_year}-12-31', freq='D')
        all_days_df = pd.DataFrame({'Data': all_days_of_year})
        
        heatmap_df = pd.merge(all_days_df, year_df_filtered, on='Data', how='left')
        
        heatmap_df['day_of_week_num'] = heatmap_df['Data'].dt.dayofweek
        heatmap_df['week_of_year'] = heatmap_df['Data'].dt.isocalendar().week
        heatmap_df['month_abbr'] = heatmap_df['Data'].dt.month.apply(lambda m: month_names.get(m, '')[:3])
        
        month_labels = heatmap_df.groupby('month_abbr')['week_of_year'].min().reset_index()
        month_order = [month_names[i][:3] for i in range(1, 13)]
        month_labels['month_cat'] = pd.Categorical(month_labels['month_abbr'], categories=month_order, ordered=True)
        month_labels = month_labels.sort_values('month_cat')
        
        month_labels_dict = dict(zip(month_labels['week_of_year'], month_labels['month_abbr']))
        label_expr = f"datum.value in {list(month_labels_dict.keys())} ? {month_labels_dict}[datum.value] : ''"

        heatmap = alt.Chart(heatmap_df).mark_rect(
            width=15, height=15, cornerRadius=3, stroke='white', strokeWidth=2
        ).encode(
            x=alt.X('week_of_year:O', title=None, axis=alt.Axis(labels=True, ticks=False, domain=False, labelExpr=label_expr, labelAlign='left', labelOffset=10, labelPadding=5)),
            y=alt.Y('day_of_week_num:O', title=None, sort=None, axis=alt.Axis(labels=True, ticks=False, domain=False, labelExpr="['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'][datum.value]")),
            color=alt.condition(
                'isValid(datum["Energia Gerada (kWh)"])',
                alt.Color('Energia Gerada (kWh):Q', 
                          legend=alt.Legend(title="kWh", orient='bottom'), 
                          scale=alt.Scale(scheme='greens')),
                alt.value('#d3d3d3')
            ),
            tooltip=[alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'), alt.Tooltip('Energia Gerada (kWh):Q', title='Gerado', format=',.2f')]
        ).properties(
            height=150
        ).configure(
            background='transparent'
        ).configure_view(
            strokeWidth=0
        )
        st.altair_chart(heatmap, use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True) # Fecha o main-container
