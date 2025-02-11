import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# Configura a página para ter layout wide (largo)
st.set_page_config(layout='wide')

# Função para formatar números com unidades
def formata_numero(valor, prefixo=''):
    for unidade in ['', 'mil']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'

# Título do dashboard
st.title('DASHBOARD DE VENDAS :shopping_trolley:')

# URL da API dos dados
url = 'https://labdados.com/produtos'
regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']
st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)

if regiao == "Brasil":
    regiao = ''
    
todos_anos = st.sidebar.checkbox('Dados de todo o período', value=True)

if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023)
    
query_string = {'regiao': regiao.lower(), 'ano': ano}
response = requests.get(url, params=query_string)

# Verifica se a requisição foi bem-sucedida
if response.status_code == 200:
    dados = pd.DataFrame.from_dict(response.json())
else:
    st.error(f"Erro ao acessar a API: {response.status_code}")
    st.stop()

# Conversão da coluna 'Data da Compra' para o formato datetime
if 'Data da Compra' in dados.columns:
    dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y')
else:
    st.error("Coluna 'Data da Compra' não encontrada nos dados.")
    st.stop()

# Filtro de vendedores
filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

# Agrupamento de dados por estado para calcular a receita
receita_estados = dados.groupby('Local da compra')['Preço'].sum().reset_index()
receita_estados = receita_estados.merge(
    dados[['Local da compra', 'lat', 'lon']].drop_duplicates(subset='Local da compra'),
    on='Local da compra'
).sort_values('Preço', ascending=False)

# Agrupamento de dados por mês para calcular a receita mensal
receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()

# Agrupamento de dados por categoria para calcular a receita por categoria
receita_categorias = dados.groupby('Categoria do Produto')['Preço'].sum().sort_values(ascending=False)

# Gráficos
fig_mapa_receita = px.scatter_geo(receita_estados,
                                lat='lat',
                                lon='lon',
                                scope='south america',
                                size='Preço',
                                template='seaborn',
                                hover_name='Local da compra',
                                hover_data={'lat': False, 'lon': False},
                                title='Receita por Estado')

fig_receita_mensal = px.line(receita_mensal,
                            x='Mes',
                            y='Preço',
                            markers=True,
                            range_y=(0, receita_mensal['Preço'].max()),
                            color='Ano',
                            line_dash='Ano',
                            title='Receita mensal')
fig_receita_mensal.update_layout(yaxis_title='Receita')

fig_receita_estados = px.bar(receita_estados.head(),
                            x='Local da compra',
                            y='Preço',
                            text_auto=True,
                            title='Top estados')

fig_receita_categorias = px.bar(receita_categorias,
                                text_auto=True,
                                title='Receita por categoria')
fig_receita_categorias.update_layout(yaxis_title='Receita')

# Função para exibir métricas e gráficos
def exibir_metricas_e_graficos(dados):
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width=True)
        st.plotly_chart(fig_receita_estados, use_container_width=True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width=True)
        st.plotly_chart(fig_receita_categorias, use_container_width=True)

# Visualização no Streamlit
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendedores'])

with aba1:
    exibir_metricas_e_graficos(dados)

with aba2:
    exibir_metricas_e_graficos(dados)

with aba3:
    qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5, key='qtd_vendedores')
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        receita_vendedores = dados.groupby('Vendedor')['Preço'].sum().sort_values(ascending=False).head(qtd_vendedores)
        fig_receita_vendedores = px.bar(
            receita_vendedores.reset_index(),
            x='Preço',
            y='Vendedor',
            text_auto=True,
            title=f'Top {qtd_vendedores} vendedores (receita)'
        )
        st.plotly_chart(fig_receita_vendedores)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        vendas_vendedores = dados.groupby('Vendedor').size().sort_values(ascending=False).head(qtd_vendedores)
        fig_vendas_vendedores = px.bar(
            vendas_vendedores.reset_index(),
            x=0,
            y='Vendedor',
            text_auto=True,
            title=f'Top {qtd_vendedores} vendedores (quantidade de vendas)'
        )
        st.plotly_chart(fig_vendas_vendedores)
