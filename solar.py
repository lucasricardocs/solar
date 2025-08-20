# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
import warnings
import altair as alt
import locale

# Ignora avisos futuros do pandas
warnings.filterwarnings('ignore', category=FutureWarning, message='.*observed=False.*')

# Tenta configurar a localidade para português, útil para formatação de data/hora
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    pass

# --- Constantes de Configuração ---
SPREADSHEET_ID = '1WI2tZ94lVV9GfaaWerdSfuChFLzWfMbU4v2m6QrwTdY'
WORKSHEET_NAME = 'Solardaily' # Nome da sua aba na planilha

# --- Configuração da Página ---
st.set_page_config(
    layout="wide",
    page_title="Dashboard de Geração de Energia Solar",
    page_icon="☀️"
)

# --- Estilo CSS Customizado (Tema Claro com Fonte Livvic) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Livvic:wght@300;400;600;700&display=swap');
html, body, [class*="st-"] {
    font-family: 'Livvic', sans-serif;
}
.stApp {
    background-color: #F0F2F6; /* Fundo claro */
    color: #333333; /* Texto escuro */
}
[data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
    border: 1px solid #E0E0E0;
    border-radius: 10px;
    padding: 20px;
    background-color: #FFFFFF; /* Containers brancos */
}
.stButton>button {
    border-radius: 8px;
    border: 1px solid #007BFF;
    background-color: #007BFF;
    color: white;
}
.stButton>button:hover {
    border: 1px solid #0056b3;
    background-color: #0056b3;
}
[data-testid="stSidebar"] {
    display: none; /* Oculta a sidebar que pode aparecer por padrão */
}
h1, h2, h3 {
    color: #007BFF; /* Azul como cor de destaque */
}
</style>
""", unsafe_allow_html=True)

# --- Conexão com Google Sheets ---
@st.cache_resource
def connect_to_gsheets():
    """Conecta ao Google Sheets usando as credenciais do Streamlit Secrets."""
    scopes = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    try:
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.worksheet(WORKSHEET_NAME)
        return sheet
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("Planilha não encontrada. Verifique o SPREADSHEET_ID.")
        st.stop()
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"Aba '{WORKSHEET_NAME}' não encontrada. Verifique o WORKSHEET_NAME.")
        st.stop()

sheet = connect_to_gsheets()

# --- Funções de Dados ---
@st.cache_data(ttl=600)
def load_data():
    """Carrega os dados da planilha, processa e retorna um DataFrame."""
    data = sheet.get_all_records()
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    df.columns = [col.lower() for col in df.columns]

    if 'data' not in df.columns or 'gerado' not in df.columns:
        st.error("Erro: A planilha deve conter as colunas 'data' e 'gerado'. Verifique os nomes das colunas.")
        return pd.DataFrame()

    df.rename(columns={'data': 'Data', 'gerado': 'Energia Gerada (kWh)'}, inplace=True)
    
    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
    
    # --- CORREÇÃO APLICADA AQUI ---
    # Garante que a coluna de energia seja tratada como texto, substitui a vírgula
    # por ponto e então converte para número. Isso resolve o problema de leitura.
    if 'Energia Gerada (kWh)' in df.columns:
        df['Energia Gerada (kWh)'] = df['Energia Gerada (kWh)'].astype(str).str.replace(',', '.', regex=False)
        df['Energia Gerada (kWh)'] = pd.to_numeric(df['Energia Gerada (kWh)'], errors='coerce')

    df.dropna(subset=['Data', 'Energia Gerada (kWh)'], inplace=True)
    df = df.sort_values(by='Data')
    return df

def append_data(date, energy):
    """Adiciona uma nova linha de dados na planilha."""
    try:
        formatted_date = date.strftime('%d/%m/%Y')
        # Salva o valor numérico. O Google Sheets formatará com vírgula se a localidade for Brasil.
        sheet.append_row([formatted_date, energy])
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar os dados: {e}")
        return False

# --- Página Principal ---
st.title("Dashboard de Geração de Energia Solar")
st.markdown("Acompanhe a performance da sua geração de energia de forma visual e interativa.")

# --- Formulário de Cadastro (em um expander) ---
with st.expander("☀️ Cadastrar Nova Geração", expanded=True):
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            input_date = st.date_input("Data da Geração (dd/mm/aaaa)", value=datetime.today(), format="DD/MM/YYYY")
        with col2:
            input_energy_str = st.text_input("Energia Gerada (kWh)", placeholder="Ex: 20,13")

        submitted = st.form_submit_button("Salvar Geração")

        if submitted:
            if input_energy_str:
                try:
                    energy_value = float(input_energy_str.replace(',', '.'))
                    if energy_value > 0:
                        if append_data(input_date, energy_value):
                            st.success("Dados salvos com sucesso!")
                        else:
                            st.error("Falha ao salvar os dados.")
                    else:
                        st.warning("A energia gerada deve ser maior que zero.")
                except ValueError:
                    st.error("Valor de energia inválido. Por favor, insira um número (ex: 20 ou 20,13).")
            else:
                st.warning("Por favor, preencha o valor da energia gerada.")

# --- Análise de Dados ---
df = load_data()

if df.empty:
    st.warning("Nenhum dado encontrado. Comece cadastrando uma nova geração.")
else:
    st.divider()
    
    # --- Filtros ---
    st.header("🔍 Filtros e Análise")
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        years = sorted(df['Data'].dt.year.unique(), reverse=True)
        selected_year = st.selectbox("Selecione o Ano", options=years)
    with filter_col2:
        months = sorted(df[df['Data'].dt.year == selected_year]['Data'].dt.month.unique())
        month_names = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
        selected_month_num = st.selectbox("Selecione o Mês", options=months, format_func=lambda x: month_names.get(x, ''))

    filtered_df = df[(df['Data'].dt.year == selected_year) & (df['Data'].dt.month == selected_month_num)]
    
    # --- Insights e Gráficos ---
    st.header(f"Análise de {month_names.get(selected_month_num, '')} de {selected_year}")

    if not filtered_df.empty:
        # --- Métricas (Insights) ---
        total = filtered_df['Energia Gerada (kWh)'].sum()
        avg = filtered_df['Energia Gerada (kWh)'].mean()
        best = filtered_df.loc[filtered_df['Energia Gerada (kWh)'].idxmax()]
        worst = filtered_df.loc[filtered_df['Energia Gerada (kWh)'].idxmin()]
        
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        metric_col1.metric("Total no Mês", f"{total:,.2f} kWh".replace(",", "X").replace(".", ",").replace("X", "."))
        metric_col2.metric("Média Diária", f"{avg:,.2f} kWh".replace(",", "X").replace(".", ",").replace("X", "."))
        metric_col3.metric("Melhor Dia", f"{best['Energia Gerada (kWh)']:,.2f} kWh".replace(",", "X").replace(".", ",").replace("X", "."), delta=best['Data'].strftime('%d/%m'))
        metric_col4.metric("Pior Dia", f"{worst['Energia Gerada (kWh)']:,.2f} kWh".replace(",", "X").replace(".", ",").replace("X", "."), delta=worst['Data'].strftime('%d/%m'), delta_color="inverse")

        st.write("") # Espaçamento

        # --- Gráficos ---
        col1, col2 = st.columns(2)
        with col1:
            bar_chart = alt.Chart(filtered_df).mark_bar(
                cornerRadiusTopLeft=5, cornerRadiusTopRight=5, color="#007BFF"
            ).encode(
                x=alt.X('Data:T', title='Dia', axis=alt.Axis(format='%d', grid=False, labelAngle=0)),
                y=alt.Y('Energia Gerada (kWh):Q', title='Energia (kWh)', axis=alt.Axis(grid=False)),
                tooltip=[alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'), alt.Tooltip('Energia Gerada (kWh):Q', title='Gerado', format=',.2f')]
            ).properties(title="Produção Diária").configure_view(stroke=None).configure_axis(
                labelColor='#333', titleColor='#333'
            ).configure_title(color='#333').interactive()
            st.altair_chart(bar_chart, use_container_width=True)

        with col2:
            filtered_df['Acumulado'] = filtered_df['Energia Gerada (kWh)'].cumsum()
            area_chart = alt.Chart(filtered_df).mark_area(
                line={'color':'#007BFF'},
                color=alt.Gradient(
                    gradient='linear',
                    stops=[alt.GradientStop(color='#007BFF', offset=0), alt.GradientStop(color='rgba(0,123,255,0)', offset=1)],
                    x1=1, x2=1, y1=1, y2=0
                )
            ).encode(
                x=alt.X('Data:T', title='Dia', axis=alt.Axis(format='%d', grid=False, labelAngle=0)),
                y=alt.Y('Acumulado:Q', title='Energia Acumulada (kWh)', axis=alt.Axis(grid=False)),
                tooltip=[alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'), alt.Tooltip('Acumulado:Q', title='Acumulado', format=',.2f')]
            ).properties(title="Geração Mensal Acumulada").configure_view(stroke=None).configure_axis(
                labelColor='#333', titleColor='#333'
            ).configure_title(color='#333').interactive()
            st.altair_chart(area_chart, use_container_width=True)

        st.divider()
        st.header(f"Mapa de Calor da Geração de {selected_year}")
        year_df = df[df['Data'].dt.year == selected_year].copy()
        year_df['day_of_week'] = year_df['Data'].dt.day_name()
        year_df['week_of_year'] = year_df['Data'].dt.isocalendar().week

        heatmap = alt.Chart(year_df).mark_rect().encode(
            x=alt.X('week_of_year:O', title='Semana do Ano', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('day_of_week:O', title='Dia da Semana', sort=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']),
            color=alt.Color('Energia Gerada (kWh):Q', legend=alt.Legend(title="Energia (kWh)"), scale=alt.Scale(scheme='blues')),
            tooltip=[alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'), alt.Tooltip('Energia Gerada (kWh):Q', title='Gerado', format=',.2f')]
        ).properties(title=f"Geração Diária em {selected_year}").configure_view(stroke=None).configure_axis(
            labelColor='#333', titleColor='#333'
        ).configure_title(color='#333').configure_legend(labelColor='#333', titleColor='#333')
        st.altair_chart(heatmap, use_container_width=True)
    else:
        st.info("Nenhum dado para exibir para o período selecionado.")
