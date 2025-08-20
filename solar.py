# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import streamlit as st
import gspread
import time
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
import warnings
import altair as alt
import locale

# Ignora avisos futuros do pandas
warnings.filterwarnings('ignore', category=FutureWarning, message='.*observed=False.*')

# Configuração do Altair para melhor performance
alt.data_transformers.enable('json')

# Tenta configurar a localidade para português
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR')
    except:
        pass

# --- Constantes de Configuração ---
SPREADSHEET_ID = '1WI2tZ94lVV9GfaaWerdSfuChFLzWfMbU4v2m6QrwTdY'
WORKSHEET_NAME = 'solardaily'

# Definir FONT_SIZES para evitar erro
FONT_SIZES = {
    'chart_axis': 10,
    'chart_title': 14,
    'chart_label': 12
}

# --- Configuração da Página ---
st.set_page_config(
    layout="wide",
    page_title="SolarAnalytics Pro | Dashboard Energia Solar",
    page_icon="⚡",
    initial_sidebar_state="collapsed"
)

# --- Estilo CSS Profissional e Limpo ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;500;600;700&display=swap');

:root {
    --primary-color: #1f2937;
    --secondary-color: #3b82f6;
    --accent-color: #10b981;
    --text-primary: #1f2937;
    --text-secondary: #6b7280;
    --bg-light: #f8fafc;
    --border-light: #e2e8f0;
}

* {
    font-family: 'Nunito', sans-serif !important;
}

html, body, [class*="st-"], .stApp, .main, div, p, span, h1, h2, h3, h4, h5, h6, label, input, button, select, textarea {
    font-family: 'Nunito', sans-serif !important;
}

.stApp {
    background-color: var(--bg-light);
}

.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}

/* Header */
.header-section {
    background: linear-gradient(135deg, var(--primary-color), #374151);
    color: white;
    padding: 2rem;
    border-radius: 12px;
    margin-bottom: 2rem;
    text-align: center;
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

/* Cards */
[data-testid="metric-container"] {
    background: white;
    border: 1px solid var(--border-light);
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Forms */
.stForm {
    background: white;
    border: 1px solid var(--border-light);
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 2rem;
}

/* Buttons */
.stButton > button {
    background: var(--secondary-color);
    color: white;
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    font-weight: 500;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    background: #2563eb;
    transform: translateY(-1px);
}

/* Inputs */
.stSelectbox > div > div,
.stTextInput > div > div,
.stDateInput > div > div,
.stNumberInput > div > div {
    background: white;
    border: 1px solid var(--border-light);
    border-radius: 6px;
}

.stSelectbox > div > div:focus,
.stTextInput > div > div:focus,
.stDateInput > div > div:focus,
.stNumberInput > div > div:focus {
    border-color: var(--secondary-color);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Charts */
.vega-embed {
    background: white;
    border-radius: 8px;
    padding: 1rem;
    border: 1px solid var(--border-light);
    margin-bottom: 1rem;
}

/* Dataframe */
.dataframe {
    background: white;
    border: 1px solid var(--border-light);
    border-radius: 8px;
}

/* Status badges */
.status-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
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

/* Headers */
h1, h2, h3 {
    color: var(--text-primary);
    font-weight: 600;
}

/* Hide Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Scrollbar */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}

::-webkit-scrollbar-track {
    background: #f1f5f9;
    border-radius: 3px;
}

::-webkit-scrollbar-thumb {
    background: var(--secondary-color);
    border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
    background: #2563eb;
}
</style>
""", unsafe_allow_html=True)

# --- Inicialização do Session State ---
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False

# --- Header ---
st.markdown("""
<div class="header-section">
    <div class="header-title">⚡ SolarAnalytics Pro</div>
    <div class="header-subtitle">Monitoramento Inteligente de Geração de Energia Solar</div>
</div>
""", unsafe_allow_html=True)

# --- Conexão com Google Sheets ---
@st.cache_resource(show_spinner="🔌 Conectando ao Google Sheets...")
def connect_to_gsheets():
    """Conecta ao Google Sheets com tratamento robusto de erros"""
    try:
        scopes = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Testar a conexão
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.worksheet(WORKSHEET_NAME)
        
        # Verificar se as colunas existem
        try:
            headers = sheet.row_values(1)
            if not headers:
                st.error("⚠️ **Erro**: A planilha está vazia ou sem cabeçalhos.")
                return None
                
            headers_lower = [h.lower().strip() for h in headers]
            if 'data' not in headers_lower or 'gerado' not in headers_lower:
                st.error("⚠️ **Erro de Configuração**: A planilha deve conter as colunas 'data' e 'gerado'.")
                st.info("💡 **Dica**: Certifique-se de que a primeira linha da planilha contém os cabeçalhos 'data' e 'gerado'.")
                return None
        except Exception as e:
            st.error(f"❌ **Erro ao verificar cabeçalhos**: {str(e)}")
            return None
        
        return sheet
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("📋 **Planilha não encontrada**: Verifique se o SPREADSHEET_ID está correto e se você tem permissão de acesso.")
        return None
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"📊 **Aba não encontrada**: A aba '{WORKSHEET_NAME}' não existe na planilha.")
        return None
    except KeyError:
        st.error("🔑 **Erro de Credenciais**: Configuração do Google Sheets não encontrada no st.secrets.")
        return None
    except Exception as e:
        st.error(f"🚨 **Erro de Conexão**: {str(e)}")
        return None

# Conexão e status
sheet = connect_to_gsheets()
if sheet:
    st.sidebar.markdown(
        '<span class="status-badge status-connected">✅ Conectado</span>', 
        unsafe_allow_html=True
    )
else:
    st.sidebar.markdown(
        '<span class="status-badge status-disconnected">❌ Erro de conexão</span>', 
        unsafe_allow_html=True
    )
    st.error("⚠️ **Sistema Offline**: Não foi possível conectar ao Google Sheets.")
    st.stop()

# --- Funções de Dados ---
@st.cache_data(ttl=300, show_spinner="📊 Carregando dados...")
def load_data():
    """Carrega e processa os dados da planilha"""
    try:
        # Obter todos os valores
        values = sheet.get_all_values()
        
        if len(values) < 2: 
            return pd.DataFrame()
        
        # Criar DataFrame
        df = pd.DataFrame(values[1:], columns=values[0])
        df.columns = [col.lower().strip() for col in df.columns]
        
        # Verificar colunas essenciais
        if 'data' not in df.columns or 'gerado' not in df.columns:
            st.error("⚠️ **Erro de Configuração**: A planilha deve conter as colunas 'data' e 'gerado'.")
            return pd.DataFrame()
        
        # Renomear colunas
        df.rename(columns={
            'data': 'Data', 
            'gerado': 'Energia Gerada (kWh)'
        }, inplace=True)
        
        # Processar datas
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        if df['Data'].isna().any():
            df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        
        # Processar valores de energia
        df['Energia Gerada (kWh)'] = df['Energia Gerada (kWh)'].astype(str).str.replace(',', '.', regex=False)
        df['Energia Gerada (kWh)'] = pd.to_numeric(df['Energia Gerada (kWh)'], errors='coerce')
        
        # Limpar dados inválidos
        df.dropna(subset=['Data', 'Energia Gerada (kWh)'], inplace=True)
        df = df[df['Energia Gerada (kWh)'] >= 0]
        df = df.sort_values(by='Data').drop_duplicates(subset=['Data'], keep='last')
        
        return df.reset_index(drop=True)
        
    except Exception as e:
        st.error(f"🚨 **Erro ao carregar dados**: {str(e)}")
        return pd.DataFrame()

def append_data(date, energy):
    """Adiciona um novo registro à planilha"""
    try:
        formatted_date = date.strftime('%d/%m/%Y')
        energy_str = str(energy).replace('.', ',')
        sheet.append_row([formatted_date, energy_str], value_input_option='USER_ENTERED')
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"🚨 **Erro ao salvar**: {str(e)}")
        return False

def update_data(row_index, date, energy):
    """Atualiza um registro existente"""
    try:
        formatted_date = date.strftime('%d/%m/%Y')
        energy_str = str(energy).replace('.', ',')
        sheet.update_cell(row_index + 2, 1, formatted_date)
        sheet.update_cell(row_index + 2, 2, energy_str)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"🚨 **Erro ao atualizar**: {str(e)}")
        return False

def delete_data(row_index):
    """Exclui um registro da planilha"""
    try:
        sheet.delete_rows(row_index + 2)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"🚨 **Erro ao excluir**: {str(e)}")
        return False

def format_number_br(number, decimals=2):
    """Formata números no padrão brasileiro"""
    return f"{number:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- Formulário de Cadastro ---
st.header("☀️ Registro de Geração")
with st.form("entry_form", clear_on_submit=True):
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        input_date = st.date_input(
            "📅 Data da Geração", 
            value=datetime.today(),
            format="DD/MM/YYYY"
        )
        
    with col2:
        input_energy = st.number_input(
            "⚡ Energia Gerada (kWh)",
            min_value=0.0,
            max_value=999.9,
            step=0.1,
            format="%.2f"
        )
        
    with col3:
        st.write("")
        st.write("")
        submitted = st.form_submit_button("💾 Salvar", use_container_width=True)
    
    if submitted:
        if input_energy > 0:
            with st.spinner("💾 Salvando dados..."):
                if append_data(input_date, input_energy):
                    st.success("✅ Dados salvos com sucesso!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Falha ao salvar os dados.")
        else:
            st.warning("💡 Digite um valor maior que zero.")

# --- Análise de Dados ---
df = load_data()
if df.empty:
    st.info("📊 **Nenhum dado encontrado**. Comece registrando sua primeira geração de energia solar!")
else:
    # --- Filtros ---
    st.header("🔍 Filtros de Análise")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        years = sorted(df['Data'].dt.year.unique(), reverse=True)
        selected_year = st.selectbox("📅 Ano", options=years)
        
    with col2:
        months = sorted(df[df['Data'].dt.year == selected_year]['Data'].dt.month.unique())
        month_names = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        
        if months:
            selected_month_num = st.selectbox(
                "📊 Mês", 
                options=months, 
                format_func=lambda x: month_names.get(x, '')
            )
        else:
            st.info("Nenhum dado disponível para este ano")
            selected_month_num = None
            
    with col3:
        total_year = df[df['Data'].dt.year == selected_year]['Energia Gerada (kWh)'].sum()
        st.metric(f"📈 Total em {selected_year}", f"{format_number_br(total_year)} kWh")
    
    if selected_month_num is not None:
        # Filtrar dados
        filtered_df = df[
            (df['Data'].dt.year == selected_year) & 
            (df['Data'].dt.month == selected_month_num)
        ].copy()
        
        if not filtered_df.empty:
            # --- Métricas do Mês ---
            total = filtered_df['Energia Gerada (kWh)'].sum()
            avg = filtered_df['Energia Gerada (kWh)'].mean()
            best = filtered_df.loc[filtered_df['Energia Gerada (kWh)'].idxmax()]
            worst = filtered_df.loc[filtered_df['Energia Gerada (kWh)'].idxmin()]
            
            st.header(f"📊 Análise de {month_names.get(selected_month_num, '')} de {selected_year}")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🔋 Total no Mês", f"{format_number_br(total)} kWh")
            with col2:
                st.metric("📈 Média Diária", f"{format_number_br(avg)} kWh")
            with col3:
                st.metric("⭐ Melhor Dia", f"{format_number_br(best['Energia Gerada (kWh)'])} kWh", 
                         delta=best['Data'].strftime('%d/%m'))
            with col4:
                st.metric("⚠️ Menor Dia", f"{format_number_br(worst['Energia Gerada (kWh)'])} kWh",
                         delta=worst['Data'].strftime('%d/%m'), delta_color="inverse")
            
            # --- Abas de Análise ---
            tab1, tab2, tab3 = st.tabs(["📊 Produção Diária", "📈 Geração Acumulada", "📋 Dados"])
            
            with tab1:
                # Gráfico de barras - CORRIGIDO
                bar_chart = alt.Chart(filtered_df).mark_bar(
                    color="#3b82f6",
                    cornerRadiusTopLeft=4,
                    cornerRadiusTopRight=4,
                    size=30
                ).encode(
                    x=alt.X(
                        'Data:T', 
                        title='Data',
                        axis=alt.Axis(
                            format='%d/%m',
                            labelAngle=-45,
                            tickCount='day',
                            labelFontSize=FONT_SIZES['chart_axis']
                        ),
                        scale=alt.Scale(nice=False)
                    ),
                    y=alt.Y('Energia Gerada (kWh):Q', title='Energia Gerada (kWh)'),
                    tooltip=[
                        alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'), 
                        alt.Tooltip('Energia Gerada (kWh):Q', title='Energia', format='.2f')
                    ]
                )
                
                # Linha da média
                media_diaria = filtered_df['Energia Gerada (kWh)'].mean()
                linha_media = alt.Chart(pd.DataFrame({'media': [media_diaria]})).mark_rule(
                    color='red',
                    strokeWidth=2,
                    strokeDash=[5, 5]
                ).encode(
                    y=alt.Y('media:Q'),
                    tooltip=alt.value(f'Média: {format_number_br(media_diaria)} kWh')
                )
                
                # Combinar gráfico
                final_chart = (bar_chart + linha_media).properties(
                    height=400,
                    title=f"Geração Diária - {month_names.get(selected_month_num, '')} {selected_year}"
                ).resolve_scale(
                    x='independent'
                )
                
                st.altair_chart(final_chart, use_container_width=True)
            
            with tab2:
                # Gráfico acumulado
                filtered_df_sorted = filtered_df.sort_values('Data').copy()
                filtered_df_sorted['Acumulado'] = filtered_df_sorted['Energia Gerada (kWh)'].cumsum()
                
                area_chart = alt.Chart(filtered_df_sorted).mark_area(
                    line={'color':'#10b981', 'strokeWidth': 3}, 
                    color=alt.Gradient(
                        gradient='linear', 
                        stops=[
                            alt.GradientStop(color='#10b981', offset=0), 
                            alt.GradientStop(color='rgba(16, 185, 129, 0.3)', offset=1)
                        ],
                        x1=1, x2=1, y1=1, y2=0
                    ),
                    interpolate='monotone'
                ).encode(
                    x=alt.X('Data:T', title='Data'),
                    y=alt.Y('Acumulado:Q', title='Energia Acumulada (kWh)'),
                    tooltip=[
                        alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'),
                        alt.Tooltip('Energia Gerada (kWh):Q', title='Geração', format='.2f'),
                        alt.Tooltip('Acumulado:Q', title='Acumulado', format='.2f')
                    ]
                ).properties(
                    height=400,
                    title=f"Geração Acumulada - {month_names.get(selected_month_num, '')} {selected_year}"
                )
                
                st.altair_chart(area_chart, use_container_width=True)
            
            with tab3:
                # Tabela de dados
                display_df = filtered_df.copy()
                display_df['Data_str'] = display_df['Data'].dt.strftime('%d/%m/%Y')
                display_df['Energia_str'] = display_df['Energia Gerada (kWh)'].apply(lambda x: format_number_br(x))
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.dataframe(
                        display_df[['Data_str', 'Energia_str']].rename(columns={
                            'Data_str': 'Data',
                            'Energia_str': 'Energia Gerada (kWh)'
                        }),
                        use_container_width=True,
                        hide_index=True
                    )
                
                with col2:
                    if st.button("✏️ Editar Registros", use_container_width=True):
                        st.session_state.edit_mode = not st.session_state.edit_mode
                
                # Modo de edição
                if st.session_state.edit_mode:
                    st.divider()
                    st.subheader("✏️ Editar Registros")
                    
                    if len(filtered_df) > 0:
                        selected_index = st.selectbox(
                            "Selecione o registro", 
                            options=range(len(filtered_df)),
                            format_func=lambda x: f"{filtered_df.iloc[x]['Data'].strftime('%d/%m/%Y')} - {format_number_br(filtered_df.iloc[x]['Energia Gerada (kWh)'])} kWh"
                        )
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            edit_date = st.date_input("📅 Data", 
                                value=filtered_df.iloc[selected_index]['Data'], 
                                format="DD/MM/YYYY")
                            
                        with col2:
                            edit_energy = st.number_input("⚡ Energia (kWh)", 
                                value=float(filtered_df.iloc[selected_index]['Energia Gerada (kWh)']), 
                                min_value=0.0, step=0.1, format="%.2f")
                        
                        with col3:
                            st.write("")
                            save_col, delete_col = st.columns(2)
                            
                            with save_col:
                                if st.button("💾 Salvar", use_container_width=True):
                                    original_index = filtered_df.index[selected_index]
                                    if update_data(original_index, edit_date, edit_energy):
                                        st.success("✅ Atualizado!")
                                        st.session_state.edit_mode = False
                                        time.sleep(1)
                                        st.rerun()
                            
                            with delete_col:
                                if st.button("🗑️ Excluir", use_container_width=True):
                                    original_index = filtered_df.index[selected_index]
                                    if delete_data(original_index):
                                        st.success("✅ Excluído!")
                                        st.session_state.edit_mode = False
                                        time.sleep(1)
                                        st.rerun()
        
        # --- Análise Anual ---
        year_df = df[df['Data'].dt.year == selected_year].copy()
        
        if not year_df.empty:
            st.header(f"📅 Resumo Anual de {selected_year}")
            
            # Gráfico mensal
            monthly_summary = year_df.groupby(
                year_df['Data'].dt.month
            )['Energia Gerada (kWh)'].sum().reset_index()
            
            monthly_summary.rename(columns={'Data': 'Mês'}, inplace=True)
            monthly_summary['Nome Mês'] = monthly_summary['Mês'].apply(
                lambda m: month_names[m][:3]
            )
            
            # Gráfico de barras mensais - CORRIGIDO
            monthly_bars = alt.Chart(monthly_summary).mark_bar(
                color="#f59e0b",
                cornerRadiusTopLeft=4,
                cornerRadiusTopRight=4,
                size=40
            ).encode(
                x=alt.X(
                    'Nome Mês:N', 
                    title='Mês', 
                    sort=[m[:3] for m in month_names.values()],
                    axis=alt.Axis(labelFontSize=FONT_SIZES['chart_axis'])
                ),
                y=alt.Y('Energia Gerada (kWh):Q', title='Total Mensal (kWh)'),
                tooltip=[
                    alt.Tooltip('Nome Mês:N', title='Mês'), 
                    alt.Tooltip('Energia Gerada (kWh):Q', title='Total', format='.2f')
                ]
            )
            
            # Linha da média mensal
            media_mensal = monthly_summary['Energia Gerada (kWh)'].mean()
            linha_media_mensal = alt.Chart(pd.DataFrame({'media': [media_mensal]})).mark_rule(
                color='red',
                strokeWidth=2,
                strokeDash=[5, 5]
            ).encode(
                y=alt.Y('media:Q'),
                tooltip=alt.value(f'Média Mensal: {format_number_br(media_mensal)} kWh')
            )
            
            # Combinar gráfico mensal
            monthly_chart = (monthly_bars + linha_media_mensal).properties(
                height=500,
                title=f"Geração Mensal - {selected_year}"
            ).resolve_scale(
                x='independent'
            )
            
            st.altair_chart(monthly_chart, use_container_width=True)
            
            # --- Heatmap estilo GitHub ---
            st.subheader(f"🗓️ Heatmap de Geração - {selected_year}")
            
            # Preparar dados para heatmap
            start_date = datetime(selected_year, 1, 1)
            end_date = datetime(selected_year, 12, 31)
            all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # Criar DataFrame base
            heatmap_df = pd.DataFrame({'date': all_dates})
            heatmap_df['date_str'] = heatmap_df['date'].dt.strftime('%Y-%m-%d')
            
            # Preparar dados existentes
            year_data_heat = year_df.copy()
            year_data_heat['date_str'] = year_data_heat['Data'].dt.strftime('%Y-%m-%d')
            year_data_heat = year_data_heat.groupby('date_str')['Energia Gerada (kWh)'].sum().reset_index()
            
            # Merge dos dados
            heatmap_df = pd.merge(heatmap_df, year_data_heat, on='date_str', how='left')
            heatmap_df['Energia Gerada (kWh)'] = heatmap_df['Energia Gerada (kWh)'].fillna(0)
            
            # Adicionar informações de calendário
            heatmap_df['week'] = heatmap_df['date'].dt.isocalendar().week
            heatmap_df['day_of_week'] = heatmap_df['date'].dt.dayofweek
            heatmap_df['month'] = heatmap_df['date'].dt.month
            
            # Ajustar semanas
            min_week = heatmap_df['week'].min()
            heatmap_df['week_adj'] = heatmap_df['week'] - min_week
            
            # Criar heatmap - CORRIGIDO
            heatmap = alt.Chart(heatmap_df).mark_rect(
                stroke='white',
                strokeWidth=2
            ).encode(
                x=alt.X(
                    'week_adj:O',
                    title=None,
                    axis=alt.Axis(labels=False, ticks=False, domain=False)
                ),
                y=alt.Y(
                    'day_of_week:O',
                    title=None,
                    axis=alt.Axis(
                        labelExpr="['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'][datum.value]",
                        ticks=False,
                        domain=False,
                        labelFontSize=FONT_SIZES['chart_axis']
                    )
                ),
                color=alt.Color(
                    'Energia Gerada (kWh):Q',
                    title='kWh',
                    scale=alt.Scale(
                        scheme='greens',
                        range=['#ebedf0', '#c6e48b', '#7bc96f', '#239a3b', '#196127']
                    )
                ),
                tooltip=[
                    alt.Tooltip('date:T', title='Data', format='%d/%m/%Y'),
                    alt.Tooltip('Energia Gerada (kWh):Q', title='Geração', format='.2f')
                ]
            ).properties(
                width=650,
                height=120,
                title=f"Contribuições de Energia Solar - {selected_year}"
            )
            
            st.altair_chart(heatmap, use_container_width=True)
            
            st.subheader("📈 Estatísticas do Ano")
            
            year_total = year_df['Energia Gerada (kWh)'].sum()
            year_avg = year_df['Energia Gerada (kWh)'].mean()
            year_max = year_df['Energia Gerada (kWh)'].max()
            year_min = year_df['Energia Gerada (kWh)'].min()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🏆 Total do Ano", f"{format_number_br(year_total)} kWh")
            with col2:
                st.metric("📊 Média Diária", f"{format_number_br(year_avg)} kWh")
            with col3:
                st.metric("⚡ Pico Máximo", f"{format_number_br(year_max)} kWh")
            with col4:
                st.metric("📉 Mínimo", f"{format_number_br(year_min)} kWh")

# --- Análise da Conta de Energia ---
if not df.empty:
    st.header("⚡ Análise da Conta de Energia Atual")
    
    # Dados da fatura (exemplo baseado no documento fornecido)
    conta_dados = {
        'uc': '15491948',
        'consumo_kwh': 253,
        'geracao_kwh': 464,
        'saldo_creditos_kwh': 211,
        'valor_fatura': 39.34,
        'tarifa_scee': 0.653688,
        'taxa_injecao_perc': 24.57,
        'icms_perc': 19,
        'iluminacao_publica': 8.38,
        'mes_referencia': 'JUL/2025'
    }
    
    # Métricas principais da conta
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💡 Consumo da Rede", f"{conta_dados['consumo_kwh']} kWh")
    with col2:
        st.metric("☀️ Geração Solar", f"{conta_dados['geracao_kwh']} kWh")
    with col3:
        st.metric("🔋 Saldo de Créditos", f"{conta_dados['saldo_creditos_kwh']} kWh")
    with col4:
        st.metric("💰 Valor da Fatura", f"R$ {format_number_br(conta_dados['valor_fatura'])}")
    
    # Cálculos de economia e performance
    performance_perc = (conta_dados['geracao_kwh'] / conta_dados['consumo_kwh'] * 100) if conta_dados['consumo_kwh'] > 0 else 0
    valor_sem_solar = conta_dados['geracao_kwh'] * conta_dados['tarifa_scee']
    economia_mensal = valor_sem_solar - conta_dados['valor_fatura']
    economia_perc = (economia_mensal / valor_sem_solar * 100) if valor_sem_solar > 0 else 0
    
    # Container para análise de performance
    with st.container():
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 1.5rem; border-radius: 12px; margin: 1rem 0;">
            <h3 style="margin-bottom: 0.5rem;">📊 Performance do Sistema Solar</h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🎯 Eficiência do Sistema", f"{performance_perc:.0f}%", 
                     delta="Geração vs Consumo")
        with col2:
            st.metric("💸 Economia Mensal", f"R$ {format_number_br(economia_mensal)}", 
                     delta=f"{economia_perc:.0f}% economia")
        with col3:
            st.metric("⚡ Excedente", f"{conta_dados['geracao_kwh'] - conta_dados['consumo_kwh']} kWh",
                     delta="Créditos gerados")
    
    # Container para análise financeira
    with st.container():
        st.markdown("""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                    color: white; padding: 1.5rem; border-radius: 12px; margin: 1rem 0;">
            <h3 style="margin-bottom: 0.5rem;">💰 Análise Financeira Detalhada</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Tabela de composição da conta
        composicao_df = pd.DataFrame([
            ["Consumo SCEE", f"{conta_dados['consumo_kwh']} kWh", f"R$ {format_number_br(conta_dados['consumo_kwh'] * conta_dados['tarifa_scee'])}", "Cobrança"],
            ["Injeção SCEE", f"{conta_dados['consumo_kwh']} kWh", f"-R$ {format_number_br(conta_dados['consumo_kwh'] * conta_dados['tarifa_scee'])}", "Desconto"],
            ["Taxa de Injeção", f"{conta_dados['taxa_injecao_perc']}%", f"R$ {format_number_br(conta_dados['consumo_kwh'] * conta_dados['tarifa_scee'] * conta_dados['taxa_injecao_perc'] / 100)}", "Nova cobrança"],
            ["ICMS", f"{conta_dados['icms_perc']}%", f"R$ {format_number_br(conta_dados['consumo_kwh'] * conta_dados['tarifa_scee'] * conta_dados['icms_perc'] / 100)}", "Imposto"],
            ["Iluminação Pública", "Taxa fixa", f"R$ {format_number_br(conta_dados['iluminacao_publica'])}", "Municipal"],
            ["TOTAL", "Valor final", f"R$ {format_number_br(conta_dados['valor_fatura'])}", "A pagar"]
        ], columns=["Item", "Descrição", "Valor", "Tipo"])
        
        st.dataframe(composicao_df, use_container_width=True, hide_index=True)
    
    # Container para impostos
    with st.container():
        st.markdown("""
        <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
                    color: white; padding: 1.5rem; border-radius: 12px; margin: 1rem 0;">
            <h3 style="margin-bottom: 0.5rem;">📋 Detalhamento de Impostos</h3>
        </div>
        """, unsafe_allow_html=True)
        
        impostos_df = pd.DataFrame([
            ["ICMS", "19%", f"R$ {format_number_br(conta_dados['consumo_kwh'] * conta_dados['tarifa_scee'] * 0.19)}", "Sobre energia compensada"],
            ["PIS/PASEP", "1,0554%", "R$ 0,00", "Isento na compensação"],
            ["COFINS", "4,8687%", "R$ 0,00", "Isento na compensação"],
            ["Taxa Injeção", "24,57%", f"R$ {format_number_br(conta_dados['consumo_kwh'] * conta_dados['tarifa_scee'] * 0.2457)}", "Nova regulamentação"]
        ], columns=["Imposto/Taxa", "Alíquota", "Valor", "Observação"])
        
        st.dataframe(impostos_df, use_container_width=True, hide_index=True)
    
    # Container para nova regulamentação
    with st.container():
        st.markdown("""
        <div style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); 
                    color: #333; padding: 1.5rem; border-radius: 12px; margin: 1rem 0;">
            <h3 style="margin-bottom: 0.5rem;">⚖️ Nova Regulamentação (Lei 14.300/21)</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.warning("""
        **Mudanças Importantes:**
        - Taxa de 24,57% sobre energia injetada na rede
        - ICMS de 19% sobre uso da infraestrutura elétrica
        - Cobrança gradual implementada até 2028
        - Mesmo com as taxas, economia de 87% ainda é mantida
        """)
    
    # Container para comparação e economia
    with st.container():
        st.markdown("""
        <div style="background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); 
                    color: #333; padding: 1.5rem; border-radius: 12px; margin: 1rem 0;">
            <h3 style="margin-bottom: 0.5rem;">💸 Comparativo de Economia</h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🚫 Sem Energia Solar", 
                     f"R$ {format_number_br(valor_sem_solar)}", 
                     delta=f"{conta_dados['geracao_kwh']} kWh × R$ {conta_dados['tarifa_scee']:.3f}")
        with col2:
            st.metric("⚡ Com Energia Solar", 
                     f"R$ {format_number_br(conta_dados['valor_fatura'])}", 
                     delta="Valor atual da fatura")
        with col3:
            st.metric("💰 Economia Mensal", 
                     f"R$ {format_number_br(economia_mensal)}", 
                     delta=f"{economia_perc:.0f}% de economia!", 
                     delta_color="normal")
    
    # Gráfico de comparação
    with st.container():
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 1.5rem; border-radius: 12px; margin: 1rem 0;">
            <h3 style="margin-bottom: 0.5rem;">📊 Comparativo Visual: Com vs Sem Energia Solar</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Dados para o gráfico de comparação
        comparacao_df = pd.DataFrame([
            {"Situação": "Sem Solar", "Valor": valor_sem_solar, "Tipo": "Gasto Total"},
            {"Situação": "Com Solar", "Valor": conta_dados['valor_fatura'], "Tipo": "Fatura Atual"},
            {"Situação": "Economia", "Valor": economia_mensal, "Tipo": "Economia Mensal"}
        ])
        
        comparacao_chart = alt.Chart(comparacao_df).mark_bar(
            cornerRadiusTopLeft=8,
            cornerRadiusTopRight=8,
            size=100
        ).encode(
            x=alt.X('Situação:N', title='Cenário', axis=alt.Axis(labelFontSize=FONT_SIZES['chart_axis'])),
            y=alt.Y('Valor:Q', title='Valor (R$)', axis=alt.Axis(labelFontSize=FONT_SIZES['chart_axis'])),
            color=alt.Color('Situação:N', 
                           scale=alt.Scale(range=['#ef4444', '#10b981', '#3b82f6']),
                           legend=None),
            tooltip=[
                alt.Tooltip('Situação:N', title='Cenário'),
                alt.Tooltip('Valor:Q', title='Valor', format='.2f'),
                alt.Tooltip('Tipo:N', title='Descrição')
            ]
        ).properties(
            height=400,
            title=f"Comparativo Financeiro - {conta_dados['mes_referencia']}"
        )
        
        st.altair_chart(comparacao_chart, use_container_width=True)
    
    # Gráfico de composição da fatura
    with st.container():
        st.markdown("""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                    color: white; padding: 1.5rem; border-radius: 12px; margin: 1rem 0;">
            <h3 style="margin-bottom: 0.5rem;">🥧 Composição da Fatura Atual</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Dados para o gráfico pizza
        pizza_df = pd.DataFrame([
            {"Componente": "Taxa Injeção", "Valor": conta_dados['consumo_kwh'] * conta_dados['tarifa_scee'] * 0.2457},
            {"Componente": "ICMS", "Valor": conta_dados['consumo_kwh'] * conta_dados['tarifa_scee'] * 0.19},
            {"Componente": "Iluminação Pública", "Valor": conta_dados['iluminacao_publica']},
            {"Componente": "Outros", "Valor": max(0, conta_dados['valor_fatura'] - 
                                                 (conta_dados['consumo_kwh'] * conta_dados['tarifa_scee'] * 0.2457 + 
                                                  conta_dados['consumo_kwh'] * conta_dados['tarifa_scee'] * 0.19 + 
                                                  conta_dados['iluminacao_publica']))}
        ])
        
        pizza_chart = alt.Chart(pizza_df).mark_arc(
            innerRadius=50,
            outerRadius=120
        ).encode(
            theta=alt.Theta('Valor:Q', title='Valor'),
            color=alt.Color('Componente:N', 
                           scale=alt.Scale(range=['#ef4444', '#f59e0b', '#10b981', '#3b82f6'])),
            tooltip=[
                alt.Tooltip('Componente:N', title='Componente'),
                alt.Tooltip('Valor:Q', title='Valor', format='.2f')
            ]
        ).properties(
            height=300,
            title=f"Composição da Fatura - {conta_dados['mes_referencia']}"
        )
        
        st.altair_chart(pizza_chart, use_container_width=True)

# --- Footer ---
st.divider()
st.markdown(f"""
<div style="text-align: center; color: var(--text-secondary); padding: 1rem;">
    <p>🌱 <strong>SolarAnalytics Pro</strong> - Monitoramento de Energia Solar</p>
    <p><em>Última atualização: {datetime.now().strftime('%d/%m/%Y às %H:%M')}</em></p>
</div>
""", unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.markdown("### 📊 Informações")
if not df.empty:
    st.sidebar.metric("📅 Registros", len(df))
    st.sidebar.metric("📆 Período", f"{df['Data'].min().strftime('%m/%Y')} - {df['Data'].max().strftime('%m/%Y')}")
    st.sidebar.metric("⚡ Total", f"{format_number_br(df['Energia Gerada (kWh)'].sum())} kWh")

st.sidebar.markdown("### 🔧 Controles")
if st.sidebar.button("🔄 Atualizar"):
    st.cache_data.clear()
    st.rerun()

if st.sidebar.button("❌ Sair Edição"):
    st.session_state.edit_mode = False
    st.rerun()
