# functions/fc_dash_vendas.py

import streamlit as st
from google.cloud import bigquery
import pandas as pd

# A inicialização do cliente pode ficar fora das funções,
# pois só precisa ser feita uma vez.
client = bigquery.Client()


# --- FUNÇÕES DE BUSCA DE DADOS (COM CACHE) ---
# Estas são as funções que realmente acessam o banco de dados.
# Aplicamos o cache aqui para que qualquer chamada a elas com os mesmos
# parâmetros retorne o resultado guardado, sem fazer uma nova query.

@st.cache_data
def dados_pedidos(people_id, start_date, end_date):
    """Busca todos os pedidos (concluídos) no período."""
    query = """
        SELECT *
        FROM payvip_database.vw_order 
        WHERE created_at_gmt_minus_3 BETWEEN @start_date AND @end_date
          AND people_id_conciliation = @people_id
          AND status IN ('PGCON')
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "TIMESTAMP", start_date),
            bigquery.ScalarQueryParameter("end_date", "TIMESTAMP", end_date),
            bigquery.ScalarQueryParameter("people_id", "STRING", people_id),
        ]
    )
    df_orders = client.query(query, job_config=job_config).to_dataframe()
    return df_orders


@st.cache_data
def dados_pedidos_total(people_id, start_date, end_date):
    """Busca todos os pedidos (todos os status) no período."""
    query = """
        SELECT *
        FROM payvip_database.vw_order 
        WHERE created_at_gmt_minus_3 BETWEEN @start_date AND @end_date
          AND people_id_conciliation = @people_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "TIMESTAMP", start_date),
            bigquery.ScalarQueryParameter("end_date", "TIMESTAMP", end_date),
            bigquery.ScalarQueryParameter("people_id", "STRING", people_id),
        ]
    )
    df_orders = client.query(query, job_config=job_config).to_dataframe()
    return df_orders


@st.cache_data
def dados_pedidos_itens_total(people_id, start_date, end_date):
    """Busca todos os itens de pedidos no período."""
    query = """
        SELECT oi.*, p.alias_name
        FROM payvip_database.vw_order_itens AS oi
        LEFT JOIN `payvip_database.vw_peoples` AS p
          ON oi.people_id = p.people_id
        WHERE oi.responsible_id = @people_id
          AND oi.created_at_gmt_minus_3 BETWEEN @start_date AND @end_date
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "TIMESTAMP", start_date),
            bigquery.ScalarQueryParameter("end_date", "TIMESTAMP", end_date),
            bigquery.ScalarQueryParameter("people_id", "STRING", people_id),
        ]
    )
    df_orders_itens_total = client.query(query, job_config=job_config).to_dataframe()
    return df_orders_itens_total


@st.cache_data
def dados_transacoes(people_id, start_date, end_date):
    """Busca todas as transações no período."""
    query = """
        SELECT *
        FROM payvip_database.vw_transactions_split
        WHERE created_at_gmt_minus_3 BETWEEN @start_date AND @end_date
          AND people_id_conciliation = @people_id
          AND seller_principal = 'S'
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "TIMESTAMP", start_date),
            bigquery.ScalarQueryParameter("end_date", "TIMESTAMP", end_date),
            bigquery.ScalarQueryParameter("people_id", "STRING", people_id),
        ]
    )
    df_transactions = client.query(query, job_config=job_config).to_dataframe()
    return df_transactions


# --- FUNÇÕES ORQUESTRADORAS (SEM CACHE) ---
# Estas funções não precisam de cache, pois as funções que elas chamam já estão cacheadas.
# Elas apenas organizam as chamadas de dados para cada aba.

def dados_dashboard_principal(people_id, start_date, end_date):
    """Prepara os dados para a aba principal de Vendas."""
    # Usa a função que busca todos os status de pedidos
    df_pedidos = dados_pedidos_total(people_id, start_date, end_date)
    df_transacoes = dados_transacoes(people_id, start_date, end_date)
    return df_pedidos, df_transacoes


def dados_kpi(people_id, year_date):
    """Prepara os dados para a aba de KPI (ano inteiro)."""
    start_date = f"{year_date}-01-01 00:00:00"
    end_date = f"{year_date}-12-31 23:59:59"

    # Usa a função que busca todos os status de pedidos
    df_pedidos = dados_pedidos_total(people_id, start_date, end_date)
    df_transacoes = dados_transacoes(people_id, start_date, end_date)
    return df_pedidos, df_transacoes


def dados_gestao_pedidos(people_id, start_date, end_date):
    """Prepara os dados para a aba de Gestão de Pedidos."""
    # Usa a função que busca todos os status de pedidos
    df_pedidos = dados_pedidos_total(people_id, start_date, end_date)
    df_itens_pedido = dados_pedidos_itens_total(people_id, start_date, end_date)
    return df_pedidos, df_itens_pedido
