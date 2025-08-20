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
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler

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

/* Cards de métricas */
.metric-card {
    background: var(--card-background);
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: var(--shadow);
    border: 1px solid var(--border-color);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    height: 100%;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
}

.metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--primary-color);
    margin-bottom: 0.5rem;
}

.metric-label {
    color: var(--text-secondary);
    font-size: 0.875rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.metric-change {
    font-size: 0.75rem;
    margin-top: 0.5rem;
    padding: 0.25rem 0.5rem;
    border-radius: 6px;
}

.metric-change.positive {
    background-color: rgba(16, 185, 129, 0.1);
    color: var(--success-color);
}

.metric-change.negative {
    background-color: rgba(239, 68, 68, 0.1);
    color: #ef4444;
}

/* Seções */
.section-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 2rem 0 1rem 0;
    padding-bottom: 0.75rem;
    border-bottom: 2px solid var(--border-color);
}

.section-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--primary-color);
    margin: 0;
}

.section-icon {
    font-size: 1.5rem;
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

/* Charts container */
.chart-container {
    background: var(--card-background);
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: var(--shadow);
    border: 1px solid var(--border-color);
    margin-bottom: 1.5rem;
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

/* Alertas customizados */
.custom-alert {
    padding: 1rem;
    border-radius: 8px;
    border-left: 4px solid;
    margin: 1rem 0;
}

.alert-success {
    background-color: rgba(16, 185, 129, 0.1);
    border-left-color: var(--success-color);
    color: #047857;
}

.alert-info {
    background-color: rgba(59, 130, 246, 0.1);
    border-left-color: var(--secondary-color);
    color: #1d4ed8;
}

.alert-warning {
    background-color: rgba(245, 158, 11, 0.1);
    border-left-color: var(--accent-color);
    color: #92400e;
}

/* Footer */
.footer {
    text-align: center;
    padding: 2rem;
    color: var(--text-secondary);
    font-size: 0.875rem;
    border-top: 1px solid var(--border-color);
    margin-top: 3rem;
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

# --- FUNÇÃO DE PREVISÃO COM MACHINE LEARNING ---
@st.cache_data(ttl=3600)
def generate_smart_predictions(df, days_ahead):
    df_ml = df.copy()
    df_ml = df_ml.set_index('Data')
    
    # Feature Engineering
    df_ml['day_of_year'] = df_ml.index.dayofyear
    df_ml['month'] = df_ml.index.month
    df_ml['day_of_week'] = df_ml.index.dayofweek
    df_ml['quarter'] = df_ml.index.quarter
    df_ml['is_weekend'] = (df_ml.index.dayofweek >= 5).astype(int)
    
    X = df_ml[['day_of_year', 'month', 'day_of_week', 'quarter', 'is_weekend']]
    y = df_ml['Energia Gerada (kWh)']
    
    # Treinamento do Modelo
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Métricas de Performance
    preds = model.predict(X_test)
    r2 = r2_score(y_test, preds)
    mae = mean_absolute_error(y_test, preds)
    mape = np.mean(np.abs((y_test - preds) / y_test)) * 100
    quality = 'Excelente' if r2 > 0.8 else 'Bom' if r2 > 0.6 else 'Moderado'
    
    ml_metrics = {'model_name': 'Random Forest', 'r2': r2, 'mae': mae, 'mape': mape, 'quality': quality}

    # Gerar Datas Futuras
    last_date = df['Data'].max()
    future_dates = pd.to_datetime([last_date + timedelta(days=i) for i in range(1, days_ahead + 1)])
    future_df = pd.DataFrame(index=future_dates)
    future_df['day_of_year'] = future_df.index.dayofyear
    future_df['month'] = future_df.index.month
    future_df['day_of_week'] = future_df.index.dayofweek
    future_df['quarter'] = future_df.index.quarter
    future_df['is_weekend'] = (future_df.index.dayofweek >= 5).astype(int)
    
    # Previsões
    future_predictions = model.predict(future_df)
    
    # Criar DataFrame de resultado
    predictions_df = pd.DataFrame({
        'Data': future_dates,
        'Previsao': np.maximum(0, future_predictions) # Evitar previsões negativas
    })
    
    # Intervalo de Confiança Simulado
    std_error = np.std([tree.predict(X_test) for tree in model.estimators_], axis=0)
    confidence_margin = 1.96 * np.mean(std_error)
    predictions_df['Limite_Inferior'] = np.maximum(0, predictions_df['Previsao'] - confidence_margin)
    predictions_df['Limite_Superior'] = predictions_df['Previsao'] + confidence_margin
    
    return predictions_df, ml_metrics

# --- Formulário de Cadastro ---
st.markdown("""
<div class="section-header">
    <span class="section-icon">☀️</span>
    <h2 class="section-title">Registro de Geração</h2>
</div>
<div class="form-container">
""", unsafe_allow_html=True)

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
st.markdown("</div>", unsafe_allow_html=True)

# --- Análise de Dados ---
df = load_data()

if df.empty:
    st.info("📊 Nenhum dado encontrado. Comece registrando sua primeira geração.")
else:
    # --- Filtros ---
    st.markdown("""
    <div class="section-header">
        <span class="section-icon">🔍</span>
        <h2 class="section-title">Filtros de Análise</h2>
    </div>
    <div class="filters-container">
    """, unsafe_allow_html=True)
    
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        years = sorted(df['Data'].dt.year.unique(), reverse=True)
        selected_year = st.selectbox("📅 Ano", options=years)
    with filter_col2:
        months = sorted(df[df['Data'].dt.year == selected_year]['Data'].dt.month.unique())
        month_names = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
        selected_month_num = st.selectbox("📊 Mês", options=months, format_func=lambda x: month_names.get(x, ''))
    st.markdown("</div>", unsafe_allow_html=True)

    filtered_df = df[(df['Data'].dt.year == selected_year) & (df['Data'].dt.month == selected_month_num)]
    
    if not filtered_df.empty:
        # --- Métricas ---
        total = filtered_df['Energia Gerada (kWh)'].sum()
        avg = filtered_df['Energia Gerada (kWh)'].mean()
        best = filtered_df.loc[filtered_df['Energia Gerada (kWh)'].idxmax()]
        
        st.header(f"Análise de {month_names.get(selected_month_num, '')} de {selected_year}")
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.metric("Total no Mês", f"{total:,.2f} kWh".replace(",", "X").replace(".", ",").replace("X", "."))
        with metric_col2:
            st.metric("Média Diária", f"{avg:,.2f} kWh".replace(",", "X").replace(".", ",").replace("X", "."))
        with metric_col3:
            st.metric("Melhor Dia", f"{best['Energia Gerada (kWh)']:,.2f} kWh".replace(",", "X").replace(".", ",").replace("X", "."), delta=best['Data'].strftime('%d/%m'))

        # --- Gráficos do Mês ---
        col1, col2 = st.columns(2)
        with col1:
            bar_chart = alt.Chart(filtered_df).mark_bar(
                color="#3b82f6",
                width=20
            ).encode(
                x=alt.X('Data:T', title='Dia'), y=alt.Y('Energia Gerada (kWh):Q', title='Energia (kWh)'),
                tooltip=[alt.Tooltip('Data:T', title='Data'), alt.Tooltip('Energia Gerada (kWh):Q', title='Gerado')]
            ).properties(title="Produção Diária").configure(background='transparent')
            st.altair_chart(bar_chart, use_container_width=True)
        with col2:
            filtered_df['Acumulado'] = filtered_df['Energia Gerada (kWh)'].cumsum()
            area_chart = alt.Chart(filtered_df).mark_area(line={'color':'#10b981'}, color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color='#10b981', offset=0), alt.GradientStop(color='rgba(16, 185, 129, 0)', offset=1)])).encode(
                x=alt.X('Data:T', title='Dia'), y=alt.Y('Acumulado:Q', title='Energia Acumulada (kWh)'),
                tooltip=[alt.Tooltip('Data:T', title='Data'), alt.Tooltip('Acumulado:Q', title='Acumulado')]
            ).properties(title="Geração Acumulada").configure(background='transparent')
            st.altair_chart(area_chart, use_container_width=True)

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
            color="#f59e0b",
            width=30
        ).encode(
            x=alt.X('Nome Mês:N', title='Mês', sort=[m[:3] for m in month_names.values()]),
            y=alt.Y('Energia Gerada (kWh):Q', title='Total (kWh)'),
            tooltip=[alt.Tooltip('Nome Mês', title='Mês'), alt.Tooltip('Energia Gerada (kWh):Q', title='Total Gerado')]
        ).properties(title="Produção Mensal Total").configure(background='transparent')
        st.altair_chart(monthly_chart, use_container_width=True)
        
        # --- HEATMAP ESTILO GITHUB ---
        st.markdown('<div style="margin-top: 2rem;"></div>', unsafe_allow_html=True)
        
        # Filtrar dados apenas para o ano de 2025 para o heatmap
        heatmap_data_2025 = df[df['Data'].dt.year == 2025].copy()
        
        # Criar um DataFrame com todos os dias do ano de 2025
        all_days_of_2025 = pd.date_range(start='2025-01-01', end='2025-12-31', freq='D')
        all_days_df = pd.DataFrame({'Data': all_days_of_2025})
        
        # Juntar com os dados existentes de 2025
        heatmap_df = pd.merge(all_days_df, heatmap_data_2025, on='Data', how='left')
        
        heatmap_df['day_of_week_num'] = heatmap_df['Data'].dt.dayofweek
        heatmap_df['week_of_year'] = heatmap_df['Data'].dt.isocalendar().week
        
        heatmap = alt.Chart(heatmap_df).mark_rect(
            width=15, height=15, cornerRadius=3
        ).encode(
            x=alt.X('week_of_year:O', title='Semana do Ano', axis=alt.Axis(labels=False, ticks=False, domain=False)),
            y=alt.Y('day_of_week_num:O', title='Dia da Semana', sort=None, axis=alt.Axis(labels=True, ticks=False, domain=False, labelExpr="['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'][datum.value]")),
            color=alt.condition(
                'isValid(datum["Energia Gerada (kWh)"])',
                alt.Color('Energia Gerada (kWh):Q', 
                          legend=alt.Legend(title="kWh", orient='bottom'), 
                          scale=alt.Scale(scheme='greens', domain=[8, 25], clamp=True)),
                alt.value('#f0f0f0') # Cor para dias sem dados
            ),
            tooltip=[alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'), alt.Tooltip('Energia Gerada (kWh):Q', title='Gerado', format=',.2f')]
        ).properties(
            title="Calendário de Geração - 2025"
        ).configure(
            background='transparent'
        ).configure_view(
            strokeWidth=0
        )
        st.altair_chart(heatmap, use_container_width=True)


        # --- SISTEMA DE PREVISÕES ---
        if len(year_df_filtered) >= 30:
            st.markdown("""
            <div class="section-header">
                <span class="section-icon">🔮</span>
                <h2 class="section-title">Previsões Inteligentes</h2>
            </div>
            """, unsafe_allow_html=True)
            
            pred_col1, pred_col2 = st.columns([2, 1])
            with pred_col2:
                days_ahead = st.slider("📅 Dias para prever", 7, 60, 30)
            
            with st.spinner("📊 Analisando padrões e gerando previsões..."):
                predictions_df, ml_metrics = generate_smart_predictions(year_df_filtered, days_ahead)

            with pred_col2:
                st.markdown(f"""
                **🤖 Modelo:** {ml_metrics['model_name']}
                **📊 Performance:**
                - Precisão (R²): {ml_metrics['r2']:.1%}
                - Erro Médio: {ml_metrics['mae']:.2f} kWh
                """)

            with pred_col1:
                if not predictions_df.empty:
                    historical_df = year_df_filtered.tail(30).copy()
                    historical_df['Tipo'] = 'Histórico'
                    historical_df['Previsao'] = historical_df['Energia Gerada (kWh)']
                    historical_df['Limite_Inferior'] = historical_df['Energia Gerada (kWh)']
                    historical_df['Limite_Superior'] = historical_df['Energia Gerada (kWh)']
                    
                    predictions_df['Tipo'] = 'Previsão'
                    
                    combined_df = pd.concat([historical_df, predictions_df], ignore_index=True)
                    
                    base = alt.Chart(combined_df)
                    
                    historical_line = base.transform_filter(alt.datum.Tipo == 'Histórico').mark_line(color='#3b82f6', strokeWidth=3).encode(
                        x=alt.X('Data:T', title='Data'), y=alt.Y('Energia Gerada (kWh):Q', title='Energia (kWh)'),
                        tooltip=[alt.Tooltip('Data:T', title='Data'), alt.Tooltip('Energia Gerada (kWh):Q', title='Real')]
                    )
                    
                    prediction_line = base.transform_filter(alt.datum.Tipo == 'Previsão').mark_line(color='#f59e0b', strokeWidth=3, strokeDash=[8, 4]).encode(
                        x='Data:T', y='Previsao:Q',
                        tooltip=[alt.Tooltip('Data:T', title='Data'), alt.Tooltip('Previsao:Q', title='Previsão')]
                    )
                    
                    confidence_band = base.transform_filter(alt.datum.Tipo == 'Previsão').mark_area(opacity=0.3, color='#f59e0b').encode(
                        x='Data:T', y='Limite_Inferior:Q', y2='Limite_Superior:Q'
                    )
                    
                    final_chart = (confidence_band + historical_line + prediction_line).properties(
                        title=f"Previsão de Geração - Próximos {days_ahead} dias"
                    ).configure(background='transparent').interactive()
                    
                    st.altair_chart(final_chart, use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True) # Fecha o main-container
