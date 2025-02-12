import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob
from sklearn.preprocessing import MinMaxScaler

# Função para ler todos os arquivos CSV da pasta 'newFiles'
def ler_csvs_pasta(pasta):
    arquivos = [f for f in os.listdir(pasta) if f.endswith('.csv')]
    dados = []
    for arquivo in arquivos:
        caminho = os.path.join(pasta, arquivo)
        df = pd.read_csv(caminho)
        # Extraindo o nome da cripto do nome do arquivo (antes do primeiro '-')
        cripto_nome = arquivo.split('-')[0]
        dados.append((cripto_nome, df))  # Guardando o nome da cripto junto com os dados
    return dados

# Função para normalização Min-Max
def normalizar_min_max(series):
    """Normaliza uma série para uma escala entre 0 e 1."""
    return (series - series.min()) / (series.max() - series.min())

# Função para calcular e plotar a matriz de correlação
def analise_correlacao(df_completo):
    # Pivotar os dados para ter preços de diferentes criptomoedas em colunas separadas
    pivot_df = df_completo.pivot(index='snapped_at', columns='crypto', values='price')
    correlation_matrix = pivot_df.corr()
    
    # Exibir a matriz de correlação
    plt.figure(figsize=(12, 8))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt='.2f', linewidths=0.5)
    plt.title("Matriz de Correlação entre o BTC e Outras Criptos")
    plt.tight_layout()
    plt.show()

# Função para análise das variações de preço
def analise_variacao_precos(dados_csv):
    # Variação do preço no último ano (em %)
    cryptos = []
    variations = []
    
    for cripto_nome, df in dados_csv:
        # Usando as últimas 30 linhas (último mês)
        df = df.tail(30)
        
        # Calculando a variação do preço
        start_price = df['price'].iloc[0]
        end_price = df['price'].iloc[-1]
        variation = ((end_price - start_price) / start_price) * 100
        
        cryptos.append(cripto_nome)
        variations.append(variation)
    
    # Gráfico de barras da variação do preço
    plt.figure(figsize=(12, 8))
    plt.barh(cryptos, variations, color='lightgreen')
    plt.xlabel('Variação do Preço (%)')
    plt.title('Variação do Preço das Criptos no Último Mês')
    plt.tight_layout()
    plt.show()

# Função para análise de correlação e variação de preços
def analisar_tendencia_comparativa(dados_csv):
    # Definindo o scaler para normalização dos dados
    scaler = MinMaxScaler()

    # Criando um único gráfico
    plt.figure(figsize=(12, 8))

    for cripto_nome, df in dados_csv:
        # Converter a coluna 'snapped_at' para datetime
        df['snapped_at'] = pd.to_datetime(df['snapped_at'], errors='coerce')

        # Garantir que os preços estejam no formato correto (remover o símbolo '$' e converter para float)
        df['price'] = df['price'].replace({'\$': '', ',': ''}, regex=True).astype(float)

        # Normalização dos preços de fechamento
        df['Normalized_Close'] = scaler.fit_transform(df[['price']])

        # Suavização Exponencial para identificar a tendência
        df['Smoothed_Close'] = df['Normalized_Close'].ewm(span=20, adjust=False).mean()

        # Calculando a taxa de crescimento diária
        df['Growth_Rate'] = df['price'].pct_change()

        # Calculando a média da taxa de crescimento
        average_growth_rate = df['Growth_Rate'].mean()

        # Plotando no gráfico
        plt.plot(df['snapped_at'].values, df['Smoothed_Close'].values, label=f'Tendência {cripto_nome} (Média de Crescimento: {average_growth_rate:.4f})')

    # Adicionando título e rótulos
    plt.title('Tendência de Preços Normalizados das Criptomoedas')
    plt.xlabel('Data')
    plt.ylabel('Preço Normalizado (USD)')
    plt.legend()

    # Exibindo o gráfico
    plt.tight_layout()
    plt.show()

# Função principal que carrega e processa todos os arquivos
def executar_analises(pasta_path):
    dados_csv = ler_csvs_pasta(pasta_path)

    # Consolidar todos os dados
    df_completo = pd.concat([df.assign(crypto=cripto_nome) for cripto_nome, df in dados_csv], ignore_index=True)

    # Analisar a correlação entre as criptos e o BTC
    analise_correlacao(df_completo)

    # Analisar a variação de preço no último mês de cada cripto
    analise_variacao_precos(dados_csv)

    # Gerar gráfico comparativo de tendência
    analisar_tendencia_comparativa(dados_csv)

# Caminho da pasta onde os arquivos CSV estão localizados
pasta_path = './newFiles'  # Substitua pelo caminho correto para sua pasta

# Executando as análises
executar_analises(pasta_path)
