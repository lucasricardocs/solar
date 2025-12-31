# -*- coding: utf-8 -*-
"""
SolarAnalytics Pro - Sistema Integrado de Monitoramento Fotovoltaico
Versão: 5.0.0 (No Sidebar Edition)
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
        pass

# Constantes de Conexão
SPREADSHEET_ID = '1WI2tZ94lVV9GfaaWerdSfuChFLzWfMbU4v2m6QrwTdY'
WORKSHEET_NAME = 'solardaily'

# Configuração da Página Streamlit (Layout Wide)
st.set_page_config(
    layout="wide",
    page_title="SolarAnalytics Pro | Dashboard",
    page_icon="⚡",
    initial_sidebar_state="collapsed" # Esconde a sidebar nativa
)

# Inicialização do Session State
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False

if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True # Começa escuro por padrão para contraste

if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

# ==============================================================================
# 2. SISTEMA DE TEMAS E ESTILIZAÇÃO (CSS AVANÇADO)
# ==============================================================================

def get_theme_colors():
    """
    Retorna o dicionário de cores baseado no estado atual (Claro/Escuro).
    """
    if st.session_state.dark_mode:
        return {
            'mode': 'dark',
            'primary_color': '#FFFFFF',      # Títulos em Branco Puro
            'secondary_color': '#06b6d4',    # Ciano (Cyan 500)
            'accent_color': '#10b981',       # Verde Esmeralda
            'warning_color': '#f59e0b',      # Amarelo (Amber 500)
            'danger_color': '#ef4444',       # Vermelho (Red 500)
            'text_primary': '#f8fafc',       # Branco Gelo (Slate 50)
            'text_secondary': '#94a3b8',     # Cinza médio (Slate 400)
            'bg_main': '#0f172a',            # Azul Noturno (Slate 900)
            'bg_light': '#1e293b',           # Slate 800
            'bg_card': '#334155',            # Slate 700
            'border_light': '#475569',       # Slate 600
            'header_bg': 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
            'subheader_bg': '#1e293b',
            'form_bg': '#1e293b',
            'metric_bg': '#1e293b',
            'heatmap_stroke': '#475569',
            'heatmap_zero': '#1e293b',
            'chart_grid': '#334155',
            'bar_color': '#22d3ee'           # Cor Neon para as barras no escuro
        }
    else:
        return {
            'mode': 'light',
            'primary_color': '#111827',
            'secondary_color': '#3b82f6',
            'accent_color': '#10b981',
            'warning_color': '#f59e0b',
            'danger_color': '#ef4444',
            'text_primary': '#1f2937',
            'text_secondary': '#6b7280',
            'bg_main': '#f8fafc',
            'bg_light': '#ffffff',
            'bg_card': '#ffffff',
            'border_light': '#e2e8f0',
            'header_bg': 'linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)',
            'subheader_bg': '#ffffff',
            'form_bg': '#ffffff',
            'metric_bg': '#ffffff',
            'heatmap_stroke': '#e2e8f0',
            'heatmap_zero': '#f1f5f9',
            'chart_grid': '#e5e7eb',
            'bar_color': '#3b82f6'           # Azul para barras no claro
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
    padding-top: 1rem;
    padding-bottom: 3rem;
    max-width: 1600px;
}}

/* --- Header Personalizado --- */
.header-section {{
    background: {theme['header_bg']};
    color: {theme['text_primary']};
    padding: 1.5rem 2rem;
    border-radius: 12px;
    border: 1px solid {theme['border_light']};
    margin-bottom: 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between; /* Espalha conteúdo */
    gap: 1.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}}

.header-content {{
    display: flex;
    align-items: center;
    gap: 1rem;
}}

.header-title {{
    font-size: 2rem;
    font-weight: 800;
    margin-bottom: 0.2rem;
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
    padding: 10px 15px;
    background: {theme['subheader_bg']};
    border-radius: 8px;
    border-left: 5px solid;
    border-top: 1px solid {theme['border_light']};
    border-right: 1px solid {theme['border_light']};
    border-bottom: 1px solid {theme['border_light']};
    display: flex;
    align-items: center;
}}

.subheader-container h2 {{
    font-size: 1.1rem;
    font-weight: 700;
    margin: 0;
    color: {theme['text_primary']};
}}

.border-blue {{ border-left-color: {theme['secondary_color']}; }}
.border-green {{ border-left-color: {theme['accent_color']}; }}
.border-orange {{ border-left-color: {theme['warning_color']}; }}
.border-pink {{ border-left-color: {theme['danger_color']}; }}

/* --- Métricas (KPI Cards) --- */
[data-testid="metric-container"] {{
    background-color: {theme['metric_bg']};
    border: 1px solid {theme['border_light']};
    border-radius: 10px;
    padding: 1rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}}

[data-testid="metric-label"] {{
    font-size: 0.9rem !important;
    color: {theme['text_secondary']} !important;
}}

[data-testid="metric-value"] {{
    font-size: 1.5rem !important;
    color: {theme['text_primary']} !important;
    font-weight: 800 !important;
}}

/* --- Formulários e Inputs --- */
.stForm {{
    background-color: {theme['form_bg']};
    border: 1px solid {theme['border_light']};
    border-radius: 10px;
    padding: 1.5rem;
}}

.stTextInput > div > div, 
.stNumberInput > div > div, 
.stDateInput > div > div, 
.stSelectbox > div > div {{
    background-color: {theme['bg_card']} !important;
    color: {theme['text_primary']} !important;
    border-color: {theme['border_light']} !important;
    border-radius: 6px;
}}

/* Inputs Hover */
.stTextInput:hover > div > div, 
.stNumberInput:hover > div > div {{
    border-color: {theme['secondary_color']} !important;
}}

/* Botões */
button[kind="secondary"] {{
    background-color: {theme['bg_card']};
    border: 1px solid {theme['border_light']};
    color: {theme['text_primary']};
    border-radius: 6px;
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
    border-radius: 6px;
    font-weight: 700;
}}

/* Badges e Utilitários */
.status-badge {{
    padding: 0.3rem 0.8rem;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 700;
    display: inline-block;
}}

.status-online {{ 
    background-color: rgba(16, 185, 129, 0.15); 
    color: #10B981; 
    border: 1px solid rgba(16, 185, 129, 0.3);
}}

/* Remove elementos padrão */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header {{visibility: hidden;}}
[data-testid="stSidebar"] {{display: none;}} /* Força remoção da sidebar */

</style>
""", unsafe_allow_html=True)

# — Configuração do Tema Altair (Gráficos) —
def configure_altair_theme():
    """Configura o tema dos gráficos para combinar com o modo Claro/Escuro."""
    font = "Nunito"
    
    bg_color = 'transparent'
    text_color = theme['text_primary']
    grid_color = theme['chart_grid']
    
    alt.themes.enable('none')
    alt.themes.register("custom_theme", lambda: {
        "config": {
            "background": bg_color,
            "view": { "stroke": "transparent" },
            "title": { "font": font, "fontSize": 14, "color": text_color },
            "axis": {
                "labelFont": font, "titleFont": font,
                "labelColor": theme['text_secondary'], "titleColor": theme['text_secondary'],
                "gridColor": grid_color, "domainColor": grid_color, "tickColor": grid_color,
            },
            "legend": {
                "labelFont": font, "titleFont": font,
                "labelColor": text_color, "titleColor": text_color,
            }
        }
    })
    alt.themes.enable("custom_theme")

configure_altair_theme()

# ==============================================================================
# 3. CONEXÃO E DADOS
# ==============================================================================

def format_br(val):
    if val is None: return "0,00"
    return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

@st.cache_resource(show_spinner="Conectando...")
def connect_gsheets():
    try:
        scopes = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
    except Exception as e:
        st.error(f"Erro Conexão: {e}")
        return None

@st.cache_data(ttl=300)
def load_data():
    try:
        sheet = connect_gsheets()
        if not sheet: return pd.DataFrame()
        
        vals = sheet.get_all_values()
        if len(vals) < 2: return pd.DataFrame()
        
        df = pd.DataFrame(vals[1:], columns=vals[0])
        df.columns = [c.lower().strip() for c in df.columns]
        df.rename(columns={'data': 'Data', 'gerado': 'Energia'}, inplace=True)
        
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        df['Energia'] = (df['Energia'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False))
        df['Energia'] = pd.to_numeric(df['Energia'], errors='coerce')
        
        df.dropna(subset=['Data', 'Energia'], inplace=True)
        df = df[df['Energia'] >= 0]
        return df.sort_values('Data').drop_duplicates(subset=['Data'], keep='last').reset_index(drop=True)
    except: return pd.DataFrame()

def save_data(dt, val):
    try:
        s = connect_gsheets()
        s.append_row([dt.strftime('%d/%m/%Y'), str(val).replace('.', ',')], value_input_option='USER_ENTERED')
        st.cache_data.clear()
        return True
    except: return False

def update_data(idx, dt, val):
    try:
        s = connect_gsheets()
        s.update_cell(idx+2, 1, dt.strftime('%d/%m/%Y'))
        s.update_cell(idx+2, 2, str(val).replace('.', ','))
        st.cache_data.clear()
        return True
    except: return False

def delete_data(idx):
    try:
        s = connect_gsheets()
        s.delete_rows(idx+2)
        st.cache_data.clear()
        return True
    except: return False

# ==============================================================================
# 4. LÓGICA FINANCEIRA (LEI 14.300)
# ==============================================================================

def calc_financeiro(total_kwh, t_cheia, t_fio, simult):
    fator = simult / 100.0
    
    # Volumes
    auto = total_kwh * fator
    injecao = total_kwh * (1 - fator)
    
    # Regra de Transição (Fio B progressivo)
    ano = datetime.now().year
    # Tabela 14.300
    tab = {2023:0.15, 2024:0.30, 2025:0.45, 2026:0.60, 2027:0.75, 2028:0.90}
    perc_taxa = tab.get(ano, 1.0)
    
    # Custos e Economias
    taxa_fio_b = injecao * (t_fio * perc_taxa)
    econ_bruta = (auto * t_cheia) + (injecao * t_cheia)
    econ_liq = econ_bruta - taxa_fio_b
    
    return {
        'econ_liq': econ_liq,
        'taxa': taxa_fio_b,
        'auto_kwh': auto,
        'perc': perc_taxa * 100
    }

# ==============================================================================
# 5. APP PRINCIPAL
# ==============================================================================

def main():
    
    # --- HEADER ---
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(f"""
        <div class="header-section">
            <div class="header-content">
                <span style="font-size: 2.5rem;">⚡</span>
                <div>
                    <h1 class="header-title">SolarAnalytics Pro</h1>
                    <p class="header-subtitle">Enterprise Edition • Lei 14.300 Ready</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_h2:
        # Botão de Tema no Header
        icon = "☀️" if not st.session_state.dark_mode else "🌙"
        lbl = "Mudar Tema"
        if st.button(f"{icon} {lbl}", use_container_width=True):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
        
        if st.button("🔄 Recarregar Dados", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # --- CONTROLES SUPERIORES (SUBSTITUI SIDEBAR) ---
    with st.expander("⚙️ Configurações, Tarifas e Filtros", expanded=False):
        c_conf1, c_conf2, c_conf3 = st.columns([1, 1, 2])
        
        with c_conf1:
            st.markdown("##### 💰 Tarifas")
            t_cheia = st.number_input("Tarifa Cheia (R$)", 0.9555, format="%.4f")
            t_fio = st.number_input("Tarifa Fio B (R$)", 0.4900, format="%.4f")
            
        with c_conf2:
            st.markdown("##### ⚙️ Sistema")
            f_simult = st.slider("Simultaneidade (%)", 0, 100, 30)
            invest = st.number_input("Investimento (R$)", 15000.0)
            
        with c_conf3:
            st.markdown("##### 📅 Filtros de Data")
            tipo_filtro = st.radio("Período:", ["Mês Específico", "Intervalo", "Ano Completo", "Tudo"], horizontal=True)
            
            # Carrega dados para filtros
            df = load_data()
            
            df_view = df.copy()
            label_per = "Geral"
            heatmap_year = datetime.now().year
            
            if not df.empty:
                # Limites Globais para Heatmap (Baseado no histórico total)
                g_max = df['Energia'].max()
                g_min = df[df['Energia'] > 0]['Energia'].min() if not df[df['Energia'] > 0].empty else 0.1
                if pd.isna(g_max): g_max = 20
                if pd.isna(g_min): g_min = 0.1

                if tipo_filtro == "Mês Específico":
                    ys = sorted(df['Data'].dt.year.unique(), reverse=True)
                    sy = st.selectbox("Ano", ys)
                    ms = sorted(df[df['Data'].dt.year == sy]['Data'].dt.month.unique())
                    sm = st.selectbox("Mês", ms)
                    df_view = df[(df['Data'].dt.year == sy) & (df['Data'].dt.month == sm)]
                    label_per = f"{sm}/{sy}"
                    heatmap_year = sy
                    
                elif tipo_filtro == "Intervalo":
                    d1, d2 = df['Data'].min().date(), df['Data'].max().date()
                    dr = st.date_input("De / Até", [d1, d2])
                    if len(dr) == 2:
                        df_view = df[(df['Data'].dt.date >= dr[0]) & (df['Data'].dt.date <= dr[1])]
                        label_per = "Personalizado"
                        
                elif tipo_filtro == "Ano Completo":
                    ys = sorted(df['Data'].dt.year.unique(), reverse=True)
                    sy = st.selectbox("Ano", ys)
                    df_view = df[df['Data'].dt.year == sy]
                    label_per = str(sy)
                    heatmap_year = sy
                else:
                    label_per = "Todo o Histórico"

    # --- INPUT DE DADOS ---
    st.markdown('<div class="subheader-container border-blue"><h2>📝 Registrar Produção</h2></div>', unsafe_allow_html=True)
    with st.form("add_data"):
        c1, c2, c3 = st.columns([2, 2, 1])
        d_in = c1.date_input("Data", datetime.today())
        v_in = c2.number_input("Energia Gerada (kWh)", min_value=0.0, step=0.1)
        if c3.form_submit_button("Salvar Registro", use_container_width=True):
            if v_in > 0:
                if save_data(d_in, v_in):
                    st.success("Salvo!")
                    time.sleep(0.5)
                    st.rerun()
            else:
                st.warning("Valor deve ser > 0")

    # --- DASHBOARD ---
    if df_view.empty:
        st.info("Nenhum dado para exibir neste período.")
    else:
        # Cálculos
        total_kwh = df_view['Energia'].sum()
        media_kwh = df_view['Energia'].mean()
        fin = calc_financeiro(total_kwh, t_cheia, t_fio, f_simult)
        
        # Cards KPI
        st.markdown(f'<div class="subheader-container border-green"><h2>📊 Resultados: {label_per}</h2></div>', unsafe_allow_html=True)
        
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Economia Líquida", f"R$ {format_br(fin['econ_liq'])}", help="Já descontando o fio B")
        k2.metric("Geração Total", f"{format_br(total_kwh)} kWh", delta=f"Média: {format_br(media_kwh)}")
        k3.metric("Taxa Paga (Fio B)", f"R$ {format_br(fin['taxa'])}", delta=f"{fin['perc']:.0f}%", delta_color="inverse")
        k4.metric("Autoconsumo", f"{format_br(fin['auto_kwh'])} kWh")

        st.divider()

        # Tabs
        t1, t2, t3, t4 = st.tabs(["📊 Produção Diária", "📈 Acumulado", "💰 Financeiro", "📋 Dados"])

        with t1:
            # Gráfico Diário Adaptativo
            st.markdown("##### Produção Diária")
            
            # Garante que as barras apareçam usando band padding nativo
            # Se tiver muitos dados, aumenta o padding (barras finas).
            # Se tiver poucos dados, diminui o padding (barras grossas).
            count = len(df_view)
            pad = 0.1 if count < 20 else (0.3 if count < 60 else 0.05)
            
            bars = alt.Chart(df_view).mark_bar(
                color=theme['bar_color'],
                cornerRadiusTopLeft=3,
                cornerRadiusTopRight=3
            ).encode(
                # Use band=True implicitamente com Ordinal/Temporal e padding controlado
                x=alt.X('Data:T', axis=alt.Axis(format='%d/%m', labelAngle=-45)),
                y=alt.Y('Energia:Q', title='kWh'),
                tooltip=['Data', alt.Tooltip('Energia', format='.2f')]
            )
            
            line = alt.Chart(pd.DataFrame({'y':[media_kwh]})).mark_rule(
                color=theme['danger_color'], strokeDash=[5,5]
            ).encode(y='y', tooltip=alt.value(f"Média: {media_kwh:.2f}"))
            
            st.altair_chart((bars + line).interactive(), use_container_width=True)

        with t2:
            st.markdown("##### Curva Acumulada")
            df_acc = df_view.sort_values('Data').copy()
            df_acc['Acumulado'] = df_acc['Energia'].cumsum()
            
            area = alt.Chart(df_acc).mark_area(
                line={'color': theme['secondary_color']},
                color=alt.Gradient(
                    gradient='linear',
                    stops=[alt.GradientStop(color=theme['bg_main'], offset=0), 
                           alt.GradientStop(color=theme['secondary_color'], offset=1)],
                    x1=1, x2=1, y1=1, y2=0
                )
            ).encode(
                x='Data:T', y='Acumulado:Q', tooltip=['Data', 'Acumulado']
            )
            st.altair_chart(area, use_container_width=True)

        with t3:
            st.markdown("##### Análise de Retorno")
            # Projeção simples anualizada
            fator_anual = 365 / max(1, len(df_view))
            econ_proj = fin['econ_liq'] * fator_anual
            payback = invest / econ_proj if econ_proj > 0 else 0
            
            c1, c2 = st.columns(2)
            c1.metric("Payback Estimado", f"{payback:.1f} Anos")
            c2.metric("Projeção Anual (R$)", f"R$ {format_br(econ_proj)}")
            
            # Fluxo de Caixa
            anos = list(range(26))
            fluxo = [-invest]
            acum = -invest
            for i in range(1, 26):
                acum += econ_proj * ((1 - 0.005) ** i) # Degradação 0.5%
                fluxo.append(acum)
            
            df_cf = pd.DataFrame({'Ano': anos, 'Saldo': fluxo})
            
            cf_chart = alt.Chart(df_cf).mark_line(
                point=True, color=theme['accent_color'], strokeWidth=3
            ).encode(
                x='Ano:O', y='Saldo:Q', tooltip=['Ano', alt.Tooltip('Saldo', format=',.2f')]
            )
            zero = alt.Chart(pd.DataFrame({'y':[0]})).mark_rule(color='gray').encode(y='y')
            st.altair_chart(cf_chart + zero, use_container_width=True)

        with t4:
            c_d1, c_d2 = st.columns([3, 1])
            with c_d1:
                st.dataframe(df_view.style.format({"Energia": "{:.2f}"}), use_container_width=True, height=400)
            
            with c_d2:
                if st.button("Ativar Edição"): st.session_state.edit_mode = not st.session_state.edit_mode
                if st.session_state.edit_mode:
                    sid = st.selectbox("ID", df_view.index)
                    if sid is not None:
                        row = df_view.loc[sid]
                        ndt = st.date_input("Data", row['Data'])
                        nvl = st.number_input("Valor", value=float(row['Energia']))
                        if st.button("Atualizar"):
                            update_data(sid, ndt, nvl)
                            st.rerun()
                        if st.button("Deletar"):
                            delete_data(sid)
                            st.rerun()

        # --- HEATMAP FORA DAS ABAS (Visão Global) ---
        st.divider()
        st.markdown(f'<div class="subheader-container border-orange"><h2>🗓️ Mapa de Calor Anual ({heatmap_year})</h2></div>', unsafe_allow_html=True)
        
        # Filtra o ano para o heatmap
        df_heat_src = df[df['Data'].dt.year == heatmap_year].copy()
        
        if not df_heat_src.empty:
            # Cria calendário completo
            d1 = datetime(heatmap_year, 1, 1)
            d2 = datetime(heatmap_year, 12, 31)
            full_dates = pd.date_range(d1, d2)
            df_full = pd.DataFrame({'Data': full_dates})
            
            df_hm = pd.merge(df_full, df_heat_src, on='Data', how='left').fillna(0)
            df_hm['Semana'] = df_hm['Data'].dt.isocalendar().week
            df_hm['Dia'] = df_hm['Data'].dt.dayofweek
            df_hm['Mes'] = df_hm['Data'].dt.month
            
            # Ajuste virada ano
            df_hm.loc[(df_hm['Mes']==1) & (df_hm['Semana']>50), 'Semana'] = 0
            df_hm.loc[(df_hm['Mes']==12) & (df_hm['Semana']==1), 'Semana'] = 53

            # Labels Meses
            lbls = df_hm.groupby('Mes')['Semana'].min().reset_index()
            lbls['Nome'] = lbls['Mes'].apply(lambda x: datetime(2023, x, 1).strftime('%b'))
            
            c_lbl = alt.Chart(lbls).mark_text(align='left', dy=10, color=theme['text_secondary']).encode(
                x=alt.X('Semana:O', axis=None), text='Nome'
            )
            
            # Heatmap com escala global corrigida
            c_hm = alt.Chart(df_hm).mark_rect(
                stroke=theme['heatmap_stroke'], 
                strokeWidth=1, 
                cornerRadius=2
            ).encode(
                x=alt.X('Semana:O', axis=None),
                y=alt.Y('Dia:O', axis=None, title=''),
                color=alt.condition(
                    'datum.Energia > 0',
                    alt.Color('Energia:Q', 
                              scale=alt.Scale(scheme='yellowgreen', domain=[g_min, g_max]),
                              legend=alt.Legend(title="kWh")),
                    alt.value(theme['heatmap_zero'])
                ),
                tooltip=['Data', alt.Tooltip('Energia', format='.2f')]
            ).properties(height=180)
            
            st.altair_chart(alt.vconcat(c_lbl, c_hm), use_container_width=True)
        else:
            st.warning(f"Sem dados para o ano {heatmap_year}")

    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: {theme['text_secondary']}; font-size: 0.8rem; margin-top: 3rem;">
        SolarAnalytics Pro v5.0 • Desenvolvido com Python & Streamlit<br>
        Última atualização: {datetime.now().strftime('%d/%m/%Y às %H:%M')}
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
