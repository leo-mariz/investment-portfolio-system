from flask import Flask, render_template
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from flask import jsonify
import requests


def obter_precos_historicos(ativo, data_inicio):
    ticker = yf.Ticker(ativo)
    dados = ticker.history(start=data_inicio)
    return dados['Close']


def obter_precos_atuais(ativos):
    precos_atuais = {}
    for ativo in ativos:
        moeda = ativo
        base = 'USDT'
        simbolo = moeda+base
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={simbolo}"
        requisicao = requests.get(url)
        resposta = requisicao.json()
        precos_atuais[moeda] = float(resposta['price'])
    return precos_atuais


def atualizar_dados(df, dolar):
    ativos = df['Ativo'].unique()
    precos_atuais = obter_precos_atuais(ativos)

    # Atualiza o preço atual e calcula o valor investido atual
    df['Preço Atual ($)'] = df['Ativo'].map(precos_atuais)
    df['Investido Atual (R$)'] = df['Preço Atual ($)'] * df['Qtde efet']*dolar
    df['Var (R$)'] = df['Investido Atual (R$)'] - df['Valor Investido']
    df['Var (%)'] = (df['Investido Atual (R$)']*100/df['Valor Investido'])-100
    df['% Carteira'] = (df['Investido Atual (R$)'] /
                        df['Valor Investido'].sum()) * 100
    df = df.sort_values('Valor Investido',
                        ascending=False).reset_index(drop=True)

    # Calcular totais para o resumo da carteira
    total_investido = df['Valor Investido'].sum()
    valor_total_carteira = df['Investido Atual (R$)'].sum()
    valorizacao_total_carteira = valor_total_carteira - total_investido
    percentual_valorizacao = (valor_total_carteira / total_investido - 1) * 100

    # Preparar dados para a resposta
    resposta = {
        'total_investido': total_investido,
        'valor_total_carteira': valor_total_carteira,
        'valorizacao_total_carteira': valorizacao_total_carteira,
        'percentual_valorizacao': percentual_valorizacao,
        'dados_tabela': df.to_dict(orient='records')
    }

    return jsonify(resposta)


def gerar_grafico_btc():
    # Obtenha os dados históricos do Bitcoin
    btc_data = yf.download('BTC-USD', start='2014-09-17')
    # Crie a figura e o eixo com Matplotlib
    plt.figure(figsize=(10, 5))
    plt.plot(btc_data['Close'], label='Bitcoin')
    plt.title('Preço de Fechamento do Bitcoin (USD)')
    plt.xlabel('Data')
    plt.ylabel('Preço de Fechamento (USD)')
    plt.legend()
    # Salve o gráfico como um arquivo PNG
    plt.savefig('static/grafico_bitcoin.png', bbox_inches='tight')
    plt.close()


df = pd.read_excel('Carteira 2.xlsx')

# Definindo valores gerais
total_investido = df['Valor Investido'].sum()
total_gasto = df['Valor pago'].sum()
quantidade_ativos = df['Ativo'].nunique()
custos_transacao = total_gasto - total_investido
investimento_por_ativo = df.groupby('Ativo')['Valor Investido'].sum()

# Calculando cotação atual dolar
usd_brl_symbol = 'BRL=X'
stock = yf.Ticker(usd_brl_symbol)
historical_data = stock.history(period="id")
closing_prices = historical_data["Close"]
current_price = closing_prices.iloc[-1]
dolar = current_price

# Cálculo do preço médio de compra
agrupado = df.groupby('Ativo').agg({
    'Valor Investido': 'sum',
    'Qtde efet': 'sum'
}).reset_index()
agrupado['Preço Médio (R$)'] = agrupado['Valor Investido'] / \
    agrupado['Qtde efet']
agrupado['Preço Médio ($)'] = agrupado['Preço Médio (R$)'] / dolar

# Calculando os preços atuais dos ativos
ativos = df['Ativo'].unique()
precos_atuais = obter_precos_atuais(ativos)

# Organizando a tabela investimento_por_ativo
investimento_por_ativo = df.groupby('Ativo')['Qtde efet'].sum().reset_index()
total_inv_por_ativo = df.groupby(
    'Ativo')['Valor Investido'].sum().reset_index()
investimento_por_ativo = investimento_por_ativo.merge(
    agrupado[['Ativo', 'Preço Médio ($)']], on='Ativo', how='left')
investimento_por_ativo['Preço Atual ($)'] = investimento_por_ativo['Ativo'].map(
    precos_atuais)
investimento_por_ativo = investimento_por_ativo.merge(
    total_inv_por_ativo, on='Ativo', how='left')
investimento_por_ativo = investimento_por_ativo.sort_values(
    'Valor Investido', ascending=False).reset_index(drop=True)


# Calcula o valor atual em reais
investimento_por_ativo['Investido Atual (R$)'] = investimento_por_ativo['Preço Atual ($)'] * \
    investimento_por_ativo['Qtde efet'] * dolar
# Valorização/Desvalorização da carteira
investimento_por_ativo['Var (R$)'] = investimento_por_ativo['Investido Atual (R$)'] - \
    investimento_por_ativo['Valor Investido']
investimento_por_ativo['Var (%)'] = (
    investimento_por_ativo['Investido Atual (R$)']*100/investimento_por_ativo['Valor Investido'])-100
# Totais para o resumo da carteira
valor_total_carteira = investimento_por_ativo['Investido Atual (R$)'].sum()
valorizacao_total_carteira = valor_total_carteira - total_investido
percentual_valorizacao = (valor_total_carteira*100/total_investido)-100
investimento_por_ativo['% Carteira'] = (
    investimento_por_ativo['Investido Atual (R$)'] / total_investido) * 100
investimento_por_ativo.reset_index(drop=True, inplace=True)

# Adicionando as novasa colunas ao dataframe
principais_ativos = ['BTC', 'ETH', 'DOGE']
investimento_por_ativo['Categoria'] = investimento_por_ativo['Ativo'].apply(
    lambda x: x if x in principais_ativos else 'Outros')
investimento_agrupado = investimento_por_ativo.groupby(
    'Categoria', as_index=False)['Investido Atual (R$)'].sum()


# Gráfico de pizza - Distribuição dos ativos
fig, ax = plt.subplots(figsize=(4.5, 3))
fig.patch.set_facecolor('none')
fig.patch.set_alpha(0)
ax.set_facecolor('none')
wedges, texts, autotexts = ax.pie(
    investimento_agrupado['Investido Atual (R$)'],
    labels=investimento_agrupado['Categoria'],
    autopct='%1.1f%%',
    textprops=dict(color="white")  # Define a propriedade de cor do texto
)
plt.setp(texts, color='white', weight="bold")
plt.setp(autotexts, color='white')
ax.axis('equal')
buf = BytesIO()
fig.savefig(buf, format='png', bbox_inches='tight', transparent=True)
buf.seek(0)
image_png = buf.getvalue()
graph_url = base64.b64encode(image_png).decode('utf-8')
buf.close()

# Iniciando o app dashboard

app = Flask(__name__)


@app.route('/')
def dashboard():
    return render_template('dashboard.html',
                           total_investido=total_investido,
                           quantidade_ativos=quantidade_ativos,
                           custos_transacao=custos_transacao,
                           valor_total_carteira=valor_total_carteira,
                           valorizacao_total_carteira=valorizacao_total_carteira,
                           percentual_valorizacao=percentual_valorizacao,
                           dolar=dolar,
                           distribuicao_ativos=investimento_por_ativo.to_dict('records'),
                           graph_url=graph_url)


@app.route('/cadastrar-compra')
def cadastrar_compra():
    return render_template('compra.html')


@app.route('/cadastrar-venda')
def cadastrar_venda():
    return render_template('venda.html')


@app.route('/api/atualizar-dados')
def api_atualizar_dados():
    return atualizar_dados(agrupado, dolar)


if __name__ == '__main__':
    app.run(debug=True)
