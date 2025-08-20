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
from streamlit_tags import st_tags

# Ignora avisos futuros do pandas
warnings.filterwarnings('ignore', category=FutureWarning, message='.*observed=False.*')

# Tenta configurar a localidade para português
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    pass

# --- Constantes de Configuração ---
SPREADSHEET_ID = '1WI2tZ94lVV9GfaaWerdSfuChFLzWfMbU4v2m6QrwTdY'
WORKSHEET_NAME = 'solardaily'

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

/* Background principal com degradê de #dcdcdc para #d3d3d3 */
.stApp {
    background: linear-gradient(135deg, #dcdcdc 0%, #d3d3d3 100%);
    min-height: 100vh;
}

.main .block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}

/* Container principal com glassmorphism */
.main-container {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(15px);
    border-radius: 20px;
    padding: 2rem;
    margin: 0 auto;
    box-shadow: var(--shadow-lg);
    border: 1px solid rgba(255, 255, 255, 0.3);
    position: relative;
}

/* Header customizado com padrão sutil */
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
    opacity: 0.6;
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

/* Formulário e containers com glassmorphism */
.stForm {
    background: rgba(255, 255, 255, 0.9) !important;
    backdrop-filter: blur(10px);
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: var(--shadow);
    padding: 2rem;
    margin-bottom: 2rem;
}

/* Containers com borda */
[data-testid="stVerticalBlock"] > div:has(.element-container) {
    background: rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(10px);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: var(--shadow);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}

/* Botões com efeito hover aprimorado */
.stButton>button {
    background: linear-gradient(135deg, var(--secondary-color), #2563eb) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px;
    padding: 0.75rem 1.5rem;
    font-weight: 600;
    box-shadow: var(--shadow);
    transition: all 0.3s ease;
    font-size: 1rem;
}

.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
}

/* Inputs e selectboxes com glassmorphism */
.stSelectbox > div > div,
.stTextInput > div > div,
.stDateInput > div > div {
    background: rgba(255, 255, 255, 0.9) !important;
    backdrop-filter: blur(5px);
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
    border-radius: 8px;
    transition: all 0.2s ease;
}

.stSelectbox > div > div:hover,
.stTextInput > div > div:hover,
.stDateInput > div > div:hover {
    background: rgba(255, 255, 255, 0.95) !important;
    border-color: var(--secondary-color) !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Métricas com efeito glassmorphism */
[data-testid="metric-container"] {
    background: rgba(255, 255, 255, 0.9) !important;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 12px;
    box-shadow: var(--shadow);
    padding: 1rem;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

[data-testid="metric-container"]:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
}

/* Headers com melhor espaçamento */
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    color: var(--text-primary) !important;
    font-weight: 600;
    margin-bottom: 1rem !important;
    position: relative;
    z-index: 1;
}

/* Gráficos com fundo transparente aprimorado */
.vega-embed {
    background: rgba(255, 255, 255, 0.9) !important;
    backdrop-filter: blur(10px);
    border-radius: 12px;
    padding: 1rem;
    box-shadow: var(--shadow);
    border: 1px solid rgba(255, 255, 255, 0.2);
    margin-bottom: 1rem;
}

/* Divider personalizado */
.stDivider {
    margin: 2rem 0;
}

.stDivider > div {
    background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.3), transparent);
    height: 2px;
    border-radius: 1px;
}

/* Info, warning, error, success com glassmorphism */
.stAlert {
    background: rgba(255, 255, 255, 0.9) !important;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    box-shadow: var(--shadow);
}

/* Scrollbar personalizada */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}

::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
}

::-webkit-scrollbar-thumb {
    background: rgba(59, 130, 246, 0.5);
    border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(59, 130, 246, 0.7);
}

/* Esconder elementos padrão do Streamlit */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Animação de entrada suave */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.main-container {
    animation: fadeInUp 0.8s ease-out;
}

/* Efeito de hover nos containers */
.element-container:hover {
    transition: all 0.3s ease;
}

/* Estilo para tooltips dos gráficos */
#vg-tooltip-element {
    background: rgba(255, 255, 255, 0.95) !important;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 8px;
    box-shadow: var(--shadow-lg);
}

/* Badge para status */
.status-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    display: inline-block;
}

.status-connected {
    background-color: #10B98120;
    color: #10B981;
}

.status-disconnected {
    background-color: #EF444420;
    color: #EF4444;
}

.status-warning {
    background-color: #F59E0B20;
    color: #F59E0B;
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
""", unsafe_allow_html=True)

# --- Conexão com Google Sheets ---
@st.cache_resource(show_spinner="Conectando ao Google Sheets...")
def connect_to_gsheets():
    try:
        scopes = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Testar a conexão
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.worksheet(WORKSHEET_NAME)
        
        # Verificar se as colunas existem
        headers = sheet.row_values(1)
        if 'data' not in [h.lower() for h in headers] or 'gerado' not in [h.lower() for h in headers]:
            st.error("⚠️ **Erro de Configuração**: A planilha deve conter as colunas 'data' e 'gerado'.")
            return None
        
        return sheet
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("📋 Planilha não encontrada. Verifique o SPREADSHEET_ID.")
        return None
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"📊 Aba '{WORKSHEET_NAME}' não encontrada. Verifique o WORKSHEET_NAME.")
        return None
    except Exception as e:
        st.error(f"🚨 **Erro de Conexão**: {str(e)}")
        return None

# Mostrar status da conexão
sheet = connect_to_gsheets()
if sheet:
    st.sidebar.markdown(f'<span class="status-badge status-connected">✅ Conectado ao Google Sheets</span>', unsafe_allow_html=True)
else:
    st.sidebar.markdown(f'<span class="status-badge status-disconnected">❌ Erro de conexão</span>', unsafe_allow_html=True)
    st.error("Não foi possível conectar ao Google Sheets. Verifique as credenciais e tente novamente.")
    st.stop()

# --- Funções de Dados ---
@st.cache_data(ttl=300, show_spinner="Carregando dados...")
def load_data():
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
        df['Energia Gerada (kWh)'] = df['Energia Gerada (kWh)'].astype(str).str.replace(',', '.', regex=False)
        df['Energia Gerada (kWh)'] = pd.to_numeric(df['Energia Gerada (kWh)'], errors='coerce')
        df.dropna(subset=['Data', 'Energia Gerada (kWh)'], inplace=True)
        df = df.sort_values(by='Data').drop_duplicates(subset=['Data'], keep='last')
        return df
    except Exception as e:
        st.error(f"🚨 **Erro ao carregar dados**: {str(e)}")
        return pd.DataFrame()

def append_data(date, energy):
    try:
        formatted_date = date.strftime('%d/%m/%Y')
        sheet.append_row([formatted_date, str(energy).replace('.', ',')], value_input_option='USER_ENTERED')
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"🚨 **Erro ao salvar**: {str(e)}")
        return False

def update_data(row_index, date, energy):
    try:
        formatted_date = date.strftime('%d/%m/%Y')
        # +2 porque a planilha começa na linha 1 (cabeçalho) e a indexação começa em 0
        sheet.update_cell(row_index + 2, 1, formatted_date)
        sheet.update_cell(row_index + 2, 2, str(energy).replace('.', ','))
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"🚨 **Erro ao atualizar**: {str(e)}")
        return False

def delete_data(row_index):
    try:
        # +2 porque a planilha começa na linha 1 (cabeçalho) e a indexação começa em 0
        sheet.delete_rows(row_index + 2)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"🚨 **Erro ao excluir**: {str(e)}")
        return False

# --- Formulário de Cadastro ---
st.header("☀️ Registro de Geração")
with st.container():
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
                    if energy_value <= 0:
                        st.error("⚠️ O valor deve ser maior que zero!")
                    elif append_data(input_date, energy_value):
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
        filter_col1, filter_col2, filter_col3 = st.columns([1, 1, 2])
        with filter_col1:
            years = sorted(df['Data'].dt.year.unique(), reverse=True)
            selected_year = st.selectbox("📅 Ano", options=years, key='year_filter')
        with filter_col2:
            months = sorted(df[df['Data'].dt.year == selected_year]['Data'].dt.month.unique())
            month_names = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 
                          7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
            selected_month_num = st.selectbox("📊 Mês", options=months, format_func=lambda x: month_names.get(x, ''), key='month_filter')
        with filter_col3:
            # Mostrar estatísticas rápidas
            total_year = df[df['Data'].dt.year == selected_year]['Energia Gerada (kWh)'].sum()
            st.metric(f"📈 Total em {selected_year}", f"{total_year:,.0f} kWh".replace(",", "X").replace(".", ",").replace("X", "."))

    filtered_df = df[(df['Data'].dt.year == selected_year) & (df['Data'].dt.month == selected_month_num)]
    
    if not filtered_df.empty:
        # --- Métricas ---
        total = filtered_df['Energia Gerada (kWh)'].sum()
        avg = filtered_df['Energia Gerada (kWh)'].mean()
        best = filtered_df.loc[filtered_df['Energia Gerada (kWh)'].idxmax()]
        worst = filtered_df.loc[filtered_df['Energia Gerada (kWh)'].idxmin()]
        
        st.header(f"📊 Análise de {month_names.get(selected_month_num, '')} de {selected_year}")
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        with metric_col1:
            st.metric("🔋 Total no Mês", f"{total:,.2f} kWh".replace(",", "X").replace(".", ",").replace("X", "."))
        with metric_col2:
            st.metric("📈 Média Diária", f"{avg:,.2f} kWh".replace(",", "X").replace(".", ",").replace("X", "."))
        with metric_col3:
            st.metric("⭐ Melhor Dia", f"{best['Energia Gerada (kWh)']:,.2f} kWh".replace(",", "X").replace(".", ",").replace("X", "."), 
                     delta=best['Data'].strftime('%d/%m'))
        with metric_col4:
            st.metric("⚠️ Menor Dia", f"{worst['Energia Gerada (kWh)']:,.2f} kWh".replace(",", "X").replace(".", ",").replace("X", "."), 
                     delta=worst['Data'].strftime('%d/%m'), delta_color="inverse")

        # --- Gráficos do Mês ---
        tab1, tab2, tab3 = st.tabs(["📊 Produção Diária", "📈 Geração Acumulada", "📋 Dados Detalhados"])
        
        with tab1:
            bar_chart = alt.Chart(filtered_df).mark_bar(
                color="#3b82f6",
                cornerRadiusTopLeft=3,
                cornerRadiusTopRight=3
            ).encode(
                x=alt.X('Data:T', title='Dia', scale=alt.Scale(paddingInner=0.1)),
                y=alt.Y('Energia Gerada (kWh):Q', title='Energia (kWh)'),
                tooltip=[
                    alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'), 
                    alt.Tooltip('Energia Gerada (kWh):Q', title='Gerado', format='.2f')
                ]
            ).properties(height=400).configure(background='transparent').configure_view(strokeWidth=0)
            st.altair_chart(bar_chart, use_container_width=True)
        
        with tab2:
            base = alt.Chart(filtered_df).encode(
                x=alt.X('Data:T', title='Dia'),
                tooltip=[
                    alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'), 
                    alt.Tooltip('Acumulado:Q', title='Acumulado', format='.2f')
                ]
            ).transform_window(
                Acumulado='sum(`Energia Gerada (kWh)`)',
                frame=[None, 0]
            )

            area = base.mark_area(
                line={'color':'#10b981', 'strokeWidth': 3}, 
                color=alt.Gradient(
                    gradient='linear', 
                    stops=[alt.GradientStop(color='#10b981', offset=0), 
                           alt.GradientStop(color='rgba(16, 185, 129, 0.3)', offset=0.5),
                           alt.GradientStop(color='rgba(16, 185, 129, 0)', offset=1)],
                    x1=1, x2=1, y1=1, y2=0
                ),
                opacity=0.8
            ).encode(y=alt.Y('Acumulado:Q', title='Energia Acumulada (kWh)'))
            
            points = base.mark_point(
                size=60,
                color='#10b981',
                opacity=0.8,
                filled=True,
                stroke='white',
                strokeWidth=2
            ).encode(y=alt.Y('Acumulado:Q'))

            st.altair_chart((area + points).properties(height=400).configure(background='transparent').configure_view(strokeWidth=0), 
                           use_container_width=True)
        
        with tab3:
            # Adicionar funcionalidade de edição
            st.subheader("📋 Dados Detalhados do Mês")
            edited_df = filtered_df.copy()
            edited_df['Data'] = edited_df['Data'].dt.strftime('%d/%m/%Y')
            
            # Preparar dados para edição
            display_df = edited_df.reset_index(drop=True)
            display_df.index = display_df.index + 1
            
            # Mostrar tabela com opção de edição
            col1, col2 = st.columns([3, 1])
            with col1:
                st.dataframe(display_df[['Data', 'Energia Gerada (kWh)']], use_container_width=True)
            
            with col2:
                st.write("")
                st.write("")
                if st.button("✏️ Editar Registros", use_container_width=True):
                    st.session_state.edit_mode = not st.session_state.get('edit_mode', False)
            
            if st.session_state.get('edit_mode', False):
                st.subheader("Editar Registros")
                selected_index = st.selectbox("Selecione o registro para editar", 
                                             options=range(len(filtered_df)),
                                             format_func=lambda x: f"{filtered_df.iloc[x]['Data'].strftime('%d/%m/%Y')} - {filtered_df.iloc[x]['Energia Gerada (kWh)']} kWh")
                
                edit_col1, edit_col2, edit_col3 = st.columns(3)
                with edit_col1:
                    edit_date = st.date_input("Data", value=filtered_df.iloc[selected_index]['Data'], format="DD/MM/YYYY", key="edit_date")
                with edit_col2:
                    edit_energy = st.number_input("Energia (kWh)", value=float(filtered_df.iloc[selected_index]['Energia Gerada (kWh)']), min_value=0.0, step=0.1, key="edit_energy")
                
                with edit_col3:
                    st.write("")
                    save_col, delete_col = st.columns(2)
                    with save_col:
                        if st.button("💾 Salvar", use_container_width=True):
                            if update_data(filtered_df.index[selected_index], edit_date, edit_energy):
                                st.success("Registro atualizado com sucesso!")
                                st.session_state.edit_mode = False
                                st.rerun()
                    with delete_col:
                        if st.button("🗑️ Excluir", use_container_width=True):
                            if delete_data(filtered_df.index[selected_index]):
                                st.success("Registro excluído com sucesso!")
                                st.session_state.edit_mode = False
                                st.rerun()

    # --- Análise Anual ---
    year_df_filtered = df[df['Data'].dt.year == selected_year].copy()
    if not year_df_filtered.empty:
        st.divider()
        st.header(f"📅 Resumo Anual de {selected_year}")
        
        # Gráfico Mensal
        monthly_summary = year_df_filtered.groupby(year_df_filtered['Data'].dt.month)['Energia Gerada (kWh)'].sum().reset_index()
        monthly_summary.rename(columns={'Data': 'Mês'}, inplace=True)
        monthly_summary['Nome Mês'] = monthly_summary['Mês'].apply(lambda m: month_names[m][:3])
        
        monthly_chart = alt.Chart(monthly_summary).mark_bar(
            color="#f59e0b",
            cornerRadiusTopLeft=4,
            cornerRadiusTopRight=4
        ).encode(
            x=alt.X('Nome Mês:N', title='Mês', sort=[m[:3] for m in month_names.values()], 
                   scale=alt.Scale(paddingInner=0.2)),
            y=alt.Y('Energia Gerada (kWh):Q', title='Total (kWh)'),
            tooltip=[
                alt.Tooltip('Nome Mês', title='Mês'), 
                alt.Tooltip('Energia Gerada (kWh):Q', title='Total Gerado', format='.2f')
            ]
        ).properties(height=400).configure(background='transparent').configure_view(strokeWidth=0)
        st.altair_chart(monthly_chart, use_container_width=True)
        
        # --- HEATMAP ESTILO GITHUB APRIMORADO ---
        st.subheader(f"🗓️ Calendário de Geração - {selected_year}")
        
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
            width=14, height=14, cornerRadius=2, stroke='white', strokeWidth=1.5
        ).encode(
            x=alt.X('week_of_year:O', title=None, 
                   axis=alt.Axis(labels=True, ticks=False, domain=False, labelExpr=label_expr, 
                                labelAlign='left', labelOffset=8, labelPadding=3, labelFontSize=10)),
            y=alt.Y('day_of_week_num:O', title=None, sort=None, 
                   axis=alt.Axis(labels=True, ticks=False, domain=False, 
                                labelExpr="['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'][datum.value]",
                                labelFontSize=10)),
            color=alt.condition(
                'isValid(datum["Energia Gerada (kWh)"])',
                alt.Color('Energia Gerada (kWh):Q', 
                          legend=alt.Legend(title="Energia (kWh)", orient='bottom', titleFontSize=12), 
                          scale=alt.Scale(scheme='greens', range=[0.2, 1])),
                alt.value('#e5e7eb')
            ),
            tooltip=[
                alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'), 
                alt.Tooltip('Energia Gerada (kWh):Q', title='Gerado', format='.2f')
            ]
        ).properties(
            height=160
        ).configure(
            background='transparent'
        ).configure_view(
            strokeWidth=0
        )
        st.altair_chart(heatmap, use_container_width=True)

        # --- Estatísticas Adicionais ---
        st.subheader("📈 Estatísticas do Ano")
        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
        
        year_total = year_df_filtered['Energia Gerada (kWh)'].sum()
        year_avg = year_df_filtered['Energia Gerada (kWh)'].mean()
        year_max = year_df_filtered['Energia Gerada (kWh)'].max()
        year_min = year_df_filtered['Energia Gerada (kWh)'].min()
        
        with stats_col1:
            st.metric("🏆 Total do Ano", f"{year_total:,.1f} kWh".replace(",", "X").replace(".", ",").replace("X", "."))
        with stats_col2:
            st.metric("📊 Média Anual", f"{year_avg:,.1f} kWh".replace(",", "X").replace(".", ",").replace("X", "."))
        with stats_col3:
            st.metric("⚡ Pico Máximo", f"{year_max:,.1f} kWh".replace(",", "X").replace(".", ",").replace("X", "."))
        with stats_col4:
            st.metric("📉 Mínimo", f"{year_min:,.1f} kWh".replace(",", "X").replace(".", ",").replace("X", "."))

st.markdown("</div>", unsafe_allow_html=True) # Fecha o main-container

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: var(--text-secondary); margin-top: 1rem;">
    <p>🌱 <strong>SolarAnalytics Pro</strong> - Monitoramento Inteligente de Energia Solar</p>
    <p><em>Conectado ao Google Sheets | Atualização automática a cada 5 minutos</em></p>
</div>
""", unsafe_allow_html=True)
