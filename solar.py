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

# — Constantes de Configuração —
SPREADSHEET_ID = '1WI2tZ94lVV9GfaaWerdSfuChFLzWfMbU4v2m6QrwTdY'
WORKSHEET_NAME = 'solardaily'

# — Configuração da Página —
st.set_page_config(
    layout="wide",
    page_title="SolarAnalytics Pro | Dashboard Energia Solar",
    page_icon="⚡",
    initial_sidebar_state="collapsed"
)

# — Inicialização do Session State —
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False

# Inicializa o tema (padrão: claro)
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# Função para obter as cores do tema
def get_theme_colors():
    if st.session_state.dark_mode:
        return {
            'primary_color': '#ffffff',
            'secondary_color': '#60a5fa',
            'accent_color': '#34d399',
            'text_primary': '#f3f4f6',
            'text_secondary': '#d1d5db',
            'bg_main': '#111827',
            'bg_light': '#1f2937',
            'bg_card': '#374151',
            'border_light': '#4b5563',
            'header_bg': 'linear-gradient(135deg, #1f2937, #111827)',
            'subheader_bg': '#374151',
            'form_bg': '#374151',
            'metric_bg': '#374151'
        }
    else:
        return {
            'primary_color': '#1f2937',
            'secondary_color': '#3b82f6',
            'accent_color': '#10b981',
            'text_primary': '#1f2937',
            'text_secondary': '#6b7280',
            'bg_main': '#f8fafc',
            'bg_light': '#f8fafc',
            'bg_card': '#ffffff',
            'border_light': '#e2e8f0',
            'header_bg': 'linear-gradient(135deg, #e6f3ff, #f0f0f0)',
            'subheader_bg': '#ffffff',
            'form_bg': 'white',
            'metric_bg': '#ffffff'
        }

theme = get_theme_colors()

# — CSS Dinâmico baseado no tema —
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600;700&display=swap');

:root {{
    --primary-color: {theme['primary_color']};
    --secondary-color: {theme['secondary_color']};
    --accent-color: {theme['accent_color']};
    --text-primary: {theme['text_primary']};
    --text-secondary: {theme['text_secondary']};
    --bg-main: {theme['bg_main']};
    --bg-light: {theme['bg_light']};
    --bg-card: {theme['bg_card']};
    --border-light: {theme['border_light']};
}}

/* Aplica a fonte Nunito a todos os elementos */
html, body, [class*="st-"], .stApp, .main {{
    font-family: 'Nunito', sans-serif !important;
}}

.stApp {{
    background-color: var(--bg-main);
    color: var(--text-primary);
}}

.main .block-container {{
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}}

/* Header com altura reduzida e animação */
.header-section {{
    background: {theme['header_bg']};
    color: {theme['text_primary']};
    padding: 1rem 2rem;
    border-radius: 12px;
    border: 1px solid {theme['border_light']};
    margin-bottom: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    height: 120px;
    animation: headerPulse 6s ease-in-out infinite alternate;
}}

@keyframes headerPulse {{
    0% {{ 
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
        transform: scale(1);
    }}
    100% {{ 
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.2);
        transform: scale(1.01);
    }}
}}

.header-content {{
    display: flex;
    align-items: center;
    gap: 1rem;
}}

.solar-icon {{
    width: 100px;
    height: 100px;
    flex-shrink: 0;
}}

.header-text {{
    text-align: left;
}}

.header-title {{
    font-size: 1.8rem;
    font-weight: 700;
    margin-bottom: 0.2rem;
    background: linear-gradient(135deg, {theme['text_primary']}, {theme['secondary_color']});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.1;
}}

.header-subtitle {{
    font-size: 0.95rem;
    opacity: 0.8;
    font-weight: 400;
    color: {theme['text_primary']};
    margin: 0;
    line-height: 1.2;
}}

/* Padrão para containers de subheaders - BORDA LATERAL ESQUERDA APENAS */
.subheader-container {{
    margin: 20px 0;
    padding: 12px 20px;
    background: {theme['subheader_bg']};
    border-radius: 8px;
    border-left: 4px solid;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    transition: all 0.3s ease;
}}

.subheader-container:hover {{
    transform: translateX(5px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15) !important;
}}

.subheader-container.blue {{ border-left-color: #3498db; }}
.subheader-container.green {{ border-left-color: #2ecc71; }}
.subheader-container.orange {{ border-left-color: #f39c12; }}
.subheader-container.purple {{ border-left-color: #9b59b6; }}
.subheader-container.pink {{ border-left-color: #e91e63; }}
.subheader-container.teal {{ border-left-color: #1abc9c; }}

/* Ajuste do tamanho da fonte dos títulos dentro dos containers */
.subheader-container h2 {{
    font-size: 1.25rem;
    font-weight: 600;
    margin: 0;
    color: {theme['text_primary']};
}}

.subheader-container h3 {{
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0;
    color: {theme['text_primary']};
}}

/* Cards com borda mínima */
[data-testid="metric-container"] {{
    background: {theme['metric_bg']};
    border: 1px solid {theme['border_light']};
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}}

/* Forms com borda mínima */
.stForm {{
    background: {theme['form_bg']};
    border: 1px solid {theme['border_light']};
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 2rem;
}}

/* Inputs e elementos do Streamlit */
.stSelectbox > div > div {{
    background-color: {theme['bg_card']};
    color: {theme['text_primary']};
}}

.stDateInput > div > div > input {{
    background-color: {theme['bg_card']};
    color: {theme['text_primary']};
}}

.stNumberInput > div > div > input {{
    background-color: {theme['bg_card']};
    color: {theme['text_primary']};
}}

.stTextInput > div > div > input {{
    background-color: {theme['bg_card']};
    color: {theme['text_primary']};
}}

/* Status badges */
.status-badge {{
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    display: inline-block;
}}

.status-connected {{ background-color: #10B98120; color: #10B981; }}
.status-disconnected {{ background-color: #EF444420; color: #EF4444; }}

/* Explicações dos indicadores econômicos */
.economic-explanation {{
    background: {theme['bg_card']};
    border: 1px solid {theme['border_light']};
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
    font-size: 0.9rem;
    color: {theme['text_secondary']};
}}

.economic-explanation h4 {{
    color: {theme['text_primary']};
    margin-top: 0;
    margin-bottom: 0.5rem;
    font-size: 1rem;
    font-weight: 600;
}}

.economic-explanation ul {{
    margin: 0.5rem 0;
    padding-left: 1.2rem;
}}

.economic-explanation li {{
    margin-bottom: 0.3rem;
}}

/* Hide Streamlit elements */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

# — TEMA DOS GRÁFICOS —
def configure_altair_theme():
    """Configura um tema global para todos os gráficos Altair baseado no tema atual."""
    font = "Nunito"
    
    # Cores baseadas no tema
    if st.session_state.dark_mode:
        bg_color = "#374151"
        text_color = "#f3f4f6"
        grid_color = "#4b5563"
        tick_color = "#d1d5db"
    else:
        bg_color = "transparent"
        text_color = "#1f2937"
        grid_color = "#e2e8f0"
        tick_color = "#6b7280"
    
    # Desativa o tema padrão para começar do zero
    alt.themes.enable('none')
    
    # Registra e ativa o tema customizado
    alt.themes.register("custom_theme", lambda: {
        "config": {
            "background": bg_color,
            "view": {
                "fill": bg_color,
                "strokeWidth": 0
            },
            "title": {
                "font": font,
                "fontSize": 0,
                "fontWeight": 0,
                "anchor": "middle",
                "color": "transparent"
            },
            "axis": {
                "labelFont": font,
                "titleFont": font,
                "labelFontSize": 11,
                "titleFontSize": 0,
                "gridColor": grid_color,
                "domain": False,
                "tickColor": tick_color,
                "labelColor": tick_color,
                "titleColor": "transparent",
                "titleFontWeight": 0,
                "labelFontWeight": 400,
                "title": None
            },
            "legend": {
                "labelFont": font,
                "titleFont": font,
                "labelFontSize": 11,
                "titleFontSize": 12,
                "titleFontWeight": 600,
                "labelColor": tick_color,
                "titleColor": text_color
            }
        }
    })
    alt.themes.enable("custom_theme")

# Aplica o tema aos gráficos
configure_altair_theme()

# — Header —
st.markdown("""
<div class="header-section">
    <div class="header-content">
        <img src="https://raw.githubusercontent.com/lucasricardocs/solar/refs/heads/main/solar.png" 
             class="solar-icon" 
             alt="Solar Icon"
             onerror="this.style.display='none'">
        <div class="header-text">
            <div class="header-title">⚡ SolarAnalytics Pro</div>
            <div class="header-subtitle">Monitoramento Inteligente de Geração de Energia Solar</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# — Conexão com Google Sheets —
@st.cache_resource(show_spinner="🔌 Conectando ao Google Sheets…")
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

        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.worksheet(WORKSHEET_NAME)
        
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

# — Funções de Dados —
@st.cache_data(ttl=300, show_spinner="📊 Carregando dados…")
def load_data():
    """Carrega e processa os dados da planilha"""
    try:
        values = sheet.get_all_values()

        if len(values) < 2: 
            return pd.DataFrame()
        
        df = pd.DataFrame(values[1:], columns=values[0])
        df.columns = [col.lower().strip() for col in df.columns]
        
        if 'data' not in df.columns or 'gerado' not in df.columns:
            st.error("⚠️ **Erro de Configuração**: A planilha deve conter as colunas 'data' e 'gerado'.")
            return pd.DataFrame()
        
        df.rename(columns={
            'data': 'Data', 
            'gerado': 'Energia Gerada (kWh)'
        }, inplace=True)
        
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        if df['Data'].isna().any():
            df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        
        df['Energia Gerada (kWh)'] = df['Energia Gerada (kWh)'].astype(str).str.replace(',', '.', regex=False)
        df['Energia Gerada (kWh)'] = pd.to_numeric(df['Energia Gerada (kWh)'], errors='coerce')
        
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

# — NOVA FUNÇÃO: Cálculo Financeiro Lei 14.300 —
def calcular_economia_lei14300(geracao_total, tarifa_cheia, tarifa_fio_b, simultaneidade_percent):
    """Calcula a economia real considerando a taxação progressiva do Fio B."""
    fator = simultaneidade_percent / 100.0
    
    # 1. Energia Autoconsumida (Isenta)
    autoconsumo = geracao_total * fator
    economia_autoconsumo = autoconsumo * tarifa_cheia
    
    # 2. Energia Injetada (Taxada)
    injecao = geracao_total * (1 - fator)
    
    # Regra de Transição: % cobrado sobre o Fio B
    ano_atual = datetime.now().year
    tabela = {2023: 0.15, 2024: 0.30, 2025: 0.45, 2026: 0.60, 2027: 0.75, 2028: 0.90}
    percentual_taxa = tabela.get(ano_atual, 1.0)
    
    custo_pedagio = injecao * (tarifa_fio_b * percentual_taxa)
    economia_injecao = (injecao * tarifa_cheia) - custo_pedagio
    
    return {
        "economia_reais": economia_autoconsumo + economia_injecao,
        "taxa_paga": custo_pedagio,
        "kwh_autoconsumo": autoconsumo,
        "percentual_taxa": percentual_taxa * 100
    }

# — Formulário de Cadastro —
st.markdown("""
<div class="subheader-container blue">
    <h2>☀️ Registro de Geração</h2>
</div>
""", unsafe_allow_html=True)

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

# — Análise de Dados —
df = load_data()

if df.empty:
    st.info("📊 **Nenhum dado encontrado**. Comece registrando sua primeira geração de energia solar!")
else:
    # — CONTROLES ADICIONAIS NA SIDEBAR (Lei 14.300) —
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💰 Configuração Financeira (Lei 14.300)")
    
    tarifa_cheia = st.sidebar.number_input("Tarifa Cheia (R$/kWh)", value=0.9555, format="%.4f")
    tarifa_fio_b = st.sidebar.number_input("Tarifa Fio B (R$/kWh)", value=0.4900, format="%.4f")
    fator_simultaneidade = st.sidebar.slider("Fator de Simultaneidade (%)", 0, 100, 30)
    
    investimento_inicial = st.sidebar.number_input("Investimento (R$)", value=15000.0)
    data_instalacao = st.sidebar.date_input("Data Instalação", datetime(2025, 5, 1))

    # — Filtros —
    st.markdown("""
    <div class="subheader-container green">
        <h2>🔍 Filtros de Análise</h2>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        # Lógica para pré-selecionar o ano atual
        years = sorted(df['Data'].dt.year.unique(), reverse=True)
        current_year = datetime.now().year
        year_index = 0 
        if current_year in years:
            year_index = years.index(current_year)
            
        selected_year = st.selectbox("📅 Ano", options=years, index=year_index)
        
    with col2:
        # Lógica para pré-selecionar o mês atual
        months = sorted(df[df['Data'].dt.year == selected_year]['Data'].dt.month.unique())
        month_names = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        
        selected_month_num = None
        if months:
            current_month = datetime.now().month
            month_index = 0
            if current_month in months:
                month_index = months.index(current_month)
            else:
                month_index = len(months) - 1
            selected_month_num = st.selectbox(
                "📊 Mês", 
                options=months, 
                format_func=lambda x: month_names.get(x, ''),
                index=month_index
            )
        else:
            st.info("Nenhum dado disponível para este ano")

    if selected_month_num is not None:
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
            
            st.markdown(f"""
            <div class="subheader-container orange">
                <h2>📊 Análise de {month_names.get(selected_month_num, '')} de {selected_year}</h2>
            </div>
            """, unsafe_allow_html=True)
            
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
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Produção Diária", "📈 Geração Acumulada", "📅 Acumulada Anual", "📋 Dados"])
            
            with tab1:
                # --- GRÁFICO DE GERAÇÃO DIÁRIA (BARRAS ADAPTATIVAS) ---
                # A alteração principal está aqui: removido size=35
                bar_chart = alt.Chart(filtered_df).mark_bar(
                    color="green",
                    cornerRadiusTopLeft=3,
                    cornerRadiusTopRight=3,
                    stroke="black",
                    strokeWidth=1,
                    # size=35 FOI REMOVIDO para que as barras sejam adaptativas
                ).encode(
                    x=alt.X(
                        'Data:O',  # Mudamos de :T para :O (Ordinal)
                        timeUnit='date',  # Extrai apenas o dia (1, 2, 3...)
                        title='',
                        axis=alt.Axis(labelAngle=0), # Mantém os números retos
                        scale=alt.Scale(padding=0.075) # 0.05 = Barras bem grossas (5% de espaço)
                    ),
                    y=alt.Y('Energia Gerada (kWh):Q', title=''),
                    tooltip=[
                        alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'), 
                        alt.Tooltip('Energia Gerada (kWh):Q', title='Energia', format='.2f')
                    ]
                )
                
                media_diaria = filtered_df['Energia Gerada (kWh)'].mean()
                linha_media = alt.Chart(pd.DataFrame({'media': [media_diaria]})).mark_rule(
                    color='red',
                    strokeWidth=2,
                ).encode(
                    y=alt.Y('media:Q'),
                    tooltip=alt.value(f'Média: {format_number_br(media_diaria)} kWh')
                )
                
                final_chart = (bar_chart + linha_media).properties(
                    height=400,
                    title=''
                )
                
                st.altair_chart(final_chart, use_container_width=True)
                st.divider()
            
            with tab2:
                filtered_df_sorted = filtered_df.sort_values('Data').copy()
                filtered_df_sorted['Acumulado'] = filtered_df_sorted['Energia Gerada (kWh)'].cumsum()
                
                area_chart = alt.Chart(filtered_df_sorted).mark_area(
                    line={'color':'darkgreen'},
                    color=alt.Gradient(
                        gradient='linear',
                        stops=[alt.GradientStop(color='white', offset=0),
                               alt.GradientStop(color='darkgreen', offset=1)],
                        x1=1,
                        x2=1,
                        y1=1,
                        y2=0
                    ),
                    interpolate='monotone'
                ).encode(
                    x=alt.X('Data:T', title=''),
                    y=alt.Y('Acumulado:Q', title=''),
                    tooltip=[
                        alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'),
                        alt.Tooltip('Energia Gerada (kWh):Q', title='Geração', format='.2f'),
                        alt.Tooltip('Acumulado:Q', title='Acumulado', format='.2f')
                    ]
                ).properties(
                    height=400,
                    title=''
                )
                
                st.altair_chart(area_chart, use_container_width=True)
                st.divider()
            
            with tab3:
                # --- ABA 3: ACUMULADA ANUAL ---
                year_df = df[df['Data'].dt.year == selected_year].copy()
                year_df_sorted = year_df.sort_values('Data').copy()
                year_df_sorted['Acumulado Anual'] = year_df_sorted['Energia Gerada (kWh)'].cumsum()
                
                area_chart_annual = alt.Chart(year_df_sorted).mark_area(
                    line={'color':'#8b5cf6'},
                    color=alt.Gradient(
                        gradient='linear',
                        stops=[alt.GradientStop(color='white', offset=0),
                               alt.GradientStop(color='#8b5cf6', offset=1)],
                        x1=1,
                        x2=1,
                        y1=1,
                        y2=0
                    ),
                    interpolate='monotone'
                ).encode(
                    x=alt.X('Data:T', title=''),
                    y=alt.Y('Acumulado Anual:Q', title=''),
                    tooltip=[
                        alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'),
                        alt.Tooltip('Energia Gerada (kWh):Q', title='Geração do Dia', format='.2f'),
                        alt.Tooltip('Acumulado Anual:Q', title='Acumulado no Ano', format='.2f')
                    ]
                ).properties(
                    height=400,
                    title=''
                )
                
                st.altair_chart(area_chart_annual, use_container_width=True)
                
                # Métricas do acumulado anual
                col1, col2, col3 = st.columns(3)
                
                current_date = datetime(selected_year, selected_month_num, 1)
                end_of_month = datetime(selected_year, selected_month_num, 
                                        pd.Timestamp(selected_year, selected_month_num, 1).days_in_month)
                
                acumulado_ate_mes = year_df[year_df['Data'] <= end_of_month]['Energia Gerada (kWh)'].sum()
                total_year = year_df['Energia Gerada (kWh)'].sum()
                
                meses_completos = len(year_df.groupby(year_df['Data'].dt.month))
                if meses_completos > 0:
                    media_mensal = acumulado_ate_mes / meses_completos
                    projecao_anual = media_mensal * 12
                else:
                    projecao_anual = 0
                
                with col1:
                    st.metric("📊 Acumulado até o Mês", f"{format_number_br(acumulado_ate_mes)} kWh")
                with col2:
                    st.metric("📈 Total do Ano", f"{format_number_br(total_year)} kWh")
                with col3:
                    st.metric("🎯 Projeção Anual", f"{format_number_br(projecao_anual)} kWh")
                
                st.divider()
            
            with tab4:
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
    
    year_df = df[df['Data'].dt.year == selected_year].copy()
    
    if not year_df.empty:
        st.markdown(f"""
        <div class="subheader-container purple">
            <h2>📅 Resumo Anual de {selected_year}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        monthly_summary = year_df.groupby(
            year_df['Data'].dt.month
        )['Energia Gerada (kWh)'].sum().reset_index()
        
        monthly_summary.rename(columns={'Data': 'Mês'}, inplace=True)
        monthly_summary['Nome Mês'] = monthly_summary['Mês'].apply(
            lambda m: month_names[m][:3]
        )
        
        # --- GRÁFICO MENSAL (BARRAS ADAPTATIVAS) ---
        monthly_bars = alt.Chart(monthly_summary).mark_bar(
            color="#f59e0b",
            cornerRadiusTopLeft=2,
            cornerRadiusTopRight=2,
            stroke="black",
            strokeWidth=1,
            # size=50 REMOVIDO para largura variável
        ).encode(
            x=alt.X(
                'Nome Mês:N', 
                title='',
                sort=[m[:3] for m in month_names.values()],
                scale=alt.Scale(padding=0.1) # Barras largas
            ),
            y=alt.Y('Energia Gerada (kWh):Q', title=''),
            tooltip=[
                alt.Tooltip('Nome Mês:N', title='Mês'), 
                alt.Tooltip('Energia Gerada (kWh):Q', title='Total', format='.2f')
            ]
        )
        
        media_mensal = monthly_summary['Energia Gerada (kWh)'].mean()
        linha_media_mensal = alt.Chart(pd.DataFrame({'media': [media_mensal]})).mark_rule(
            color='red',
            strokeWidth=2,
        ).encode(
            y=alt.Y('media:Q'),
            tooltip=alt.value(f'Média Mensal: {format_number_br(media_mensal)} kWh')
        )
        
        monthly_chart = (monthly_bars + linha_media_mensal).properties(
            height=400,
            title=''
        )
        
        st.altair_chart(monthly_chart, use_container_width=True)
        st.divider()
        
        # --- HEATMAP ATUALIZADO ---
        st.markdown("""
        <div class="subheader-container teal">
            <h3>🗓️ Heatmap de Geração Anual</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Criação do calendário do ano inteiro
        start_date = datetime(selected_year, 1, 1)
        end_date = datetime(selected_year, 12, 31)
        all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
        heatmap_df = pd.DataFrame({'date': all_dates})
        
        year_data_heat = year_df.copy()
        year_data_heat['date'] = pd.to_datetime(year_data_heat['Data'])
        heatmap_df = pd.merge(
            heatmap_df,
            year_data_heat[['date', 'Energia Gerada (kWh)']],
            on='date', how='left'
        ).fillna(0)
        
        # Colunas auxiliares
        heatmap_df['day_of_week'] = heatmap_df['date'].dt.dayofweek
        heatmap_df['month'] = heatmap_df['date'].dt.month
        heatmap_df['week_num'] = heatmap_df['date'].dt.isocalendar().week
        
        # Ajustes para semanas quebradas
        heatmap_df.loc[(heatmap_df['week_num'] >= 52) & (heatmap_df['month'] == 1), 'week_num'] = 0
        heatmap_df.loc[(heatmap_df['week_num'] == 1) & (heatmap_df['month'] == 12), 'week_num'] = 54
        
        # Heatmap (retângulos dos dias)
        heatmap_grid = alt.Chart(heatmap_df).mark_rect(
            cornerRadius=2,
            stroke='#d3d3d3',
            strokeWidth=0.5
        ).encode(
            x=alt.X(
                'week_num:O',
                title=None,
                axis=alt.Axis(labels=False, ticks=False, domain=False),
                scale=alt.Scale(padding=0.02)
            ),
            y=alt.Y(
                'day_of_week:O',
                title=None,
                axis=alt.Axis(
                    labelExpr="['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'][datum.value]",
                    ticks=False,
                    domain=False 
                ),
                scale=alt.Scale(padding=0.04)
            ),
            color=alt.condition(
                alt.datum['Energia Gerada (kWh)'] > 0,
                alt.Color(
                    'Energia Gerada (kWh):Q',
                    scale=alt.Scale(
                        scheme='goldgreen',
                        domainMin=10,
                        domainMax=28
                    ),
                    legend=alt.Legend(title="kWh Gerado")
                ),
                alt.value('#eeeeee')
            ),
            tooltip=[
                alt.Tooltip('date:T', title='Data', format='%d/%m/%Y'),
                alt.Tooltip('Energia Gerada (kWh):Q', title='Geração', format='.2f')
            ]
        ).properties(height=250)
        
        # Rótulos dos meses acima do primeiro dia de cada mês
        month_starts = heatmap_df.groupby('month').agg(first_week=('week_num', 'min')).reset_index()
        month_starts['month_name'] = month_starts['month'].apply(lambda m: month_names[m][:3])
        
        month_labels_chart = alt.Chart(month_starts).mark_text(
            align='left', baseline='bottom', dx=1,
            font='Nunito', fontSize=11, color='#6b7280'
        ).encode(
            x=alt.X('first_week:O', title=None, axis=None),
            text='month_name:N'
        ).properties(height=15)
        
        # Combinação final
        final_heatmap = alt.vconcat(
            month_labels_chart,
            heatmap_grid,
            spacing=25
        ).properties(
            title=''
        ).resolve_scale(
            x='shared'
        ).configure_view(
            strokeWidth=0
        )
        
        st.altair_chart(final_heatmap, use_container_width=True)
        st.divider()
        
        # --- Análise de Viabilidade Econômica (ATUALIZADA COM LEI 14.300) ---
        st.markdown("""
        <div class="subheader-container pink">
            <h3>💰 Análise de Viabilidade Econômica (Lei 14.300)</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Parâmetros do sistema solar (AGORA NA VARIÁVEL, VINDO DO SIDEBAR)
        # INVESTIMENTO_INICIAL, TARIFA_ENERGIA, ETC já foram definidos acima
        
        # Cálculos básicos
        year_total = year_df['Energia Gerada (kWh)'].sum()
        
        # LÓGICA FINANCEIRA FIO B
        financas_periodo = calcular_economia_lei14300(year_total, tarifa_cheia, tarifa_fio_b, fator_simultaneidade)
        economia_anual_reais = financas_periodo['economia_reais']
        
        # Payback simples (anos)
        payback_simples = investimento_inicial / economia_anual_reais if economia_anual_reais > 0 else 0
        
        # Economia total em 25 anos
        vida_util = 25
        economia_total_25_anos = economia_anual_reais * vida_util
        
        # ROI
        roi_percentual = ((economia_total_25_anos - investimento_inicial) / investimento_inicial) * 100 if investimento_inicial > 0 else 0
        
        # Tempo decorrido desde instalação
        hoje = datetime.now()
        meses_funcionamento = max(1, (hoje.year - data_instalacao.year) * 12 + (hoje.month - data_instalacao.month))
        
        # Valor já economizado (Considerando todo o histórico do DF principal)
        total_historico = df['Energia Gerada (kWh)'].sum()
        financas_historico = calcular_economia_lei14300(total_historico, tarifa_cheia, tarifa_fio_b, fator_simultaneidade)
        valor_ja_economizado = financas_historico['economia_reais']
        
        percentual_recuperado = (valor_ja_economizado / investimento_inicial) * 100
        
        # TIR estimada
        tir_anual = (economia_anual_reais / investimento_inicial) * 100
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("💰 Economia Líquida (Ano)", f"R$ {format_number_br(economia_anual_reais)}")
            st.metric("⏱️ Payback Simples", f"{payback_simples:.1f} anos")
            st.metric("💸 Taxa Paga (Fio B)", f"R$ {format_number_br(financas_periodo['taxa_paga'])}")
        
        with col2:
            st.metric("📈 ROI (25 anos)", f"{roi_percentual:.1f}%")
            st.metric("⚡ Fator Simultaneidade", f"{fator_simultaneidade}%")
            st.metric("🎯 TIR Estimada", f"{tir_anual:.1f}% a.a.")
        with col3:
            st.metric("💵 Já Economizado (Total)", f"R$ {format_number_br(valor_ja_economizado)}")
            st.metric("🔄 Investimento Recuperado", f"{percentual_recuperado:.1f}%")
        
        # --- EXPLICAÇÕES DOS INDICADORES ECONÔMICOS ---
        st.markdown("""
        <div class="economic-explanation">
            <h4>📚 Entenda os Indicadores (Lei 14.300):</h4>
            <ul>
                <li><strong>💰 Economia Líquida:</strong> Economia real na conta, já descontando a taxação do Fio B sobre a energia injetada.</li>
                <li><strong>💸 Taxa Paga (Fio B):</strong> Valor pago à concessionária pelo uso da rede de distribuição.</li>
                <li><strong>⚡ Fator Simultaneidade:</strong> Porcentagem da energia consumida instantaneamente (não paga taxa). Quanto maior, melhor.</li>
                <li><strong>⏱️ Payback Simples:</strong> Tempo para o sistema se pagar com a economia atual.</li>
                <li><strong>📈 ROI:</strong> Retorno sobre o investimento em 25 anos.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Gráfico de Fluxo de Caixa Projetado
        st.markdown("##### 📈 Fluxo de Caixa Projetado (25 anos)")
        
        # Criando dados para o gráfico de fluxo de caixa
        anos = list(range(0, vida_util + 1))
        fluxo_caixa_acumulado = [-investimento_inicial]
        
        for ano in range(1, vida_util + 1):
            # Degradação dos painéis (0.5% ao ano)
            fator_degradacao = (1 - 0.005) ** ano
            economia_ano = economia_anual_reais * fator_degradacao
            fluxo_caixa_acumulado.append(fluxo_caixa_acumulado[-1] + economia_ano)
        
        fluxo_df = pd.DataFrame({
            'Ano': anos,
            'Fluxo de Caixa Acumulado': fluxo_caixa_acumulado
        })
        
        # Gráfico de linha para fluxo de caixa
        fluxo_chart = alt.Chart(fluxo_df).mark_line(
            color='#10b981',
            strokeWidth=2,
            point={'filled': True, 'size': 50}
        ).encode(
            x=alt.X('Ano:O', title=''),
            y=alt.Y('Fluxo de Caixa Acumulado:Q', title=''),
            tooltip=[
                alt.Tooltip('Ano:O', title='Ano'),
                alt.Tooltip('Fluxo de Caixa Acumulado:Q', title='Acumulado', format=',.0f')
            ]
        )
        
        # Linha do zero (break-even)
        linha_zero = alt.Chart(pd.DataFrame({'zero': [0]})).mark_rule(
            color='red',
            strokeWidth=1,
            strokeDash=[5, 5]
        ).encode(
            y=alt.Y('zero:Q'),
            tooltip=alt.value('Break-even')
        )
        
        fluxo_final = (fluxo_chart + linha_zero).properties(
            height=350,
            title=''
        )
        
        st.altair_chart(fluxo_final, use_container_width=True)
        
        # Análises Complementares
        st.markdown("##### 🔍 Indicadores de Performance")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            vpl_simples = economia_total_25_anos - investimento_inicial
            st.metric("💎 VPL Simples", f"R$ {format_number_br(vpl_simples)}")
        
        with col2:
            custo_energia_rede_25_anos = 363.88 * 12 * tarifa_cheia * vida_util # Usando média fixa antiga ou poderia ser input
            economia_vs_rede = economia_total_25_anos / custo_energia_rede_25_anos * 100 if custo_energia_rede_25_anos > 0 else 0
            st.metric("🔋 Economia vs Rede", f"{economia_vs_rede:.1f}%")
        
        with col3:
            potencia_estimada = 10
            produtividade_anual = (year_total / potencia_estimada) if potencia_estimada > 0 else 0
            st.metric("⚡ Produtividade", f"{format_number_br(produtividade_anual)} kWh/kW.ano")
        
        with col4:
            tempo_restante_payback = max(0, payback_simples - (meses_funcionamento / 12))
            st.metric("⏳ Restam p/ Payback", f"{tempo_restante_payback:.1f} anos")

# — Footer —
st.divider()
st.markdown(f"""
<div style="text-align: center; color: var(--text-secondary); padding: 0.1rem; font-size: 0.9rem;">
    <p>🌱 <strong>SolarAnalytics Pro</strong> - Monitoramento de Energia Solar</p>
    <p><em>Última atualização: {datetime.now().strftime('%d/%m/%Y às %H:%M')}</em></p>
</div>
""", unsafe_allow_html=True)

# — Sidebar com Controle de Tema —
st.sidebar.markdown("### 🎨 Tema")
theme_icon = "🌙" if st.session_state.dark_mode else "☀️"
theme_text = "Modo Claro" if st.session_state.dark_mode else "Modo Escuro"

if st.sidebar.button(f"{theme_icon} {theme_text}", use_container_width=True, key="theme_toggle"):
    st.session_state.dark_mode = not st.session_state.dark_mode
    st.rerun()

st.sidebar.markdown("### 📊 Informações")
if not df.empty:
    st.sidebar.metric("📅 Registros", len(df))
    st.sidebar.metric("📆 Período", f"{df['Data'].min().strftime('%m/%Y')} - {df['Data'].max().strftime('%m/%Y')}")
    st.sidebar.metric("⚡ Total", f"{format_number_br(df['Energia Gerada (kWh)'].sum())} kWh")

st.sidebar.markdown("### 🔧 Controles")
if st.sidebar.button("🔄 Atualizar"):
    st.cache_data.clear()
    configure_altair_theme()
    st.rerun()

if st.session_state.edit_mode:
    if st.sidebar.button("❌ Sair do Modo Edição"):
        st.session_state.edit_mode = False
        st.rerun()
