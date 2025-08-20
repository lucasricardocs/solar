# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
import calendar

# Ignora avisos futuros do pandas
warnings.filterwarnings('ignore', category=FutureWarning, message='.*observed=False.*')

# --- Configuração da Página ---
st.set_page_config(
    layout="wide",
    page_title="SolarAnalytics Pro | Dashboard Energia Solar",
    page_icon="⚡",
    initial_sidebar_state="collapsed"
)

# --- Estilo CSS Profissional com Background Degradê ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --primary-color: #1f2937;
    --secondary-color: #3b82f6;
    --accent-color: #f59e0b;
    --success-color: #10b981;
    --text-primary: #1f2937;
    --text-secondary: #6b7280;
    --border-color: #e5e7eb;
    --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

html, body, [class*="st-"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Background principal com degradê de cinza escuro para claro */
.stApp {
    background: linear-gradient(135deg, #4a5568 0%, #718096 25%, #a0aec0 75%, #e2e8f0 100%);
    min-height: 100vh;
}

.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Container principal */
.main-container {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    padding: 2rem;
    margin: 0 auto;
    box-shadow: var(--shadow-lg);
    border: 1px solid rgba(255, 255, 255, 0.2);
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

.header-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: 
        radial-gradient(circle at 25% 25%, rgba(255, 255, 255, 0.1) 2px, transparent 2px),
        radial-gradient(circle at 75% 75%, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
    background-size: 50px 50px;
}

.header-title {
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    background: linear-gradient(135deg, #fbbf24, #f59e0b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    position: relative;
    z-index: 2;
}

.header-subtitle {
    font-size: 1.1rem;
    opacity: 0.9;
    font-weight: 400;
    position: relative;
    z-index: 2;
}

/* Cards com efeito glassmorphism */
.metric-card {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(10px);
    padding: 1.5rem;
    border-radius: 16px;
    box-shadow: var(--shadow);
    border: 1px solid rgba(255, 255, 255, 0.2);
    margin-bottom: 1rem;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
}

/* Formulário */
.stForm {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(10px);
    padding: 2rem;
    border-radius: 16px;
    box-shadow: var(--shadow);
    border: 1px solid rgba(255, 255, 255, 0.2);
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
    border: none !important;
}

.stButton>button:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow-lg);
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
}

/* Selectbox e inputs */
.stSelectbox > div > div {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(10px);
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.stTextInput > div > div {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(10px);
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.stDateInput > div > div {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(10px);
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.2);
}

/* Métricas */
[data-testid="metric-container"] {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    padding: 1rem;
    border-radius: 12px;
    box-shadow: var(--shadow);
}

/* Gráficos */
.js-plotly-plot {
    background: rgba(255, 255, 255, 0.9) !important;
    backdrop-filter: blur(10px);
    border-radius: 12px;
    padding: 1rem;
    box-shadow: var(--shadow);
    border: 1px solid rgba(255, 255, 255, 0.2);
}

/* Esconder elementos padrão do Streamlit */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Container com borda */
.element-container:has(.metric-card) {
    background: transparent;
}

/* Headers */
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    color: var(--text-primary);
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# --- Header Profissional ---
st.markdown("""
<div class="main-container">
    <div class="header-container">
        <div class="header-title">⚡ SolarAnalytics Pro</div>
        <div class="header-subtitle">Monitoramento Inteligente de Geração de Energia Solar</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Dados de Exemplo (simulando planilha) ---
@st.cache_data
def generate_sample_data():
    """Gera dados de exemplo para demonstração"""
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    
    # Simula variação sazonal e diária realista
    data = []
    for date in dates:
        # Variação sazonal (verão = mais energia)
        month_factor = 1.2 if date.month in [12, 1, 2] else 0.8 if date.month in [6, 7, 8] else 1.0
        
        # Variação por dia da semana (fins de semana podem ter padrões diferentes)
        weekday_factor = 0.9 if date.weekday() in [5, 6] else 1.0
        
        # Simulação de clima (algumas variações aleatórias)
        weather_factor = np.random.uniform(0.7, 1.3)
        
        # Base de geração com todos os fatores
        base_generation = 25 * month_factor * weekday_factor * weather_factor
        
        # Adiciona um pouco de ruído
        energy = max(0, base_generation + np.random.normal(0, 3))
        
        data.append({
            'Data': date,
            'Energia Gerada (kWh)': round(energy, 2)
        })
    
    return pd.DataFrame(data)

# --- Simulação de funções de dados ---
def load_data():
    """Simula carregamento de dados da planilha"""
    return generate_sample_data()

def append_data(date, energy):
    """Simula salvamento de dados"""
    # Em um ambiente real, aqui salvaria na planilha
    return True

# --- Formulário de Cadastro ---
st.header("☀️ Registro de Geração")
with st.container():
    with st.form("entry_form", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            input_date = st.date_input("📅 Data da Geração", value=datetime.today())
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
                        st.balloons()
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
    with st.container():
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            years = sorted(df['Data'].dt.year.unique(), reverse=True)
            selected_year = st.selectbox("📅 Ano", options=years)
        with filter_col2:
            months = sorted(df[df['Data'].dt.year == selected_year]['Data'].dt.month.unique())
            month_names = {i: calendar.month_name[i] for i in range(1, 13)}
            selected_month_num = st.selectbox("📊 Mês", options=months, 
                                            format_func=lambda x: month_names.get(x, ''))

    filtered_df = df[(df['Data'].dt.year == selected_year) & 
                    (df['Data'].dt.month == selected_month_num)]
    
    if not filtered_df.empty:
        # --- Métricas ---
        total = filtered_df['Energia Gerada (kWh)'].sum()
        avg = filtered_df['Energia Gerada (kWh)'].mean()
        best_day = filtered_df.loc[filtered_df['Energia Gerada (kWh)'].idxmax()]
        worst_day = filtered_df.loc[filtered_df['Energia Gerada (kWh)'].idxmin()]
        
        st.header(f"📊 Análise de {month_names.get(selected_month_num, '')} de {selected_year}")
        
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        with metric_col1:
            st.metric("🔋 Total no Mês", f"{total:,.1f} kWh", help="Energia total gerada no mês")
        with metric_col2:
            st.metric("📈 Média Diária", f"{avg:,.1f} kWh", help="Média de geração por dia")
        with metric_col3:
            st.metric("⭐ Melhor Dia", f"{best_day['Energia Gerada (kWh)']:,.1f} kWh", 
                     delta=best_day['Data'].strftime('%d/%m'), help="Maior geração do mês")
        with metric_col4:
            st.metric("⚠️ Menor Dia", f"{worst_day['Energia Gerada (kWh)']:,.1f} kWh", 
                     delta=worst_day['Data'].strftime('%d/%m'), delta_color="inverse", 
                     help="Menor geração do mês")

        # --- Gráfico de Produção Diária ---
        st.subheader("📊 Produção Diária")
        
        fig_daily = px.bar(
            filtered_df,
            x='Data',
            y='Energia Gerada (kWh)',
            title=f'Geração Diária - {month_names[selected_month_num]} {selected_year}',
            color='Energia Gerada (kWh)',
            color_continuous_scale='Viridis',
            hover_data={'Data': '|%d/%m/%Y'}
        )
        
        fig_daily.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Inter", size=12),
            title_font_size=16,
            xaxis_title="Data",
            yaxis_title="Energia (kWh)",
            showlegend=False,
            height=400
        )
        
        fig_daily.update_xaxis(
            showgrid=True, 
            gridcolor='rgba(128,128,128,0.2)',
            tickformat='%d/%m'
        )
        fig_daily.update_yaxis(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
        
        st.plotly_chart(fig_daily, use_container_width=True)

        # --- Gráfico de Produção Acumulada ---
        st.subheader("📈 Geração Acumulada no Mês")
        
        filtered_df_sorted = filtered_df.sort_values('Data')
        filtered_df_sorted['Acumulado'] = filtered_df_sorted['Energia Gerada (kWh)'].cumsum()
        
        fig_cumulative = go.Figure()
        
        # Área preenchida
        fig_cumulative.add_trace(go.Scatter(
            x=filtered_df_sorted['Data'],
            y=filtered_df_sorted['Acumulado'],
            mode='lines',
            fill='tonexty',
            fillcolor='rgba(16, 185, 129, 0.3)',
            line=dict(color='#10b981', width=3),
            name='Acumulado',
            hovertemplate='<b>%{x|%d/%m/%Y}</b><br>Acumulado: %{y:.1f} kWh<extra></extra>'
        ))
        
        # Pontos
        fig_cumulative.add_trace(go.Scatter(
            x=filtered_df_sorted['Data'],
            y=filtered_df_sorted['Acumulado'],
            mode='markers',
            marker=dict(color='#10b981', size=6, line=dict(color='white', width=2)),
            name='Pontos',
            showlegend=False,
            hovertemplate='<b>%{x|%d/%m/%Y}</b><br>Acumulado: %{y:.1f} kWh<extra></extra>'
        ))
        
        fig_cumulative.update_layout(
            title=f'Energia Acumulada - {month_names[selected_month_num]} {selected_year}',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Inter", size=12),
            title_font_size=16,
            xaxis_title="Data",
            yaxis_title="Energia Acumulada (kWh)",
            showlegend=False,
            height=400
        )
        
        fig_cumulative.update_xaxis(
            showgrid=True, 
            gridcolor='rgba(128,128,128,0.2)',
            tickformat='%d/%m'
        )
        fig_cumulative.update_yaxis(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
        
        st.plotly_chart(fig_cumulative, use_container_width=True)

    # --- Análise Anual ---
    year_df_filtered = df[df['Data'].dt.year == selected_year].copy()
    if not year_df_filtered.empty:
        st.divider()
        st.header(f"📅 Resumo Anual de {selected_year}")
        
        # Resumo por mês
        monthly_summary = year_df_filtered.groupby(
            year_df_filtered['Data'].dt.month
        )['Energia Gerada (kWh)'].agg(['sum', 'mean', 'count']).reset_index()
        monthly_summary.rename(columns={'Data': 'Mês'}, inplace=True)
        monthly_summary['Nome Mês'] = monthly_summary['Mês'].apply(
            lambda m: calendar.month_abbr[m]
        )
        
        # Gráfico Mensal
        fig_monthly = px.bar(
            monthly_summary,
            x='Nome Mês',
            y='sum',
            title=f'Geração Mensal - {selected_year}',
            color='sum',
            color_continuous_scale='Plasma',
            labels={'sum': 'Total (kWh)', 'Nome Mês': 'Mês'}
        )
        
        fig_monthly.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Inter", size=12),
            title_font_size=16,
            showlegend=False,
            height=400
        )
        
        fig_monthly.update_xaxis(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
        fig_monthly.update_yaxis(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
        
        st.plotly_chart(fig_monthly, use_container_width=True)
        
        # --- Heatmap de Geração (Calendário) ---
        st.subheader(f"🗓️ Calendário de Geração - {selected_year}")
        
        # Preparar dados para heatmap
        year_df_filtered['day_of_year'] = year_df_filtered['Data'].dt.dayofyear
        year_df_filtered['week'] = year_df_filtered['Data'].dt.isocalendar().week
        year_df_filtered['day_of_week'] = year_df_filtered['Data'].dt.dayofweek
        year_df_filtered['month_abbr'] = year_df_filtered['Data'].dt.month.apply(
            lambda x: calendar.month_abbr[x]
        )
        
        # Criar matriz para heatmap
        weeks = range(1, 54)  # Máximo de semanas em um ano
        days = range(7)  # Dias da semana (0=Segunda, 6=Domingo)
        
        heatmap_data = np.full((7, 53), np.nan)  # 7 dias x 53 semanas
        
        for _, row in year_df_filtered.iterrows():
            week = min(row['week'] - 1, 52)  # Ajusta para índice 0-based
            day = row['day_of_week']
            heatmap_data[day, week] = row['Energia Gerada (kWh)']
        
        # Criar heatmap com Plotly
        day_labels = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
        
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            colorscale='Greens',
            showscale=True,
            colorbar=dict(title="kWh"),
            hoverongaps=False,
            hovertemplate='Semana %{x}<br>%{y}<br>Geração: %{z:.1f} kWh<extra></extra>'
        ))
        
        fig_heatmap.update_layout(
            title=f'Calendário de Geração - {selected_year}',
            xaxis_title="Semanas do Ano",
            yaxis_title="Dias da Semana",
            yaxis=dict(
                tickmode='array',
                tickvals=list(range(7)),
                ticktext=day_labels
            ),
            height=200,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Inter", size=12),
            title_font_size=16
        )
        
        st.plotly_chart(fig_heatmap, use_container_width=True)

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: var(--text-secondary); margin-top: 2rem;">
    <p>🌱 <strong>SolarAnalytics Pro</strong> - Desenvolvido para otimizar sua geração de energia solar</p>
    <p><em>Dados atualizados em tempo real | Última atualização: {}</em></p>
</div>
""".format(datetime.now().strftime("%d/%m/%Y às %H:%M")), unsafe_allow_html=True)
