import sys
import os
import streamlit as st
from google.cloud import firestore

CREDENTIALS_PATH = "gcp-credentials.json"



# Adiciona a pasta raiz do projeto ao caminho do Python
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

# --- IMPORTAÇÕES ---
try:
    from tabs import vendas, kpi, gestao_pedidos
except ImportError as e:
    st.error(f"Erro de importação: {e}. Verifique a estrutura de pastas e os arquivos.")
    st.stop()

# --- CONFIGURAÇÃO DA PÁGINA E ESTILOS ---
st.set_page_config(page_title="Dashboard de Vendas", layout="wide")
st.markdown("""
<style>
    header, [data-testid="stSidebar"], footer, button[title="View big"] { display: none; visibility: hidden; }
    .main .block-container { padding-top: 0rem; padding-bottom: 1rem; padding-left: 2.5rem; padding-right: 2.5rem; }
    div[data-testid="metric-container"] { background-color: #FFFFFF; border: 1px solid #E6E6E6; border-radius: 10px; padding: 15px 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.04); height: 100%; }
    div[data-testid="metric-container"] > label { font-size: 0.85rem; font-weight: 600; color: #4A5568; }
    div[data-testid="metric-container"] > div > div > div { font-size: 1.6rem; font-weight: 700; color: #4A3A75; }
    button[data-testid="stTab"] { font-size: 16px; font-weight: 600; padding: 10px 15px; }
    .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
    .card-title { font-size: 1rem; font-weight: 600; color: #5A6372; display: flex; align-items: center; }
    .card-title::before { content: ''; display: block; width: 4px; height: 18px; background-color: #4A3A75; margin-right: 10px; }
    .grid-container { display: flex; flex-direction: column; }
    .grid-row { display: grid; grid-template-columns: 1fr 2fr 2.5fr 1.5fr 1.2fr; gap: 15px; align-items: center; padding: 12px 5px; border-bottom: 1px solid #F0F2F6; font-size: 0.85rem; }
    .grid-header-row { color: #878787; font-weight: 600; border-bottom: 2px solid #F0F2F6; }
    .grid-col { display: flex; flex-direction: column; justify-content: center; }
    .grid-col.valor { text-align: right; font-weight: 600; }
    .status-text { font-weight: 700; font-size: 0.7rem; margin-bottom: 4px; }
    .status-Aprovada { color: #28a745; }
    .status-Cancelada { color: #dc3545; }
    .status-Chargeback { color: #ffc107; }
    .status-Estornada { color: #6c757d; }
    .client-name { font-weight: 600; color: #333; }
    .client-cnpj { font-size: 0.8rem; color: #878787; }
</style>
""", unsafe_allow_html=True)

# --- LÓGICA PRINCIPAL DE ORQUESTRAÇÃO ---
people_id = st.query_params.get("people_id")

if not people_id:
    st.error("Parâmetro 'people_id' não encontrado na URL.")
    st.stop()

exibe_kpi = False
exibe_gestao_pedidos = False
gmv_metas = {}
tpv_metas = {}
try:
    # Inicializa o cliente explicitamente com as credenciais
    db = firestore.Client.from_service_account_json(CREDENTIALS_PATH)

    people_doc = db.collection('peoples').document(people_id).get()
    # ... (resto da lógica do Firestore) ...
except FileNotFoundError:
    # Se o arquivo não for encontrado, tenta a autenticação padrão
    db = firestore.Client()
    people_doc = db.collection('peoples').document(people_id).get()
    # ... (copie a lógica de processamento do people_doc aqui também) ...
except Exception as e:
    st.error(f"Erro ao buscar dados no Firestore: {e}")
    st.stop()
"""
try:
    db = firestore.Client()
    people_doc = db.collection('peoples').document(people_id).get()
    if people_doc.exists:
        people_data = people_doc.to_dict()

        if people_data.get("kpi_control") == "S":
            exibe_kpi = True
            kpis_data = people_data.get('kpis', [{}])[0]
            for item in kpis_data.get('GMV', []): gmv_metas.update(item)
            for item in kpis_data.get('TPV', []): tpv_metas.update(item)

        if people_data.get("dashboard_order_control") == "S":
            exibe_gestao_pedidos = True

except Exception as e:
    st.error(f"Erro ao buscar dados no Firestore: {e}")
    st.stop()
"""

if 'page_number' not in st.session_state:
    st.session_state.page_number = 0

tab_names = ["Vendas"]
# <<< MUDANÇA: A ORDEM FOI ALTERADA AQUI >>>
if exibe_gestao_pedidos:
    tab_names.append("Gestão de Pedidos")
if exibe_kpi:
    tab_names.append("KPI")

if len(tab_names) > 1:
    tabs = st.tabs(tab_names)

    # Renderiza a aba Vendas (sempre a primeira)
    with tabs[0]:
        vendas.render(people_id)

    # Renderiza a aba Gestão de Pedidos, se existir
    if exibe_gestao_pedidos:
        with tabs[tab_names.index("Gestão de Pedidos")]:
            gestao_pedidos.render(people_id)

    # Renderiza a aba KPI, se existir
    if exibe_kpi:
        with tabs[tab_names.index("KPI")]:
            kpi.render(people_id, gmv_metas, tpv_metas)
else:
    # Caso apenas a aba de Vendas seja exibida
    st.markdown('<style>.stTabs { display: none; }</style>', unsafe_allow_html=True)
    vendas.render(people_id)