# tabs/kpi.py

import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
from functions.fc_dash_vendas import dados_kpi

# <<< MUDANÇA: DICIONÁRIO COM OS TEXTOS DOS TOOLTIPS >>>
# Centraliza todos os textos explicativos em um único lugar para fácil manutenção.
TOOLTIPS = {
    "total_pedidos_acumulado": "Soma de todos os pedidos criados desde o início do ano até o final do mês selecionado.",
    "gmv_meta_acumulada": "Gross Merchandise Volume (GMV) é o valor total de vendas. Esta é a soma das metas mensais de GMV para o período acumulado.",
    "gmv_real_acumulado": "Soma do valor total de todos os pedidos concluídos (status 'Pagamento Concluído') no período acumulado.",
    "aderencia_gmv_acumulada": "Percentual do GMV Realizado em relação à Meta de GMV para o período acumulado. (Real / Meta) * 100.",

    "total_pedidos_mes": "Total de pedidos criados dentro do mês de referência selecionado.",
    "gmv_meta_mes": "Meta de Gross Merchandise Volume (GMV) definida para o mês de referência selecionado.",
    "gmv_real_mes": "Soma do valor total de todos os pedidos concluídos (status 'Pagamento Concluído') dentro do mês de referência.",
    "aderencia_gmv_mes": "Percentual do GMV Realizado em relação à Meta de GMV para o mês de referência. (Real / Meta) * 100.",

    "qtd_transacoes_acumulado": "Soma de todas as transações realizadas desde o início do ano até o final do mês selecionado.",
    "tpv_meta_acumulada": "Total Payment Volume (TPV) é o valor total processado em transações. Esta é a soma das metas mensais de TPV para o período acumulado.",
    "tpv_real_acumulado": "Soma do valor de todas as transações processadas no período acumulado.",
    "aderencia_tpv_acumulada": "Percentual do TPV Realizado em relação à Meta de TPV para o período acumulado. (Real / Meta) * 100.",

    "qtd_transacoes_mes": "Total de transações realizadas dentro do mês de referência selecionado.",
    "tpv_meta_mes": "Meta de Total Payment Volume (TPV) definida para o mês de referência selecionado.",
    "tpv_real_mes": "Soma do valor de todas as transações processadas dentro do mês de referência.",
    "aderencia_tpv_mes": "Percentual do TPV Realizado em relação à Meta de TPV para o mês de referência. (Real / Meta) * 100."
}


# --- FUNÇÃO PRINCIPAL DE RENDERIZAÇÃO DA ABA ---
def render(people_id, gmv_metas, tpv_metas):
    st.markdown("##### Acompanhamento de Metas (KPI)")

    lista_meses_meta = sorted(gmv_metas.keys(), key=lambda x: datetime.strptime(x, "%m/%Y"), reverse=True)
    if not lista_meses_meta:
        st.warning("Nenhuma meta de KPI encontrada para este usuário.")
        return

    mes_atual_str = datetime.now().strftime("%m/%Y")
    try:
        default_index = lista_meses_meta.index(mes_atual_str)
    except ValueError:
        default_index = 0

    mes_selecionado_kpi = st.selectbox("Selecione o Mês da Meta", options=lista_meses_meta, index=default_index)

    ano_kpi = int(mes_selecionado_kpi.split('/')[1])
    try:
        with st.spinner(f"Buscando dados de KPI para o ano de {ano_kpi}..."):
            df_pedidos_kpi_ano, df_transacoes_kpi_ano = dados_kpi(people_id=people_id, year_date=str(ano_kpi))
    except Exception as e:
        st.error(f"Ocorreu um erro ao buscar os dados de KPI: {e}")
        return

    if df_pedidos_kpi_ano is not None and not df_pedidos_kpi_ano.empty and df_transacoes_kpi_ano is not None and not df_transacoes_kpi_ano.empty:
        df_pedidos_kpi_ano.columns = df_pedidos_kpi_ano.columns.str.strip().str.lower()
        df_pedidos_kpi_ano['total_amount'] = pd.to_numeric(df_pedidos_kpi_ano['total_amount'], errors='coerce').fillna(
            0)
        df_pedidos_kpi_ano['created_at_gmt_minus_3'] = pd.to_datetime(df_pedidos_kpi_ano['created_at_gmt_minus_3'],
                                                                      errors='coerce').dt.tz_localize(None)

        df_transacoes_kpi_ano.columns = df_transacoes_kpi_ano.columns.str.strip().str.lower()
        df_transacoes_kpi_ano['amount'] = pd.to_numeric(df_transacoes_kpi_ano['amount'], errors='coerce').fillna(0)
        df_transacoes_kpi_ano['created_at_gmt_minus_3'] = pd.to_datetime(
            df_transacoes_kpi_ano['created_at_gmt_minus_3'], errors='coerce').dt.tz_localize(None)

        mes_num, ano_num = map(int, mes_selecionado_kpi.split('/'))
        start_date_mes = datetime(ano_num, mes_num, 1)
        end_date_mes = start_date_mes.replace(day=calendar.monthrange(ano_num, mes_num)[1])
        start_date_acumulado = datetime(ano_num, 1, 1)
        end_date_acumulado = end_date_mes

        df_pedidos_mes = df_pedidos_kpi_ano[df_pedidos_kpi_ano['created_at_gmt_minus_3'].between(start_date_mes,
                                                                                                 end_date_mes.replace(
                                                                                                     hour=23, minute=59,
                                                                                                     second=59))]
        df_pedidos_acumulado = df_pedidos_kpi_ano[
            df_pedidos_kpi_ano['created_at_gmt_minus_3'].between(start_date_acumulado,
                                                                 end_date_acumulado.replace(hour=23, minute=59,
                                                                                            second=59))]
        df_transacoes_mes = df_transacoes_kpi_ano[
            df_transacoes_kpi_ano['created_at_gmt_minus_3'].between(start_date_mes,
                                                                    end_date_mes.replace(hour=23, minute=59,
                                                                                         second=59))]
        df_transacoes_acumulado = df_transacoes_kpi_ano[
            df_transacoes_kpi_ano['created_at_gmt_minus_3'].between(start_date_acumulado,
                                                                    end_date_acumulado.replace(hour=23, minute=59,
                                                                                               second=59))]

        def formatar_moeda(valor):
            return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        total_pedidos_acumulado = len(df_pedidos_acumulado)
        gmv_meta_acumulada = sum(v for k, v in gmv_metas.items() if datetime.strptime(k, "%m/%Y") <= end_date_mes)
        gmv_real_acumulado = df_pedidos_acumulado['total_amount'].sum()
        aderencia_gmv_acumulada = (gmv_real_acumulado / gmv_meta_acumulada * 100) if gmv_meta_acumulada > 0 else 0
        total_pedidos_mes = len(df_pedidos_mes)
        gmv_meta_mes = gmv_metas.get(mes_selecionado_kpi, 0)
        gmv_real_mes = df_pedidos_mes['total_amount'].sum()
        aderencia_gmv_mes = (gmv_real_mes / gmv_meta_mes * 100) if gmv_meta_mes > 0 else 0

        qtd_transacoes_acumulado = len(df_transacoes_acumulado)
        tpv_meta_acumulada = sum(v for k, v in tpv_metas.items() if datetime.strptime(k, "%m/%Y") <= end_date_mes)
        tpv_real_acumulado = df_transacoes_acumulado['amount'].sum()
        aderencia_tpv_acumulada = (tpv_real_acumulado / tpv_meta_acumulada * 100) if tpv_meta_acumulada > 0 else 0
        qtd_transacoes_mes = len(df_transacoes_mes)
        tpv_meta_mes = tpv_metas.get(mes_selecionado_kpi, 0)
        tpv_real_mes = df_transacoes_mes['amount'].sum()
        aderencia_tpv_mes = (tpv_real_mes / tpv_meta_mes * 100) if tpv_meta_mes > 0 else 0

        st.markdown("<h6>GMV Acumulado no Ano</h6>", unsafe_allow_html=True)
        kpi_cols1 = st.columns(4)
        with kpi_cols1[0]:
            st.metric(label="Total Pedidos Acumulado", value=f"{total_pedidos_acumulado:,}".replace(",", "."),
                      help=TOOLTIPS["total_pedidos_acumulado"])
        with kpi_cols1[1]:
            st.metric(label="GMV Meta Acumulada (R$)", value=formatar_moeda(gmv_meta_acumulada),
                      help=TOOLTIPS["gmv_meta_acumulada"])
        with kpi_cols1[2]:
            st.metric(label="GMV Real Acumulado (R$)", value=formatar_moeda(gmv_real_acumulado),
                      help=TOOLTIPS["gmv_real_acumulado"])
        with kpi_cols1[3]:
            st.metric(label="Aderência ao GMV (%)", value=f"{aderencia_gmv_acumulada:.2f}%",
                      help=TOOLTIPS["aderencia_gmv_acumulada"])

        st.markdown("<h6 style='margin-top:15px'>GMV Mês de Referência</h6>", unsafe_allow_html=True)
        kpi_cols2 = st.columns(4)
        with kpi_cols2[0]:
            st.metric(label="Total Pedidos Mês", value=f"{total_pedidos_mes:,}".replace(",", "."),
                      help=TOOLTIPS["total_pedidos_mes"])
        with kpi_cols2[1]:
            st.metric(label="GMV Meta Mês (R$)", value=formatar_moeda(gmv_meta_mes), help=TOOLTIPS["gmv_meta_mes"])
        with kpi_cols2[2]:
            st.metric(label="GMV Real Mês (R$)", value=formatar_moeda(gmv_real_mes), help=TOOLTIPS["gmv_real_mes"])
        with kpi_cols2[3]:
            st.metric(label="Aderência ao GMV (%)", value=f"{aderencia_gmv_mes:.2f}%",
                      help=TOOLTIPS["aderencia_gmv_mes"])

        st.divider()

        st.markdown("<h6>TPV Acumulado no Ano</h6>", unsafe_allow_html=True)
        kpi_cols3 = st.columns(4)
        with kpi_cols3[0]:
            st.metric(label="Qtd. Transações Acumulado", value=f"{qtd_transacoes_acumulado:,}".replace(",", "."),
                      help=TOOLTIPS["qtd_transacoes_acumulado"])
        with kpi_cols3[1]:
            st.metric(label="TPV Meta Acumulada (R$)", value=formatar_moeda(tpv_meta_acumulada),
                      help=TOOLTIPS["tpv_meta_acumulada"])
        with kpi_cols3[2]:
            st.metric(label="TPV Real Acumulado (R$)", value=formatar_moeda(tpv_real_acumulado),
                      help=TOOLTIPS["tpv_real_acumulado"])
        with kpi_cols3[3]:
            st.metric(label="Aderência ao TPV (%)", value=f"{aderencia_tpv_acumulada:.2f}%",
                      help=TOOLTIPS["aderencia_tpv_acumulada"])

        st.markdown("<h6 style='margin-top:15px'>TPV Mês de Referência</h6>", unsafe_allow_html=True)
        kpi_cols4 = st.columns(4)
        with kpi_cols4[0]:
            st.metric(label="Qtd. Transações Mês", value=f"{qtd_transacoes_mes:,}".replace(",", "."),
                      help=TOOLTIPS["qtd_transacoes_mes"])
        with kpi_cols4[1]:
            st.metric(label="TPV Meta Mês (R$)", value=formatar_moeda(tpv_meta_mes), help=TOOLTIPS["tpv_meta_mes"])
        with kpi_cols4[2]:
            st.metric(label="TPV Real Mês (R$)", value=formatar_moeda(tpv_real_mes), help=TOOLTIPS["tpv_real_mes"])
        with kpi_cols4[3]:
            st.metric(label="Aderência ao TPV (%)", value=f"{aderencia_tpv_mes:.2f}%",
                      help=TOOLTIPS["aderencia_tpv_mes"])

    else:
        st.warning(f"Não há dados de KPI para o ano de {ano_kpi}.")