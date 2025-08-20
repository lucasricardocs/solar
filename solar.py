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
from streamlit_tags import st_tags

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

# --- Configuração da Página ---
st.set_page_config(
    layout="wide",
    page_title="SolarAnalytics Pro | Dashboard Energia Solar",
    page_icon="⚡",
    initial_sidebar_state="collapsed"
)

# --- Estilo CSS Profissional Melhorado ---
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

.stApp {
    background: linear-gradient(135deg, #dcdcdc 0%, #d3d3d3 100%);
    min-height: 100vh;
}

.main .block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

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

.stForm {
    background: rgba(255, 255, 255, 0.9) !important;
    backdrop-filter: blur(10px);
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: var(--shadow);
    padding: 2rem;
    margin-bottom: 2rem;
}

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

.stSelectbox > div > div,
.stTextInput > div > div,
.stDateInput > div > div,
.stNumberInput > div > div {
    background: rgba(255, 255, 255, 0.9) !important;
    backdrop-filter: blur(5px);
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
    border-radius: 8px;
    transition: all 0.2s ease;
}

.stSelectbox > div > div:hover,
.stTextInput > div > div:hover,
.stDateInput > div > div:hover,
.stNumberInput > div > div:hover {
    background: rgba(255, 255, 255, 0.95) !important;
    border-color: var(--secondary-color) !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

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

.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    color: var(--text-primary) !important;
    font-weight: 600;
    margin-bottom: 1rem !important;
    position: relative;
    z-index: 1;
}

.vega-embed {
    background: rgba(255, 255, 255, 0.9) !important;
    backdrop-filter: blur(10px);
    border-radius: 12px;
    padding: 1rem;
    box-shadow: var(--shadow);
    border: 1px solid rgba(255, 255, 255, 0.2);
    margin-bottom: 1rem;
}

.heatmap-container {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 2rem;
    margin: 1rem 0;
    box-shadow: var(--shadow);
    border: 1px solid rgba(255, 255, 255, 0.2);
}

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

.dataframe {
    background: rgba(255, 255, 255, 0.9) !important;
    backdrop-filter: blur(10px);
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.2);
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

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
</style>
""", unsafe_allow_html=True)

# --- Inicialização do Session State ---
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False

# --- Header Profissional ---
st.markdown("""
<div class="main-container">
    <div class="header-container">
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
        '<span class="status-badge status-connected">✅ Conectado ao Google Sheets</span>', 
        unsafe_allow_html=True
    )
else:
    st.sidebar.markdown(
        '<span class="status-badge status-disconnected">❌ Erro de conexão</span>', 
        unsafe_allow_html=True
    )
    st.error("⚠️ **Sistema Offline**: Não foi possível conectar ao Google Sheets. Verifique as credenciais e tente novamente.")
    st.info("🔧 **Para administradores**: Verifique as configurações de API e permissões da planilha.")
    st.stop()

# --- Funções de Dados Melhoradas ---
@st.cache_data(ttl=300, show_spinner="📊 Carregando dados do Google Sheets...")
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
        
        # Processar datas com múltiplos formatos
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        if df['Data'].isna().any():
            # Tentar outros formatos
            df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        
        # Processar valores de energia
        df['Energia Gerada (kWh)'] = df['Energia Gerada (kWh)'].astype(str).str.replace(',', '.', regex=False)
        df['Energia Gerada (kWh)'] = pd.to_numeric(df['Energia Gerada (kWh)'], errors='coerce')
        
        # Limpar dados inválidos
        df.dropna(subset=['Data', 'Energia Gerada (kWh)'], inplace=True)
        
        # Remover valores negativos
        df = df[df['Energia Gerada (kWh)'] >= 0]
        
        # Ordenar e remover duplicatas
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
        # +2 porque a planilha começa na linha 1 (cabeçalho) e a indexação começa em 0
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
        # +2 porque a planilha começa na linha 1 (cabeçalho) e a indexação começa em 0
        sheet.delete_rows(row_index + 2)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"🚨 **Erro ao excluir**: {str(e)}")
        return False

def format_number_br(number, decimals=2):
    """Formata números no padrão brasileiro"""
    return f"{number:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- Formulário de Cadastro Melhorado ---
st.header("☀️ Registro de Geração")

with st.container():
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
            input_energy = st.number_input(
                "⚡ Energia Gerada (kWh)",
                min_value=0.0,
                max_value=999.9,
                step=0.1,
                format="%.2f",
                help="Digite o valor da energia gerada em kWh"
            )
            
        with col3:
            st.write("")
            st.write("")
            submitted = st.form_submit_button(
                "💾 Salvar", 
                use_container_width=True,
                help="Clique para salvar o registro"
            )

        if submitted:
            if input_energy > 0:
                with st.spinner("💾 Salvando dados..."):
                    if append_data(input_date, input_energy):
                        st.success("✅ **Dados salvos com sucesso!**")
                        st.balloons()
                        time.sleep(1)  # Dar tempo para mostrar a mensagem
                        st.rerun()
                    else:
                        st.error("❌ **Falha ao salvar os dados**. Tente novamente.")
            else:
                st.warning("💡 **Atenção**: Digite um valor maior que zero.")

# --- Análise de Dados ---
with st.spinner("📊 Carregando análises..."):
    df = load_data()

if df.empty:
    st.info("📊 **Nenhum dado encontrado**. Comece registrando sua primeira geração de energia solar!")
    st.markdown("""
    ### 🌟 Primeiros Passos:
    1. 📅 Selecione a data da geração
    2. ⚡ Digite o valor em kWh gerado
    3. 💾 Clique em "Salvar"
    4. 📈 Acompanhe suas estatísticas aqui!
    """)
else:
    # --- Filtros Melhorados ---
    st.header("🔍 Filtros de Análise")
    
    with st.container():
        filter_col1, filter_col2, filter_col3 = st.columns([1, 1, 2])
        
        with filter_col1:
            years = sorted(df['Data'].dt.year.unique(), reverse=True)
            selected_year = st.selectbox(
                "📅 Ano", 
                options=years, 
                key='year_filter',
                help="Selecione o ano para análise"
            )
            
        with filter_col2:
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
                    format_func=lambda x: month_names.get(x, ''), 
                    key='month_filter',
                    help="Selecione o mês para análise detalhada"
                )
            else:
                st.info("Nenhum dado disponível para este ano")
                selected_month_num = None
                
        with filter_col3:
            # Estatísticas rápidas do ano
            total_year = df[df['Data'].dt.year == selected_year]['Energia Gerada (kWh)'].sum()
            st.metric(
                f"📈 Total em {selected_year}", 
                f"{format_number_br(total_year)} kWh",
                help=f"Total de energia gerada no ano de {selected_year}"
            )

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
            
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            
            with metric_col1:
                st.metric(
                    "🔋 Total no Mês", 
                    f"{format_number_br(total)} kWh",
                    help="Energia total gerada no mês"
                )
                
            with metric_col2:
                st.metric(
                    "📈 Média Diária", 
                    f"{format_number_br(avg)} kWh",
                    help="Média diária de geração"
                )
                
            with metric_col3:
                st.metric(
                    "⭐ Melhor Dia", 
                    f"{format_number_br(best['Energia Gerada (kWh)'])} kWh",
                    delta=best['Data'].strftime('%d/%m'),
                    help="Dia com maior geração"
                )
                
            with metric_col4:
                st.metric(
                    "⚠️ Menor Dia", 
                    f"{format_number_br(worst['Energia Gerada (kWh)'])} kWh",
                    delta=worst['Data'].strftime('%d/%m'),
                    delta_color="inverse",
                    help="Dia com menor geração"
                )

            # --- Abas de Análise ---
            tab1, tab2, tab3 = st.tabs(["📊 Produção Diária", "📈 Geração Acumulada", "📋 Dados Detalhados"])
            
            with tab1:
                st.subheader("📊 Produção Diária")
                
                # Gráfico de barras melhorado
                bar_chart = alt.Chart(filtered_df).mark_bar(
                    color="#3b82f6",
                    cornerRadiusTopLeft=4,
                    cornerRadiusTopRight=4,
                    opacity=0.8
                ).encode(
                    x=alt.X(
                        'Data:T', 
                        title='Data',
                        axis=alt.Axis(
                            format='%d/%m',
                            labelAngle=-45
                        )
                    ),
                    y=alt.Y(
                        'Energia Gerada (kWh):Q', 
                        title='Energia Gerada (kWh)',
                        scale=alt.Scale(nice=True)
                    ),
                    tooltip=[
                        alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'), 
                        alt.Tooltip('Energia Gerada (kWh):Q', title='Energia Gerada', format='.2f')
                    ]
                ).properties(
                    height=400,
                    title=f"Geração Diária - {month_names.get(selected_month_num, '')} {selected_year}"
                ).configure_title(
                    fontSize=16,
                    anchor='start'
                ).interactive()
                
                st.altair_chart(bar_chart, use_container_width=True)
            
            with tab2:
                st.subheader("📈 Geração Acumulada")
                
                # Preparar dados para gráfico acumulado
                filtered_df_sorted = filtered_df.sort_values('Data').copy()
                filtered_df_sorted['Acumulado'] = filtered_df_sorted['Energia Gerada (kWh)'].cumsum()
                
                # Gráfico de área com linha
                base = alt.Chart(filtered_df_sorted).encode(
                    x=alt.X(
                        'Data:T', 
                        title='Data',
                        axis=alt.Axis(format='%d/%m')
                    )
                )

                area = base.mark_area(
                    line={'color':'#10b981', 'strokeWidth': 3}, 
                    color=alt.Gradient(
                        gradient='linear', 
                        stops=[
                            alt.GradientStop(color='#10b981', offset=0), 
                            alt.GradientStop(color='rgba(16, 185, 129, 0.4)', offset=0.5),
                            alt.GradientStop(color='rgba(16, 185, 129, 0.1)', offset=1)
                        ],
                        x1=1, x2=1, y1=1, y2=0
                    ),
                    opacity=0.7,
                    interpolate='monotone'
                ).encode(
                    y=alt.Y('Acumulado:Q', title='Energia Acumulada (kWh)'),
                    tooltip=[
                        alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'),
                        alt.Tooltip('Energia Gerada (kWh):Q', title='Geração do Dia', format='.2f'),
                        alt.Tooltip('Acumulado:Q', title='Total Acumulado', format='.2f')
                    ]
                )
                
                points = base.mark_circle(
                    size=60,
                    color='#10b981',
                    opacity=0.8,
                    stroke='white',
                    strokeWidth=2
                ).encode(
                    y=alt.Y('Acumulado:Q'),
                    tooltip=[
                        alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'),
                        alt.Tooltip('Acumulado:Q', title='Total Acumulado', format='.2f')
                    ]
                )

                chart = (area + points).properties(
                    height=400,
                    title=f"Geração Acumulada - {month_names.get(selected_month_num, '')} {selected_year}"
                ).configure_title(
                    fontSize=16,
                    anchor='start'
                ).interactive()
                
                st.altair_chart(chart, use_container_width=True)
            
            with tab3:
                st.subheader("📋 Dados Detalhados do Mês")
                
                # Preparar dados para visualização
                display_df = filtered_df.copy()
                display_df['Data_str'] = display_df['Data'].dt.strftime('%d/%m/%Y')
                display_df['Energia_str'] = display_df['Energia Gerada (kWh)'].apply(lambda x: format_number_br(x))
                
                # Mostrar tabela
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
                    st.write("")
                    st.write("")
                    if st.button("✏️ Editar Registros", use_container_width=True):
                        st.session_state.edit_mode = not st.session_state.edit_mode
                
                # Modo de edição
                if st.session_state.edit_mode:
                    st.markdown("---")
                    st.subheader("✏️ Editar Registros")
                    
                    if len(filtered_df) > 0:
                        selected_index = st.selectbox(
                            "Selecione o registro para editar", 
                            options=range(len(filtered_df)),
                            format_func=lambda x: f"{filtered_df.iloc[x]['Data'].strftime('%d/%m/%Y')} - {format_number_br(filtered_df.iloc[x]['Energia Gerada (kWh)'])} kWh"
                        )
                        
                        edit_col1, edit_col2, edit_col3 = st.columns(3)
                        
                        with edit_col1:
                            edit_date = st.date_input(
                                "📅 Data", 
                                value=filtered_df.iloc[selected_index]['Data'], 
                                format="DD/MM/YYYY",
                                key="edit_date"
                            )
                            
                        with edit_col2:
                            edit_energy = st.number_input(
                                "⚡ Energia (kWh)", 
                                value=float(filtered_df.iloc[selected_index]['Energia Gerada (kWh)']), 
                                min_value=0.0, 
                                step=0.1,
                                format="%.2f",
                                key="edit_energy"
                            )
                        
                        with edit_col3:
                            st.write("")
                            save_col, delete_col = st.columns(2)
                            
                            with save_col:
                                if st.button("💾 Salvar", use_container_width=True):
                                    with st.spinner("💾 Salvando alterações..."):
                                        original_index = filtered_df.index[selected_index]
                                        if update_data(original_index, edit_date, edit_energy):
                                            st.success("✅ Registro atualizado com sucesso!")
                                            st.session_state.edit_mode = False
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error("❌ Erro ao atualizar o registro.")
                            
                            with delete_col:
                                if st.button("🗑️ Excluir", use_container_width=True):
                                    with st.spinner("🗑️ Excluindo registro..."):
                                        original_index = filtered_df.index[selected_index]
                                        if delete_data(original_index):
                                            st.success("✅ Registro excluído com sucesso!")
                                            st.session_state.edit_mode = False
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error("❌ Erro ao excluir o registro.")

        # --- Análise Anual ---
        year_df_filtered = df[df['Data'].dt.year == selected_year].copy()
        
        if not year_df_filtered.empty:
            st.divider()
            st.header(f"📅 Resumo Anual de {selected_year}")
            
            # Preparar dados mensais
            monthly_summary = year_df_filtered.groupby(
                year_df_filtered['Data'].dt.month
            )['Energia Gerada (kWh)'].sum().reset_index()
            
            monthly_summary.rename(columns={'Data': 'Mês'}, inplace=True)
            monthly_summary['Nome Mês'] = monthly_summary['Mês'].apply(
                lambda m: month_names[m][:3]
            )
            
            # Gráfico mensal melhorado
            monthly_chart = alt.Chart(monthly_summary).mark_bar(
                color="#f59e0b",
                cornerRadiusTopLeft=4,
                cornerRadiusTopRight=4,
                opacity=0.8
            ).encode(
                x=alt.X(
                    'Nome Mês:N', 
                    title='Mês', 
                    sort=[m[:3] for m in month_names.values()],
                    axis=alt.Axis(labelAngle=0)
                ),
                y=alt.Y(
                    'Energia Gerada (kWh):Q', 
                    title='Total Mensal (kWh)',
                    scale=alt.Scale(nice=True)
                ),
                tooltip=[
                    alt.Tooltip('Nome Mês:N', title='Mês'), 
                    alt.Tooltip('Energia Gerada (kWh):Q', title='Total Gerado', format='.2f')
                ]
            ).properties(
                height=400,
                title=f"Geração Mensal - {selected_year}"
            ).configure_title(
                fontSize=16,
                anchor='start'
            ).interactive()
            
            st.altair_chart(monthly_chart, use_container_width=True)
            
            # --- HEATMAP FUNCIONAL ---
            st.markdown('<div class="heatmap-container">', unsafe_allow_html=True)
            st.subheader(f"🗓️ Calendário de Geração - {selected_year}")
            
            # Preparar dados para o heatmap
            start_date = datetime(selected_year, 1, 1)
            end_date = datetime(selected_year, 12, 31)
            
            # Criar range completo de datas do ano
            all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
            heatmap_data = pd.DataFrame({'date': all_dates})
            
            # Preparar dados existentes
            year_data = year_df_filtered.copy()
            year_data['date'] = year_data['Data'].dt.date
            year_data = year_data.groupby('date')['Energia Gerada (kWh)'].sum().reset_index()
            
            # Merge dos dados
            heatmap_data['date_only'] = heatmap_data['date'].dt.date
            heatmap_data = pd.merge(
                heatmap_data, 
                year_data, 
                left_on='date_only', 
                right_on='date', 
                how='left'
            )
            
            # Preencher valores nulos com 0
            heatmap_data['Energia Gerada (kWh)'] = heatmap_data['Energia Gerada (kWh)'].fillna(0)
            
            # Adicionar informações de calendário
            heatmap_data['day_of_year'] = heatmap_data['date'].dt.dayofyear
            heatmap_data['week'] = heatmap_data['date'].dt.isocalendar().week
            heatmap_data['day_of_week'] = heatmap_data['date'].dt.dayofweek
            heatmap_data['month'] = heatmap_data['date'].dt.month
            heatmap_data['day'] = heatmap_data['date'].dt.day
            
            # Ajustar semanas para melhor visualização
            min_week = heatmap_data['week'].min()
            heatmap_data['week_adjusted'] = heatmap_data['week'] - min_week + 1
            
            # Criar o heatmap com Altair
            heatmap_chart = alt.Chart(heatmap_data).mark_rect(
                stroke='white',
                strokeWidth=1
            ).encode(
                x=alt.X(
                    'week_adjusted:O',
                    title=None,
                    axis=alt.Axis(
                        labels=False,
                        ticks=False,
                        domain=False
                    )
                ),
                y=alt.Y(
                    'day_of_week:O',
                    title=None,
                    axis=alt.Axis(
                        labels=['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'],
                        ticks=False,
                        domain=False,
                        labelFontSize=10
                    ),
                    scale=alt.Scale(reverse=False)
                ),
                color=alt.Color(
                    'Energia Gerada (kWh):Q',
                    title='kWh',
                    scale=alt.Scale(
                        scheme='greens',
                        domain=[0, heatmap_data['Energia Gerada (kWh)'].max()],
                        type='linear'
                    ),
                    legend=alt.Legend(
                        orient='right',
                        titleFontSize=12,
                        labelFontSize=10
                    )
                ),
                tooltip=[
                    alt.Tooltip('date:T', title='Data', format='%d/%m/%Y'),
                    alt.Tooltip('Energia Gerada (kWh):Q', title='Energia Gerada', format='.2f'),
                    alt.Tooltip('month:O', title='Mês')
                ]
            ).properties(
                width=800,
                height=150,
                title=alt.TitleParams(
                    text=f"Heatmap de Geração Solar - {selected_year}",
                    fontSize=14,
                    anchor='start'
                )
            ).resolve_scale(
                color='independent'
            )
            
            # Adicionar labels dos meses
            month_labels = heatmap_data.groupby('month').agg({
                'week_adjusted': 'first',
                'date': 'first'
            }).reset_index()
            
            month_labels['month_name'] = month_labels['month'].map({
                1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
            })
            
            month_text = alt.Chart(month_labels).mark_text(
                align='left',
                baseline='middle',
                dy=-80,
                fontSize=10,
                fontWeight='bold',
                color='#374151'
            ).encode(
                x=alt.X('week_adjusted:O'),
                y=alt.value(0),
                text='month_name:N'
            )
            
            # Combinar gráficos
            final_heatmap = heatmap_chart + month_text
            
            st.altair_chart(final_heatmap, use_container_width=True)
            
            # Estatísticas do heatmap
            dias_com_geracao = (heatmap_data['Energia Gerada (kWh)'] > 0).sum()
            total_dias = len(heatmap_data)
            percentual_ativo = (dias_com_geracao / total_dias) * 100
            
            heat_col1, heat_col2, heat_col3 = st.columns(3)
            with heat_col1:
                st.metric("📅 Dias com Geração", f"{dias_com_geracao}/{total_dias}")
            with heat_col2:
                st.metric("📊 Percentual Ativo", f"{percentual_ativo:.1f}%")
            with heat_col3:
                melhor_dia = heatmap_data.loc[heatmap_data['Energia Gerada (kWh)'].idxmax()]
                st.metric(
                    "⭐ Melhor Dia do Ano", 
                    f"{format_number_br(melhor_dia['Energia Gerada (kWh)'])} kWh",
                    delta=melhor_dia['date'].strftime('%d/%m')
                )
            
            st.markdown('</div>', unsafe_allow_html=True)

            # --- Estatísticas Anuais Detalhadas ---
            st.subheader("📈 Estatísticas Detalhadas do Ano")
            
            stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
            
            year_total = year_df_filtered['Energia Gerada (kWh)'].sum()
            year_avg = year_df_filtered['Energia Gerada (kWh)'].mean()
            year_max = year_df_filtered['Energia Gerada (kWh)'].max()
            year_min = year_df_filtered['Energia Gerada (kWh)'].min()
            
            with stats_col1:
                st.metric(
                    "🏆 Total do Ano", 
                    f"{format_number_br(year_total)} kWh",
                    help="Total de energia gerada no ano"
                )
                
            with stats_col2:
                st.metric(
                    "📊 Média Diária", 
                    f"{format_number_br(year_avg)} kWh",
                    help="Média diária de geração"
                )
                
            with stats_col3:
                st.metric(
                    "⚡ Pico Máximo", 
                    f"{format_number_br(year_max)} kWh",
                    help="Maior geração em um único dia"
                )
                
            with stats_col4:
                st.metric(
                    "📉 Mínimo", 
                    f"{format_number_br(year_min)} kWh",
                    help="Menor geração registrada"
                )
            
            # Análise adicional por trimestre
            st.subheader("📊 Análise Trimestral")
            
            # Criar dados trimestrais
            year_df_filtered['trimestre'] = year_df_filtered['Data'].dt.quarter
            quarterly_data = year_df_filtered.groupby('trimestre')['Energia Gerada (kWh)'].agg([
                'sum', 'mean', 'count'
            ]).reset_index()
            
            quarterly_data.columns = ['Trimestre', 'Total', 'Média', 'Dias']
            quarterly_data['Nome'] = quarterly_data['Trimestre'].map({
                1: '1º Tri (Jan-Mar)',
                2: '2º Tri (Abr-Jun)', 
                3: '3º Tri (Jul-Set)',
                4: '4º Tri (Out-Dez)'
            })
            
            for idx, row in quarterly_data.iterrows():
                col = st.columns(4)[idx]
                with col:
                    st.metric(
                        row['Nome'],
                        f"{format_number_br(row['Total'])} kWh",
                        delta=f"{format_number_br(row['Média'])} kWh/dia"
                    )

# Fechar container principal
st.markdown("</div>", unsafe_allow_html=True)

# --- Footer Informativo ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: var(--text-secondary); margin-top: 2rem;">
    <p>🌱 <strong>SolarAnalytics Pro</strong> - Monitoramento Inteligente de Energia Solar</p>
    <p><em>Conectado ao Google Sheets | Atualização automática a cada 5 minutos</em></p>
    <p>🔄 Última atualização: {}</p>
</div>
""".format(datetime.now().strftime('%d/%m/%Y às %H:%M')), unsafe_allow_html=True)

# Adicionar informações na sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Informações do Sistema")

if not df.empty:
    st.sidebar.metric("📅 Registros Totais", len(df))
    st.sidebar.metric("📆 Período", f"{df['Data'].min().strftime('%d/%m/%Y')} - {df['Data'].max().strftime('%d/%m/%Y')}")
    st.sidebar.metric("⚡ Total Geral", f"{format_number_br(df['Energia Gerada (kWh)'].sum())} kWh")

st.sidebar.markdown("### 🔧 Controles")
if st.sidebar.button("🔄 Atualizar Dados", help="Recarregar dados do Google Sheets"):
    st.cache_data.clear()
    st.rerun()

if st.sidebar.button("❌ Sair do Modo Edição", help="Desativar modo de edição"):
    st.session_state.edit_mode = False
    st.rerun()

# Adicionar informações de ajuda
st.sidebar.markdown("### ❓ Ajuda")
st.sidebar.markdown("""
**Como usar:**
1. 📅 Selecione a data
2. ⚡ Digite a energia em kWh  
3. 💾 Clique em Salvar
4. 📊 Visualize as análises

**Recursos:**
- ✏️ Edição de registros
- 📈 Gráficos interativos
- 🗓️ Heatmap anual
- 📊 Estatísticas detalhadas
""")

# Import time para sleep
