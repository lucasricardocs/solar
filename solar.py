# -*- coding: utf-8 -*-
"""
SolarAnalytics Pro - Versão Final Corrigida
- Sem Sidebar
- Sem Expansíveis
- Modo Claro (Flat Design)
- Barras Adaptativas
- Cálculo Lei 14.300 (Fio B)
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
# 1. CONFIGURAÇÕES INICIAIS
# ==============================================================================

# Ignora avisos para manter o app limpo
warnings.filterwarnings('ignore')

# Otimização do Altair
alt.data_transformers.enable('json')

# Tenta configurar localidade para formato de moeda R$
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

# Configuração da Página (Layout Wide, Sem Sidebar)
st.set_page_config(
    layout="wide",
    page_title="SolarAnalytics Pro",
    page_icon="☀️",
    initial_sidebar_state="collapsed"
)

# Inicialização do Estado da Sessão
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False

# Força Modo Claro
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# ==============================================================================
# 2. ESTILO (CSS FLAT & LIGHT)
# ==============================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600;700&display=swap');

/* Reset Global para Design Flat */
html, body, [class*="st-"], .stApp {
    font-family: 'Nunito', sans-serif !important;
    background-color: #ffffff !important;
    color: #1f2937 !important;
}

/* Remover Sidebar nativa */
[data-testid="stSidebar"] { display: none; }

/* Headers */
.header-container {
    border-bottom: 2px solid #e5e7eb;
    padding-bottom: 20px;
    margin-bottom: 30px;
    display: flex;
    align-items: center;
    gap: 15px;
}

.header-title {
    font-size: 2rem;
    font-weight: 800;
    color: #111827;
    margin: 0;
}

.header-subtitle {
    font-size: 1rem;
    color: #6b7280;
    margin: 0;
}

/* Painéis de Controle (Substituindo Sidebar/Expander) */
.control-panel {
    background-color: #f9fafb; /* Cinza muito suave */
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
}

.control-label {
    font-size: 0.85rem;
    font-weight: 700;
    color: #4b5563;
    text-transform: uppercase;
    margin-bottom: 10px;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 5px;
}

/* KPIs (Métricas) - Estilo Flat */
[data-testid="metric-container"] {
    background-color: #ffffff !important;
    border: 1px solid #e5e7eb !important;
    box-shadow: none !important;
    border-radius: 8px;
    padding: 15px;
}

[data-testid="metric-label"] {
    color: #6b7280 !important;
    font-size: 0.9rem !important;
}

[data-testid="metric-value"] {
    color: #111827 !important;
    font-size: 1.6rem !important;
    font-weight: 800 !important;
}

/* Inputs Unificados */
.stTextInput > div > div, 
.stNumberInput > div > div, 
.stDateInput > div > div, 
.stSelectbox > div > div {
    background-color: #ffffff !important;
    border: 1px solid #d1d5db !important;
    color: #1f2937 !important;
    border-radius: 6px;
}

/* Botões */
button[kind="secondary"] {
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    color: #374151;
    border-radius: 6px;
}

button[kind="primary"] {
    background-color: #2563eb;
    color: white;
    border: none;
    border-radius: 6px;
}

/* Esconder menus padrão */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

</style>
""", unsafe_allow_html=True)

# Configuração do Tema dos Gráficos (Altair Clean)
def configure_altair_theme():
    alt.themes.enable('none')
    alt.themes.register("clean_theme", lambda: {
        "config": {
            "background": "#ffffff",
            "view": {"stroke": "transparent"},
            "title": {"font": "Nunito", "color": "#1f2937"},
            "axis": {
                "labelFont": "Nunito",
                "titleFont": "Nunito",
                "labelColor": "#6b7280",
                "titleColor": "#6b7280",
                "gridColor": "#f3f4f6",
                "domainColor": "#e5e7eb"
            },
            "legend": {
                "labelFont": "Nunito",
                "titleFont": "Nunito",
                "labelColor": "#374151"
            }
        }
    })
    alt.themes.enable("clean_theme")

configure_altair_theme()

# ==============================================================================
# 3. CONEXÃO E DADOS
# ==============================================================================

def format_br(val):
    """Formata número para string PT-BR."""
    if val is None: return "0,00"
    return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

@st.cache_resource(show_spinner=False)
def connect_gsheets():
    """Conecta ao Google Sheets."""
    try:
        scopes = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
    except: return None

@st.cache_data(ttl=60)
def load_data():
    """Carrega dados da planilha."""
    try:
        sheet = connect_gsheets()
        if not sheet: return pd.DataFrame()
        
        vals = sheet.get_all_values()
        if len(vals) < 2: return pd.DataFrame()
        
        df = pd.DataFrame(vals[1:], columns=vals[0])
        df.columns = [c.lower().strip() for c in df.columns]
        df.rename(columns={'data': 'Data', 'gerado': 'Energia'}, inplace=True)
        
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        df['Energia'] = pd.to_numeric(
            df['Energia'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False),
            errors='coerce'
        )
        
        df.dropna(subset=['Data', 'Energia'], inplace=True)
        df = df[df['Energia'] >= 0]
        return df.sort_values('Data').drop_duplicates(subset=['Data'], keep='last').reset_index(drop=True)
    except: return pd.DataFrame()

# CRUD (Salvar, Atualizar, Deletar)
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
# 4. LÓGICA FINANCEIRA (LEI 14.300 - FIO B)
# ==============================================================================

def calcular_lei_14300(total_kwh, t_cheia, t_fio, simultaneidade):
    """
    Calcula economia real descontando a 'Taxação do Sol' (Fio B).
    """
    fator = simultaneidade / 100.0
    
    # Energia consumida na hora (Autoconsumo) - Isento
    auto = total_kwh * fator
    
    # Energia injetada na rede - Taxada
    injecao = total_kwh * (1 - fator)
    
    # Tabela progressiva de cobrança
    ano = datetime.now().year
    # 2023: 15%, 2024: 30%, 2025: 45%, etc.
    tab = {2023:0.15, 2024:0.30, 2025:0.45, 2026:0.60, 2027:0.75, 2028:0.90}
    perc_cobrado = tab.get(ano, 1.0)
    
    # Cálculo do custo (taxa)
    custo_taxa = injecao * (t_fio * perc_cobrado)
    
    # Economia Bruta (se não houvesse taxa)
    econ_bruta = (auto * t_cheia) + (injecao * t_cheia)
    
    # Economia Líquida (Real)
    econ_liquida = econ_bruta - custo_taxa
    
    return {
        'econ_liq': econ_liquida,
        'taxa': custo_taxa,
        'auto_kwh': auto,
        'perc_taxa': perc_cobrado * 100
    }

# ==============================================================================
# 5. APLICAÇÃO PRINCIPAL
# ==============================================================================

def main():
    
    # --- HEADER ---
    st.markdown("""
    <div class="header-container">
        <div style="font-size: 2.5rem;">⚡</div>
        <div>
            <h1 class="header-title">SolarAnalytics Pro</h1>
            <p class="header-subtitle">Gestão Inteligente de Energia Fotovoltaica</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- CONTROLES (TOPO - SEM SIDEBAR) ---
    st.markdown('<div class="control-panel">', unsafe_allow_html=True)
    c_conf1, c_conf2, c_conf3 = st.columns([1, 1, 2])
    
    with c_conf1:
        st.markdown('<div class="control-label">💰 Tarifas (R$/kWh)</div>', unsafe_allow_html=True)
        t_cheia = st.number_input("Tarifa Cheia", 0.9555, format="%.4f")
        t_fio = st.number_input("Tarifa Fio B", 0.4900, format="%.4f")
        
    with c_conf2:
        st.markdown('<div class="control-label">⚙️ Sistema</div>', unsafe_allow_html=True)
        f_simult = st.slider("Simultaneidade (%)", 0, 100, 30)
        invest = st.number_input("Investimento (R$)", 15000.0)
        
    with c_conf3:
        st.markdown('<div class="control-label">📅 Seleção de Período</div>', unsafe_allow_html=True)
        # Filtros Horizontais
        tipo_filtro = st.radio("Filtro:", ["Mês Atual", "Mês Específico", "Intervalo", "Ano Completo", "Tudo"], horizontal=True, label_visibility="collapsed")
        
        # Carrega dados
        df = load_data()
        df_view = df.copy()
        label_per = "Geral"
        hm_year = datetime.now().year
        
        # Lógica de Filtro
        if not df.empty:
            if tipo_filtro == "Mês Atual":
                hj = datetime.today()
                df_view = df[(df['Data'].dt.year == hj.year) & (df['Data'].dt.month == hj.month)]
                label_per = f"{hj.strftime('%m/%Y')}"
                hm_year = hj.year
                
            elif tipo_filtro == "Mês Específico":
                c_y, c_m = st.columns(2)
                ys = sorted(df['Data'].dt.year.unique(), reverse=True)
                sy = c_y.selectbox("Ano", ys)
                ms = sorted(df[df['Data'].dt.year == sy]['Data'].dt.month.unique())
                sm = c_m.selectbox("Mês", ms)
                df_view = df[(df['Data'].dt.year == sy) & (df['Data'].dt.month == sm)]
                label_per = f"{sm}/{sy}"
                hm_year = sy
                
            elif tipo_filtro == "Intervalo":
                d1, d2 = df['Data'].min().date(), df['Data'].max().date()
                dr = st.date_input("Período", [d1, d2])
                if len(dr) == 2:
                    df_view = df[(df['Data'].dt.date >= dr[0]) & (df['Data'].dt.date <= dr[1])]
                    label_per = "Personalizado"
            
            elif tipo_filtro == "Ano Completo":
                ys = sorted(df['Data'].dt.year.unique(), reverse=True)
                sy = st.selectbox("Ano", ys)
                df_view = df[df['Data'].dt.year == sy]
                label_per = str(sy)
                hm_year = sy
            
            else:
                label_per = "Histórico Completo"
    
    st.markdown('</div>', unsafe_allow_html=True) # Fim painel controles

    # --- ÁREA DE REGISTRO (INPUT) ---
    with st.form("add_data"):
        c1, c2, c3 = st.columns([2, 2, 1])
        c1.date_input("Data", datetime.today(), key="in_date")
        c2.number_input("Energia Gerada (kWh)", min_value=0.0, step=0.1, key="in_val")
        c3.write("")
        c3.write("")
        if c3.form_submit_button("➕ Adicionar", use_container_width=True):
            if st.session_state.in_val > 0:
                if save_data(st.session_state.in_date, st.session_state.in_val):
                    st.success("Salvo!")
                    time.sleep(0.5)
                    st.rerun()

    # --- DASHBOARD ---
    if df_view.empty:
        st.info("Nenhum dado encontrado para este filtro.")
    else:
        # Cálculos
        tot = df_view['Energia'].sum()
        med = df_view['Energia'].mean()
        # Chama função financeira
        fin = calcular_lei_14300(tot, t_cheia, t_fio, f_simult)
        
        # Cards KPI
        st.markdown(f"### 📊 Resultados: {label_per}")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Economia Líquida", f"R$ {format_br(fin['econ_liq'])}", help="Já descontado o Fio B")
        k2.metric("Geração Total", f"{format_br(tot)} kWh", delta=f"Méd: {format_br(med)}")
        k3.metric("Taxa Paga (Fio B)", f"R$ {format_br(fin['taxa'])}", delta=f"-{fin['perc_taxa']:.0f}%", delta_color="inverse")
        k4.metric("Autoconsumo", f"{format_br(fin['auto_kwh'])} kWh")
        
        st.write("") 

        # TABS
        t1, t2, t3, t4 = st.tabs(["📊 Gráficos", "📈 Acumulado", "💰 Financeiro", "📋 Dados"])
        
        with t1:
            # GRÁFICO DE BARRAS (CORRIGIDO)
            # Removemos configurações manuais de 'size' para que o Altair gerencie
            # a largura automaticamente e as barras sempre apareçam.
            
            base = alt.Chart(df_view).encode(
                x=alt.X('Data:T', title='', axis=alt.Axis(format='%d/%m', labelAngle=-45)),
                tooltip=['Data', alt.Tooltip('Energia', format='.2f')]
            )

            bars = base.mark_bar(
                color='#10b981', 
                cornerRadiusTopLeft=3,
                cornerRadiusTopRight=3
            ).encode(
                y=alt.Y('Energia:Q', title='kWh')
            )
            
            line = base.mark_rule(color='#ef4444', strokeDash=[5,5]).encode(
                y=alt.datum(med)
            )
            
            st.altair_chart((bars + line).interactive(), use_container_width=True)

        with t2:
            df_acc = df_view.sort_values('Data').copy()
            df_acc['Acumulado'] = df_acc['Energia'].cumsum()
            
            area = alt.Chart(df_acc).mark_area(
                line={'color': '#3b82f6'},
                color=alt.Gradient(
                    gradient='linear',
                    stops=[alt.GradientStop(color='#ffffff', offset=0), 
                           alt.GradientStop(color='#3b82f6', offset=1)],
                    x1=1, x2=1, y1=1, y2=0
                )
            ).encode(
                x='Data:T', y='Acumulado:Q', tooltip=['Data', 'Acumulado']
            )
            st.altair_chart(area, use_container_width=True)

        with t3:
            # Financeiro Simplificado
            fator_anual = 365 / max(1, len(df_view))
            econ_proj = fin['econ_liq'] * fator_anual
            payback = invest / econ_proj if econ_proj > 0 else 0
            
            c1, c2 = st.columns(2)
            c1.metric("Payback Estimado", f"{payback:.1f} Anos")
            c2.metric("Projeção Anual", f"R$ {format_br(econ_proj)}")
            
            # Fluxo
            anos = list(range(26))
            fluxo = [-invest]
            acum = -invest
            for i in range(1, 26):
                acum += econ_proj * ((1 - 0.005) ** i)
                fluxo.append(acum)
            
            cf_chart = alt.Chart(pd.DataFrame({'Ano': anos, 'Saldo': fluxo})).mark_line(
                point=True, color='#10b981', strokeWidth=3
            ).encode(
                x='Ano:O', y='Saldo:Q', tooltip=['Ano', alt.Tooltip('Saldo', format=',.2f')]
            )
            zero = alt.Chart(pd.DataFrame({'y':[0]})).mark_rule(color='#9ca3af').encode(y='y')
            st.altair_chart(cf_chart + zero, use_container_width=True)

        with t4:
            # Tabela e Edição
            cd1, cd2 = st.columns([3, 1])
            with cd1:
                st.dataframe(df_view.style.format({"Energia": "{:.2f}"}), use_container_width=True, height=400)
            
            with cd2:
                if st.button("Ativar Edição"): st.session_state.edit_mode = not st.session_state.edit_mode
                if st.session_state.edit_mode:
                    st.info("Selecione ID")
                    sid = st.selectbox("ID", df_view.index)
                    if sid is not None:
                        row = df_view.loc[sid]
                        ndt = st.date_input("Nova Data", row['Data'])
                        nvl = st.number_input("Novo Valor", value=float(row['Energia']))
                        if st.button("Atualizar"):
                            update_data(sid, ndt, nvl)
                            st.rerun()
                        if st.button("Excluir", type="primary"):
                            delete_data(sid)
                            st.rerun()

        # --- HEATMAP GLOBAL ---
        st.markdown("---")
        st.markdown(f"### Mapa de Calor Anual ({hm_year})")
        
        df_heat_src = df[df['Data'].dt.year == hm_year].copy()
        
        if not df_heat_src.empty:
            d1 = datetime(hm_year, 1, 1)
            d2 = datetime(hm_year, 12, 31)
            full_dates = pd.date_range(d1, d2)
            df_full = pd.DataFrame({'Data': full_dates})
            
            df_hm = pd.merge(df_full, df_heat_src, on='Data', how='left').fillna(0)
            df_hm['Semana'] = df_hm['Data'].dt.isocalendar().week
            df_hm['Dia'] = df_hm['Data'].dt.dayofweek
            df_hm['Mes'] = df_hm['Data'].dt.month
            
            df_hm.loc[(df_hm['Mes']==1) & (df_hm['Semana']>50), 'Semana'] = 0
            df_hm.loc[(df_hm['Mes']==12) & (df_hm['Semana']==1), 'Semana'] = 53

            # Limites para cor
            g_max = df['Energia'].max()
            g_min = df[df['Energia'] > 0]['Energia'].min() if not df[df['Energia'] > 0].empty else 0.1
            if pd.isna(g_max): g_max = 20
            if pd.isna(g_min): g_min = 0

            # Labels
            lbls = df_hm.groupby('Mes')['Semana'].min().reset_index()
            lbls['Nome'] = lbls['Mes'].apply(lambda x: datetime(2023, x, 1).strftime('%b'))
            
            c_lbl = alt.Chart(lbls).mark_text(align='left', dy=10, color='#6b7280').encode(
                x=alt.X('Semana:O', axis=None), text='Nome'
            )
            
            # Heatmap com escala global e visual original
            c_hm = alt.Chart(df_hm).mark_rect(
                stroke='#e5e7eb', 
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
                    alt.value('#f9fafb')
                ),
                tooltip=['Data', alt.Tooltip('Energia', format='.2f')]
            ).properties(height=180)
            
            st.altair_chart(alt.vconcat(c_lbl, c_hm), use_container_width=True)
        else:
            st.warning("Sem dados para este ano.")

if __name__ == "__main__":
    main()
