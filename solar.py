import streamlit as st
import pandas as pd
import altair as alt
from google.oauth2.service_account import Credentials
import gspread
import calendar
import locale
import warnings

# --- CONFIGURAÇÕES GLOBAIS ---

# Ignora avisos futuros do pandas para um output mais limpo
warnings.filterwarnings('ignore', category=FutureWarning, message='.*observed=False.*')

# Tenta configurar a localidade para português do Brasil (para nomes de meses, etc.)
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    st.warning("Localidade 'pt_BR.UTF-8' não encontrada. Os nomes dos meses podem aparecer em inglês.")

# --- Constantes de Configuração do Google Sheets ---
SPREADSHEET_ID = '1WI2tZ94lVV9GfaaWerdSfuChFLzWfMbU4v2m6QrwTdY'
WORKSHEET_NAME = 'Solardaily'

# --- CONEXÃO COM GOOGLE SHEETS ---
@st.cache_data(ttl=600)
def load_data():
    """Carrega dados da planilha do Google Sheets e faz o pré-processamento."""
    try:
        # A autenticação continua via st.secrets para segurança
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict)
        gc = gspread.authorize(creds)
        
        # Usa as constantes que você forneceu para abrir a planilha
        worksheet = gc.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)

        # --- PROCESSAMENTO INICIAL DOS DADOS ---
        # ATENÇÃO AQUI: Verifique se os nomes das colunas ('PRODUÇÃO TOTAL', 'DATA', etc.)
        # correspondem exatamente aos nomes na sua aba 'Solardaily'.
        numeric_cols = ['PRODUÇÃO TOTAL'] # Adicione outras colunas numéricas se houver
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
        df.dropna(subset=['DATA'] + numeric_cols, inplace=True)

        df['ANO'] = df['DATA'].dt.year
        df['MES'] = df['DATA'].dt.month
        df['DIA'] = df['DATA'].dt.day
        return df
    except Exception as e:
        st.error(f"Erro ao conectar com o Google Sheets: {e}")
        return pd.DataFrame()

# --- CARREGAMENTO DOS DADOS ---
df = load_data()

if df.empty:
    st.warning("Não foi possível carregar os dados. Verifique a planilha ou as credenciais.")
    st.stop()

# --- BARRA LATERAL COM FILTROS ---
st.sidebar.header("Filtros")
anos_disponiveis = sorted(df['ANO'].unique(), reverse=True)
ano_selecionado = st.sidebar.selectbox("Selecione o Ano", anos_disponiveis)

# Graças ao 'locale', os nomes dos meses agora devem aparecer em português
nomes_meses = {i: calendar.month_name[i].capitalize() for i in range(1, 13)}
meses_disponiveis = sorted(df[df['ANO'] == ano_selecionado]['MES'].unique())

if meses_disponiveis:
    mes_selecionado = st.sidebar.selectbox(
        "Selecione o Mês",
        meses_disponiveis,
        format_func=lambda mes: nomes_meses[mes]
    )
    # --- FILTRANDO O DATAFRAME COM BASE NAS SELEÇÕES ---
    df_filtrado_mes = df[(df['ANO'] == ano_selecionado) & (df['MES'] == mes_selecionado)]
else:
    st.sidebar.warning("Não há dados para os meses deste ano.")
    df_filtrado_mes = pd.DataFrame() # Cria um dataframe vazio para evitar erros

df_filtrado_ano = df[df['ANO'] == ano_selecionado]

# --- LAYOUT PRINCIPAL ---
st.title(f"Dashboard de Produção")
if meses_disponiveis:
    st.subheader(f"Análise de {nomes_meses[mes_selecionado]} de {ano_selecionado}")
st.markdown("---")

# --- GRÁFICOS PARA O MÊS SELECIONADO ---
if not df_filtrado_mes.empty:
    col1, col2 = st.columns(2)

    with col1:
        st.header("Produção Diária (Histograma)")
        chart_hist = alt.Chart(df_filtrado_mes).mark_bar(
            stroke='black',
            strokeWidth=1
        ).encode(
            x=alt.X('DIA:O', title='Dia do Mês'),
            y=alt.Y('sum(PRODUÇÃO TOTAL):Q', title='Produção Total Acumulada'),
            tooltip=[
                alt.Tooltip('DIA', title='Dia'),
                alt.Tooltip('sum(PRODUÇÃO TOTAL)', title='Produção Total', format=',.0f')
            ]
        ).properties(
            height=350
        )
        st.altair_chart(chart_hist, use_container_width=True)

    with col2:
        st.header("Produção Acumulada (Montanha)")
        df_diario = df_filtrado_mes.groupby('DIA')['PRODUÇÃO TOTAL'].sum().reset_index()
        
        chart_area = alt.Chart(df_diario).mark_area(
            line={'color': '#1f77b4'},
            color=alt.Gradient(
                gradient='linear',
                stops=[alt.GradientStop(color='white', offset=0), alt.GradientStop(color='#1f77b4', offset=1)],
                x1=1, x2=1, y1=1, y2=0
            )
        ).encode(
            x=alt.X('DIA:Q', title='Dia do Mês'),
            y=alt.Y('cumulative_sum:Q', title='Produção Acumulada'),
            tooltip=[
                alt.Tooltip('DIA', title='Dia'),
                alt.Tooltip('cumulative_sum:Q', title='Acumulado', format=',.0f')
            ]
        ).transform_window(
            cumulative_sum='sum(PRODUÇÃO TOTAL)',
            sort=[{'field': 'DIA'}]
        ).properties(
            height=350
        )
        st.altair_chart(chart_area, use_container_width=True)
else:
    st.info("Selecione um mês com dados para ver os gráficos mensais.")

st.markdown("---")

# --- HEATMAP ANUAL ESTILO GITHUB ---
st.header(f"Heatmap de Atividade Anual ({ano_selecionado})")

if not df_filtrado_ano.empty:
    dias_do_ano = pd.to_datetime(pd.date_range(start=f'{ano_selecionado}-01-01', end=f'{ano_selecionado}-12-31'))
    df_calendario = pd.DataFrame({'DATA_COMPLETA': dias_do_ano})

    # ATENÇÃO AQUI: Verifique o nome da coluna 'PRODUÇÃO TOTAL'
    df_producao_diaria = df_filtrado_ano.groupby(df_filtrado_ano['DATA'].dt.date)['PRODUÇÃO TOTAL'].sum().reset_index()
    df_producao_diaria['DATA'] = pd.to_datetime(df_producao_diaria['DATA'])
    
    df_heatmap = pd.merge(df_calendario, df_producao_diaria, left_on='DATA_COMPLETA', right_on='DATA', how='left').fillna({'PRODUÇÃO TOTAL': 0})

    df_heatmap['DIA_DA_SEMANA'] = df_heatmap['DATA_COMPLETA'].dt.dayofweek
    df_heatmap['SEMANA_DO_ANO'] = df_heatmap['DATA_COMPLETA'].dt.isocalendar().week
    df_heatmap['NOME_MES'] = df_heatmap['DATA_COMPLETA'].dt.month.apply(lambda x: calendar.month_abbr[x].capitalize())

    df_heatmap.loc[df_heatmap['DATA_COMPLETA'].dt.month == 1, 'SEMANA_DO_ANO'] = df_heatmap.loc[df_heatmap['DATA_COMPLETA'].dt.month == 1, 'SEMANA_DO_ANO'].replace(52, 0).replace(53, 0)
    df_heatmap.loc[df_heatmap['DATA_COMPLETA'].dt.month == 12, 'SEMANA_DO_ANO'] = df_heatmap.loc[df_heatmap['DATA_COMPLETA'].dt.month == 12, 'SEMANA_DO_ANO'].replace(1, 53)

    heatmap = alt.Chart(df_heatmap).mark_rect().encode(
        x=alt.X('SEMANA_DO_ANO:O', title=None, axis=alt.Axis(labels=False, ticks=False, domain=False)),
        y=alt.Y('DIA_DA_SEMANA:O', title=None, axis=alt.Axis(labelExpr="['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'][datum.value]", ticks=False, domain=False)),
        color=alt.Color('PRODUÇÃO TOTAL:Q', legend=alt.Legend(title='Produção'), scale=alt.Scale(scheme='greens')),
        tooltip=[alt.Tooltip('DATA_COMPLETA:T', title='Data'), alt.Tooltip('PRODUÇÃO TOTAL:Q', title='Produção', format=',.0f')]
    ).properties(width=alt.Step(15))
    
    st.altair_chart(heatmap, use_container_width=True)
else:
    st.info("Sem dados de produção para este ano.")
