import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import altair as alt
from datetime import datetime

# --- Configuração da Página ---
st.set_page_config(
    layout="wide",
    page_title="Dashboard de Geração de Energia Solar",
    page_icon="☀️"
)

# --- Estilo CSS Customizado ---
# Fonte Poppins do Google Fonts e estilo customizado
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

html, body, [class*="st-"] {
    font-family: 'Poppins', sans-serif;
}

/* Cor de fundo principal */
.stApp {
    background-color: #1a1a1a;
    color: #ffffff;
}

/* Estilo dos containers */
[data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
    border: 1px solid #2e2e2e;
    border-radius: 10px;
    padding: 20px;
    background-color: #262730;
}

/* Estilo dos botões */
.stButton>button {
    border-radius: 8px;
    border: 1px solid #00b894;
    background-color: #00b894;
    color: white;
}
.stButton>button:hover {
    border: 1px solid #00a383;
    background-color: #00a383;
}

/* Estilo da sidebar */
[data-testid="stSidebar"] {
    background-color: #262730;
}

/* Títulos */
h1, h2, h3 {
    color: #00b894; /* Verde menta */
}
</style>
""", unsafe_allow_html=True)


# --- Conexão com Google Sheets ---
# Cacheia a conexão para não reconectar a cada interação
@st.cache_resource
def connect_to_gsheets():
    """Conecta ao Google Sheets e retorna o objeto da planilha."""
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    try:
        spreadsheet = client.open("EnergiaSolar")
        sheet = spreadsheet.worksheet("Dados")
        return sheet
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("Planilha 'EnergiaSolar' não encontrada. Verifique o nome e as permissões de compartilhamento.")
        st.stop()
    except gspread.exceptions.WorksheetNotFound:
        st.error("Aba 'Dados' não encontrada na planilha. Verifique o nome da aba.")
        st.stop()

sheet = connect_to_gsheets()

# --- Funções de Dados ---
# Cacheia os dados para performance, com TTL para atualizar periodicamente
@st.cache_data(ttl=600)
def load_data():
    """Carrega os dados da planilha, processa e retorna um DataFrame."""
    data = sheet.get_all_records()
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    
    # *** ALTERAÇÃO AQUI: Renomeia as colunas da sua planilha para as que o app espera ***
    df.rename(columns={'data': 'Data', 'gerado': 'Energia Gerada (kWh)'}, inplace=True)
    
    # O resto do código continua normalmente
    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
    df['Energia Gerada (kWh)'] = pd.to_numeric(df['Energia Gerada (kWh)'], errors='coerce')
    df.dropna(subset=['Data', 'Energia Gerada (kWh)'], inplace=True)
    df = df.sort_values(by='Data')
    return df

def append_data(date, energy):
    """Adiciona uma nova linha de dados na planilha."""
    try:
        formatted_date = date.strftime('%d/%m/%Y')
        # A ordem aqui (data, gerado) corresponde à sua planilha
        sheet.append_row([formatted_date, energy])
        st.cache_data.clear() # Limpa o cache dos dados após a inserção
        return True
    except Exception as e:
        st.error(f"Erro ao salvar os dados: {e}")
        return False

# --- Barra Lateral (Sidebar) ---
with st.sidebar:
    st.header("☀️ Cadastro de Geração")
    with st.form("entry_form", clear_on_submit=True):
        input_date = st.date_input("Selecione a Data", value=datetime.today())
        input_energy = st.number_input("Energia Gerada (kWh)", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("Salvar Geração")

        if submitted:
            if input_energy > 0:
                if append_data(input_date, input_energy):
                    st.success("Dados salvos com sucesso!")
                else:
                    st.error("Falha ao salvar os dados.")
            else:
                st.warning("A energia gerada deve ser maior que zero.")

    # Carrega os dados para os filtros
    df = load_data()
    
    if not df.empty:
        st.divider()
        st.header("🔍 Filtros")
        years = sorted(df['Data'].dt.year.unique(), reverse=True)
        selected_year = st.selectbox("Selecione o Ano", options=years)

        months = sorted(df[df['Data'].dt.year == selected_year]['Data'].dt.month.unique())
        month_names = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
        selected_month_num = st.selectbox("Selecione o Mês", options=months, format_func=lambda x: month_names[x])

        # --- Painel de Curiosidades ---
        st.divider()
        st.header("💡 Insights do Mês")
        
        filtered_df = df[(df['Data'].dt.year == selected_year) & (df['Data'].dt.month == selected_month_num)]
        if not filtered_df.empty:
            total_generated = filtered_df['Energia Gerada (kWh)'].sum()
            avg_daily_generation = filtered_df['Energia Gerada (kWh)'].mean()
            best_day = filtered_df.loc[filtered_df['Energia Gerada (kWh)'].idxmax()]
            worst_day = filtered_df.loc[filtered_df['Energia Gerada (kWh)'].idxmin()]

            st.metric(label="Total Gerado no Mês", value=f"{total_generated:.2f} kWh")
            st.metric(label="Média Diária de Geração", value=f"{avg_daily_generation:.2f} kWh")
            st.metric(label="Melhor Dia", value=f"{best_day['Energia Gerada (kWh)']:.2f} kWh", delta=best_day['Data'].strftime('%d/%m'))
            st.metric(label="Pior Dia", value=f"{worst_day['Energia Gerada (kWh)']:.2f} kWh", delta=worst_day['Data'].strftime('%d/%m'), delta_color="inverse")
        else:
            st.info("Nenhum dado para o período selecionado.")

# --- Página Principal ---
st.title("Dashboard de Geração de Energia Solar")
st.markdown("Acompanhe a performance da sua geração de energia de forma visual e interativa.")

if df.empty:
    st.warning("Nenhum dado encontrado. Comece cadastrando uma nova geração na barra lateral.")
else:
    # --- Gráficos do Mês Selecionado ---
    st.header(f"Análise de {month_names[selected_month_num]} de {selected_year}")

    if filtered_df.empty:
        st.info("Nenhum dado para exibir para o período selecionado.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            # Gráfico de Colunas com fundo transparente
            bar_chart = alt.Chart(filtered_df).mark_bar(
                cornerRadiusTopLeft=5,
                cornerRadiusTopRight=5,
                color="#00b894"
            ).encode(
                x=alt.X('Data:T', title='Dia do Mês', axis=alt.Axis(format='%d', grid=False, labelAngle=0)),
                y=alt.Y('Energia Gerada (kWh):Q', title='Energia (kWh)', axis=alt.Axis(grid=False)),
                tooltip=[alt.Tooltip('Data:T', title='Data'), alt.Tooltip('Energia Gerada (kWh):Q', title='Gerado', format='.2f')]
            ).properties(
                title="Produção Diária"
            ).configure_view(
                fill='transparent'
            ).configure_axis(
                labelColor='white',
                titleColor='white'
            ).configure_title(
                color='white'
            ).interactive()
            st.altair_chart(bar_chart, use_container_width=True)

        with col2:
            # Gráfico de Área Acumulativo
            filtered_df['Acumulado'] = filtered_df['Energia Gerada (kWh)'].cumsum()
            area_chart = alt.Chart(filtered_df).mark_area(
                line={'color':'#00b894'},
                color=alt.Gradient(
                    gradient='linear',
                    stops=[alt.GradientStop(color='#00b894', offset=0),
                           alt.GradientStop(color='rgba(0,184,148,0)', offset=1)],
                    x1=1, x2=1, y1=1, y2=0
                )
            ).encode(
                x=alt.X('Data:T', title='Dia do Mês', axis=alt.Axis(format='%d', grid=False, labelAngle=0)),
                y=alt.Y('Acumulado:Q', title='Energia Acumulada (kWh)', axis=alt.Axis(grid=False)),
                tooltip=[alt.Tooltip('Data:T', title='Data'), alt.Tooltip('Acumulado:Q', title='Acumulado', format='.2f')]
            ).properties(
                title="Geração Mensal Acumulada"
            ).configure_view(
                fill='transparent'
            ).configure_axis(
                labelColor='white',
                titleColor='white'
            ).configure_title(
                color='white'
            ).interactive()
            st.altair_chart(area_chart, use_container_width=True)

        # --- Análise Anual ---
        st.divider()
        st.header(f"Mapa de Calor da Geração de {selected_year}")

        year_df = df[df['Data'].dt.year == selected_year].copy()
        
        # Adiciona colunas para o dia da semana e semana do ano
        year_df['day_of_week'] = year_df['Data'].dt.day_name()
        year_df['week_of_year'] = year_df['Data'].dt.isocalendar().week

        heatmap = alt.Chart(year_df).mark_rect().encode(
            x=alt.X('week_of_year:O', title='Semana do Ano', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('day_of_week:O', title='Dia da Semana', sort=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']),
            color=alt.Color('Energia Gerada (kWh):Q',
                legend=alt.Legend(title="Energia (kWh)"),
                scale=alt.Scale(scheme='greens')
            ),
            tooltip=[
                alt.Tooltip('Data:T', title='Data'),
                alt.Tooltip('Energia Gerada (kWh):Q', title='Gerado', format='.2f')
            ]
        ).properties(
            title=f"Geração Diária em {selected_year}"
        ).configure_view(
            fill='transparent'
        ).configure_axis(
            labelColor='white',
            titleColor='white'
        ).configure_title(
            color='white'
        ).configure_legend(
            labelColor='white',
            titleColor='white'
        )
        
        st.altair_chart(heatmap, use_container_width=True)

