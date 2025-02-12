import pandas as pd
import numpy as np
import glob
import os

# Função de limpeza dos dados
def clean_data(df):
    columns_to_clean = ['price', 'market_cap', 'total_volume']
    for col in columns_to_clean:
        df[col] = df[col].astype(float)
    return df

# Função para normalização Min-Max
def normalizar_min_max(series):
    """Normaliza uma série para uma escala entre 0 e 1."""
    return (series - series.min()) / (series.max() - series.min())

# Função para carregar e processar dados
def processar_dados_csv(file_path, crypto_name):
    df = pd.read_csv(file_path)
    df = clean_data(df)
    df['snapped_at'] = pd.to_datetime(df['snapped_at'])
    df = df.sort_values(by='snapped_at', ascending=True)
    df['MA30'] = df['price'].rolling(window=30, min_periods=30).mean()
    df['crypto'] = crypto_name  # Adiciona uma coluna para identificar a criptomoeda
    return df

# Função para analisar tendência com base no movimento de preço em relação à MA30
def analisar_tendencias_com_15_porcento(df, dias_minimos=5, limite_percentual=15):
    # Inicializar a coluna de tendência
    tendencias = []
    dias_consecutivos = 0
    tendencia_atual = 'Neutra'  # A tendência inicial é neutra
    preco_inicio = 0
    preco_fim = 0
    data_inicio = None
    data_fim = None

    # Loop para analisar a tendência com base na média móvel
    for i in range(1, len(df)):
        preco_atual = df['price'].iloc[i]
        preco_anterior = df['price'].iloc[i-1]
        ma30_atual = df['MA30'].iloc[i]

        # Calcular a diferença percentual entre o preço e a MA30
        distancia_percentual = (preco_atual - ma30_atual) / ma30_atual * 100
        
        if distancia_percentual > limite_percentual:
            # Se o preço está acima da MA30 por mais de 15%, conta os dias consecutivos
            if tendencia_atual != 'Alta':
                if tendencia_atual != 'Neutra':
                    # Registrar tendência anterior
                    var_percentual = (preco_fim - preco_inicio) / preco_inicio * 100
                    tendencias.append({
                        'Tendência': tendencia_atual,
                        'Início': data_inicio,
                        'Fim': data_fim,
                        'Variação Percentual': var_percentual,
                        'Criptomoeda': df['crypto'].iloc[0]  # Incluir a criptomoeda
                    })
                dias_consecutivos = 1
                tendencia_atual = 'Alta'
                preco_inicio = preco_atual
                data_inicio = df['snapped_at'].iloc[i]
            else:
                dias_consecutivos += 1
        elif distancia_percentual < -limite_percentual:
            # Se o preço está abaixo da MA30 por mais de 15%, conta os dias consecutivos
            if tendencia_atual != 'Baixa':
                if tendencia_atual != 'Neutra':
                    # Registrar tendência anterior
                    var_percentual = (preco_fim - preco_inicio) / preco_inicio * 100
                    tendencias.append({
                        'Tendência': tendencia_atual,
                        'Início': data_inicio,
                        'Fim': data_fim,
                        'Variação Percentual': var_percentual,
                        'Criptomoeda': df['crypto'].iloc[0]  # Incluir a criptomoeda
                    })
                dias_consecutivos = 1
                tendencia_atual = 'Baixa'
                preco_inicio = preco_atual
                data_inicio = df['snapped_at'].iloc[i]
            else:
                dias_consecutivos += 1
        else:
            # Se o preço está dentro da faixa de 15%, reinicia o contador
            if dias_consecutivos >= dias_minimos:
                var_percentual = (preco_fim - preco_inicio) / preco_inicio * 100
                tendencias.append({
                    'Tendência': tendencia_atual,
                    'Início': data_inicio,
                    'Fim': data_fim,
                    'Variação Percentual': var_percentual,
                    'Criptomoeda': df['crypto'].iloc[0]  # Incluir a criptomoeda
                })
            dias_consecutivos = 0
            tendencia_atual = 'Neutra'
        
        # Atualizar preço final da tendência
        if tendencia_atual != 'Neutra':
            preco_fim = preco_atual
            data_fim = df['snapped_at'].iloc[i]

    # Verifica se a última tendência foi longa o suficiente
    if dias_consecutivos >= dias_minimos:
        var_percentual = (preco_fim - preco_inicio) / preco_inicio * 100
        tendencias.append({
            'Tendência': tendencia_atual,
            'Início': data_inicio,
            'Fim': data_fim,
            'Variação Percentual': var_percentual,
            'Criptomoeda': df['crypto'].iloc[0]  # Incluir a criptomoeda
        })
    
    return tendencias

# Função principal que carrega e processa todos os arquivos
def executar_analises(pasta_path):
    arquivos = glob.glob(os.path.join(pasta_path, '*-usd-max.csv'))
    dfs = []
    all_tendencias = []

    for arquivo in arquivos:
        crypto_name = os.path.basename(arquivo).split('-')[0]  # Extrai o nome da criptomoeda do nome do arquivo
        print(f"Processando {arquivo} para {crypto_name}")
        df = processar_dados_csv(arquivo, crypto_name)
        tendencias = analisar_tendencias_com_15_porcento(df, dias_minimos=5, limite_percentual=15)
        all_tendencias.extend(tendencias)

    # Calcular a média e o desvio padrão das variações percentuais separadas para alta e baixa
    tendencias_df = pd.DataFrame(all_tendencias)
    
    # Filtrando as tendências de alta e baixa
    alta_tendencias = tendencias_df[tendencias_df['Tendência'] == 'Alta']
    baixa_tendencias = tendencias_df[tendencias_df['Tendência'] == 'Baixa']
    
    # Média e desvio padrão das variações percentuais de alta e baixa
    medias_alta = alta_tendencias.groupby('Criptomoeda')['Variação Percentual'].mean()
    medias_baixa = baixa_tendencias.groupby('Criptomoeda')['Variação Percentual'].mean()
    
    desvios_alta = alta_tendencias.groupby('Criptomoeda')['Variação Percentual'].std()
    desvios_baixa = baixa_tendencias.groupby('Criptomoeda')['Variação Percentual'].std()

    # Salvar as tendências e as métricas no CSV
    tendencias_df.to_csv('tendencias_criptomoedas.csv', index=False)
    medias_alta.to_csv('media_variacao_percentual_alta.csv', header=['Média Alta'], index=True)
    medias_baixa.to_csv('media_variacao_percentual_baixa.csv', header=['Média Baixa'], index=True)
    desvios_alta.to_csv('desvio_padrao_variacao_percentual_alta.csv', header=['Desvio Padrão Alta'], index=True)
    desvios_baixa.to_csv('desvio_padrao_variacao_percentual_baixa.csv', header=['Desvio Padrão Baixa'], index=True)

    print("Análise concluída. Tendências e métricas exportadas para os arquivos CSV.")

# Caminho para a pasta de arquivos
pasta_path = "./newFiles"  # Substitua pelo caminho correto para sua pasta

# Executando as análises
executar_analises(pasta_path)
