# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import streamlit as st
import gspread
import time
from datetime import datetime
from google.oauth2.service_account import Credentials
import warnings
import altair as alt
import locale
import matplotlib.pyplot as plt

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
    
    # Desativa o tema padrão para começar do zero
    alt.themes.enable('none')
    
    # Registra e ativa o tema customizado
    alt.themes.register("custom_theme", lambda: {
        "config": {
            "background": "transparent",
            "view": {
                "fill": "transparent",
                "strokeWidth": 0
            },
            "title": {
                "font": font,
                "fontSize": 18,
                "fontWeight": 700,
                "anchor": "middle",
                "color": "#1f2937"
            },
            "axis": {
                "labelFont": font,
                "titleFont": font,
                "labelFontSize": 11,
                "titleFontSize": 13,
                "gridColor": "#e2e8f0",
                "domain": False,
                "tickColor": "#6b7280",
                "labelColor": "#6b7280",
                "titleColor": "#1f2937",
                "titleFontWeight": 600,
                "labelFontWeight": 400
            },
            "legend": {
                "labelFont": font,
                "titleFont": font,
                "labelFontSize": 11,
                "titleFontSize": 12,
                "titleFontWeight": 600,
                "labelColor": "#6b7280",
                "titleColor": "#1f2937"
            }
        }
    })
    alt.themes.enable("custom_theme")

# Aplica o tema aos gráficos
configure_altair_theme()


# --- Inicialização do Session State ---
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False

# --- Header ---
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

# --- Funções de Dados ---
@st.cache_data(ttl=300, show_spinner="📊 Carregando dados...")
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

# --- Formulário de Cadastro ---
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

# --- Análise de Dados ---
df = load_data()
if df.empty:
    st.info("📊 **Nenhum dado encontrado**. Comece registrando sua primeira geração de energia solar!")
else:
    # --- Filtros ---
    st.markdown("""
    <div class="subheader-container green">
        <h2>🔍 Filtros de Análise</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        years = sorted(df['Data'].dt.year.unique(), reverse=True)
        current_year = datetime.now().year
        year_index = 0
        if current_year in years:
            year_index = years.index(current_year)
            
        selected_year = st.selectbox("📅 Ano", options=years, index=year_index)
        
    with col2:
        months = sorted(df[df['Data'].dt.year == selected_year]['Data'].dt.month.unique())
        month_names = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        
        period_options = ["Ano Inteiro"] + months
        
        default_index = 0
        current_month = datetime.now().month
        if selected_year == datetime.now().year and current_month in period_options:
            default_index = period_options.index(current_month)

        selected_period = st.selectbox(
            "📊 Período", 
            options=period_options, 
            format_func=lambda x: "Ano Inteiro" if isinstance(x, str) else month_names.get(x, ''),
            index=default_index
        )
        
    with col3:
        total_year = df[df['Data'].dt.year == selected_year]['Energia Gerada (kWh)'].sum()
        st.metric(f"📈 Total Gerado em {selected_year}", f"{format_number_br(total_year)} kWh")
    
    # --- LÓGICA DE EXIBIÇÃO ---

    # CASO 1: USUÁRIO SELECIONOU "ANO INTEIRO"
    if selected_period == "Ano Inteiro":
        year_df = df[df['Data'].dt.year == selected_year].copy()
        
        if not year_df.empty:
            st.markdown(f"""
            <div class="subheader-container purple">
                <h2>📅 Resumo Anual de {selected_year}</h2>
            </div>
            """, unsafe_allow_html=True)
            
            # Gráfico de barras mensal
            monthly_summary = year_df.groupby(
                year_df['Data'].dt.month
            )['Energia Gerada (kWh)'].sum().reset_index()
            monthly_summary.rename(columns={'Data': 'Mês'}, inplace=True)
            monthly_summary['Nome Mês'] = monthly_summary['Mês'].apply(lambda m: month_names[m][:3])
            
            monthly_bars = alt.Chart(monthly_summary).mark_bar(
                color="#f59e0b",
                cornerRadiusTopLeft=4,
                cornerRadiusTopRight=4,
            ).encode(
                x=alt.X('Nome Mês:N', title='Mês', sort=[m[:3] for m in month_names.values()]),
                y=alt.Y('Energia Gerada (kWh):Q', title='Total Mensal (kWh)'),
                tooltip=[alt.Tooltip('Nome Mês:N', title='Mês'), alt.Tooltip('Energia Gerada (kWh):Q', title='Total', format='.2f')]
            )
            media_mensal = monthly_summary['Energia Gerada (kWh)'].mean()
            linha_media_mensal = alt.Chart(pd.DataFrame({'media': [media_mensal]})).mark_rule(
                color='red', strokeWidth=2, strokeDash=[5, 5]
            ).encode(y=alt.Y('media:Q'), tooltip=alt.value(f'Média Mensal: {format_number_br(media_mensal)} kWh'))
            
            monthly_chart = (monthly_bars + linha_media_mensal).properties(height=400, title=f"Geração Mensal - {selected_year}")
            st.altair_chart(monthly_chart, use_container_width=True)
            st.divider()
            
            # Heatmap Anual com Matplotlib
            st.markdown("""<div class="subheader-container teal"><h3>🗓️ Heatmap de Geração Anual</h3></div>""", unsafe_allow_html=True)

            year = selected_year
            start_date = pd.to_datetime(f'{year}-01-01')
            end_date = pd.to_datetime(f'{year}-12-31')
            all_days = pd.date_range(start=start_date, end=end_date, freq='D')
            heatmap_df = pd.DataFrame(index=all_days)
            heatmap_df = heatmap_df.join(year_df.set_index('Data')[['Energia Gerada (kWh)']], how='left').fillna(0)
            
            data = heatmap_df['Energia Gerada (kWh)'].values
            dates = heatmap_df.index

            cmap = plt.cm.get_cmap('YlGn')
            vmin = data.min()
            vmax = data.max()

            fig, ax = plt.subplots(figsize=(12, 2.5))
            fig.patch.set_facecolor('#f8fafc')  # Cor de fundo igual ao do app
            ax.set_facecolor('#f8fafc')

            # Calcula a posição de cada dia (semana no eixo X, dia da semana no eixo Y)
            day_of_week = dates.weekday
            week_of_year = dates.isocalendar().week
            
            # Desenha um retângulo para cada dia
            for i, day in enumerate(dates):
                # O isocalendar() pode ter a semana 53 no início do ano, ajustamos para a semana 0
                week_num = week_of_year[i]
                if day.month == 1 and week_num >= 52:
                    week_num = 0
                
                # O isocalendar() pode ter a semana 1 no final do ano, ajustamos para a semana 53
                if day.month == 12 and week_num == 1:
                    week_num = 53

                # Normaliza a cor baseado no valor
                color_value = (data[i] - vmin) / (vmax - vmin) if vmax > vmin else 0
                rect = plt.Rectangle((week_num, day_of_week[i]), 1, 1, 
                                     facecolor=cmap(color_value), 
                                     edgecolor='white', linewidth=0.5)
                ax.add_patch(rect)
                
                # Adiciona texto para valores altos
                if data[i] > vmax * 0.7:  # Apenas em dias de alta geração para não poluir
                    ax.text(week_num + 0.5, day_of_week[i] + 0.5, f'{data[i]:.0f}', 
                            ha='center', va='center', fontsize=6, color='black')

            # Labels dos meses
            month_labels = [d.strftime('%b') for d in pd.date_range(start_date, end_date, freq='MS')]
            month_weeks = [d.isocalendar().week for d in pd.date_range(start_date, end_date, freq='MS')]
            
            ax.set_xticks(month_weeks)
            ax.set_xticklabels(month_labels)
            ax.xaxis.tick_top()
            ax.xaxis.set_label_position('top')

            # Labels dos dias da semana
            ax.set_yticks(np.arange(7) + 0.5)
            ax.set_yticklabels(['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'], fontsize=9)
            ax.invert_yaxis() # Inverte o eixo Y para ter Segunda no topo

            # Ajustes finais
            ax.set_title(f'Atividade de Geração Solar em {year}', fontsize=16, fontweight='bold', color='#1f2937', pad=40)
            ax.tick_params(axis='both', which='both', bottom=False, top=False, left=False, labelbottom=False)
            
            st.pyplot(fig, use_container_width=True)
            st.divider()
            
            # Estatísticas do Ano
            st.markdown("""<div class="subheader-container pink"><h3>📈 Estatísticas do Ano</h3></div>""", unsafe_allow_html=True)
            year_total = year_df['Energia Gerada (kWh)'].sum()
            year_avg = year_df['Energia Gerada (kWh)'].mean()
            year_max = year_df['Energia Gerada (kWh)'].max()
            year_min = year_df['Energia Gerada (kWh)'].min()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("🏆 Total do Ano", f"{format_number_br(year_total)} kWh")
            with col2: st.metric("📊 Média Diária", f"{format_number_br(year_avg)} kWh")
            with col3: st.metric("⚡ Pico Máximo", f"{format_number_br(year_max)} kWh")
            with col4: st.metric("📉 Mínimo", f"{format_number_br(year_min)} kWh")

    # CASO 2: USUÁRIO SELECIONOU UM MÊS ESPECÍFICO
    elif isinstance(selected_period, int):
        filtered_df = df[
            (df['Data'].dt.year == selected_year) & 
            (df['Data'].dt.month == selected_period)
        ].copy()
        
        if not filtered_df.empty:
            st.markdown(f"""
            <div class="subheader-container orange">
                <h2>📊 Análise de {month_names.get(selected_period, '')} de {selected_year}</h2>
            </div>
            """, unsafe_allow_html=True)
            
            total = filtered_df['Energia Gerada (kWh)'].sum()
            avg = filtered_df['Energia Gerada (kWh)'].mean()
            best = filtered_df.loc[filtered_df['Energia Gerada (kWh)'].idxmax()]
            worst = filtered_df.loc[filtered_df['Energia Gerada (kWh)'].idxmin()]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("🔋 Total no Mês", f"{format_number_br(total)} kWh")
            with col2: st.metric("📈 Média Diária", f"{format_number_br(avg)} kWh")
            with col3: st.metric("⭐ Melhor Dia", f"{format_number_br(best['Energia Gerada (kWh)'])} kWh", delta=best['Data'].strftime('%d/%m'))
            with col4: st.metric("⚠️ Menor Dia", f"{format_number_br(worst['Energia Gerada (kWh)'])} kWh", delta=worst['Data'].strftime('%d/%m'), delta_color="inverse")
            
            tab1, tab2, tab3 = st.tabs(["📊 Produção Diária", "📈 Geração Acumulada", "📋 Dados"])
            
            with tab1:
                bar_chart = alt.Chart(filtered_df).mark_bar(
                    color="#3b82f6", cornerRadiusTopLeft=4, cornerRadiusTopRight=4,
                    stroke="#dcdcdc", strokeWidth=2, size=25
                ).encode(
                    x=alt.X('Data:T', title='Data', axis=alt.Axis(format='%d/%m', labelAngle=-45, tickCount='day'), scale=alt.Scale(nice=False)),
                    y=alt.Y('Energia Gerada (kWh):Q', title='Energia Gerada (kWh)'),
                    tooltip=[alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'), alt.Tooltip('Energia Gerada (kWh):Q', title='Energia', format='.2f')]
                )
                media_diaria = filtered_df['Energia Gerada (kWh)'].mean()
                linha_media = alt.Chart(pd.DataFrame({'media': [media_diaria]})).mark_rule(
                    color='red', strokeWidth=2,
                ).encode(y=alt.Y('media:Q'), tooltip=alt.value(f'Média: {format_number_br(media_diaria)} kWh'))
                final_chart = (bar_chart + linha_media).properties(height=400, title=f"Geração Diária - {month_names.get(selected_period, '')} {selected_year}")
                st.altair_chart(final_chart, use_container_width=True)
            
            with tab2:
                filtered_df_sorted = filtered_df.sort_values('Data').copy()
                filtered_df_sorted['Acumulado'] = filtered_df_sorted['Energia Gerada (kWh)'].cumsum()
                area_chart = alt.Chart(filtered_df_sorted).mark_area(
                    line={'color':'#10b981', 'strokeWidth': 3}, 
                    color=alt.Gradient(
                        gradient='linear', 
                        stops=[alt.GradientStop(color='#10b981', offset=0), alt.GradientStop(color='rgba(16, 185, 129, 0)', offset=1)],
                        x1=1, x2=1, y1=1, y2=0
                    ),
                    interpolate='monotone'
                ).encode(
                    x=alt.X('Data:T', title='Data'),
                    y=alt.Y('Acumulado:Q', title='Energia Acumulada (kWh)'),
                    tooltip=[alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'), alt.Tooltip('Energia Gerada (kWh):Q', title='Geração', format='.2f'), alt.Tooltip('Acumulado:Q', title='Acumulado', format='.2f')]
                ).properties(height=400, title=f"Geração Acumulada - {month_names.get(selected_period, '')} {selected_year}")
                st.altair_chart(area_chart, use_container_width=True)
            
            with tab3:
                display_df = filtered_df.copy()
                display_df['Data_str'] = display_df['Data'].dt.strftime('%d/%m/%Y')
                display_df['Energia_str'] = display_df['Energia Gerada (kWh)'].apply(lambda x: format_number_br(x))
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.dataframe(display_df[['Data_str', 'Energia_str']].rename(columns={'Data_str': 'Data', 'Energia_str': 'Energia Gerada (kWh)'}), use_container_width=True, hide_index=True)
                with col2:
                    if st.button("✏️ Editar Registros", use_container_width=True):
                        st.session_state.edit_mode = not st.session_state.edit_mode
                if st.session_state.edit_mode:
                    st.divider()
                    st.subheader("✏️ Editar Registros")
                    if len(filtered_df) > 0:
                        selected_index = st.selectbox(
                            "Selecione o registro", options=range(len(filtered_df)),
                            format_func=lambda x: f"{filtered_df.iloc[x]['Data'].strftime('%d/%m/%Y')} - {format_number_br(filtered_df.iloc[x]['Energia Gerada (kWh)'])} kWh"
                        )
                        col1, col2, col3 = st.columns(3)
                        with col1: edit_date = st.date_input("📅 Data", value=filtered_df.iloc[selected_index]['Data'], format="DD/MM/YYYY")
                        with col2: edit_energy = st.number_input("⚡ Energia (kWh)", value=float(filtered_df.iloc[selected_index]['Energia Gerada (kWh)']), min_value=0.0, step=0.1, format="%.2f")
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
