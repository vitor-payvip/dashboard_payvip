# tabs/gestao_pedidos.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from functions.fc_dash_vendas import dados_gestao_pedidos
from tabs.utils import cores_payvip

# --- FUNÇÃO HELPER PARA FORMATAR VALORES DO GRÁFICO ---
def formatar_valor_abreviado(valor):
    if valor >= 1000000:
        return f"R$ {valor / 1000000:,.2f} Mi".replace(",", ".")
    if valor >= 1000:
        return f"R$ {valor / 1000:,.0f} Mil".replace(",", ".")
    return f"R$ {valor:,.0f}".replace(",", ".")


# --- FUNÇÃO PRINCIPAL DE RENDERIZAÇÃO DA ABA ---
def render(people_id):
    st.markdown("##### Gestão de Pedidos")

    col_filtro1, col_filtro2 = st.columns([1, 3])
    with col_filtro1:
        hoje = datetime.now().date()
        primeiro_dia_mes = hoje.replace(day=1)
        datas_selecionadas = st.date_input(
            "Selecione o Período",
            value=(primeiro_dia_mes, hoje),
            max_value=hoje,
            key="filtro_gestao_pedidos"
        )

    if len(datas_selecionadas) == 2:
        data_inicio, data_fim = datas_selecionadas
        if (data_fim - data_inicio).days > 180:
            st.error("O período selecionado não pode ser maior que 180 dias.")
            return
    else:
        data_inicio, data_fim = primeiro_dia_mes, hoje

    start_date_str = datetime.combine(data_inicio, datetime.min.time()).strftime('%Y-%m-%d %H:%M:%S')
    end_date_str = datetime.combine(data_fim, datetime.max.time()).strftime('%Y-%m-%d %H:%M:%S')

    try:
        with st.spinner("Buscando dados de pedidos..."):
            df_pedidos, df_itens_pedidos = dados_gestao_pedidos(
                people_id=people_id,
                start_date=start_date_str,
                end_date=end_date_str
            )
    except Exception as e:
        st.error(f"Ocorreu um erro ao buscar os dados de pedidos: {e}")
        return

    if df_pedidos is not None and not df_pedidos.empty:
        df_pedidos.columns = df_pedidos.columns.str.strip().str.lower()

        value_cols = ['value', 'value_paid', 'value_pending', 'total_split']
        for col in value_cols:
            if col in df_pedidos.columns:
                df_pedidos[col] = pd.to_numeric(df_pedidos[col], errors='coerce').fillna(0)

        df_concluidos = df_pedidos[df_pedidos['status'] == 'PGCON'].copy()
        df_parciais = df_pedidos[df_pedidos['status'] == 'PGPAG'].copy()
        df_repassados = df_pedidos[df_pedidos['status'].isin(['PGCON', 'PGPAG'])].copy()

        total_pedidos_concluidos = len(df_concluidos)
        valor_vendas_concluidas = df_concluidos['value'].sum()
        total_pedidos_parciais = len(df_parciais)
        valor_pago_parcialmente = df_parciais['value_paid'].sum()
        valor_pendente_receber = df_parciais['value_pending'].sum()
        total_repassado = df_repassados['total_split'].sum()

        def formatar_moeda(valor):
            return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        st.divider()

        kpi_cols1 = st.columns(3)
        kpi_cols1[0].metric(label="Total Pedidos Concluídos", value=f"{total_pedidos_concluidos:,}".replace(",", "."))
        kpi_cols1[1].metric(label="Valor Vendas Concluídas", value=formatar_moeda(valor_vendas_concluidas))
        kpi_cols1[2].metric(label="Total Repassado", value=formatar_moeda(total_repassado))

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

        kpi_cols2 = st.columns(3)
        kpi_cols2[0].metric(label="Pedidos Pagos Parcialmente", value=f"{total_pedidos_parciais:,}".replace(",", "."))
        kpi_cols2[1].metric(label="Valor Pago Parcialmente", value=formatar_moeda(valor_pago_parcialmente))
        kpi_cols2[2].metric(label="Valor Pendente a Receber", value=formatar_moeda(valor_pendente_receber))

        st.divider()

        if df_itens_pedidos is not None and not df_itens_pedidos.empty:
            df_itens_pedidos.columns = df_itens_pedidos.columns.str.strip().str.lower()
            df_itens_pedidos['value_discount'] = pd.to_numeric(df_itens_pedidos['value_discount'],
                                                               errors='coerce').fillna(0)

            # <<< CORREÇÃO APLICADA AQUI >>>
            # Seleciona as colunas do df_pedidos para o merge
            df_pedidos_para_merge = df_pedidos[['document_id', 'status']].copy()

            # Faz o merge, adicionando sufixos para diferenciar as colunas 'status'
            df_itens_completo = pd.merge(
                df_itens_pedidos,
                df_pedidos_para_merge,
                on='document_id',
                how='left',
                suffixes=('_item', '_pedido')  # Adiciona sufixos
            )

            # Agora, a coluna de status do pedido se chama 'status_pedido'
            # Filtra os itens com base no status do pedido correspondente
            df_itens_concluidos = df_itens_completo[df_itens_completo['status_pedido'] == 'PGCON'].copy()

            col_grafico1, col_grafico2 = st.columns(2)

            with col_grafico1:
                with st.container(border=True, height=500):
                    st.markdown("<h6>Faturamento por Profissional</h6>", unsafe_allow_html=True)

                    df_faturamento_prof = df_itens_concluidos.groupby('alias_name')[
                        'value_discount'].sum().reset_index()
                    df_faturamento_prof = df_faturamento_prof.sort_values('value_discount',
                                                                          ascending=False).reset_index(drop=True)
                    df_faturamento_prof['texto_valor'] = df_faturamento_prof['value_discount'].apply(
                        formatar_valor_abreviado)

                    fig_prof = go.Figure(go.Bar(
                        x=df_faturamento_prof['value_discount'],
                        y=df_faturamento_prof['alias_name'],
                        text=df_faturamento_prof['texto_valor'],
                        textposition='outside', orientation='h', marker_color=cores_payvip["roxo"]
                    ))
                    fig_prof.update_layout(
                        title_text=None, plot_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
                        yaxis=dict(autorange="reversed"), bargap=0.4,
                        height=len(df_faturamento_prof) * 35 + 50,
                        margin=dict(l=150, r=20, t=10, b=20)
                    )
                    st.plotly_chart(fig_prof, use_container_width=True)

            with col_grafico2:
                with st.container(border=True, height=500):
                    st.markdown("<h6>Faturamento por Produto/Serviço</h6>", unsafe_allow_html=True)

                    df_faturamento_prod = df_itens_concluidos.groupby('description')[
                        'value_discount'].sum().reset_index()
                    df_faturamento_prod = df_faturamento_prod.sort_values('value_discount',
                                                                          ascending=False).reset_index(drop=True)
                    df_faturamento_prod['texto_valor'] = df_faturamento_prod['value_discount'].apply(
                        formatar_valor_abreviado)

                    fig_prod = go.Figure(go.Bar(
                        x=df_faturamento_prod['value_discount'],
                        y=df_faturamento_prod['description'],
                        text=df_faturamento_prod['texto_valor'],
                        textposition='outside', orientation='h', marker_color=cores_payvip["roxo"]
                    ))
                    fig_prod.update_layout(
                        title_text=None, plot_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
                        yaxis=dict(autorange="reversed"), bargap=0.4,
                        height=len(df_faturamento_prod) * 35 + 50,
                        margin=dict(l=150, r=20, t=10, b=20)
                    )
                    st.plotly_chart(fig_prod, use_container_width=True)

    else:
        st.warning("Não há dados de pedidos para o período selecionado.")