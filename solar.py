# -*- coding: utf-8 -*-
"""
SolarAnalytics Pro - Dashboard de Monitoramento de Energia Solar
Versão: 3.2.0 (Enterprise Edition - Visual Fidelity)
Autor: Adaptado por Gemini AI
Data: Dezembro 2025

Descrição:
Este sistema realiza o monitoramento, gestão e análise financeira de geração 
distribuída de energia solar fotovoltaica. Compatível com o Marco Legal 
da Geração Distribuída (Lei 14.300/2021).

Funcionalidades:
- Conexão segura via Google Sheets API.
- Dashboard interativo com Streamlit e Altair.
- Análise financeira detalhada (Payback, VPL, TIR, ROI).
- Cálculo de tarifas com desconto do Fio B (Taxação do Sol).
- Heatmaps fiéis ao design original com escala dinâmica.
- Gráficos de barras adaptativos (preenchimento otimizado).
- Design responsivo com temas Claro/Escuro.
"""

# ==============================================================================
# 1. IMPORTAÇÃO DE BIBLIOTECAS E CONFIGURAÇÃO INICIAL
# ==============================================================================

import pandas as pd
import numpy as np
import streamlit as st
import gspread
import time
import io
import warnings
import locale
import altair as alt
from datetime import datetime, timedelta, date
from google.oauth2.service_account import Credentials
from dateutil.relativedelta import relativedelta

# Configurações de warnings para manter o log limpo e profissional
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', message='.*observed=False.*')

# Otimização do Altair para grandes volumes de dados JSON
alt.data_transformers.enable('json')

# Tentativa de configuração de Localidade para formato de moeda e data (pt-BR)
# Isso garante que R$ e datas apareçam no formato brasileiro correto
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except Exception:
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR')
    except Exception:
        try:
            # Fallback para ambientes Windows
            locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
        except Exception:
            pass # Mantém o padrão do sistema se tudo falhar

# ==============================================================================
# 2. CONSTANTES E VARIÁVEIS GLOBAIS
# ==============================================================================

# ID da Planilha Google (Deve ser mantido conforme original)
SPREADSHEET_ID = '1WI2tZ94lVV9GfaaWerdSfuChFLzWfMbU4v2m6QrwTdY'
WORKSHEET_NAME = 'solardaily'

# Configuração da Página Streamlit
# Define o layout wide (tela cheia) e recolhe a sidebar inicialmente para foco nos dados
st.set_page_config(
    layout="wide",
    page_title="SolarAnalytics Pro | Enterprise Dashboard",
    page_icon="⚡",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.github.com/lucasricardocs',
        'Report a bug': "mailto:support@solaranalytics.com",
        'About': "# SolarAnalytics Pro v3.2\nMonitoramento avançado de energia solar com fidelidade visual."
    }
)

# Inicialização do Session State (Estado da Sessão) para persistência de dados
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False

if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

# ==============================================================================
# 3. GERENCIAMENTO DE TEMA E ESTILO (CSS AVANÇADO)
# ==============================================================================

class ThemeManager:
    """
    Classe responsável por gerenciar as cores, estilos e injeção de CSS
    dinâmico na aplicação. Mantém a consistência visual entre modo Claro/Escuro.
    """
    
    @staticmethod
    def get_colors():
        """
        Retorna o dicionário de cores baseado no modo (Claro/Escuro).
        Essas cores são usadas tanto no CSS quanto nos gráficos Altair.
        """
        if st.session_state.dark_mode:
            return {
                'primary': '#ffffff',
                'secondary': '#60a5fa',     # Azul claro vibrante
                'accent': '#34d399',        # Verde esmeralda
                'warning': '#fbbf24',       # Amarelo alerta
                'danger': '#ef4444',        # Vermelho erro
                'text_main': '#f3f4f6',     # Cinza muito claro
                'text_sub': '#9ca3af',      # Cinza médio
                'bg_main': '#111827',       # Azul muito escuro (quase preto)
                'bg_paper': '#1f2937',      # Azul escuro
                'bg_card': '#374151',       # Cinza azulado
                'border': '#4b5563',        # Borda sutil
                'header_grad': 'linear-gradient(135deg, #1f2937 0%, #111827 100%)',
                'metric_box': '#374151',
                'heatmap_stroke': '#4b5563' # Cor da borda do heatmap no modo escuro
            }
        else:
            return {
                'primary': '#1f2937',
                'secondary': '#3b82f6',     # Azul padrão
                'accent': '#10b981',        # Verde padrão
                'warning': '#f59e0b',       # Laranja
                'danger': '#dc2626',        # Vermelho
                'text_main': '#1f2937',     # Cinza escuro
                'text_sub': '#6b7280',      # Cinza texto
                'bg_main': '#f8fafc',       # Branco gelo
                'bg_paper': '#ffffff',      # Branco puro
                'bg_card': '#ffffff',       # Branco puro
                'border': '#e2e8f0',        # Cinza claro
                'header_grad': 'linear-gradient(135deg, #eff6ff 0%, #f0f9ff 100%)',
                'metric_box': '#ffffff',
                'heatmap_stroke': '#d3d3d3' # Cor da borda do heatmap no modo claro (original)
            }

    @staticmethod
    def apply_css():
        """
        Gera e injeta o CSS na página.
        Este bloco CSS é extenso para garantir o controle total da aparência.
        """
        c = ThemeManager.get_colors()
        
        css = f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600;700;800&display=swap');

        :root {{
            --primary: {c['primary']};
            --secondary: {c['secondary']};
            --accent: {c['accent']};
            --bg-main: {c['bg_main']};
            --bg-paper: {c['bg_paper']};
            --text-main: {c['text_main']};
            --text-sub: {c['text_sub']};
            --border: {c['border']};
        }}

        /* --- Reset Global e Fontes --- */
        html, body, [class*="st-"], .stApp, .main {{
            font-family: 'Nunito', sans-serif !important;
            color: var(--text-main) !important;
        }}

        .stApp {{
            background-color: var(--bg-main);
        }}

        /* --- Header Section (Animado) --- */
        .header-wrapper {{
            background: {c['header_grad']};
            padding: 1.5rem 2rem;
            border-radius: 16px;
            border: 1px solid {c['border']};
            margin-bottom: 2rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
        }}

        .header-wrapper:hover {{
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
            border-color: {c['secondary']};
        }}

        .header-icon {{
            font-size: 3.5rem;
            animation: float 6s ease-in-out infinite;
        }}

        @keyframes float {{
            0% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-10px); }}
            100% {{ transform: translateY(0px); }}
        }}

        .header-content {{
            display: flex;
            flex-direction: column;
        }}

        .header-title {{
            font-size: 2rem;
            font-weight: 800;
            background: linear-gradient(to right, {c['text_main']}, {c['secondary']});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
            line-height: 1.2;
        }}

        .header-subtitle {{
            font-size: 1rem;
            color: {c['text_sub']};
            font-weight: 500;
            margin-top: 0.25rem;
        }}

        /* --- Subheaders Coloridos --- */
        /* Estilo idêntico ao original, com borda esquerda colorida */
        .section-header {{
            margin: 25px 0 15px 0;
            padding: 12px 20px;
            background: {c['bg_paper']};
            border-radius: 8px;
            border-left: 5px solid;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            display: flex;
            align-items: center;
            transition: transform 0.2s;
        }}
        
        .section-header:hover {{ transform: translateX(4px); }}
        
        .section-header h2, .section-header h3 {{
            margin: 0;
            font-size: 1.2rem;
            font-weight: 700;
            color: {c['text_main']};
        }}

        .border-blue {{ border-left-color: #3b82f6; }}
        .border-green {{ border-left-color: #10b981; }}
        .border-orange {{ border-left-color: #f59e0b; }}
        .border-purple {{ border-left-color: #8b5cf6; }}
        .border-pink {{ border-left-color: #ec4899; }}
        .border-teal {{ border-left-color: #14b8a6; }}

        /* --- Métricas (KPI Cards) --- */
        [data-testid="metric-container"] {{
            background-color: {c['metric_box']};
            border: 1px solid {c['border']};
            border-radius: 12px;
            padding: 1rem;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            transition: all 0.2s ease;
        }}

        [data-testid="metric-container"]:hover {{
            border-color: {c['secondary']};
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}

        [data-testid="metric-label"] {{ font-size: 0.9rem !important; color: {c['text_sub']} !important; }}
        [data-testid="metric-value"] {{ font-size: 1.6rem !important; color: {c['text_main']} !important; font-weight: 700 !important; }}

        /* --- Formulários e Inputs --- */
        .stTextInput > div > div, .stNumberInput > div > div, .stDateInput > div > div, .stSelectbox > div > div {{
            background-color: {c['bg_card']};
            color: {c['text_main']};
            border-color: {c['border']};
            border-radius: 8px;
        }}

        .stForm {{
            background-color: {c['bg_paper']};
            border: 1px solid {c['border']};
            padding: 2rem;
            border-radius: 12px;
        }}

        /* --- Botões Customizados --- */
        button[kind="secondary"] {{
            background-color: {c['bg_card']};
            border: 1px solid {c['border']};
            color: {c['text_main']};
            transition: all 0.2s;
        }}
        
        button[kind="secondary"]:hover {{
            border-color: {c['secondary']};
            color: {c['secondary']};
        }}

        /* --- Tabelas (Dataframe) --- */
        [data-testid="stDataFrame"] {{
            border: 1px solid {c['border']};
            border-radius: 8px;
            overflow: hidden;
        }}

        /* --- Explicações Educativas --- */
        .info-box {{
            background-color: {c['bg_paper']};
            border: 1px solid {c['border']};
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1rem 0;
            font-size: 0.95rem;
            color: {c['text_sub']};
            line-height: 1.6;
        }}
        
        .info-box h4 {{
            color: {c['text_main']};
            margin-top: 0;
            margin-bottom: 0.8rem;
            font-weight: 700;
        }}
        
        .info-box li {{ margin-bottom: 0.5rem; }}

        /* --- Badges de Status --- */
        .status-badge {{
            padding: 0.25rem 0.75rem; 
            border-radius: 20px; 
            font-size: 0.75rem; 
            font-weight: 600; 
            display: inline-block;
        }}
        .status-connected {{ background-color: #10B98120; color: #10B981; }}
        .status-disconnected {{ background-color: #EF444420; color: #EF4444; }}

        /* --- Elementos Ocultos --- */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)

    @staticmethod
    def configure_altair():
        """Configura o tema dos gráficos Altair."""
        c = ThemeManager.get_colors()
        font = "Nunito"
        
        alt.themes.enable('none')
        alt.themes.register("custom_theme", lambda: {
            "config": {
                "background": "transparent",
                "view": { "stroke": "transparent" },
                "title": { "font": font, "color": c['text_main'], "fontSize": 14 },
                "axis": {
                    "labelFont": font, "titleFont": font, 
                    "labelColor": c['text_sub'], "titleColor": c['text_sub'],
                    "gridColor": c['border'], "tickColor": c['border'],
                    "domain": False
                },
                "legend": {
                    "labelFont": font, "titleFont": font,
                    "labelColor": c['text_sub'], "titleColor": c['text_main']
                },
                "range": {
                    "category": [c['secondary'], c['accent'], c['warning'], c['danger']]
                }
            }
        })
        alt.themes.enable("custom_theme")

# ==============================================================================
# 4. LÓGICA DE NEGÓCIO E FINANCEIRA (LEI 14.300)
# ==============================================================================

class FinancialCalculator:
    """
    Motor de cálculo financeiro especializado em Geração Distribuída no Brasil.
    Implementa as regras de transição da Lei 14.300/2021 (Cobrança do Fio B).
    """
    
    @staticmethod
    def get_fio_b_percentage(year):
        """
        Retorna o percentual de cobrança do Fio B conforme o ano,
        seguindo a regra de transição da Lei 14.300.
        """
        transition_table = {
            2023: 0.15,
            2024: 0.30,
            2025: 0.45,
            2026: 0.60,
            2027: 0.75,
            2028: 0.90,
            2029: 1.00
        }
        return transition_table.get(year, 1.00) # 100% para anos futuros > 2029

    @staticmethod
    def calculate_savings(generation_kwh, tarifa_total, tarifa_fio_b, simultaneity_factor):
        """
        Calcula a economia financeira real.
        
        Parâmetros:
        - generation_kwh (float): Energia gerada no período.
        - tarifa_total (float): Valor cheio do kWh (TE + TUSD + Impostos).
        - tarifa_fio_b (float): Valor da componente Fio B da TUSD.
        - simultaneity_factor (float): % de autoconsumo imediato (0.0 a 1.0).
        
        Retorno:
        - Dict com detalhamento financeiro.
        """
        if generation_kwh <= 0:
            return {
                "gross_savings": 0.0,
                "net_savings": 0.0,
                "tax_paid": 0.0,
                "autoconsumption_kwh": 0.0,
                "injection_kwh": 0.0,
                "autoconsumption_value": 0.0,
                "injection_credit_value": 0.0
            }

        # 1. Separação Física da Energia
        autoconsumption_kwh = generation_kwh * simultaneity_factor
        injection_kwh = generation_kwh * (1 - simultaneity_factor)

        # 2. Valor do Autoconsumo (Isento de Taxas)
        # O autoconsumo "evita" a compra da energia cheia.
        autoconsumption_value = autoconsumption_kwh * tarifa_total

        # 3. Cálculo da Taxação sobre a Injeção
        current_year = datetime.now().year
        tax_percentage = FinancialCalculator.get_fio_b_percentage(current_year)
        
        # O "Pedágio" é pago apenas sobre a energia injetada que será compensada
        tax_cost_per_kwh = tarifa_fio_b * tax_percentage
        total_tax_paid = injection_kwh * tax_cost_per_kwh

        # 4. Valor do Crédito Líquido
        # O crédito gerado vale a tarifa cheia MENOS o pedágio pago
        injection_gross_value = injection_kwh * tarifa_total
        injection_net_value = injection_gross_value - total_tax_paid

        # 5. Consolidação
        gross_savings = autoconsumption_value + injection_gross_value
        net_savings = autoconsumption_value + injection_net_value

        return {
            "gross_savings": gross_savings,         # Economia se não houvesse lei 14.300
            "net_savings": net_savings,             # Economia Real (no bolso)
            "tax_paid": total_tax_paid,             # Valor deixado na mesa (Taxação)
            "autoconsumption_kwh": autoconsumption_kwh,
            "injection_kwh": injection_kwh,
            "tax_percentage_applied": tax_percentage * 100
        }

# ==============================================================================
# 5. GERENCIAMENTO DE DADOS E CONEXÃO
# ==============================================================================

class DataManager:
    """
    Classe responsável pela conexão com Google Sheets, cache e operações CRUD.
    """
    
    @staticmethod
    def format_number_br(number, decimals=2):
        """Formata float para string brasileira (vírgula decimal)."""
        if number is None or pd.isna(number):
            return "0,00"
        return f"{number:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @staticmethod
    @st.cache_resource(show_spinner=False)
    def connect_gsheets():
        """Estabelece conexão segura com Google API."""
        try:
            scopes = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
            client = gspread.authorize(creds)
            spreadsheet = client.open_by_key(SPREADSHEET_ID)
            sheet = spreadsheet.worksheet(WORKSHEET_NAME)
            return sheet
        except Exception as e:
            st.error(f"Erro Crítico de Conexão: {str(e)}")
            return None

    @staticmethod
    @st.cache_data(ttl=60, show_spinner="Sincronizando dados...")
    def fetch_data(_sheet_obj):
        """Busca e trata os dados da planilha."""
        if _sheet_obj is None:
            return pd.DataFrame()
        
        try:
            # Obtém todos os valores como lista de listas
            data = _sheet_obj.get_all_values()
            
            if len(data) < 2:
                return pd.DataFrame(columns=['Data', 'Energia Gerada (kWh)'])

            # Cria DataFrame
            df = pd.DataFrame(data[1:], columns=data[0])
            
            # Normalização de colunas
            df.columns = [c.lower().strip() for c in df.columns]
            col_map = {'data': 'Data', 'gerado': 'Energia Gerada (kWh)'}
            df.rename(columns=col_map, inplace=True)
            
            # Verificação de colunas obrigatórias
            if 'Data' not in df.columns or 'Energia Gerada (kWh)' not in df.columns:
                st.error("Estrutura da planilha incorreta. Colunas esperadas: 'data', 'gerado'.")
                return pd.DataFrame()

            # Tratamento de Tipos
            # Data
            df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
            
            # Números (Tratamento de locale PT-BR manual para robustez)
            df['Energia Gerada (kWh)'] = (
                df['Energia Gerada (kWh)']
                .astype(str)
                .str.replace('.', '', regex=False)  # Remove milhar
                .str.replace(',', '.', regex=False) # Troca decimal
            )
            df['Energia Gerada (kWh)'] = pd.to_numeric(df['Energia Gerada (kWh)'], errors='coerce')

            # Limpeza
            df.dropna(subset=['Data', 'Energia Gerada (kWh)'], inplace=True)
            df = df[df['Energia Gerada (kWh)'] >= 0]
            df.sort_values('Data', inplace=True)
            df.drop_duplicates(subset=['Data'], keep='last', inplace=True)
            
            return df.reset_index(drop=True)

        except Exception as e:
            st.error(f"Erro ao processar dados: {e}")
            return pd.DataFrame()

    @staticmethod
    def add_entry(sheet, date_obj, value):
        """Adiciona nova linha na planilha."""
        try:
            date_str = date_obj.strftime('%d/%m/%Y')
            val_str = str(value).replace('.', ',')
            sheet.append_row([date_str, val_str], value_input_option='USER_ENTERED')
            st.cache_data.clear()
            return True
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")
            return False

    @staticmethod
    def update_entry(sheet, row_idx_pandas, date_obj, value):
        """Atualiza linha existente."""
        try:
            # Gspread usa índice 1-based e tem header, então row = idx + 2
            gspread_row = row_idx_pandas + 2
            date_str = date_obj.strftime('%d/%m/%Y')
            val_str = str(value).replace('.', ',')
            
            sheet.update_cell(gspread_row, 1, date_str)
            sheet.update_cell(gspread_row, 2, val_str)
            st.cache_data.clear()
            return True
        except Exception as e:
            st.error(f"Erro ao atualizar: {e}")
            return False

    @staticmethod
    def delete_entry(sheet, row_idx_pandas):
        """Remove linha existente."""
        try:
            gspread_row = row_idx_pandas + 2
            sheet.delete_rows(gspread_row)
            st.cache_data.clear()
            return True
        except Exception as e:
            st.error(f"Erro ao deletar: {e}")
            return False

# ==============================================================================
# 6. INTERFACE DE USUÁRIO (COMPONENTES)
# ==============================================================================

def render_header():
    """Renderiza o cabeçalho principal animado."""
    st.markdown("""
    <div class="header-wrapper">
        <div class="header-icon">☀️</div>
        <div class="header-content">
            <h1 class="header-title">SolarAnalytics Pro</h1>
            <p class="header-subtitle">Enterprise Edition • Monitoramento & Inteligência Financeira</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar_controls():
    """Renderiza todos os controles da barra lateral."""
    st.sidebar.markdown("### ⚙️ Painel de Controle")
    
    # 1. Controle de Tema
    c_theme_btn, c_refresh_btn = st.sidebar.columns(2)
    with c_theme_btn:
        theme_icon = "🌙" if st.session_state.dark_mode else "☀️"
        theme_label = "Escuro" if st.session_state.dark_mode else "Claro"
        if st.button(f"{theme_icon} {theme_label}", use_container_width=True):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
            
    with c_refresh_btn:
        if st.button("🔄 Atualizar", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    st.sidebar.markdown("---")
    
    # 2. Parâmetros Financeiros
    st.sidebar.markdown("### 💰 Parâmetros (Lei 14.300)")
    with st.sidebar.expander("Configurar Tarifas", expanded=True):
        tarifa_cheia = st.number_input(
            "Tarifa Cheia (R$/kWh)", 
            value=0.9555, format="%.4f", step=0.01,
            help="Soma de TE + TUSD + Impostos (Valor final da conta)."
        )
        tarifa_fio_b = st.number_input(
            "Tarifa Fio B (R$/kWh)", 
            value=0.4900, format="%.4f", step=0.01,
            help="Parcela referente ao uso do sistema de distribuição."
        )
        simultaneidade = st.slider(
            "Fator de Simultaneidade (%)", 
            0, 100, 35, 
            help="% da energia consumida instantaneamente (Autoconsumo)."
        ) / 100.0
        
        investimento = st.number_input("Investimento Inicial (R$)", value=15000.0, step=500.0)
        data_inicio = st.date_input("Data Instalação", datetime(2025, 5, 1))

    return {
        'tarifa_cheia': tarifa_cheia,
        'tarifa_fio_b': tarifa_fio_b,
        'simultaneidade': simultaneidade,
        'investimento': investimento,
        'data_inicio': data_inicio
    }

def render_date_filters(df):
    """Renderiza filtros de data avançados."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📅 Período de Análise")
    
    filter_mode = st.sidebar.radio(
        "Modo de Filtro:",
        ["Mês Específico", "Intervalo", "Últimos 30 Dias", "Ano Completo", "Tudo"],
        index=2
    )
    
    filtered_df = df.copy()
    period_label = "Período Personalizado"
    
    if df.empty:
        return df, "Sem Dados"

    max_date = df['Data'].max()
    min_date = df['Data'].min()

    if filter_mode == "Mês Específico":
        years = sorted(df['Data'].dt.year.unique(), reverse=True)
        sel_year = st.sidebar.selectbox("Ano", years)
        
        avail_months = sorted(df[df['Data'].dt.year == sel_year]['Data'].dt.month.unique())
        month_map = {1:'Janeiro', 2:'Fevereiro', 3:'Março', 4:'Abril', 5:'Maio', 6:'Junho',
                     7:'Julho', 8:'Agosto', 9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'}
        
        sel_month = st.sidebar.selectbox("Mês", avail_months, format_func=lambda x: month_map[x])
        
        filtered_df = df[(df['Data'].dt.year == sel_year) & (df['Data'].dt.month == sel_month)]
        period_label = f"{month_map[sel_month]} de {sel_year}"

    elif filter_mode == "Intervalo":
        d_range = st.sidebar.date_input("Selecione Intervalo", [max_date - timedelta(days=30), max_date])
        if len(d_range) == 2:
            filtered_df = df[(df['Data'].dt.date >= d_range[0]) & (df['Data'].dt.date <= d_range[1])]
            period_label = f"{d_range[0].strftime('%d/%m')} até {d_range[1].strftime('%d/%m')}"

    elif filter_mode == "Últimos 30 Dias":
        cutoff = max_date - timedelta(days=29)
        filtered_df = df[df['Data'] >= cutoff]
        period_label = "Últimos 30 Dias"

    elif filter_mode == "Ano Completo":
        years = sorted(df['Data'].dt.year.unique(), reverse=True)
        sel_year = st.sidebar.selectbox("Ano", years)
        filtered_df = df[df['Data'].dt.year == sel_year]
        period_label = f"Ano de {sel_year}"

    elif filter_mode == "Tudo":
        period_label = "Histórico Completo"

    return filtered_df, period_label

def render_entry_form(sheet_obj):
    """Renderiza o formulário de entrada de dados."""
    st.markdown('<div class="section-header border-blue"><h2>📝 Registrar Geração</h2></div>', unsafe_allow_html=True)
    
    with st.form("new_entry_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        
        with c1:
            i_date = st.date_input("Data", date.today())
        with c2:
            i_val = st.number_input("Energia (kWh)", min_value=0.0, max_value=200.0, step=0.1, format="%.2f")
        with c3:
            st.write("")
            st.write("")
            submitted = st.form_submit_button("💾 Salvar Registro", use_container_width=True)
            
        if submitted:
            if i_val > 0:
                with st.spinner("Salvando..."):
                    if DataManager.add_entry(sheet_obj, i_date, i_val):
                        st.success("Registro salvo com sucesso!")
                        time.sleep(1)
                        st.rerun()
            else:
                st.warning("O valor de geração deve ser maior que zero.")

# ==============================================================================
# 7. FUNÇÃO PRINCIPAL (MAIN LOOP)
# ==============================================================================

def main():
    # 1. Inicialização de Estilo e Conexão
    ThemeManager.apply_css()
    ThemeManager.configure_altair()
    
    sheet = DataManager.connect_gsheets()
    
    # 2. Renderização da Sidebar e Obtenção de Parâmetros
    render_header()
    
    if not sheet:
        st.error("Falha crítica de conexão. Verifique as credenciais.")
        st.stop()
        
    params = render_sidebar_controls()
    df_full = DataManager.fetch_data(sheet)
    
    # Informações Rápidas na Sidebar
    if not df_full.empty:
        st.sidebar.markdown("### 📊 Status")
        st.sidebar.info(f"Registros: {len(df_full)}\nÚltimo: {df_full['Data'].max().strftime('%d/%m/%Y')}")

        # --- CÁLCULO DOS LIMITES GLOBAIS PARA O HEATMAP ---
        # A cor do heatmap será baseada no mínimo (>0) e máximo de TODO o histórico
        # Isso garante que um dia de 20kWh seja sempre verde escuro, independente do ano
        global_max_prod = df_full['Energia Gerada (kWh)'].max()
        global_min_prod_series = df_full[df_full['Energia Gerada (kWh)'] > 0]['Energia Gerada (kWh)']
        
        if not global_min_prod_series.empty:
            global_min_prod = global_min_prod_series.min()
        else:
            global_min_prod = 0
        
        # Fallback de segurança
        if pd.isna(global_max_prod): global_max_prod = 20
        if pd.isna(global_min_prod): global_min_prod = 0
    else:
        global_max_prod = 20
        global_min_prod = 0

    # 3. Filtros de Data
    df_view, period_label = render_date_filters(df_full)

    # 4. Formulário de Entrada
    render_entry_form(sheet)

    # 5. Dashboard Principal
    if df_view.empty:
        st.warning("⚠️ Nenhum dado encontrado para o período selecionado.")
    else:
        # --- CÁLCULOS PRINCIPAIS ---
        total_gen = df_view['Energia Gerada (kWh)'].sum()
        avg_gen = df_view['Energia Gerada (kWh)'].mean()
        
        # Análise Financeira do Período
        fin_data = FinancialCalculator.calculate_savings(
            total_gen, 
            params['tarifa_cheia'], 
            params['tarifa_fio_b'], 
            params['simultaneidade']
        )
        
        # --- KPI CARDS (Métricas) ---
        st.markdown(f'<div class="section-header border-green"><h2>📊 Resultados do Período ({period_label})</h2></div>', unsafe_allow_html=True)
        
        k1, k2, k3, k4 = st.columns(4)
        
        k1.metric(
            "💵 Economia Líquida", 
            f"R$ {DataManager.format_number_br(fin_data['net_savings'])}",
            delta="Livre de Impostos"
        )
        k2.metric(
            "💸 Taxa Paga (Fio B)", 
            f"R$ {DataManager.format_number_br(fin_data['tax_paid'])}",
            delta=f"Transição ({fin_data.get('tax_percentage_applied', 0):.0f}%)",
            delta_color="inverse"
        )
        k3.metric(
            "⚡ Geração Total", 
            f"{DataManager.format_number_br(total_gen)} kWh",
            delta=f"Média: {DataManager.format_number_br(avg_gen)}"
        )
        k4.metric(
            "🏠 Autoconsumo", 
            f"{DataManager.format_number_br(fin_data['autoconsumption_kwh'])} kWh",
            help="Energia consumida instantaneamente (isenta de taxas)."
        )

        st.markdown("---")

        # --- ABAS DE ANÁLISE ---
        tab_daily, tab_acc, tab_annual, tab_roi, tab_data = st.tabs([
            "📊 Produção Diária", 
            "📈 Curva Acumulada", 
            "🗓️ Sazonalidade & Heatmap", 
            "💰 Simulador ROI",
            "📋 Dados & Exportação"
        ])

        # ABA 1: Produção Diária
        with tab_daily:
            st.markdown("##### Comportamento da Geração Diária")
            
            # Gráfico de Barras Adaptativo
            colors = ThemeManager.get_colors()
            
            # CORREÇÃO: Usando 'bin=False' e 'padding' no scale para garantir barras largas
            # quando houver poucos dados, e barras finas quando houver muitos.
            chart_bar = alt.Chart(df_view).mark_bar(
                color=colors['accent'],
                cornerRadiusTopLeft=4,
                cornerRadiusTopRight=4
            ).encode(
                x=alt.X(
                    'Data:T', 
                    title='', 
                    axis=alt.Axis(format='%d/%m', labelAngle=-45),
                    # Padding reduzido aproxima as barras
                    scale=alt.Scale(padding=0.1) 
                ),
                y=alt.Y('Energia Gerada (kWh):Q', title='Produção (kWh)'),
                tooltip=[
                    alt.Tooltip('Data', format='%d/%m/%Y'), 
                    alt.Tooltip('Energia Gerada (kWh)', format=',.2f')
                ]
            ).interactive()
            
            # Linha de Média
            line_avg = alt.Chart(pd.DataFrame({'y': [avg_gen]})).mark_rule(
                color=colors['danger'], strokeDash=[5,5]
            ).encode(y='y', tooltip=alt.value(f"Média: {avg_gen:.2f}"))
            
            st.altair_chart((chart_bar + line_avg).properties(height=400), use_container_width=True)
            
            # Detalhes Extremos
            id_max = df_view['Energia Gerada (kWh)'].idxmax()
            id_min = df_view['Energia Gerada (kWh)'].idxmin()
            
            c_best, c_worst = st.columns(2)
            c_best.success(f"**Melhor Dia:** {df_view.loc[id_max, 'Data'].strftime('%d/%m/%Y')} com **{df_view.loc[id_max, 'Energia Gerada (kWh)']:.2f} kWh**")
            c_worst.error(f"**Pior Dia:** {df_view.loc[id_min, 'Data'].strftime('%d/%m/%Y')} com **{df_view.loc[id_min, 'Energia Gerada (kWh)']:.2f} kWh**")

        # ABA 2: Acumulado
        with tab_acc:
            st.markdown("##### Evolução Acumulada no Período")
            
            df_acc = df_view.sort_values('Data').copy()
            df_acc['Acumulado'] = df_acc['Energia Gerada (kWh)'].cumsum()
            
            chart_area = alt.Chart(df_acc).mark_area(
                line={'color': colors['secondary']},
                color=alt.Gradient(
                    gradient='linear',
                    stops=[alt.GradientStop(color=colors['bg_card'], offset=0), alt.GradientStop(color=colors['secondary'], offset=1)],
                    x1=1, x2=1, y1=1, y2=0
                )
            ).encode(
                x=alt.X('Data:T', title='Data'),
                y=alt.Y('Acumulado:Q', title='Total Acumulado (kWh)'),
                tooltip=['Data', 'Acumulado']
            ).properties(height=400)
            
            st.altair_chart(chart_area, use_container_width=True)

        # ABA 3: Análise Anual e Heatmap
        with tab_annual:
            st.markdown('<div class="section-header border-teal"><h3>🗓️ Análise de Sazonalidade</h3></div>', unsafe_allow_html=True)
            
            # Seletor independente de ano
            all_years = sorted(df_full['Data'].dt.year.unique(), reverse=True)
            sel_heat_year = st.selectbox("Selecione o Ano para Análise Detalhada:", all_years)
            
            df_year_target = df_full[df_full['Data'].dt.year == sel_heat_year].copy()
            
            if df_year_target.empty:
                st.info("Sem dados para este ano.")
            else:
                # 1. Barras Mensais (Ajuste de largura)
                monthly_agg = df_year_target.groupby(df_year_target['Data'].dt.month)['Energia Gerada (kWh)'].sum().reset_index()
                # Mapa de nomes de mês curto
                m_names = {1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr', 5:'Mai', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Out', 11:'Nov', 12:'Dez'}
                monthly_agg['Nome'] = monthly_agg['Data'].map(m_names)
                
                chart_months = alt.Chart(monthly_agg).mark_bar(
                    color=colors['warning'],
                    # Removido size fixo, padding cuida do espaçamento
                ).encode(
                    x=alt.X(
                        'Nome:N', 
                        sort=list(m_names.values()), 
                        title='Mês',
                        scale=alt.Scale(padding=0.1) # Barras largas
                    ),
                    y=alt.Y('Energia Gerada (kWh):Q', title='Total (kWh)'),
                    tooltip=['Nome', 'Energia Gerada (kWh)']
                ).properties(height=300)
                
                st.altair_chart(chart_months, use_container_width=True)
                
                st.divider()
                
                # 2. Heatmap (Calendário - Estilo Original Restaurado)
                st.markdown(f"##### Mapa de Calor de Produção ({sel_heat_year})")
                
                # Prepara grid completo
                d_start = datetime(sel_heat_year, 1, 1)
                d_end = datetime(sel_heat_year, 12, 31)
                full_range = pd.date_range(d_start, d_end, freq='D')
                
                df_heat = pd.DataFrame({'Data': full_range})
                df_heat = df_heat.merge(df_year_target[['Data', 'Energia Gerada (kWh)']], on='Data', how='left').fillna(0)
                
                # Atributos para plotagem
                df_heat['Semana'] = df_heat['Data'].dt.isocalendar().week
                df_heat['DiaSemana'] = df_heat['Data'].dt.dayofweek
                df_heat['Mes'] = df_heat['Data'].dt.month
                
                # Ajustes de virada de ano
                df_heat.loc[(df_heat['Mes'] == 1) & (df_heat['Semana'] > 50), 'Semana'] = 0
                df_heat.loc[(df_heat['Mes'] == 12) & (df_heat['Semana'] == 1), 'Semana'] = 53

                # --- IMPLEMENTAÇÃO FIEL AO ORIGINAL ---
                # O usuário pediu "igual ao primeiro". Isso usa VConcat com Labels separados.
                
                # Parte 1: Labels dos Meses
                month_starts = df_heat.groupby('Mes').agg(first_week=('Semana', 'min')).reset_index()
                month_starts['NomeMes'] = month_starts['Mes'].map(m_names)
                
                month_labels_chart = alt.Chart(month_starts).mark_text(
                    align='left', baseline='bottom', dx=2,
                    font='Nunito', fontSize=12, color=colors['text_sub']
                ).encode(
                    x=alt.X('first_week:O', title=None, axis=None),
                    text='NomeMes:N'
                ).properties(height=20)

                # Parte 2: O Grid de Dias
                heatmap_grid = alt.Chart(df_heat).mark_rect(
                    stroke=colors['heatmap_stroke'], 
                    strokeWidth=0.5, 
                    cornerRadius=2
                ).encode(
                    x=alt.X(
                        'Semana:O', 
                        title=None, 
                        axis=None,
                        scale=alt.Scale(padding=0.02)
                    ),
                    y=alt.Y(
                        'DiaSemana:O', 
                        title=None, 
                        axis=alt.Axis(
                            labelExpr="['Seg','Ter','Qua','Qui','Sex','Sáb','Dom'][datum.value]",
                            ticks=False,
                            labelFont='Nunito'
                        ),
                        scale=alt.Scale(padding=0.04)
                    ),
                    # AQUI: Escala dinâmica (Min > 0 até Max Global)
                    color=alt.condition(
                        alt.datum['Energia Gerada (kWh)'] > 0,
                        alt.Color(
                            'Energia Gerada (kWh):Q',
                            scale=alt.Scale(scheme='yellowgreen', domain=[global_min_prod, global_max_prod]),
                            legend=alt.Legend(title="kWh", orient="bottom")
                        ),
                        alt.value('#f3f4f6' if not st.session_state.dark_mode else '#1f2937') # Cor para dias sem geração
                    ),
                    tooltip=[alt.Tooltip('Data', format='%d/%m/%Y'), 'Energia Gerada (kWh)']
                ).properties(height=220)

                # Combinação (Igual ao código original)
                final_heatmap = alt.vconcat(
                    month_labels_chart,
                    heatmap_grid,
                    spacing=5
                ).configure_view(strokeWidth=0)
                
                st.altair_chart(final_heatmap, use_container_width=True)

        # ABA 4: Simulador ROI (Financeiro Avançado)
        with tab_roi:
            st.markdown('<div class="section-header border-pink"><h3>💰 Viabilidade e Retorno (ROI)</h3></div>', unsafe_allow_html=True)
            
            # Dados Históricos Totais
            lifetime_gen = df_full['Energia Gerada (kWh)'].sum()
            lifetime_fin = FinancialCalculator.calculate_savings(
                lifetime_gen, params['tarifa_cheia'], params['tarifa_fio_b'], params['simultaneidade']
            )
            
            total_saved = lifetime_fin['net_savings']
            days_since_install = (datetime.now().date() - params['data_inicio']).days
            years_active = max(days_since_install / 365.25, 0.01)
            
            # Projeção Futura (baseada na média histórica)
            avg_daily_all = df_full['Energia Gerada (kWh)'].mean()
            annual_gen_proj = avg_daily_all * 365
            
            # Cálculo de Payback
            # Simula um ano futuro médio considerando a taxa de 2025+
            fin_proj_annual = FinancialCalculator.calculate_savings(
                annual_gen_proj, params['tarifa_cheia'], params['tarifa_fio_b'], params['simultaneidade']
            )
            annual_savings_proj = fin_proj_annual['net_savings']
            
            payback_years = params['investimento'] / annual_savings_proj if annual_savings_proj > 0 else 0
            
            # Métricas
            c_r1, c_r2, c_r3 = st.columns(3)
            c_r1.metric("Total Economizado (Vida Útil)", f"R$ {DataManager.format_number_br(total_saved)}")
            c_r2.metric("Saldo do Investimento", f"R$ {DataManager.format_number_br(params['investimento'] - total_saved)}")
            c_r3.metric("Payback Estimado", f"{payback_years:.1f} Anos")
            
            st.divider()
            
            # Gráfico de Fluxo de Caixa (25 Anos)
            st.markdown("##### 📉 Fluxo de Caixa Projetado (25 Anos)")
            
            cashflow_years = list(range(0, 26))
            cashflow_vals = [-params['investimento']]
            accumulated = -params['investimento']
            
            for y in range(1, 26):
                # Degradação do painel (0.5% a.a.) + Inflação Energética (simulada 4% a.a.)
                # Resultado líquido: aumento conservador de 3.5% no valor economizado
                factor = (1 + 0.035) ** y
                year_saving = annual_savings_proj * factor
                accumulated += year_saving
                cashflow_vals.append(accumulated)
            
            df_cf = pd.DataFrame({'Ano': cashflow_years, 'Saldo': cashflow_vals})
            
            chart_cf = alt.Chart(df_cf).mark_line(
                point=True, strokeWidth=3, interpolate='monotone'
            ).encode(
                x=alt.X('Ano:O'),
                y=alt.Y('Saldo:Q', title='Saldo Acumulado (R$)'),
                color=alt.condition(
                    alt.datum.Saldo > 0,
                    alt.value(colors['accent']),
                    alt.value(colors['danger'])
                ),
                tooltip=['Ano', alt.Tooltip('Saldo', format=',.2f')]
            ).properties(height=350)
            
            zero_line = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(
                strokeDash=[5,5], color='gray'
            ).encode(y='y')
            
            st.altair_chart(chart_cf + zero_line, use_container_width=True)
            
            # Box Educativo
            st.markdown("""
            <div class="info-box">
                <h4>📚 Entenda seus Números com a Lei 14.300</h4>
                <ul>
                    <li><strong>Fio B:</strong> Componente da tarifa que remunera a distribuidora. Pela nova lei, você paga essa taxa progressivamente sobre a energia que injeta na rede.</li>
                    <li><strong>Fator de Simultaneidade:</strong> Energia consumida instantaneamente. Quanto maior este fator (consumir durante o sol), menos impostos você paga e maior o retorno.</li>
                    <li><strong>Estratégia:</strong> Programe máquinas de lavar, bombas de piscina e ar-condicionado para funcionar entre 10h e 15h.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        # ABA 5: Dados e Edição
        with tab_data:
            st.markdown('<div class="section-header border-purple"><h3>📋 Gerenciamento de Dados</h3></div>', unsafe_allow_html=True)
            
            c_d1, c_d2 = st.columns([3, 1])
            
            with c_d1:
                # Botão de Download
                csv = df_view.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Baixar Dados (CSV)",
                    data=csv,
                    file_name='solar_data.csv',
                    mime='text/csv',
                )
                
                st.dataframe(
                    df_view.style.format({"Energia Gerada (kWh)": "{:.2f}"}),
                    use_container_width=True,
                    height=500
                )
                
            with c_d2:
                st.warning("Zona de Edição")
                if st.button("Ativar Modo Edição", use_container_width=True):
                    st.session_state.edit_mode = not st.session_state.edit_mode
                
                if st.session_state.edit_mode:
                    st.info("Selecione um registro da lista filtrada para editar.")
                    
                    # Seletor
                    opts_idx = df_view.index.tolist()
                    opts_lbl = [f"{df_view.loc[i, 'Data'].strftime('%d/%m')} - {df_view.loc[i, 'Energia Gerada (kWh)']} kWh" for i in opts_idx]
                    
                    sel_edit = st.selectbox("Registro:", opts_idx, format_func=lambda x: opts_lbl[opts_idx.index(x)] if x in opts_idx else "")
                    
                    if sel_edit is not None:
                        row_dat = df_view.loc[sel_edit]
                        n_date = st.date_input("Nova Data", row_dat['Data'], key="ed_d")
                        n_val = st.number_input("Novo Valor", value=float(row_dat['Energia Gerada (kWh)']), key="ed_v")
                        
                        col_save, col_del = st.columns(2)
                        
                        if col_save.button("Atualizar"):
                            if DataManager.update_entry(sheet, sel_edit, n_date, n_val):
                                st.success("Atualizado!")
                                time.sleep(1)
                                st.rerun()
                                
                        if col_del.button("Excluir"):
                            if DataManager.delete_entry(sheet, sel_edit):
                                st.success("Excluído!")
                                time.sleep(1)
                                st.rerun()

    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: var(--text-sub); font-size: 0.8rem; margin-top: 2rem;">
        SolarAnalytics Pro Enterprise v3.2 • Desenvolvido com Python & Streamlit<br>
        Última sincronização: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
