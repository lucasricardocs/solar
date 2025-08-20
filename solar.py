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

# --- Configuração da Página ---
st.set_page_config(
    layout="wide",
    page_title="SolarAnalytics Pro | Dashboard Energia Solar",
    page_icon="⚡",
    initial_sidebar_state="collapsed"
)

# --- CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600;700&display=swap');

:root {
    --primary-color: #1f2937;
    --secondary-color: #3b82f6;
    --accent-color: #10b981;
    --text-primary: #1f2937;
    --text-secondary: #6b7280;
    --bg-light: #f8fafc;
    --border-light: #e2e8f0;
}

/* Aplica a fonte Nunito a todos os elementos */
html, body, [class*="st-"], .stApp, .main {
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

/* Header com gradiente */
.header-section {
    background: linear-gradient(135deg, #e6f3ff, #f0f0f0);
    color: #1f2937;
    padding: 2rem;
    border-radius: 12px;
    border: 1px solid #d3d3d3;
    margin-bottom: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    height: 250px;
}

.header-content {
    display: flex;
    align-items: center;
    gap: 1.5rem;
}

.solar-icon {
    width: 250px;
    height: 250px;
    flex-shrink: 0;
}

.header-text {
    text-align: left;
}

.header-title {
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    background: linear-gradient(135deg, #1f2937, #3b82f6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.header-subtitle {
    font-size: 1.1rem;
    opacity: 0.8;
    font-weight: 400;
    color: #1f2937;
}

/* Padrão para containers de subheaders (MENORES) */
.subheader-container {
    margin: 20px 0;
    padding: 12px 20px; /* Padding reduzido */
    background: #ffffff;
    border-radius: 8px;
    border-left: 5px solid;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    transition: all 0.3s ease;
    animation: shadowPulse 2s infinite alternate;
}

/* Ajuste do tamanho da fonte dos títulos dentro dos containers */
.subheader-container h2 {
    font-size: 1.25rem;
    font-weight: 600;
    margin: 0;
}
.subheader-container h3 {
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0;
}

@keyframes shadowPulse {
    0% { box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05); }
    100% { box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1); }
}

.subheader-container:hover {
    transform: translateX(5px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15) !important;
}

.subheader-container.blue { border-left-color: #3498db; }
.subheader-container.green { border-left-color: #2ecc71; }
.subheader-container.orange { border-left-color: #f39c12; }
.subheader-container.purple { border-left-color: #9b59b6; }
.subheader-container.pink { border-left-color: #e91e63; }
.subheader-container.teal { border-left-color: #1abc9c; }


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

/* Status badges */
.status-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    display: inline-block;
}
.status-connected { background-color: #10B98120; color: #10B981; }
.status-disconnected { background-color: #EF444420; color: #EF4444; }

/* Hide Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

</style>
""", unsafe_allow_html=True)


# --- TEMA DOS GRÁFICOS ---
def configure_altair_theme():
    """Configura um tema global para todos os gráficos Altair."""
    font = "Nunito"
    
    alt.themes.enable('none')
    
    alt.themes.register("custom_theme", lambda: {
        "config": {
            "background": "transparent",
            "view": {"fill": "transparent", "strokeWidth": 0},
            "title": {"font": font, "fontSize": 18, "fontWeight": 700, "anchor": "middle", "color": "#1f2937"},
            "axis": {"labelFont": font, "titleFont": font, "labelFontSize": 11, "titleFontSize": 13, "gridColor": "#e2e8f0", "domain": False, "tickColor": "#6b7280", "labelColor": "#6b7280", "titleColor": "#1f2937", "titleFontWeight": 600, "labelFontWeight": 400},
            "legend": {"labelFont": font, "titleFont": font, "labelFontSize": 11, "titleFontSize": 12, "titleFontWeight": 600, "labelColor": "#6b7280", "titleColor": "#1f2937"}
        }
    })
    alt.themes.enable("custom_theme")

configure_altair_theme()


# --- Inicialização do Session State ---
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False

# --- Header ---
st.markdown("""
<div class="header-section">
    <div class="header-content">
        <img src="https://raw.githubusercontent.com/lucasricardocs/solar/refs/heads/main/solar.png" 
             class="solar-icon" alt="Solar Icon" onerror="this.style.display='none'">
        <div class="header-text">
            <div class="header-title">⚡ SolarAnalytics Pro</div>
            <div class="header-subtitle">Monitoramento Inteligente de Geração de Energia Solar</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Conexão com Google Sheets ---
@st.cache_resource(show_spinner="🔌 Conectando ao Google Sheets...")
def connect_to_gsheets():
    try:
        scopes = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
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
                return None
        except Exception as e:
            st.error(f"❌ **Erro ao verificar cabeçalhos**: {str(e)}")
            return None
        
        return sheet
    except Exception as e:
        st.error(f"🚨 **Erro de Conexão**: {str(e)}")
        return None

sheet = connect_to_gsheets()
if sheet:
    st.sidebar.markdown('<span class="status-badge status-connected">✅ Conectado</span>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('<span class="status-badge status-disconnected">❌ Erro de conexão</span>', unsafe_allow_html=True)
    st.error("⚠️ **Sistema Offline**: Não foi possível conectar ao Google Sheets.")
    st.stop()

# --- Funções de Dados ---
@st.cache_data(ttl=300, show_spinner="📊 Carregando dados...")
def load_data():
    try:
        values = sheet.get_all_values()
        if len(values) < 2: return pd.DataFrame()
        
        df = pd.DataFrame(values[1:], columns=values[0])
        df.columns = [col.lower().strip() for col in df.columns]
        
        if 'data' not in df.columns or 'gerado' not in df.columns:
            st.error("⚠️ **Erro de Configuração**: A planilha deve conter as colunas 'data' e 'gerado'.")
            return pd.DataFrame()
        
        df.rename(columns={'data': 'Data', 'gerado': 'Energia Gerada (kWh)'}, inplace=True)
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        df['Energia Gerada (kWh)'] = pd.to_numeric(df['Energia Gerada (kWh)'].astype(str).str.replace(',', '.', regex=False), errors='coerce')
        df.dropna(subset=['Data', 'Energia Gerada (kWh)'], inplace=True)
        df = df[df['Energia Gerada (kWh)'] >= 0].sort_values(by='Data').drop_duplicates(subset=['Data'], keep='last')
        return df.reset_index(drop=True)
    except Exception as e:
        st.error(f"🚨 **Erro ao carregar dados**: {str(e)}")
        return pd.DataFrame()

def append_data(date, energy):
    try:
        sheet.append_row([date.strftime('%d/%m/%Y'), str(energy).replace('.', ',')], value_input_option='USER_ENTERED')
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"🚨 **Erro ao salvar**: {str(e)}")
        return False

def update_data(row_index, date, energy):
    try:
        sheet.update_cell(row_index + 2, 1, date.strftime('%d/%m/%Y'))
        sheet.update_cell(row_index + 2, 2, str(energy).replace('.', ','))
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"🚨 **Erro ao atualizar**: {str(e)}")
        return False

def delete_data(row_index):
    try:
        sheet.delete_rows(row_index + 2)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"🚨 **Erro ao excluir**: {str(e)}")
        return False

def format_number_br(number, decimals=2):
    return f"{number:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- Formulário de Cadastro ---
st.markdown("""<div class="subheader-container blue"><h2>☀️ Registro de Geração</h2></div>""", unsafe_allow_html=True)
with st.form("entry_form", clear_on_submit=True):
    c1, c2, c3 = st.columns([2, 2, 1])
    input_date = c1.date_input("📅 Data da Geração", value=datetime.today(), format="DD/MM/YYYY")
    input_energy = c2.number_input("⚡ Energia Gerada (kWh)", min_value=0.0, max_value=999.9, step=0.1, format="%.2f")
    c3.write("")
    c3.write("")
    if c3.form_submit_button("💾 Salvar", use_container_width=True):
        if input_energy > 0:
            with st.spinner("💾 Salvando dados..."):
                if append_data(input_date, input_energy):
                    st.success("✅ Dados salvos com sucesso!"); st.balloons(); time.sleep(1); st.rerun()
                else:
                    st.error("❌ Falha ao salvar os dados.")
        else:
            st.warning("💡 Digite um valor maior que zero.")

# --- Análise de Dados ---
df = load_data()
if df.empty:
    st.info("📊 **Nenhum dado encontrado**. Comece registrando sua primeira geração de energia solar!")
else:
    st.markdown("""<div class="subheader-container green"><h2>🔍 Filtros de Análise</h2></div>""", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        years = sorted(df['Data'].dt.year.unique(), reverse=True)
        current_year = datetime.now().year
        year_index = years.index(current_year) if current_year in years else 0
        selected_year = st.selectbox("📅 Ano", options=years, index=year_index)
        
    with col2:
        month_names = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
        months_in_year = sorted(df[df['Data'].dt.year == selected_year]['Data'].dt.month.unique())
        
        # --- ATUALIZAÇÃO: Adiciona a opção "Ano Inteiro" ---
        month_options = [0] + months_in_year
        
        def format_month(x):
            return "Ano Inteiro" if x == 0 else month_names.get(x, '')

        selected_month_num = None
        if months_in_year:
            current_month = datetime.now().month
            if current_month in month_options:
                default_index = month_options.index(current_month)
            else:
                default_index = len(month_options) - 1 if len(month_options) > 1 else 0

            selected_month_num = st.selectbox("📊 Mês", options=month_options, format_func=format_month, index=default_index)
        else:
            st.info("Nenhum dado disponível para este ano")
            
    with col3:
        total_year = df[df['Data'].dt.year == selected_year]['Energia Gerada (kWh)'].sum()
        st.metric(f"📈 Total em {selected_year}", f"{format_number_br(total_year)} kWh")
    
    # --- ATUALIZAÇÃO: Define o dataframe e o título com base na seleção (Mês ou Ano) ---
    if selected_month_num is not None:
        if selected_month_num == 0: # Opção "Ano Inteiro"
            filtered_df = df[df['Data'].dt.year == selected_year].copy()
            periodo_selecionado = f"o Ano de {selected_year}"
        else: # Opção de Mês específico
            filtered_df = df[(df['Data'].dt.year == selected_year) & (df['Data'].dt.month == selected_month_num)].copy()
            periodo_selecionado = f"{month_names.get(selected_month_num, '')} de {selected_year}"

        if not filtered_df.empty:
            total = filtered_df['Energia Gerada (kWh)'].sum()
            avg = filtered_df['Energia Gerada (kWh)'].mean()
            best = filtered_df.loc[filtered_df['Energia Gerada (kWh)'].idxmax()]
            worst = filtered_df.loc[filtered_df['Energia Gerada (kWh)'].idxmin()]
            
            st.markdown(f"""<div class="subheader-container orange"><h2>📊 Análise de {periodo_selecionado}</h2></div>""", unsafe_allow_html=True)
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("🔋 Total no Período", f"{format_number_br(total)} kWh")
            c2.metric("📈 Média Diária", f"{format_number_br(avg)} kWh")
            c3.metric("⭐ Melhor Dia", f"{format_number_br(best['Energia Gerada (kWh)'])} kWh", delta=best['Data'].strftime('%d/%m'))
            c4.metric("⚠️ Menor Dia", f"{format_number_br(worst['Energia Gerada (kWh)'])} kWh", delta=worst['Data'].strftime('%d/%m'), delta_color="inverse")
            
            tab1, tab2, tab3 = st.tabs(["📊 Produção no Período", "📈 Geração Acumulada", "📋 Dados Detalhados"])
            
            with tab1:
                # --- ATUALIZAÇÃO: Gráfico dinâmico (Diário para Mês, Mensal para Ano) ---
                if selected_month_num == 0:
                    # Se "Ano Inteiro", mostra gráfico MENSAL
                    monthly_summary = filtered_df.groupby(filtered_df['Data'].dt.month)['Energia Gerada (kWh)'].sum().reset_index()
                    monthly_summary['Nome Mês'] = monthly_summary['Data'].apply(lambda m: month_names[m][:3])
                    
                    chart = alt.Chart(monthly_summary).mark_bar(color="#3b82f6", size=30, cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                        x=alt.X('Nome Mês:N', title='Mês', sort=[m[:3] for m in month_names.values()]),
                        y=alt.Y('Energia Gerada (kWh):Q', title='Total Gerado (kWh)'),
                        tooltip=[alt.Tooltip('Nome Mês:N', title='Mês'), alt.Tooltip('Energia Gerada (kWh):Q', title='Total', format='.2f')]
                    ).properties(height=400, title=f"Geração Mensal - {selected_year}")
                else:
                    # Se Mês específico, mostra gráfico DIÁRIO
                    chart = alt.Chart(filtered_df).mark_bar(color="#3b82f6", size=25, cornerRadiusTopLeft=4, cornerRadiusTopRight=4, stroke="#dcdcdc", strokeWidth=2).encode(
                        x=alt.X('Data:T', title='Data', axis=alt.Axis(format='%d/%m', labelAngle=-45, tickCount='day'), scale=alt.Scale(nice=False)),
                        y=alt.Y('Energia Gerada (kWh):Q', title='Energia Gerada (kWh)'),
                        tooltip=[alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'), alt.Tooltip('Energia Gerada (kWh):Q', title='Energia', format='.2f')]
                    )
                    media_diaria = filtered_df['Energia Gerada (kWh)'].mean()
                    linha_media = alt.Chart(pd.DataFrame({'media': [media_diaria]})).mark_rule(color='red', strokeWidth=2).encode(y='media:Q', tooltip=alt.value(f'Média: {format_number_br(media_diaria)} kWh'))
                    chart = (chart + linha_media).properties(height=400, title=f"Geração Diária - {periodo_selecionado}")

                st.altair_chart(chart, use_container_width=True)
                st.divider()
            
            with tab2:
                # Este gráfico funciona bem tanto para mês quanto para ano
                df_sorted = filtered_df.sort_values('Data').copy()
                df_sorted['Acumulado'] = df_sorted['Energia Gerada (kWh)'].cumsum()
                
                area_chart = alt.Chart(df_sorted).mark_area(line={'color':'#10b981', 'strokeWidth': 3}, color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color='#10b981', offset=0), alt.GradientStop(color='rgba(16, 185, 129, 0)', offset=1)], x1=1, x2=1, y1=1, y2=0), interpolate='monotone').encode(
                    x=alt.X('Data:T', title='Data'),
                    y=alt.Y('Acumulado:Q', title='Energia Acumulada (kWh)'),
                    tooltip=[alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'), alt.Tooltip('Energia Gerada (kWh):Q', title='Geração', format='.2f'), alt.Tooltip('Acumulado:Q', title='Acumulado', format='.2f')]
                ).properties(height=400, title=f"Geração Acumulada - {periodo_selecionado}")
                
                st.altair_chart(area_chart, use_container_width=True)
                st.divider()
            
            with tab3:
                # A tabela também funciona bem para mês ou ano
                display_df = filtered_df.copy()
                display_df['Data'] = display_df['Data'].dt.strftime('%d/%m/%Y')
                display_df['Energia Gerada (kWh)'] = display_df['Energia Gerada (kWh)'].apply(lambda x: format_number_br(x))
                st.dataframe(display_df, use_container_width=True, hide_index=True)

                if st.button("✏️ Editar Registros", use_container_width=True):
                    st.session_state.edit_mode = not st.session_state.edit_mode
                
                if st.session_state.edit_mode:
                    st.divider()
                    st.subheader("✏️ Editar Registros")
                    selected_idx = st.selectbox("Selecione o registro", options=range(len(filtered_df)), format_func=lambda x: f"{filtered_df.iloc[x]['Data'].strftime('%d/%m/%Y')} - {format_number_br(filtered_df.iloc[x]['Energia Gerada (kWh)'])} kWh")
                    
                    c1, c2, c3 = st.columns(3)
                    edit_date = c1.date_input("📅 Data", value=filtered_df.iloc[selected_idx]['Data'], format="DD/MM/YYYY")
                    edit_energy = c2.number_input("⚡ Energia (kWh)", value=float(filtered_df.iloc[selected_idx]['Energia Gerada (kWh)']), min_value=0.0, step=0.1, format="%.2f")
                    
                    c3.write("")
                    sc1, sc2 = c3.columns(2)
                    if sc1.button("💾 Salvar", use_container_width=True):
                        if update_data(filtered_df.index[selected_idx], edit_date, edit_energy):
                            st.success("✅ Atualizado!"); st.session_state.edit_mode = False; time.sleep(1); st.rerun()
                    if sc2.button("🗑️ Excluir", use_container_width=True):
                        if delete_data(filtered_df.index[selected_idx]):
                            st.success("✅ Excluído!"); st.session_state.edit_mode = False; time.sleep(1); st.rerun()
        
        year_df = df[df['Data'].dt.year == selected_year].copy()
        
        if not year_df.empty and selected_month_num != 0:
            st.markdown(f"""<div class="subheader-container purple"><h2>📅 Resumo Anual de {selected_year}</h2></div>""", unsafe_allow_html=True)
            
            monthly_summary = year_df.groupby(year_df['Data'].dt.month)['Energia Gerada (kWh)'].sum().reset_index()
            monthly_summary['Nome Mês'] = monthly_summary['Data'].apply(lambda m: month_names[m][:3])
            
            monthly_bars = alt.Chart(monthly_summary).mark_bar(color="#f59e0b", cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                x=alt.X('Nome Mês:N', title='Mês', sort=[m[:3] for m in month_names.values()]),
                y=alt.Y('Energia Gerada (kWh):Q', title='Total Mensal (kWh)'),
                tooltip=[alt.Tooltip('Nome Mês:N', title='Mês'), alt.Tooltip('Energia Gerada (kWh):Q', title='Total', format='.2f')]
            )
            media_mensal = monthly_summary['Energia Gerada (kWh)'].mean()
            linha_media_mensal = alt.Chart(pd.DataFrame({'media': [media_mensal]})).mark_rule(color='red', strokeWidth=2, strokeDash=[5, 5]).encode(y='media:Q', tooltip=alt.value(f'Média Mensal: {format_number_br(media_mensal)} kWh'))
            
            monthly_chart = (monthly_bars + linha_media_mensal).properties(height=400, title=f"Geração Mensal - {selected_year}")
            
            st.altair_chart(monthly_chart, use_container_width=True)
            st.divider()

# --- Footer ---
st.divider()
st.markdown(f"""
<div style="text-align: center; color: var(--text-secondary); padding: 1rem; font-size: 0.9rem;">
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

if st.session_state.edit_mode:
    if st.sidebar.button("❌ Sair do Modo Edição"):
        st.session_state.edit_mode = False
        st.rerun()
