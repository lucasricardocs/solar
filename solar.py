# Conteúdo do arquivo app.py

import streamlit as st
import pandas as pd
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Configurações do Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Carregar credenciais do Streamlit secrets
creds_json = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
client = gspread.authorize(creds)

# Abrir a planilha (substitua pelo nome da sua planilha)
sheet = client.open("solar").sheet1

# Obter todos os dados da planilha
data = sheet.get_all_records()
df = pd.DataFrame(data)

# Configuração da página
st.set_page_config(
    page_title="Análise Solar",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal com emoji
st.title("☀️ Análise de Dados Solares")
st.markdown("---")

# Sidebar para filtros e opções
st.sidebar.header("🔧 Opções de Filtro")

# Dados brutos em uma seção colapsável
with st.expander("📊 Ver Dados Brutos", expanded=False):
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum dado encontrado na planilha.")

# Layout em colunas para melhor organização
col1, col2 = st.columns([2, 1])

with col1:
    # Heatmap de atividade solar
    st.subheader("🔥 Heatmap de Atividade Solar")
    
    # Preparar os dados para o heatmap
    if not df.empty and 'data' in df.columns and 'gerado' in df.columns:
        try:
            df['data'] = pd.to_datetime(df['data'])
            df['gerado'] = pd.to_numeric(df['gerado'])
        except Exception as e:
            st.error(f"❌ Erro ao processar dados: {e}")
            st.info("💡 Verifique se 'data' é uma data válida e 'gerado' é um número.")
            st.stop()

        df['days'] = df['data'].dt.day_name()
        df['weeks'] = df['data'].dt.isocalendar().week.astype(int)
        df['month'] = df['data'].dt.strftime("%b")
        months_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        df['month'] = pd.Categorical(df['month'], categories=months_order, ordered=True)
        df['values'] = df['gerado']
        df['dates'] = df['data'].dt.strftime('%Y-%m-%d')

        # Definir a ordem dos dias da semana
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        df['days'] = pd.Categorical(df['days'], categories=days_of_week, ordered=True)

        # Parâmetros para o heatmap
        corner_radius = 3
        cell_width = 20
        font_size = 10
        height = 150
        width = 800
        year = str(df['data'].dt.year.iloc[0]) if not df.empty else "2025"

        # Definir o domínio e o range de cores para o heatmap
        domain = [df['values'].min(), df['values'].max()]
        range_ = ['lightgreen', 'darkgreen']

        chart = alt.Chart(df).mark_rect(
            cornerRadius=corner_radius,
            width=cell_width,
            height=cell_width
        ).encode(
            y=alt.Y(
                'days',
                sort=days_of_week,
                axis=alt.Axis(
                    tickSize=0,
                    title='',
                    domain=False,
                    values=days_of_week,
                    labelFontSize=font_size
                )
            ),
            x=alt.X(
                'month:N', 
                axis=alt.Axis(
                    tickSize=0,
                    domain=False,
                    title='',
                    labelAngle=0,
                    labelFontSize=font_size
                )
            ),
            color=alt.Color(
                'values',
                legend=None,
                scale=alt.Scale(domain=domain, range=range_)
            ),
            tooltip=[
                alt.Tooltip('dates', title='Data'),
                alt.Tooltip('values', title='Energia Gerada')
            ]
        ).properties(
            title=f"Atividade Solar - {year}",
            height=height,
            width=width
        ).configure_scale(
            rectBandPaddingInner=0.1,
        ).configure_mark(
            strokeOpacity=0,
            strokeWidth=0,
            filled=True
        ).configure_axis(
            grid=False
        ).configure_view(
            stroke=None
        )

        st.altair_chart(chart, use_container_width=True)
    else:
        st.warning("⚠️ As colunas 'data' e/ou 'gerado' não foram encontradas no DataFrame.")

with col2:
    # Estatísticas resumidas
    st.subheader("📈 Estatísticas")
    
    if not df.empty and 'gerado' in df.columns:
        try:
            gerado_numeric = pd.to_numeric(df['gerado'])
            
            # Métricas principais
            st.metric("Total Gerado", f"{gerado_numeric.sum():.2f} kWh")
            st.metric("Média Diária", f"{gerado_numeric.mean():.2f} kWh")
            st.metric("Máximo", f"{gerado_numeric.max():.2f} kWh")
            st.metric("Mínimo", f"{gerado_numeric.min():.2f} kWh")
            
            # Gráfico de barras simples
            st.subheader("📊 Gráfico de Barras")
            st.bar_chart(gerado_numeric.tail(10))
            
        except Exception as e:
            st.error(f"❌ Erro ao calcular estatísticas: {e}")
    else:
        st.info("💡 Dados não disponíveis para estatísticas.")

# Filtros na sidebar
if not df.empty:
    # Filtro por período (se houver coluna de data)
    if 'data' in df.columns:
        try:
            df['data'] = pd.to_datetime(df['data'])
            min_date = df['data'].min().date()
            max_date = df['data'].max().date()
            
            date_range = st.sidebar.date_input(
                "📅 Selecione o período",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
            if len(date_range) == 2:
                start_date, end_date = date_range
                filtered_df = df[(df['data'].dt.date >= start_date) & (df['data'].dt.date <= end_date)]
                st.sidebar.success(f"✅ {len(filtered_df)} registros no período selecionado")
        except:
            st.sidebar.warning("⚠️ Erro ao processar filtro de data")

# Remover o footer fixo que pode causar problemas de layout


