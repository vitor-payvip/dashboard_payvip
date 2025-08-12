# tabs/vendas.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar
from functions.fc_dash_vendas import dados_dashboard_principal
from tabs.utils import gerar_grid_html, cores_payvip  # <<< MUDANÇA: IMPORTA DE UTILS


def render(people_id):
    st.markdown("##### Resumo das Vendas")
    col_filtro1, col_filtro2 = st.columns([1, 3])
    with col_filtro1:
        hoje = datetime.now().date()
        primeiro_dia_mes = hoje.replace(day=1)
        datas_selecionadas = st.date_input("Selecione o Período", value=(primeiro_dia_mes, hoje), max_value=hoje,key="filtro_vendas")

    if len(datas_selecionadas) == 2:
        data_inicio, data_fim = datas_selecionadas
        if (data_fim - data_inicio).days > 31:
            st.error("O período selecionado não pode ser maior que 31 dias.")
            return
    else:
        data_inicio, data_fim = primeiro_dia_mes, hoje

    start_date_str = datetime.combine(data_inicio, datetime.min.time()).strftime('%Y-%m-%d %H:%M:%S')
    end_date_str = datetime.combine(data_fim, datetime.max.time()).strftime('%Y-%m-%d %H:%M:%S')

    try:
        with st.spinner("Buscando dados de vendas..."):
            df_pedidos, df_transacoes = dados_dashboard_principal(people_id=people_id, start_date=start_date_str,
                                                                  end_date=end_date_str)
    except Exception as e:
        st.error(f"Ocorreu um erro ao buscar os dados de vendas: {e}")
        return

    if df_transacoes is not None and not df_transacoes.empty:
        df_transacoes.columns = df_transacoes.columns.str.strip().str.lower()
        if df_pedidos is not None:
            df_pedidos.columns = df_pedidos.columns.str.strip().str.lower()
        df_transacoes['amount'] = pd.to_numeric(df_transacoes['amount'], errors='coerce').fillna(0)
        df_transacoes['created_at_gmt_minus_3'] = pd.to_datetime(df_transacoes['created_at_gmt_minus_3'],
                                                                 errors='coerce')
        df_aprovadas_seller = df_transacoes[
            (df_transacoes['status'] == 'Aprovada') & (df_transacoes['seller_principal'] == 'S')].copy()
        total_pedidos = len(df_pedidos) if df_pedidos is not None else 0
        total_transacoes = len(df_aprovadas_seller)
        vendas_aprovadas = df_aprovadas_seller['amount'].sum()
        vendas_payvip = df_aprovadas_seller[df_aprovadas_seller['entry_mode'] != 'outros']['amount'].sum()
        vendas_outros = vendas_aprovadas - vendas_payvip
        ticket_medio = vendas_aprovadas / total_transacoes if total_transacoes > 0 else 0

        def formatar_moeda(valor):
            return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        cols_kpi = st.columns(6)
        cols_kpi[0].metric(label="Total Pedidos", value=f"{total_pedidos:,}".replace(",", "."))
        cols_kpi[1].metric(label="Total Transações", value=f"{total_transacoes:,}".replace(",", "."))
        cols_kpi[2].metric(label="Vendas Aprovadas", value=formatar_moeda(vendas_aprovadas))
        cols_kpi[3].metric(label="Vendas PayVip", value=formatar_moeda(vendas_payvip))
        cols_kpi[4].metric(label="Vendas Outros Métodos", value=formatar_moeda(vendas_outros))
        cols_kpi[5].metric(label="Ticket Médio", value=formatar_moeda(ticket_medio))
        st.divider()

        col_graficos, col_grid = st.columns([2, 3])
        with col_graficos:
            with st.container(border=True):
                col_donut1, col_donut2 = st.columns(2)
                with col_donut1:
                    st.markdown("<h6>Vendas por Método</h6>", unsafe_allow_html=True)
                    conditions = [df_aprovadas_seller['product_capture'] == 'Crédito 1x',
                                  df_aprovadas_seller['product_capture'].str.startswith('Crédito', na=False)]
                    choices = ['Crédito à Vista', 'Crédito Parcelado']
                    df_aprovadas_seller['metodo_simplificado'] = np.select(conditions, choices,
                                                                           default=df_aprovadas_seller[
                                                                               'product_capture'])
                    df_grafico = df_aprovadas_seller.groupby('metodo_simplificado')['amount'].sum().reset_index()
                    fig = px.pie(df_grafico, values='amount', names='metodo_simplificado', hole=0.6,
                                 color_discrete_sequence=[cores_payvip["roxo"], cores_payvip["laranja"],
                                                          cores_payvip["cinza"], "#AAB2BD", "#C5CDE0"])
                    fig.update_traces(textinfo='percent', textfont_size=14)
                    fig.update_layout(showlegend=True,
                                      legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5),
                                      margin=dict(t=20, b=20, l=20, r=20), height=300)
                    st.plotly_chart(fig, use_container_width=True, key="vendas_donut_metodo")
                with col_donut2:
                    st.markdown("<h6>Status das Transações</h6>", unsafe_allow_html=True)
                    df_grafico = df_transacoes[df_transacoes['seller_principal'] == 'S'].groupby('status')[
                        'amount'].sum().reset_index()
                    mapa_cores = {'Aprovada': cores_payvip["roxo"], 'Cancelada': cores_payvip["laranja"],
                                  'Estornada': cores_payvip["cinza"], 'Chargeback': '#B22222'}
                    fig = px.pie(df_grafico, values='amount', names='status', hole=0.6, color='status',
                                 color_discrete_map=mapa_cores)
                    fig.update_traces(textinfo='percent', textfont_size=14)
                    fig.update_layout(showlegend=True,
                                      legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5),
                                      margin=dict(t=20, b=20, l=20, r=20), height=300)
                    st.plotly_chart(fig, use_container_width=True, key="vendas_donut_status")
                st.markdown("<h6 style='margin-top: 20px;'>Volume de Vendas Diário</h6>", unsafe_allow_html=True)
                df_vendas_diario = df_aprovadas_seller.groupby(df_aprovadas_seller['created_at_gmt_minus_3'].dt.date)[
                    'amount'].sum().reset_index()
                df_vendas_diario.columns = ['data', 'valor']
                idx = pd.date_range(start=data_inicio, end=data_fim, freq='D')
                df_completo = pd.DataFrame(idx, columns=['data'])
                df_completo['data'] = df_completo['data'].dt.date
                df_grafico_final = pd.merge(df_completo, df_vendas_diario, on='data', how='left').fillna(0)
                num_dias = len(df_grafico_final)
                largura_grafico = max(600, num_dias * 35)
                fig = go.Figure(
                    go.Bar(x=df_grafico_final['data'], y=df_grafico_final['valor'], marker_color=cores_payvip["roxo"]))
                fig.update_layout(title_text=None, plot_bgcolor='rgba(0,0,0,0)',
                                  yaxis=dict(showgrid=False, visible=False), bargap=0.4,
                                  margin=dict(t=10, b=0, l=0, r=0), height=250, width=largura_grafico,
                                  xaxis=dict(showline=False, tickformat="%d/%m", tickmode='linear', tickangle=-45))
                st.markdown(f'<div style="overflow-x: auto; width: 100%;">', unsafe_allow_html=True)
                st.plotly_chart(fig, key="vendas_bar_diario")
                st.markdown('</div>', unsafe_allow_html=True)
        with col_grid:
            with st.container(border=True):
                st.markdown('<div class="card-title">LISTA DE TRANSAÇÕES</div>', unsafe_allow_html=True)
                filtro_cliente = st.text_input("Filtrar por cliente:", placeholder="Digite o nome do cliente...",
                                               key="vendas_filtro_cliente")
                df_transacoes_filtrado = df_transacoes
                if filtro_cliente:
                    df_transacoes_filtrado = df_transacoes[
                        df_transacoes['product_name'].str.contains(filtro_cliente, case=False, na=False)]

                ITEMS_PER_PAGE = 5
                total_items = len(df_transacoes_filtrado)
                total_pages = (total_items - 1) // ITEMS_PER_PAGE + 1 if total_items > 0 else 1
                if st.session_state.page_number >= total_pages:
                    st.session_state.page_number = 0
                start_idx = st.session_state.page_number * ITEMS_PER_PAGE
                end_idx = start_idx + ITEMS_PER_PAGE
                df_paginada = df_transacoes_filtrado.iloc[start_idx:end_idx]
                grid_html = gerar_grid_html(df_paginada)
                st.html(grid_html)
                if total_pages > 1:
                    st.markdown("<br>", unsafe_allow_html=True)
                    p_cols = st.columns([1, 2, 1])
                    with p_cols[0]:
                        if st.button("Anterior", use_container_width=True,
                                     disabled=(st.session_state.page_number == 0)):
                            st.session_state.page_number -= 1
                            st.rerun()
                    with p_cols[1]:
                        st.markdown(
                            f"<div style='text-align: center; margin-top: 5px;'>Página {st.session_state.page_number + 1} de {total_pages}</div>",
                            unsafe_allow_html=True)
                    with p_cols[2]:
                        if st.button("Próximo", use_container_width=True,
                                     disabled=(st.session_state.page_number >= total_pages - 1)):
                            st.session_state.page_number += 1
                            st.rerun()
    else:
        st.warning("Não há dados de vendas para o período selecionado.")