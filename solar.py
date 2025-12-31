# -*- coding: utf-8 -*-
"""
SolarAnalytics Pro - Sistema Integrado de Monitoramento Fotovoltaico
Versão: 4.0.0 (Full Enterprise)
Compatibilidade: Lei 14.300 (Taxação do Sol)
"""

import pandas as pd
import numpy as np
import streamlit as st
import gspread
import time
from datetime import datetime, timedelta, date
from google.oauth2.service_account import Credentials
import warnings
import altair as alt
import locale

# ==============================================================================
# 1. CONFIGURAÇÕES GLOBAIS E INICIALIZAÇÃO
# ==============================================================================

# Ignora avisos futuros do pandas para manter o log limpo
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', message='.*observed=False.*')

# Configuração do Altair para lidar com datasets maiores via JSON
alt.data_transformers.enable('json')

# Configuração de Localidade (Tentativa de forçar PT-BR para moedas e datas)
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR')
    except:
        # Fallback silencioso para padrão do sistema
        pass

# Constantes de Conexão
SPREADSHEET_ID = '1WI2tZ94lVV9GfaaWerdSfuChFLzWfMbU4v2m6QrwTdY'
WORKSHEET_NAME = 'solardaily'

# Configuração da Página Streamlit (Layout Wide para Dashboard)
st.set_page_config(
    layout="wide",
    page_title="SolarAnalytics Pro | Dashboard Energia Solar",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# Inicialização do Session State
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False

if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

# ==============================================================================
# 2. SISTEMA DE TEMAS E ESTILIZAÇÃO (CSS AVANÇADO)
# ==============================================================================

def get_theme_colors():
    """
    Retorna o dicionário de cores baseado no estado atual (Claro/Escuro).
    No modo escuro, prioriza alto contraste para legibilidade.
    """
    if st.session_state.dark_mode:
        return {
            'mode': 'dark',
            'primary_color': '#FFFFFF',      # Títulos em Branco Puro
            'secondary_color': '#22D3EE',    # Ciano Neon (Destaques)
            'accent_color': '#34D399',       # Verde Esmeralda (Sucesso/Geração)
            'warning_color': '#FACC15',      # Amarelo (Alertas)
            'danger_color': '#FB7185',       # Rosa/Vermelho (Erro)
            'text_primary': '#F1F5F9',       # Cinza muito claro (Slate 100)
            'text_secondary': '#94A3B8',     # Cinza médio (Slate 400)
            'bg_main': '#020617',            # Azul Quase Preto (Slate 950) - Fundo Profundo
            'bg_light': '#0F172A',           # Slate 900 - Fundo de Seções
            'bg_card': '#1E293B',            # Slate 800 - Cards
            'border_light': '#334155',       # Slate 700 - Bordas sutis
            'header_bg': 'linear-gradient(135deg, #0F172A 0%, #020617 100%)',
            'subheader_bg': '#0F172A',
            'form_bg': '#1E293B',
            'metric_bg': '#1E293B',
            'heatmap_stroke': '#334155',     # Borda dos quadrados do heatmap
            'heatmap_zero': '#0F172A',       # Cor para valor zero
            'chart_grid': '#334155'          # Grid dos gráficos
        }
    else:
        return {
            'mode': 'light',
            'primary_color': '#111827',      # Cinza Escuro (Gray 900)
            'secondary_color': '#3B82F6',    # Azul Real (Blue 500)
            'accent_color': '#10B981',       # Verde (Emerald 500)
            'warning_color': '#F59E0B',      # Laranja
            'danger_color': '#EF4444',       # Vermelho
            'text_primary': '#1F2937',       # Gray 800
            'text_secondary': '#6B7280',     # Gray 500
            'bg_main': '#F8FAFC',            # Slate 50 - Fundo Claro
            'bg_light': '#FFFFFF',           # Branco
            'bg_card': '#FFFFFF',            # Branco
            'border_light': '#E2E8F0',       # Slate 200
            'header_bg': 'linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%)',
            'subheader_bg': '#FFFFFF',
            'form_bg': '#FFFFFF',
            'metric_bg': '#FFFFFF',
            'heatmap_stroke': '#E2E8F0',
            'heatmap_zero': '#F1F5F9',
            'chart_grid': '#E5E7EB'
        }

theme = get_theme_colors()

# Aplicação do CSS Dinâmico
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600;700;800&display=swap');

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

/* Reset Global */
html, body, [class*="st-"], .stApp {{
    font-family: 'Nunito', sans-serif !important;
    background-color: var(--bg-main) !important;
    color: var(--text-primary) !important;
}}

.main .block-container {{
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1400px;
}}

/* --- Header Personalizado --- */
.header-section {{
    background: {theme['header_bg']};
    color: {theme['text_primary']};
    padding: 1.5rem 2rem;
    border-radius: 16px;
    border: 1px solid {theme['border_light']};
    margin-bottom: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    transition: all 0.3s ease;
}}

.header-section:hover {{
    border-color: {theme['secondary_color']};
    transform: translateY(-2px);
}}

.header-title {{
    font-size: 2.2rem;
    font-weight: 800;
    margin-bottom: 0.25rem;
    background: linear-gradient(120deg, {theme['text_primary']}, {theme['secondary_color']});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1.2;
}}

.header-subtitle {{
    font-size: 1rem;
    opacity: 0.9;
    font-weight: 500;
    color: {theme['text_secondary']};
    margin: 0;
}}

/* --- Subheaders Estilizados --- */
.subheader-container {{
    margin: 25px 0 15px 0;
    padding: 12px 20px;
    background: {theme['subheader_bg']};
    border-radius: 8px;
    border-left: 5px solid;
    border-top: 1px solid {theme['border_light']};
    border-right: 1px solid {theme['border_light']};
    border-bottom: 1px solid {theme['border_light']};
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    display: flex;
    align-items: center;
}}

.subheader-container h2 {{
    font-size: 1.25rem;
    font-weight: 700;
    margin: 0;
    color: {theme['text_primary']};
}}

.subheader-container.blue {{ border-left-color: #3b82f6; }}
.subheader-container.green {{ border-left-color: #10b981; }}
.subheader-container.orange {{ border-left-color: #f59e0b; }}
.subheader-container.purple {{ border-left-color: #8b5cf6; }}
.subheader-container.pink {{ border-left-color: #ec4899; }}
.subheader-container.teal {{ border-left-color: #14b8a6; }}

/* --- Métricas (KPI Cards) --- */
[data-testid="metric-container"] {{
    background-color: {theme['metric_bg']};
    border: 1px solid {theme['border_light']};
    border-radius: 12px;
    padding: 1rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    transition: transform 0.2s;
}}

[data-testid="metric-container"]:hover {{
    transform: scale(1.02);
    border-color: {theme['secondary_color']};
}}

[data-testid="metric-label"] {{
    font-size: 0.9rem !important;
    color: {theme['text_secondary']} !important;
    font-weight: 600 !important;
}}

[data-testid="metric-value"] {{
    font-size: 1.8rem !important;
    color: {theme['text_primary']} !important;
    font-weight: 800 !important;
}}

/* --- Formulários e Inputs --- */
.stForm {{
    background-color: {theme['form_bg']};
    border: 1px solid {theme['border_light']};
    border-radius: 12px;
    padding: 2rem;
}}

/* Estilização profunda de inputs para dark mode */
.stTextInput > div > div, 
.stNumberInput > div > div, 
.stDateInput > div > div, 
.stSelectbox > div > div {{
    background-color: {theme['bg_card']} !important;
    color: {theme['text_primary']} !important;
    border-color: {theme['border_light']} !important;
    border-radius: 8px;
}}

/* Hover nos inputs */
.stTextInput:hover > div > div, 
.stNumberInput:hover > div > div {{
    border-color: {theme['secondary_color']} !important;
}}

/* Botões */
button[kind="secondary"] {{
    background-color: {theme['bg_card']};
    border: 1px solid {theme['border_light']};
    color: {theme['text_primary']};
    border-radius: 8px;
    transition: all 0.2s;
}}

button[kind="secondary"]:hover {{
    background-color: {theme['bg_light']};
    border-color: {theme['secondary_color']};
    color: {theme['secondary_color']};
}}

button[kind="primary"] {{
    background-color: {theme['secondary_color']};
    color: #ffffff;
    border: none;
    border-radius: 8px;
    font-weight: 700;
}}

/* --- Badges e Utilitários --- */
.status-badge {{
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 700;
    display: inline-block;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

.status-connected {{ 
    background-color: rgba(16, 185, 129, 0.2); 
    color: #10B981; 
    border: 1px solid rgba(16, 185, 129, 0.3);
}}

.status-disconnected {{ 
    background-color: rgba(239, 68, 68, 0.2); 
    color: #EF4444; 
    border: 1px solid rgba(239, 68, 68, 0.3);
}}

/* Explicações Financeiras */
.economic-box {{
    background: {theme['bg_card']};
    border: 1px solid {theme['border_light']};
    border-radius: 8px;
    padding: 1.5rem;
    margin: 1.5rem 0;
    color: {theme['text_secondary']};
}}

.economic-box h4 {{
    color: {theme['text_primary']};
    margin-top: 0;
    margin-bottom: 1rem;
    font-weight: 700;
}}

.economic-box li {{
    margin-bottom: 0.5rem;
    line-height: 1.5;
}}

/* Remove elementos padrão do Streamlit */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header {{visibility: hidden;}}

</style>
""", unsafe_allow_html=True)

# — Configuração do Tema Altair (Gráficos) —
def configure_altair_theme():
    """Configura o tema dos gráficos para combinar com o modo Claro/Escuro."""
    font = "Nunito"
    
    # Cores
    bg_color = 'transparent' # Fundo transparente para mesclar
    text_color = theme['text_primary']
    grid_color = theme['chart_grid']
    
    # Desativa tema padrão
    alt.themes.enable('none')
    
    # Registra tema customizado
    alt.themes.register("custom_theme", lambda: {
        "config": {
            "background": bg_color,
            "view": {
                "stroke": "transparent"
            },
            "title": {
                "font": font,
                "fontSize": 14,
                "color": text_color,
                "anchor": "start"
            },
            "axis": {
                "labelFont": font,
                "titleFont": font,
                "labelColor": theme['text_secondary'],
                "titleColor": theme['text_secondary'],
                "gridColor": grid_color,
                "domainColor": grid_color,
                "tickColor": grid_color,
            },
            "legend": {
                "labelFont": font,
                "titleFont": font,
                "labelColor": text_color,
                "titleColor": text_color,
                "padding": 10,
                "cornerRadius": 5,
                "fillColor": theme['bg_card'],
                "strokeColor": theme['border_light']
            },
            "range": {
                "category": [
                    theme['secondary_color'], 
                    theme['accent_color'], 
                    theme['warning_color'], 
                    theme['danger_color']
                ]
            }
        }
    })
    alt.themes.enable("custom_theme")

configure_altair_theme()

# ==============================================================================
# 3. LÓGICA DE DADOS E CONEXÃO
# ==============================================================================

def format_number_br(number, decimals=2):
    """Formata números para o padrão PT-BR (ex: 1.234,56)."""
    if number is None: return "0,00"
    return f"{number:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")

@st.cache_resource(show_spinner="🔌 Estabelecendo conexão segura com Google Sheets...")
def connect_to_gsheets():
    """
    Estabelece a conexão com a API do Google Sheets.
    Utiliza cache para evitar reconexões desnecessárias.
    """
    try:
        scopes = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Carrega credenciais dos segredos do Streamlit
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        
        # Autoriza e abre a planilha
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.worksheet(WORKSHEET_NAME)
        
        return sheet
    except Exception as e:
        # Log do erro (opcional) e retorno nulo
        st.error(f"Erro de Conexão: {str(e)}")
        return None

@st.cache_data(ttl=300, show_spinner="📊 Sincronizando dados...")
def load_data():
    """
    Carrega, limpa e tipa os dados da planilha.
    Cache de 5 minutos para performance.
    """
    try:
        sheet = connect_to_gsheets()
        if not sheet: 
            return pd.DataFrame()
        
        # Obtém todos os valores
        values = sheet.get_all_values()

        if len(values) < 2: 
            return pd.DataFrame()
        
        # Cria DataFrame
        df = pd.DataFrame(values[1:], columns=values[0])
        
        # Normaliza nomes de colunas
        df.columns = [col.lower().strip() for col in df.columns]
        
        # Validação básica
        if 'data' not in df.columns or 'gerado' not in df.columns:
            st.error("⚠️ Estrutura inválida: Colunas 'data' e 'gerado' são obrigatórias.")
            return pd.DataFrame()
        
        # Renomeia para padrão interno
        df.rename(columns={
            'data': 'Data', 
            'gerado': 'Energia Gerada (kWh)'
        }, inplace=True)
        
        # Conversão de Data
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        # Fallback para datas mal formatadas
        if df['Data'].isna().any():
            df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        
        # Conversão de Número (Trata padrão PT-BR 1.000,00)
        df['Energia Gerada (kWh)'] = (
            df['Energia Gerada (kWh)']
            .astype(str)
            .str.replace('.', '', regex=False)  # Remove milhar
            .str.replace(',', '.', regex=False) # Troca vírgula por ponto
        )
        df['Energia Gerada (kWh)'] = pd.to_numeric(df['Energia Gerada (kWh)'], errors='coerce')
        
        # Limpeza Final
        df.dropna(subset=['Data', 'Energia Gerada (kWh)'], inplace=True)
        df = df[df['Energia Gerada (kWh)'] >= 0]
        df = df.sort_values(by='Data')
        
        # Remove duplicatas (mantém a última inserção)
        df = df.drop_duplicates(subset=['Data'], keep='last')
        
        return df.reset_index(drop=True)
        
    except Exception as e:
        st.error(f"🚨 Falha crítica no carregamento: {str(e)}")
        return pd.DataFrame()

# --- Funções CRUD (Create, Read, Update, Delete) ---

def append_data(date, energy):
    """Adiciona um novo registro."""
    try:
        sheet = connect_to_gsheets()
        formatted_date = date.strftime('%d/%m/%Y')
        energy_str = str(energy).replace('.', ',')
        sheet.append_row([formatted_date, energy_str], value_input_option='USER_ENTERED')
        st.cache_data.clear() # Limpa cache para refletir mudança
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

def update_data(row_index, date, energy):
    """Atualiza registro existente."""
    try:
        sheet = connect_to_gsheets()
        # +2 porque gspread é 1-based e a linha 1 é cabeçalho
        gspread_row = row_index + 2 
        formatted_date = date.strftime('%d/%m/%Y')
        energy_str = str(energy).replace('.', ',')
        
        sheet.update_cell(gspread_row, 1, formatted_date)
        sheet.update_cell(gspread_row, 2, energy_str)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar: {e}")
        return False

def delete_data(row_index):
    """Remove registro."""
    try:
        sheet = connect_to_gsheets()
        gspread_row = row_index + 2
        sheet.delete_rows(gspread_row)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao excluir: {e}")
        return False

# ==============================================================================
# 4. LÓGICA FINANCEIRA (LEI 14.300 - MARCO LEGAL GD)
# ==============================================================================

def calcular_economia_lei14300(geracao_total, tarifa_cheia, tarifa_fio_b, simultaneidade_percent):
    """
    Calcula a economia real considerando a taxação do Fio B.
    
    Args:
        geracao_total: Total produzido (kWh)
        tarifa_cheia: Valor cheio da tarifa (R$/kWh)
        tarifa_fio_b: Componente Fio B (R$/kWh)
        simultaneidade_percent: % de Autoconsumo (0-100)
    
    Returns:
        Dict com economia líquida, taxa paga e volumes divididos.
    """
    if geracao_total <= 0:
        return {'economia_reais': 0, 'taxa_paga': 0, 'kwh_autoconsumo': 0, 'kwh_injetado': 0}

    fator = simultaneidade_percent / 100.0
    
    # 1. Energia Autoconsumida (Instantânea - Isenta de Taxas)
    autoconsumo = geracao_total * fator
    valor_autoconsumo = autoconsumo * tarifa_cheia
    
    # 2. Energia Injetada (Compensada - Sujeita a Taxas)
    injecao = geracao_total * (1 - fator)
    
    # Tabela de Transição da Lei 14.300
    ano_atual = datetime.now().year
    tabela_transicao = {
        2023: 0.15, 
        2024: 0.30, 
        2025: 0.45, 
        2026: 0.60, 
        2027: 0.75, 
        2028: 0.90,
        2029: 1.00 # E anos seguintes
    }
    percentual_fio_b = tabela_transicao.get(ano_atual, 1.0)
    
    # Custo do Pedágio (Taxa)
    custo_taxa = injecao * (tarifa_fio_b * percentual_fio_b)
    
    # Valor Líquido da Injeção
    valor_injecao_bruto = injecao * tarifa_cheia
    valor_injecao_liquido = valor_injecao_bruto - custo_taxa
    
    return {
        "economia_reais": valor_autoconsumo + valor_injecao_liquido,
        "taxa_paga": custo_taxa,
        "kwh_autoconsumo": autoconsumo,
        "kwh_injetado": injecao,
        "percentual_taxa": percentual_fio_b * 100
    }

# ==============================================================================
# 5. INTERFACE DO USUÁRIO (MAIN APP)
# ==============================================================================

def main():
    
    # --- Sidebar: Configurações e Menu ---
    st.sidebar.markdown("### ⚙️ Painel de Controle")
    
    # Controle de Tema
    col_theme, col_refresh = st.sidebar.columns(2)
    with col_theme:
        icon = "☀️" if not st.session_state.dark_mode else "🌙"
        lbl = "Claro" if not st.session_state.dark_mode else "Escuro"
        if st.button(f"{icon} {lbl}", use_container_width=True):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
            
    with col_refresh:
        if st.button("🔄 Atualizar", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # Parâmetros Financeiros
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💰 Configuração (Lei 14.300)")
    
    with st.sidebar.expander("📝 Editar Tarifas", expanded=True):
        tarifa_cheia = st.number_input(
            "Tarifa Cheia (R$/kWh)", 
            value=0.9555, format="%.4f", step=0.01,
            help="Soma de TE + TUSD + Impostos (Valor final da conta)."
        )
        tarifa_fio_b = st.number_input(
            "Tarifa Fio B (R$/kWh)", 
            value=0.4900, format="%.4f", step=0.01,
            help="Componente de distribuição da tarifa."
        )
        fator_simultaneidade = st.slider(
            "Simultaneidade (%)", 
            0, 100, 30, 
            help="% da energia consumida na hora que é gerada."
        )
        
        st.markdown("---")
        investimento_inicial = st.number_input("Investimento (R$)", value=15000.0, step=500.0)
        data_instalacao = st.date_input("Data Instalação", datetime(2025, 5, 1))

    # Carrega dados
    df = load_data()
    
    # Status na Sidebar
    if sheet := connect_to_gsheets():
        st.sidebar.markdown('<br><span class="status-badge status-connected">✅ ONLINE</span>', unsafe_allow_html=True)
    else:
        st.sidebar.markdown('<br><span class="status-badge status-disconnected">❌ OFFLINE</span>', unsafe_allow_html=True)
        st.stop()

    # --- Header Principal ---
    st.markdown("""
    <div class="header-section">
        <div class="header-content">
            <img src="https://raw.githubusercontent.com/lucasricardocs/solar/refs/heads/main/solar.png" 
                 class="solar-icon" width="80" style="margin-right: 20px;"
                 onerror="this.style.display='none'">
            <div class="header-text">
                <div class="header-title">⚡ SolarAnalytics Pro</div>
                <div class="header-subtitle">Monitoramento Inteligente • Enterprise Edition</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Filtros de Data (Sidebar) ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📅 Período de Análise")
    
    filtro_tipo = st.sidebar.radio(
        "Modo de Filtro:",
        ["Mês Específico", "Intervalo Personalizado", "Ano Completo", "Todo o Histórico"]
    )
    
    df_filtrado = df.copy()
    label_periodo = "Geral"
    heatmap_year_default = datetime.now().year
    
    if not df.empty:
        # Limites globais para Heatmap (Baseado no histórico total para consistência de cor)
        global_max = df['Energia Gerada (kWh)'].max()
        global_min = df[df['Energia Gerada (kWh)'] > 0]['Energia Gerada (kWh)'].min() if not df[df['Energia Gerada (kWh)'] > 0].empty else 0
        
        # Fallback
        if pd.isna(global_max): global_max = 20
        if pd.isna(global_min): global_min = 0

        # Lógica de Filtro
        if filtro_tipo == "Mês Específico":
            anos = sorted(df['Data'].dt.year.unique(), reverse=True)
            sel_ano = st.sidebar.selectbox("Ano", anos)
            meses = sorted(df[df['Data'].dt.year == sel_ano]['Data'].dt.month.unique())
            mapa_meses = {1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr', 5:'Mai', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Out', 11:'Nov', 12:'Dez'}
            sel_mes = st.sidebar.selectbox("Mês", meses, format_func=lambda x: mapa_meses[x])
            
            df_filtrado = df[(df['Data'].dt.year == sel_ano) & (df['Data'].dt.month == sel_mes)]
            label_periodo = f"{mapa_meses[sel_mes]}/{sel_ano}"
            heatmap_year_default = sel_ano

        elif filtro_tipo == "Intervalo Personalizado":
            d_min, d_max = df['Data'].min().date(), df['Data'].max().date()
            intervalo = st.sidebar.date_input("Selecione", [d_min, d_max])
            if len(intervalo) == 2:
                df_filtrado = df[(df['Data'].dt.date >= intervalo[0]) & (df['Data'].dt.date <= intervalo[1])]
                label_periodo = "Personalizado"

        elif filtro_tipo == "Ano Completo":
            anos = sorted(df['Data'].dt.year.unique(), reverse=True)
            sel_ano = st.sidebar.selectbox("Ano", anos)
            df_filtrado = df[df['Data'].dt.year == sel_ano]
            label_periodo = f"Ano {sel_ano}"
            heatmap_year_default = sel_ano
        
        else:
            label_periodo = "Todo o Histórico"

    # --- Área de Registro (Topo) ---
    st.markdown('<div class="subheader-container blue"><h2>📝 Novo Registro</h2></div>', unsafe_allow_html=True)
    with st.form("entry_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1: input_date = st.date_input("Data", datetime.today())
        with c2: input_val = st.number_input("Geração (kWh)", min_value=0.0, step=0.1, format="%.2f")
        with c3:
            st.write("")
            st.write("")
            if st.form_submit_button("💾 Salvar", use_container_width=True):
                if input_val > 0:
                    append_data(input_date, input_val)
                    st.success("Salvo!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.warning("Valor inválido")

    # --- Dashboard Principal ---
    if df_filtrado.empty:
        st.info("Nenhum dado encontrado para este filtro.")
    else:
        # Cálculos de KPI
        total_gerado = df_filtrado['Energia Gerada (kWh)'].sum()
        media_diaria = df_filtrado['Energia Gerada (kWh)'].mean()
        
        # Financeiro
        financas = calcular_economia_lei14300(total_gerado, tarifa_cheia, tarifa_fio_b, fator_simultaneidade)
        
        # Exibição de KPIs
        st.markdown(f'<div class="subheader-container green"><h2>📊 Resultados: {label_periodo}</h2></div>', unsafe_allow_html=True)
        
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("💰 Economia Líquida", f"R$ {format_number_br(financas['economia_reais'])}", delta="Livre de Impostos")
        k2.metric("🔋 Geração Total", f"{format_number_br(total_gerado)} kWh", delta=f"Média: {format_number_br(media_diaria)}")
        k3.metric("💸 Taxa Paga (Fio B)", f"R$ {format_number_br(financas['taxa_paga'])}", delta="Descontado", delta_color="inverse")
        k4.metric("🏠 Autoconsumo", f"{format_number_br(financas['kwh_autoconsumo'])} kWh", help="Energia consumida instantaneamente")

        st.markdown("---")

        # --- ABAS DE GRÁFICOS ---
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Produção Diária", "📈 Acumulado", "💰 Financeiro & ROI", "📋 Dados"])

        # TAB 1: Produção Diária (Adaptativa)
        with tab1:
            st.markdown("##### Performance Diária")
            
            # Lógica para "engordar" as barras:
            # Calculamos a largura ideal baseada no número de dias exibidos
            qtd_dias = len(df_filtrado)
            # Se tiver 5 dias, size grande (~50). Se tiver 365, size pequeno ou automático.
            # Largura estimada do chart container: 800px.
            largura_barra_calc = max(3, min(60, 800 // (qtd_dias + 1)))
            
            chart_daily = alt.Chart(df_filtrado).mark_bar(
                color=theme['secondary_color'],
                cornerRadiusTopLeft=4,
                cornerRadiusTopRight=4,
                size=largura_barra_calc  # <--- APLICAÇÃO DA LARGURA ADAPTATIVA
            ).encode(
                x=alt.X('Data:T', title='', axis=alt.Axis(format='%d/%m')),
                y=alt.Y('Energia Gerada (kWh):Q', title='Produção'),
                tooltip=['Data', alt.Tooltip('Energia Gerada (kWh)', format='.2f')]
            ).properties(height=380)
            
            line_avg = alt.Chart(pd.DataFrame({'y':[media_diaria]})).mark_rule(
                color=theme['danger_color'], strokeDash=[5,5]
            ).encode(y='y', tooltip=alt.value(f"Média: {media_diaria:.2f}"))
            
            st.altair_chart((chart_daily + line_avg).interactive(), use_container_width=True)

        # TAB 2: Acumulado
        with tab2:
            df_acc = df_filtrado.sort_values('Data').copy()
            df_acc['Acumulado'] = df_acc['Energia Gerada (kWh)'].cumsum()
            
            chart_acc = alt.Chart(df_acc).mark_area(
                line={'color': theme['secondary_color']},
                color=alt.Gradient(
                    gradient='linear',
                    stops=[alt.GradientStop(color=theme['bg_main'], offset=0), 
                           alt.GradientStop(color=theme['secondary_color'], offset=1)],
                    x1=1, x2=1, y1=1, y2=0
                )
            ).encode(
                x=alt.X('Data:T', title='Data'),
                y=alt.Y('Acumulado:Q', title='Total Acumulado (kWh)'),
                tooltip=['Data', 'Acumulado']
            ).properties(height=380)
            
            st.altair_chart(chart_acc, use_container_width=True)

        # TAB 3: Financeiro
        with tab3:
            st.markdown('<div class="subheader-container pink"><h3>Análise de Viabilidade (Estimativa)</h3></div>', unsafe_allow_html=True)
            
            # Projeção Anual baseada na média do filtro atual
            projecao_anual_kwh = media_diaria * 365
            fin_proj = calcular_economia_lei14300(projecao_anual_kwh, tarifa_cheia, tarifa_fio_b, fator_simultaneidade)
            econ_anual_reais = fin_proj['economia_reais']
            
            payback = investimento_inicial / econ_anual_reais if econ_anual_reais > 0 else 0
            
            # Dados Históricos Totais para ROI Real
            total_hist = df['Energia Gerada (kWh)'].sum()
            fin_hist = calcular_economia_lei14300(total_hist, tarifa_cheia, tarifa_fio_b, fator_simultaneidade)
            total_poupado = fin_hist['economia_reais']
            
            c_f1, c_f2, c_f3 = st.columns(3)
            c_f1.metric("Projeção Anual (R$)", f"R$ {format_number_br(econ_anual_reais)}")
            c_f2.metric("Payback Estimado", f"{payback:.1f} Anos")
            c_f3.metric("Total Já Poupado (Vida Útil)", f"R$ {format_number_br(total_poupado)}")
            
            st.divider()
            
            # Gráfico Fluxo de Caixa
            st.markdown("##### Fluxo de Caixa (25 Anos)")
            anos = list(range(26))
            fluxo = [-investimento_inicial]
            acum = -investimento_inicial
            for i in range(1, 26):
                deg = (1 - 0.005) ** i
                acum += (econ_anual_reais * deg)
                fluxo.append(acum)
            
            df_fluxo = pd.DataFrame({'Ano': anos, 'Saldo': fluxo})
            
            chart_fluxo = alt.Chart(df_fluxo).mark_line(
                point=True, color=theme['accent_color'], strokeWidth=3
            ).encode(
                x='Ano:O', 
                y='Saldo:Q',
                tooltip=['Ano', alt.Tooltip('Saldo', format=',.2f')]
            ).properties(height=300)
            
            line_zero = alt.Chart(pd.DataFrame({'y':[0]})).mark_rule(color='gray').encode(y='y')
            st.altair_chart(chart_fluxo + line_zero, use_container_width=True)
            
            st.markdown(f"""
            <div class="economic-box">
                <h4>📚 Detalhes da Lei 14.300 (Taxação do Sol)</h4>
                <ul>
                    <li><strong>Fio B:</strong> Componente da tarifa que remunera o uso da rede. Cobrança progressiva iniciada em 2023.</li>
                    <li><strong>Simultaneidade:</strong> Energia que você consome NO MOMENTO que gera não paga taxa. Aumente isso para economizar mais!</li>
                    <li><strong>Status Atual:</strong> Você está pagando {financas['percentual_taxa']:.0f}% da tarifa Fio B sobre a injeção.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        # TAB 4: Dados
        with tab4:
            c_table, c_edit = st.columns([3, 1])
            
            with c_table:
                st.dataframe(df_filtrado.style.format({"Energia Gerada (kWh)": "{:.2f}"}), use_container_width=True, height=500)
            
            with c_edit:
                st.warning("⚠️ Zona de Edição")
                if st.button("Ativar Edição", use_container_width=True):
                    st.session_state.edit_mode = not st.session_state.edit_mode
                
                if st.session_state.edit_mode:
                    sel_idx = st.selectbox("ID", df_filtrado.index)
                    if sel_idx is not None:
                        row = df_filtrado.loc[sel_idx]
                        n_dt = st.date_input("Nova Data", row['Data'])
                        n_vl = st.number_input("Novo Valor", value=float(row['Energia Gerada (kWh)']))
                        
                        if st.button("Atualizar"):
                            update_data(sel_idx, n_dt, n_vl)
                            st.rerun()
                        if st.button("Excluir"):
                            delete_data(sel_idx)
                            st.rerun()

        # --- HEATMAP FORA DAS TABS (Visão Geral) ---
        st.divider()
        st.markdown(f'<div class="subheader-container teal"><h3>🗓️ Mapa de Calor Anual ({heatmap_year_default})</h3></div>', unsafe_allow_html=True)
        
        # Filtra dados para o ano do heatmap (padrão ano atual ou selecionado)
        df_heat_src = df[df['Data'].dt.year == heatmap_year_default].copy()
        
        if not df_heat_src.empty:
            # Grid completo
            d1 = datetime(heatmap_year_default, 1, 1)
            d2 = datetime(heatmap_year_default, 12, 31)
            datas_completas = pd.date_range(d1, d2)
            df_full_year = pd.DataFrame({'Data': datas_completas})
            
            # Merge
            df_heat = pd.merge(df_full_year, df_heat_src, on='Data', how='left').fillna(0)
            
            # Atributos Temporais
            df_heat['Semana'] = df_heat['Data'].dt.isocalendar().week
            df_heat['Dia'] = df_heat['Data'].dt.dayofweek
            df_heat['Mes'] = df_heat['Data'].dt.month
            
            # Ajuste visual virada de ano
            df_heat.loc[(df_heat['Mes']==1) & (df_heat['Semana']>50), 'Semana'] = 0
            df_heat.loc[(df_heat['Mes']==12) & (df_heat['Semana']==1), 'Semana'] = 53

            # Gráfico: Labels dos Meses (Topo)
            month_labels = df_heat.groupby('Mes')['Semana'].min().reset_index()
            month_labels['Nome'] = month_labels['Mes'].apply(lambda x: datetime(2023, x, 1).strftime('%b'))
            
            c_labels = alt.Chart(month_labels).mark_text(align='left', dy=10, color=theme['text_secondary']).encode(
                x=alt.X('Semana:O', axis=None), 
                text='Nome'
            )
            
            # Gráfico: Quadrados (Heatmap)
            # CORREÇÃO DE COR: Escala do Verde vai de (Mínimo > 0) até (Máximo Histórico)
            c_squares = alt.Chart(df_heat).mark_rect(
                stroke=theme['heatmap_stroke'], 
                strokeWidth=1, 
                cornerRadius=2
            ).encode(
                x=alt.X('Semana:O', axis=None),
                y=alt.Y('Dia:O', axis=None, title=''),
                color=alt.condition(
                    'datum["Energia Gerada (kWh)"] > 0',
                    alt.Color('Energia Gerada (kWh):Q', 
                              scale=alt.Scale(scheme='yellowgreen', domain=[global_min, global_max]),
                              legend=alt.Legend(title="kWh")),
                    alt.value(theme['heatmap_zero']) # Cor para dias vazios (Zero)
                ),
                tooltip=[
                    alt.Tooltip('Data', format='%d/%m/%Y'), 
                    alt.Tooltip('Energia Gerada (kWh)', format='.2f')
                ]
            ).properties(height=180)
            
            st.altair_chart(alt.vconcat(c_labels, c_squares), use_container_width=True)
        else:
            st.warning(f"Sem dados para o ano {heatmap_year_default}")

    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: {theme['text_secondary']}; font-size: 0.8rem; margin-top: 2rem;">
        SolarAnalytics Pro v4.0 • Enterprise Edition<br>
        Última sincronização: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
