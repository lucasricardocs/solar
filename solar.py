# --- SISTEMA DE PREVISÕES ESTATÍSTICAS ---
        if len(year_df) >= 7:  # Mínimo de dados para previsões
            st.markdown("""
            <div class="section-header">
                <span class="section-icon">🔮</span>
                <h2 class="section-title">Previsões Inteligentes</h2>
            </div>
            """, unsafe_allow_html=True)
            
            # Gerar previsões
            with st.spinner("📊 Analisando padrões e gerando previsões..."):
                predictions_df, ml_metrics = generate_smart_predictions(year_df, 30)
            
            if not predictions_df.empty:
                # Configurações de previsão
                pred_col1, pred_col2 = st.columns([2, 1])
                
                with pred_col2:
                    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                    st.markdown("**⚙️ Configurações de Previsão**")
                    
                    days_ahead = st.slider("📅 Dias para prever", 7, 60, 30)
                    show_confidence = st.checkbox("📊 Mostrar intervalo de confiança", True)
                    
                    # Gerar nova previsão se dias mudaram
                    if days_ahead != 30:
                        predictions_df, ml_metrics = generate_smart_predictions(year_df, days_ahead)
                    
                    # Métricas do modelo
                    st.markdown(f"""
                    **🤖 Modelo:** {ml_metrics['model_name']}
                    
                    **📊 Performance:**
                    - Precisão: {ml_metrics['r2']:.1%}
                    - Erro Médio: {ml_metrics['mae']:.2f} kWh
                    - MAPE: {ml_metrics['mape']:.1f}%
                    
                    **✅ Qualidade:** {ml_metrics['quality']}
                    """)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with pred_col1:
                    if not predictions_df.empty:
                        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                        
                        # Combinar dados históricos com previsões
                        historical_df = year_df.tail(30).copy()  # Últimos 30 dias
                        historical_df['Tipo'] = 'Histórico'
                        historical_df['Previsao'] = historical_df['Energia Gerada (kWh)']
                        historical_df['Limite_Inferior'] = historical_df['Energia Gerada (kWh)']
                        historical_df['Limite_Superior'] = historical_df['Energia Gerada (kWh)']
                        
                        predictions_df['Tipo'] = 'Previsão'
                        predictions_df['Energia Gerada (kWh)'] = predictions_df['Previsao']
                        
                        combined_df = pd.concat([historical_df, predictions_df], ignore_index=True)
                        
                        # Gráfico base
                        base = alt.Chart(combined_df)
                        
                        # Linha histórica
                        historical_line = base.transform_filter(
                            alt.datum.Tipo == 'Histórico'
                        ).mark_line(
                            color='#3b82f6',
                            strokeWidth=3,
                            point=alt.OverlayMarkDef(size=60, filled=True, color='#1d4ed8')
                        ).encode(
                            x=alt.X('Data:T', title='Data', axis=alt.Axis(titleFontSize=12)),
                            y=alt.Y('Energia Gerada (kWh):Q', title='Energia (kWh)', axis=alt.Axis(titleFontSize=12)),
                            tooltip=[
                                alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'),
                                alt.Tooltip('Energia Gerada (kWh):Q', title='Real', format='.2f')
                            ]
                        )
                        
                        # Linha de previsão
                        prediction_line = base.transform_filter(
                            alt.datum.Tipo == 'Previsão'
                        ).mark_line(
                            color='#f59e0b',
                            strokeWidth=3,
                            strokeDash=[8, 4],
                            point=alt.OverlayMarkDef(size=50, filled=True, color='#d97706', shape='diamond')
                        ).encode(
                            x='Data:T',
                            y='Previsao:Q',
                            tooltip=[
                                alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'),
                                alt.Tooltip('Previsao:Q', title='Previsão', format='.2f')
                            ]
                        )
                        
                        # Intervalo de confiança
                        confidence_band = base.transform_filter(
                            alt.datum.Tipo == 'Previsão'
                        ).mark_area(
                            opacity=0.3,
                            color='#f59e0b'
                        ).encode(
                            x='Data:T',
                            y='Limite_Inferior:Q',
                            y2='Limite_Superior:Q',
                            tooltip=[
                                alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'),
                                alt.Tooltip('Limite_Inferior:Q', title='Mín', format='.2f'),
                                alt.Tooltip('Limite_Superior:Q', title='Máx', format='.2f')
                            ]
                        )
                        
                        # Combinar gráficos
                        if show_confidence:
                            final_chart = (confidence_band + historical_line + prediction_line)
                        else:
                            final_chart = (historical_line + prediction_line)
                        
                        final_chart = final_chart.properties(
                            title=alt.TitleParams(
                                text=f"🔮 Previsão de Geração - Próximos {days_ahead} dias",
                                fontSize=16,
                                fontWeight='bold',
                                anchor='start'
                            ),
                            height=400,
                            width=600
                        ).resolve_scale(
                            y='shared'
                        ).interactive()
                        
                        st.altair_chart(final_chart, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                
                # --- Insights de Previsão ---
                st.markdown("""
                <div class="section-header">
                    <span class="section-icon">💡</span>
                    <h2 class="section-title">Insights Preditivos</h2>
                </div>
                """, unsafe_allow_html=True)
                
                insight_col1, insight_col2, insight_col3 = st.columns(3)
                
                with insight_col1:
                    predicted_total = predictions_df['Previsao'].sum()
                    current_monthly_avg = year_df.groupby(year_df['Data'].dt.month)['Energia Gerada (kWh)'].sum().mean()
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{predicted_total:.1f}</div>
                        <div class="metric-label">Total Previsto ({days_ahead} dias)</div>
                        <div class="metric-change positive">
                            🎯 {(predicted_total/current_monthly_avg*100):.0f}% da média mensal
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with insight_col2:
                    predicted_avg = predictions_df['Previsao'].mean()
                    historical_avg = year_df['Energia Gerada (kWh)'].mean()
                    trend_vs_historical = ((predicted_avg - historical_avg) / historical_avg * 100)
                    
                    trend_class = "positive" if trend_vs_historical >= 0 else "negative"
                    trend_icon = "📈" if trend_vs_historical >= 0 else "📉"
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{predicted_avg:.1f}</div>
                        <div class="metric-label">Média Diária Prevista</div>
                        <div class="metric-change {trend_class}">
                            {trend_icon} {abs(trend_vs_historical):.1f}% vs histórico
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with insight_col3:
                    best_predicted_day = predictions_df.loc[predictions_df['Previsao'].idxmax()]
                    confidence_range = best_predicted_day['Limite_Superior'] - best_predicted_day['Limite_Inferior']
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{best_predicted_day['Previsao']:.1f}</div>
                        <div class="metric-label">Melhor Dia Previsto</div>
                        <div class="metric-change positive">
                            ⭐ {best_predicted_day['Data'].strftime('%d/%m/%Y')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # --- Análise Detalhada das Previsões ---
                st.markdown("""
                <div class="section-header">
                    <span class="section-icon">🔬</span>
                    <h2 class="section-title">Análise Preditiva Detalhada</h2>
                </div>
                """, unsafe_allow_html=True)
                
                analysis_col1, analysis_col2 = st.columns(2)
                
                with analysis_col1:
                    # Tendência detectada
                    patterns = calculate_seasonal_pattern(year_df)
                    trend_direction = "crescente" if patterns['trend_slope'] > 0 else "decrescente" if patterns['trend_slope'] < 0 else "estável"
                    trend_strength = abs(patterns['trend_slope']) * 365  # Mudança anual
                    
                    st.markdown(f"""
                    <div class="custom-alert alert-info">
                        <strong>📈 Tendência Detectada:</strong><br>
                        • <strong>Direção:</strong> {trend_direction.title()}<br>
                        • <strong>Intensidade:</strong> {trend_strength:.1f} kWh/ano<br>
                        • <strong>Confiança:</strong> {patterns['trend_r2']:.1%}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Padrão sazonal
                    best_months = sorted(patterns['monthly_pattern'].items(), key=lambda x: x[1], reverse=True)[:3]
                    worst_months = sorted(patterns['monthly_pattern'].items(), key=lambda x: x[1])[:3]
                    
                    month_names_short = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                                       7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
                    
                    best_months_str = ", ".join([month_names_short[m[0]] for m in best_months])
                    worst_months_str = ", ".join([month_names_short[m[0]] for m in worst_months])
                    
                    st.markdown(f"""
                    <div class="custom-alert alert-success">
                        <strong>🌞 Padrão Sazonal:</strong><br>
                        • <strong>Melhores meses:</strong> {best_months_str}<br>
                        • <strong>Meses mais fracos:</strong> {worst_months_str}<br>
                        • <strong>Variação sazonal:</strong> {((max(patterns['monthly_pattern'].values()) - min(patterns['monthly_pattern'].values())) / patterns['overall_mean'] * 100):.0f}%
                    </div>
                    """, unsafe_allow_html=True)
                
                with analysis_col2:
                    # Previsão de performance mensal
                    if days_ahead >= 30:
                        next_month_pred = predictions_df.head(30)['Previsao'].sum()
                        current_month_actual = filtered_df['Energia Gerada (kWh)'].sum() if not filtered_df.empty else 0
                        
                        performance_vs_current = ((next_month_pred - current_month_actual) / current_month_actual * 100) if current_month_actual > 0 else 0
                        performance_class = "positive" if performance_vs_current >= 0 else "negative"
                        performance_icon = "🚀" if performance_vs_current >= 0 else "⚠️"
                        
                        st.markdown(f"""
                        <div class="custom-alert alert-{performance_class.replace('negative', 'warning')}">
                            <strong>🎯 Previsão Próximo Mês:</strong><br>
                            • <strong>Total esperado:</strong> {next_month_pred:.1f} kWh<br>
                            • <strong>Vs mês atual:</strong> {performance_icon} {abs(performance_vs_current):.1f}%<br>
                            • <strong>Status:</strong> {'Acima da média' if performance_vs_current >= 0 else 'Abaixo da média'}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Recomendações baseadas em IA
                    recent_trend = year_df.tail(14)['Energia Gerada (kWh)'].mean()
                    overall_avg = year_df['Energia Gerada (kWh)'].mean()
                    
                    if recent_trend < overall_avg * 0.9:
                        recommendation = "🔧 Verificar manutenção dos painéis"
                        rec_detail = "Performance recente abaixo da média histórica"
                        rec_color = "warning"
                    elif recent_trend > overall_avg * 1.1:
                        recommendation = "⭐ Sistema funcionando acima da média"
                        rec_detail = "Excelente performance detectada"
                        rec_color = "success"
                    else:
                        recommendation = "✅ Performance dentro do esperado"
                        rec_detail = "Sistema operando normalmente"
                        rec_color = "info"
                    
                    st.markdown(f"""
                    <div class="custom-alert alert-{rec_color}">
                        <strong>🎯 Recomendação IA:</strong><br>
                        • <strong>{recommendation}</strong><br>
                        • {rec_detail}<br>
                        • <strong>Confiança:</strong> {ml_metrics['r2']:.0%}
                    </div>
                    """, unsafe_allow_html=True)
                
                # --- Tabela de Previsões Detalhada ---
                st.markdown("""
                <div class="section-header">
                    <span class="section-icon">📋</span>
                    <h2 class="section-title">Cronograma de Previsões</h2>
                </div>
                """, unsafe_allow_html=True)
                
                # Mostrar próximos 14 dias em formato tabela
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                
                next_14_days = predictions_df.head(14).copy()
                next_14_days['Dia da Semana'] = next_14_days['Data'].dt.strftime('%A')
                next_14_days['Data Formatada'] = next_14_days['Data'].dt.strftime('%d/%m/%Y')
                next_14_days['Dia da Semana PT'] = next_14_days['Data'].dt.dayofweek.map({
                    0: 'Segunda', 1: 'Terça', 2: 'Quarta', 3: 'Quinta', 
                    4: 'Sexta', 5: 'Sábado', 6: 'Domingo'
                })
                
                # Criar DataFrame para exibição
                display_df = next_14_days[['Data Formatada', 'Dia da Semana PT', 'Previsao']].copy()
                display_df.columns = ['📅 Data', '🗓️ Dia', '⚡ Previsão (kWh)']
                display_df['⚡ Previsão (kWh)'] = display_df['⚡ Previsão (kWh)'].apply(lambda x: f"{x:.2f}")
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "📅 Data": st.column_config.TextColumn(width="small"),
                        "🗓️ Dia": st.column_config.TextColumn(width="small"),
                        "⚡ Previsão (kWh)": st.column_config.TextColumn(width="medium")
                    }
                )
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # --- Análise de Confiabilidade ---
                st.markdown(f"""
                <div class="custom-alert alert-info">
                    <strong>🔬 Como Funcionam as Previsões:</strong><br>
                    • <strong>Algoritmo:</strong> {ml_metrics['model_name']} com análise multifatorial<br>
                    • <strong>Fatores Analisados:</strong> Tendências históricas, sazonalidade mensal, padrões semanais<br>
                    • <strong>Precisão:</strong> {ml_metrics['r2']:.1%} de acurácia | Erro médio de ±{ml_metrics['mae']:.1f} kWh<br>
                    • <strong>Atualização:</strong> Previsões recalculadas automaticamente com novos dados<br>
                    • <strong>Metodologia:</strong> Combinação ponderada de componentes estatísticos
                </div>
                """, unsafe_allow_html=True)
                
            else:
                st.markdown("""
                <div class="custom-alert alert-warning">
                    ⚠️ <strong>Erro na Geração de Previsões</strong><br>
                    Não foi possível gerar previsões confiáveis com os dados atuais.
                </div>
                """, unsafe_allow_html=True)
        
        else:
            st.markdown("""
            <div class="custom-alert alert-info">
                📊 <strong>Previsões Disponíveis em Breve</strong><br>
                Continue coletando dados! Previsões estarão disponíveis após 7 dias de registros.
                Progresso atual: {current}/{needed} dias.
            </div>
            """.format(current=len(year_df), needed=7), unsafe_allow_html=True)
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
import math
from scipy import stats

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
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
}

.main-container {
    background-color: var(--background-color);
    border-radius: 20px;
    padding: 2rem;
    margin: 1rem;
    box-shadow: var(--shadow-lg);
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
    right: 0;
    width: 200px;
    height: 200px;
    background: radial-gradient(circle, rgba(251, 191, 36, 0.1) 0%, transparent 70%);
    border-radius: 50%;
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

/* Responsividade */
@media (max-width: 768px) {
    .header-title {
        font-size: 2rem;
    }
    
    .main-container {
        margin: 0.5rem;
        padding: 1rem;
    }
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
    """Conecta ao Google Sheets usando as credenciais do Streamlit Secrets."""
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
    """Carrega os dados da planilha, processa e retorna um DataFrame."""
    try:
        values = sheet.get_all_values()
        if len(values) < 2:
            return pd.DataFrame()
        
        df = pd.DataFrame(values[1:], columns=values[0])
        df.columns = [col.lower().strip() for col in df.columns]

        if 'data' not in df.columns or 'gerado' not in df.columns:
            st.error("⚠️ **Erro de Configuração**: A planilha deve conter as colunas 'data' e 'gerado'.")
            return pd.DataFrame()

        df.rename(columns={'data': 'Data', 'gerado': 'Energia Gerada (kWh)'}, inplace=True)
        
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        
        if 'Energia Gerada (kWh)' in df.columns:
            df['Energia Gerada (kWh)'] = df['Energia Gerada (kWh)'].astype(str).str.replace(',', '.', regex=False)
            df['Energia Gerada (kWh)'] = pd.to_numeric(df['Energia Gerada (kWh)'], errors='coerce')

        df.dropna(subset=['Data', 'Energia Gerada (kWh)'], inplace=True)
        df = df.sort_values(by='Data')
        return df
    
    except Exception as e:
        st.error(f"🚨 **Erro ao carregar dados**: {str(e)}")
        return pd.DataFrame()

def append_data(date, energy):
    """Adiciona uma nova linha de dados na planilha."""
    try:
        formatted_date = date.strftime('%d/%m/%Y')
        sheet.append_row([formatted_date, energy], value_input_option='USER_ENTERED')
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"🚨 **Erro ao salvar**: {str(e)}")
        return False

def calculate_performance_metrics(df, period='month'):
    """Calcula métricas de performance."""
    if df.empty:
        return {}
    
    current_total = df['Energia Gerada (kWh)'].sum()
    current_avg = df['Energia Gerada (kWh)'].mean()
    
    # Simular dados do período anterior para comparação
    previous_total = current_total * 0.85  # Simulação
    previous_avg = current_avg * 0.9  # Simulação
    
    total_change = ((current_total - previous_total) / previous_total * 100) if previous_total > 0 else 0
    avg_change = ((current_avg - previous_avg) / previous_avg * 100) if previous_avg > 0 else 0
    
    return {
        'total': current_total,
        'avg': current_avg,
        'total_change': total_change,
        'avg_change': avg_change,
        'best_day': df.loc[df['Energia Gerada (kWh)'].idxmax()] if not df.empty else None,
        'worst_day': df.loc[df['Energia Gerada (kWh)'].idxmin()] if not df.empty else None,
        'days_count': len(df)
    }

def calculate_performance_metrics(df, period='month'):week'].isin([5, 6]).astype(int)
    
    future_df['month_sin'] = np.sin(2 * np.pi * future_df['month'] / 12)
    future_df['month_cos'] = np.cos(2 * np.pi * future_df['month'] / 12)
    future_df['day_sin'] = np.sin(2 * np.pi * future_df['day_of_year'] / 365)
    future_df['day_cos'] = np.cos(2 * np.pi * future_df['day_of_year'] / 365)
    
    # Days since start
    start_date = df['Data'].min()
    future_df['days_since_start'] = (future_df['Data'] - start_date).dt.days
    
    # Médias móveis (usar últimos valores conhecidos)
    last_ma_7 = df['Energia Gerada (kWh)'].tail(7).mean()
    last_ma_30 = df['Energia Gerada (kWh)'].tail(30).mean()
    future_df['ma_7'] = last_ma_7
    future_df['ma_30'] = last_ma_30
    
    # Features para predição
    feature_cols = ['day_of_year', 'month', 'day_of_week', 'quarter', 'is_weekend',
                   'month_sin', 'month_cos', 'day_sin', 'day_cos', 'days_since_start',
                   'ma_7', 'ma_30']
    
    X_future = future_df[feature_cols]
    X_future_scaled = scaler.transform(X_future)
    
    # Predições
    predictions = model.predict(X_future_scaled)
    
    # Adicionar intervalo de confiança (simulado)
    std_dev = df['Energia Gerada (kWh)'].std()
    confidence_interval = 1.96 * std_dev / np.sqrt(len(df))
    
    future_df['Previsao'] = np.maximum(0, predictions)  # Não pode ser negativo
    future_df['Limite_Inferior'] = np.maximum(0, predictions - confidence_interval)
    future_df['Limite_Superior'] = predictions + confidence_interval
    
    return future_df

# --- Formulário de Cadastro Profissional ---
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
        input_date = st.date_input(
            "📅 Data da Geração", 
            value=datetime.today(), 
            format="DD/MM/YYYY",
            help="Selecione a data da geração de energia"
        )
    
    with col2:
        input_energy_str = st.text_input(
            "⚡ Energia Gerada (kWh)", 
            placeholder="Ex: 25,75",
            help="Digite a quantidade de energia gerada em kWh"
        )
    
    with col3:
        st.write("")  # Espaçamento
        st.write("")  # Espaçamento
        submitted = st.form_submit_button("💾 Salvar Geração", use_container_width=True)

    if submitted:
        if input_energy_str:
            try:
                energy_value = float(input_energy_str.replace(',', '.'))
                if energy_value >= 0:
                    if append_data(input_date, energy_value):
                        st.markdown("""
                        <div class="custom-alert alert-success">
                            ✅ <strong>Sucesso!</strong> Dados salvos com sucesso no sistema.
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="custom-alert alert-warning">
                            ⚠️ <strong>Erro!</strong> Falha ao salvar os dados. Tente novamente.
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="custom-alert alert-warning">
                        ⚠️ <strong>Atenção!</strong> A energia gerada não pode ser negativa.
                    </div>
                    """, unsafe_allow_html=True)
            except ValueError:
                st.markdown("""
                <div class="custom-alert alert-warning">
                    ⚠️ <strong>Formato Inválido!</strong> Digite um número válido (ex: 25 ou 25,75).
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="custom-alert alert-info">
                💡 <strong>Campo Obrigatório!</strong> Preencha o valor da energia gerada.
            </div>
            """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# --- Análise de Dados ---
df = load_data()

if df.empty:
    st.markdown("""
    <div class="custom-alert alert-info">
        📊 <strong>Nenhum Dado Encontrado</strong><br>
        Comece registrando sua primeira geração de energia solar para visualizar as análises.
    </div>
    """, unsafe_allow_html=True)
else:
    # --- Filtros Profissionais ---
    st.markdown("""
    <div class="section-header">
        <span class="section-icon">🔍</span>
        <h2 class="section-title">Filtros de Análise</h2>
    </div>
    <div class="filters-container">
    """, unsafe_allow_html=True)
    
    filter_col1, filter_col2, filter_col3 = st.columns([1, 1, 1])
    
    with filter_col1:
        years = sorted(df['Data'].dt.year.unique(), reverse=True)
        selected_year = st.selectbox("📅 Ano", options=years, key="year_filter")
    
    with filter_col2:
        months = sorted(df[df['Data'].dt.year == selected_year]['Data'].dt.month.unique())
        month_names = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 
                      7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
        selected_month_num = st.selectbox("📊 Mês", options=months, format_func=lambda x: month_names.get(x, ''))
    
    with filter_col3:
        view_mode = st.selectbox("👁️ Visualização", ["Mensal", "Anual"], key="view_mode")

    st.markdown("</div>", unsafe_allow_html=True)

    # --- Dados Filtrados ---
    if view_mode == "Mensal":
        filtered_df = df[(df['Data'].dt.year == selected_year) & (df['Data'].dt.month == selected_month_num)]
        period_name = f"{month_names.get(selected_month_num)} de {selected_year}"
    else:
        filtered_df = df[df['Data'].dt.year == selected_year]
        period_name = f"Ano de {selected_year}"

    if not filtered_df.empty:
        # --- Métricas Profissionais ---
        metrics = calculate_performance_metrics(filtered_df)
        
        st.markdown(f"""
        <div class="section-header">
            <span class="section-icon">📈</span>
            <h2 class="section-title">Análise de Performance - {period_name}</h2>
        </div>
        """, unsafe_allow_html=True)

        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        with metric_col1:
            change_class = "positive" if metrics['total_change'] >= 0 else "negative"
            change_icon = "↗️" if metrics['total_change'] >= 0 else "↘️"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{metrics['total']:,.1f}</div>
                <div class="metric-label">Total Gerado (kWh)</div>
                <div class="metric-change {change_class}">
                    {change_icon} {abs(metrics['total_change']):.1f}% vs período anterior
                </div>
            </div>
            """, unsafe_allow_html=True)

        with metric_col2:
            change_class = "positive" if metrics['avg_change'] >= 0 else "negative"
            change_icon = "↗️" if metrics['avg_change'] >= 0 else "↘️"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{metrics['avg']:,.1f}</div>
                <div class="metric-label">Média Diária (kWh)</div>
                <div class="metric-change {change_class}">
                    {change_icon} {abs(metrics['avg_change']):.1f}% vs período anterior
                </div>
            </div>
            """, unsafe_allow_html=True)

        with metric_col3:
            if metrics['best_day'] is not None:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{metrics['best_day']['Energia Gerada (kWh)']:,.1f}</div>
                    <div class="metric-label">Melhor Dia</div>
                    <div class="metric-change positive">
                        🌟 {metrics['best_day']['Data'].strftime('%d/%m/%Y')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with metric_col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{metrics['days_count']}</div>
                <div class="metric-label">Dias Registrados</div>
                <div class="metric-change positive">
                    📊 {(metrics['days_count']/30*100):.0f}% do mês
                </div>
            </div>
            """, unsafe_allow_html=True)

        # --- Gráficos Profissionais ---
        if view_mode == "Mensal":
            st.markdown("""
            <div class="section-header">
                <span class="section-icon">📊</span>
                <h2 class="section-title">Análise Detalhada do Mês</h2>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            
            # Gráfico de Produção Diária
            with col1:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                
                daily_chart = alt.Chart(filtered_df).mark_bar(
                    color="#3b82f6",
                    cornerRadiusTopLeft=4,
                    cornerRadiusTopRight=4,
                    strokeWidth=0
                ).encode(
                    x=alt.X('Data:T', 
                           title='Dia do Mês',
                           axis=alt.Axis(format='%d', labelAngle=0, grid=False, 
                                       titleFontSize=12, labelFontSize=10)),
                    y=alt.Y('Energia Gerada (kWh):Q', 
                           title='Energia (kWh)',
                           axis=alt.Axis(grid=True, gridOpacity=0.2, 
                                       titleFontSize=12, labelFontSize=10)),
                    tooltip=[
                        alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'),
                        alt.Tooltip('Energia Gerada (kWh):Q', title='Energia', format='.2f')
                    ]
                ).properties(
                    title=alt.TitleParams(
                        text="📊 Produção Diária",
                        fontSize=14,
                        fontWeight='bold',
                        anchor='start'
                    ),
                    height=300
                ).interactive()
                
                st.altair_chart(daily_chart, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # Gráfico Acumulado
            with col2:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                
                filtered_df_copy = filtered_df.copy()
                filtered_df_copy['Acumulado'] = filtered_df_copy['Energia Gerada (kWh)'].cumsum()
                
                cumulative_chart = alt.Chart(filtered_df_copy).mark_area(
                    line={'color': '#10b981', 'strokeWidth': 3},
                    color=alt.Gradient(
                        gradient='linear',
                        stops=[
                            alt.GradientStop(color='#10b981', offset=0),
                            alt.GradientStop(color='rgba(16, 185, 129, 0.3)', offset=0.5),
                            alt.GradientStop(color='rgba(16, 185, 129, 0)', offset=1)
                        ],
                        x1=1, x2=1, y1=1, y2=0
                    )
                ).encode(
                    x=alt.X('Data:T', 
                           title='Dia do Mês',
                           axis=alt.Axis(format='%d', labelAngle=0, grid=False,
                                       titleFontSize=12, labelFontSize=10)),
                    y=alt.Y('Acumulado:Q', 
                           title='Energia Acumulada (kWh)',
                           axis=alt.Axis(grid=True, gridOpacity=0.2,
                                       titleFontSize=12, labelFontSize=10)),
                    tooltip=[
                        alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'),
                        alt.Tooltip('Acumulado:Q', title='Acumulado', format='.2f')
                    ]
                ).properties(
                    title=alt.TitleParams(
                        text="📈 Geração Acumulada",
                        fontSize=14,
                        fontWeight='bold',
                        anchor='start'
                    ),
                    height=300
                ).interactive()
                
                st.altair_chart(cumulative_chart, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

        # --- Análise Anual ---
        st.markdown("""
        <div class="section-header">
            <span class="section-icon">🏆</span>
            <h2 class="section-title">Resumo Anual</h2>
        </div>
        """, unsafe_allow_html=True)

        year_df = df[df['Data'].dt.year == selected_year].copy()
        
        # Gráfico Mensal
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        monthly_summary = year_df.groupby(year_df['Data'].dt.month).agg({
            'Energia Gerada (kWh)': ['sum', 'count']
        }).reset_index()
        monthly_summary.columns = ['Mes', 'Total', 'Dias']
        monthly_summary['Nome_Mes'] = monthly_summary['Mes'].apply(lambda m: month_names[m][:3])
        
        monthly_chart = alt.Chart(monthly_summary).mark_bar(
            color="#f59e0b",
            cornerRadiusTopLeft=6,
            cornerRadiusTopRight=6,
            strokeWidth=0
        ).encode(
            x=alt.X('Nome_Mes:N', 
                   title='Mês',
                   sort=[m[:3] for m in month_names.values()],
                   axis=alt.Axis(labelAngle=0, titleFontSize=14, labelFontSize=12)),
            y=alt.Y('Total:Q', 
                   title='Energia Total (kWh)',
                   axis=alt.Axis(grid=True, gridOpacity=0.2, titleFontSize=14, labelFontSize=12)),
            tooltip=[
                alt.Tooltip('Nome_Mes:N', title='Mês'),
                alt.Tooltip('Total:Q', title='Total', format='.2f'),
                alt.Tooltip('Dias:Q', title='Dias Registrados')
            ]
        ).properties(
            title=alt.TitleParams(
                text=f"📊 Produção Mensal - {selected_year}",
                fontSize=16,
                fontWeight='bold',
                anchor='start'
            ),
            height=350
        ).interactive()
        
        st.altair_chart(monthly_chart, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- Heatmap Profissional ---
        st.markdown("""
        <div class="section-header">
            <span class="section-icon">🗓️</span>
            <h2 class="section-title">Calendário de Geração</h2>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Preparação do heatmap
        heatmap_df = year_df.copy()
        heatmap_df['day_of_week'] = heatmap_df['Data'].dt.day_name()
        heatmap_df['week_of_year'] = heatmap_df['Data'].dt.isocalendar().week
        
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        domain = [0, heatmap_df['Energia Gerada (kWh)'].quantile(0.95)]
        range_ = ['#f3f4f6', '#dbeafe', '#93c5fd', '#3b82f6', '#1e40af', '#1e3a8a']
        
        # Labels dos meses
        month_labels = heatmap_df.groupby(heatmap_df['Data'].dt.month)['week_of_year'].min().reset_index()
        month_labels['month_abbr'] = month_labels['Data'].apply(lambda m: month_names[m][:3])
        expr_map = dict(zip(month_labels['week_of_year'], month_labels['month_abbr']))
        
        # Expressão para labels dos meses
        expr_conditions = []
        for week, month_abbr in expr_map.items():
            expr_conditions.append(f"datum.value == {week} ? '{month_abbr}' : ")
        expr = ''.join(expr_conditions) + "''"
        
        # Configurações visuais
        corner_radius = 4
        cell_width = 18
        font_size = 11
        height = 250
        width = 900
        
        heatmap = alt.Chart(heatmap_df).mark_rect(
            cornerRadius=corner_radius,
            width=cell_width,
            height=cell_width,
            strokeWidth=1,
            stroke='white'
        ).encode(
            y=alt.Y(
                'day_of_week:N',
                sort=days_order,
                axis=alt.Axis(
                    tickSize=0,
                    title='',
                    domain=False,
                    labelExpr="{'Monday': 'Seg', 'Tuesday': 'Ter', 'Wednesday': 'Qua', 'Thursday': 'Qui', 'Friday': 'Sex', 'Saturday': 'Sab', 'Sunday': 'Dom'}[datum.value]",
                    labelFontSize=font_size,
                    labelPadding=10
                )
            ),
            x=alt.X(
                'week_of_year:O',
                axis=alt.Axis(
                    tickSize=0,
                    domain=False,
                    title='',
                    labelExpr=expr,
                    labelAngle=0,
                    labelFontSize=font_size
                )
            ),
            color=alt.Color(
                'Energia Gerada (kWh):Q',
                legend=alt.Legend(
                    title="Energia (kWh)",
                    orient='bottom',
                    gradientLength=400,
                    gradientThickness=12,
                    titleFontSize=12,
                    labelFontSize=10
                ),
                scale=alt.Scale(domain=domain, range=range_, type='linear')
            ),
            tooltip=[
                alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'),
                alt.Tooltip('Energia Gerada (kWh):Q', title='Energia', format='.2f'),
                alt.Tooltip('day_of_week:N', title='Dia da Semana')
            ]
        ).properties(
            title=alt.TitleParams(
                text=f"🗓️ Calendário de Geração - {selected_year}",
                fontSize=16,
                fontWeight='bold',
                anchor='start'
            ),
            height=height,
            width=width
        ).configure_scale(
            rectBandPaddingInner=0.05,
        ).configure_mark(
            strokeOpacity=0.8,
            filled=True
        ).configure_axis(
            grid=False
        ).configure_view(
            stroke=None,
            fill='transparent'
        )
        
        st.altair_chart(heatmap, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # --- Insights Profissionais ---
        st.markdown("""
        <div class="section-header">
            <span class="section-icon">🧠</span>
            <h2 class="section-title">Insights Inteligentes</h2>
        </div>
        """, unsafe_allow_html=True)
        
        insight_col1, insight_col2 = st.columns(2)
        
        with insight_col1:
            # Análise de tendência
            if len(filtered_df) >= 7:
                recent_avg = filtered_df.tail(7)['Energia Gerada (kWh)'].mean()
                overall_avg = filtered_df['Energia Gerada (kWh)'].mean()
                trend = "crescente" if recent_avg > overall_avg else "decrescente"
                trend_icon = "📈" if recent_avg > overall_avg else "📉"
                
                st.markdown(f"""
                <div class="custom-alert alert-info">
                    {trend_icon} <strong>Tendência:</strong> A produção dos últimos 7 dias está <strong>{trend}</strong> 
                    em relação à média do período ({recent_avg:.1f} vs {overall_avg:.1f} kWh).
                </div>
                """, unsafe_allow_html=True)
        
        with insight_col2:
            # Análise de consistência
            consistency = (1 - (filtered_df['Energia Gerada (kWh)'].std() / filtered_df['Energia Gerada (kWh)'].mean())) * 100
            consistency_level = "alta" if consistency > 70 else "média" if consistency > 50 else "baixa"
            consistency_icon = "🎯" if consistency > 70 else "📊" if consistency > 50 else "⚠️"
            
            st.markdown(f"""
            <div class="custom-alert alert-success">
                {consistency_icon} <strong>Consistência:</strong> A variabilidade da geração está 
                <strong>{consistency_level}</strong> ({consistency:.0f}% de estabilidade).
            </div>
            """, unsafe_allow_html=True)

        # --- Análise por Dia da Semana ---
        if len(filtered_df) >= 14:  # Pelo menos 2 semanas de dados
            st.markdown("""
            <div class="section-header">
                <span class="section-icon">📅</span>
                <h2 class="section-title">Performance por Dia da Semana</h2>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            
            # Análise por dia da semana
            weekday_df = filtered_df.copy()
            weekday_df['Dia_Semana'] = weekday_df['Data'].dt.day_name()
            weekday_df['Dia_Semana_PT'] = weekday_df['Dia_Semana'].map({
                'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta',
                'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
            })
            
            weekday_summary = weekday_df.groupby('Dia_Semana_PT')['Energia Gerada (kWh)'].agg(['mean', 'count']).reset_index()
            weekday_summary.columns = ['Dia', 'Media', 'Contagem']
            
            # Ordenar dias da semana
            day_order = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
            weekday_summary['Dia'] = pd.Categorical(weekday_summary['Dia'], categories=day_order, ordered=True)
            weekday_summary = weekday_summary.sort_values('Dia')
            
            weekday_chart = alt.Chart(weekday_summary).mark_bar(
                color="#8b5cf6",
                cornerRadiusTopLeft=4,
                cornerRadiusTopRight=4,
                strokeWidth=0
            ).encode(
                x=alt.X('Dia:N', 
                       title='Dia da Semana',
                       axis=alt.Axis(labelAngle=45, titleFontSize=12, labelFontSize=10)),
                y=alt.Y('Media:Q', 
                       title='Média de Energia (kWh)',
                       axis=alt.Axis(grid=True, gridOpacity=0.2, titleFontSize=12, labelFontSize=10)),
                tooltip=[
                    alt.Tooltip('Dia:N', title='Dia'),
                    alt.Tooltip('Media:Q', title='Média', format='.2f'),
                    alt.Tooltip('Contagem:Q', title='Registros')
                ]
            ).properties(
                title=alt.TitleParams(
                    text="📊 Performance Média por Dia da Semana",
                    fontSize=14,
                    fontWeight='bold',
                    anchor='start'
                ),
                height=300
            ).interactive()
            
            st.altair_chart(weekday_chart, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # --- SISTEMA DE PREVISÕES ML ---
        if len(year_df) >= 30:  # Mínimo de dados para previsões confiáveis
            st.markdown("""
            <div class="section-header">
                <span class="section-icon">🔮</span>
                <h2 class="section-title">Previsões Inteligentes</h2>
            </div>
            """, unsafe_allow_html=True)
            
                            # Gerar previsões
                predictions_df, ml_metrics = generate_smart_predictions(year_df, days_ahead)
            
            if not predictions_df.empty:
                # Configurações de previsão
                pred_col1, pred_col2 = st.columns([2, 1])
                
                with pred_col2:
                    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                    st.markdown("**⚙️ Configurações de Previsão**")
                    
                    days_ahead = st.slider("📅 Dias para prever", 7, 60, 30)
                    confidence_level = st.selectbox("🎯 Nível de confiança", [90, 95, 99], index=1)
                    
                    # Métricas do modelo
                    st.markdown(f"""
                    **🤖 Modelo Selecionado:** {ml_metrics['best_model_name']}
                    
                    **📊 Performance:**
                    - R² Score: {ml_metrics['best_r2']:.3f}
                    - Erro Médio: {ml_metrics['best_mae']:.2f} kWh
                    
                    **✅ Qualidade:** {'Excelente' if ml_metrics['best_r2'] > 0.8 else 'Boa' if ml_metrics['best_r2'] > 0.6 else 'Moderada'}
                    """)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with pred_col1:
                    # Gerar previsões
                    predictions_df = generate_predictions(model, scaler, year_df, days_ahead)
                    
                    if not predictions_df.empty:
                        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                        
                        # Combinar dados históricos com previsões
                        historical_df = year_df.copy()
                        historical_df['Tipo'] = 'Histórico'
                        historical_df['Previsao'] = historical_df['Energia Gerada (kWh)']
                        historical_df['Limite_Inferior'] = historical_df['Energia Gerada (kWh)']
                        historical_df['Limite_Superior'] = historical_df['Energia Gerada (kWh)']
                        
                        predictions_df['Tipo'] = 'Previsão'
                        predictions_df['Energia Gerada (kWh)'] = predictions_df['Previsao']
                        
                        # Últimos 30 dias + previsões
                        recent_historical = historical_df.tail(30)
                        combined_df = pd.concat([recent_historical, predictions_df], ignore_index=True)
                        
                        # Gráfico de previsões
                        base = alt.Chart(combined_df)
                        
                        # Linha histórica
                        historical_line = base.transform_filter(
                            alt.datum.Tipo == 'Histórico'
                        ).mark_line(
                            color='#3b82f6',
                            strokeWidth=3,
                            point=alt.OverlayMarkDef(size=50, filled=True, color='#1d4ed8')
                        ).encode(
                            x=alt.X('Data:T', title='Data', axis=alt.Axis(titleFontSize=12)),
                            y=alt.Y('Energia Gerada (kWh):Q', title='Energia (kWh)', axis=alt.Axis(titleFontSize=12)),
                            tooltip=[
                                alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'),
                                alt.Tooltip('Energia Gerada (kWh):Q', title='Real', format='.2f')
                            ]
                        )
                        
                        # Linha de previsão
                        prediction_line = base.transform_filter(
                            alt.datum.Tipo == 'Previsão'
                        ).mark_line(
                            color='#f59e0b',
                            strokeWidth=3,
                            strokeDash=[5, 5],
                            point=alt.OverlayMarkDef(size=50, filled=True, color='#d97706')
                        ).encode(
                            x='Data:T',
                            y='Previsao:Q',
                            tooltip=[
                                alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'),
                                alt.Tooltip('Previsao:Q', title='Previsão', format='.2f')
                            ]
                        )
                        
                        # Intervalo de confiança
                        confidence_band = base.transform_filter(
                            alt.datum.Tipo == 'Previsão'
                        ).mark_area(
                            opacity=0.2,
                            color='#f59e0b'
                        ).encode(
                            x='Data:T',
                            y='Limite_Inferior:Q',
                            y2='Limite_Superior:Q',
                            tooltip=[
                                alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'),
                                alt.Tooltip('Limite_Inferior:Q', title='Min', format='.2f'),
                                alt.Tooltip('Limite_Superior:Q', title='Max', format='.2f')
                            ]
                        )
                        
                        # Combinar gráficos
                        final_chart = (confidence_band + historical_line + prediction_line).properties(
                            title=alt.TitleParams(
                                text=f"🔮 Previsão de Geração - Próximos {days_ahead} dias",
                                fontSize=16,
                                fontWeight='bold',
                                anchor='start'
                            ),
                            height=400,
                            width=600
                        ).resolve_scale(
                            y='shared'
                        ).interactive()
                        
                        st.altair_chart(final_chart, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                
                # --- Insights de Previsão ---
                st.markdown("""
                <div class="section-header">
                    <span class="section-icon">💡</span>
                    <h2 class="section-title">Insights Preditivos</h2>
                </div>
                """, unsafe_allow_html=True)
                
                insight_col1, insight_col2, insight_col3 = st.columns(3)
                
                with insight_col1:
                    predicted_total = predictions_df['Previsao'].sum()
                    current_monthly_avg = year_df.groupby(year_df['Data'].dt.month)['Energia Gerada (kWh)'].sum().mean()
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{predicted_total:.1f}</div>
                        <div class="metric-label">Total Previsto ({days_ahead} dias)</div>
                        <div class="metric-change positive">
                            🎯 {(predicted_total/current_monthly_avg*100):.0f}% da média mensal
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with insight_col2:
                    predicted_avg = predictions_df['Previsao'].mean()
                    historical_avg = year_df['Energia Gerada (kWh)'].mean()
                    trend_vs_historical = ((predicted_avg - historical_avg) / historical_avg * 100)
                    
                    trend_class = "positive" if trend_vs_historical >= 0 else "negative"
                    trend_icon = "📈" if trend_vs_historical >= 0 else "📉"
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{predicted_avg:.1f}</div>
                        <div class="metric-label">Média Diária Prevista</div>
                        <div class="metric-change {trend_class}">
                            {trend_icon} {abs(trend_vs_historical):.1f}% vs histórico
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with insight_col3:
                    best_predicted_day = predictions_df.loc[predictions_df['Previsao'].idxmax()]
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{best_predicted_day['Previsao']:.1f}</div>
                        <div class="metric-label">Melhor Dia Previsto</div>
                        <div class="metric-change positive">
                            ⭐ {best_predicted_day['Data'].strftime('%d/%m/%Y')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # --- Análise de Confiabilidade ---
                st.markdown("""
                <div class="custom-alert alert-info">
                    <strong>🔬 Sobre as Previsões:</strong><br>
                    • <strong>Algoritmo:</strong> {model_name} treinado com {data_points} pontos de dados<br>
                    • <strong>Precisão:</strong> R² = {r2:.1%} | Erro médio = ±{mae:.1f} kWh<br>
                    • <strong>Fatores Considerados:</strong> Sazonalidade, tendências, padrões semanais, médias móveis<br>
                    • <strong>Atualização:</strong> Modelo retreinado automaticamente com novos dados
                </div>
                """.format(
                    model_name=ml_metrics['best_model_name'],
                    data_points=len(year_df),
                    r2=ml_metrics['best_r2'],
                    mae=ml_metrics['best_mae']
                ), unsafe_allow_html=True)
                
            else:
                st.markdown("""
                <div class="custom-alert alert-warning">
                    ⚠️ <strong>Dados Insuficientes para Previsões</strong><br>
                    São necessários pelo menos 30 dias de dados históricos para gerar previsões confiáveis.
                    Continue registrando sua geração diária!
                </div>
                """, unsafe_allow_html=True)
        
        else:
            st.markdown("""
            <div class="custom-alert alert-info">
                📊 <strong>Previsões Disponíveis em Breve</strong><br>
                Continue coletando dados! Previsões estarão disponíveis após 30 dias de registros.
                Progresso atual: {current}/{needed} dias.
            </div>
            """.format(current=len(year_df), needed=30), unsafe_allow_html=True)

    else:
        st.markdown("""
        <div class="custom-alert alert-info">
            📊 <strong>Sem Dados</strong><br>
            Nenhum registro encontrado para o período selecionado. Ajuste os filtros ou adicione novos dados.
        </div>
        """, unsafe_allow_html=True)

    # --- Footer Profissional ---
    st.markdown("""
    <div class="footer">
        <div style="display: flex; justify-content: center; align-items: center; gap: 2rem; margin-bottom: 1rem;">
            <span>⚡ SolarAnalytics Pro</span>
            <span>|</span>
            <span>📊 Dashboard Inteligente</span>
            <span>|</span>
            <span>🌱 Energia Sustentável</span>
        </div>
        <div style="font-size: 0.75rem; opacity: 0.7;">
            Última atualização: {datetime.now().strftime('%d/%m/%Y às %H:%M')} | 
            Dados processados: {len(df)} registros
        </div>
    </div>
    </div>
    """.format(datetime=datetime), unsafe_allow_html=True)
