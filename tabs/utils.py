# tabs/utils.py

import pandas as pd

# Paleta de cores compartilhada
cores_payvip = {"roxo": "#4A3A75", "laranja": "#DB563F", "cinza": "#878787"}


# Função de grid HTML compartilhada
def gerar_grid_html(df_para_mostrar):
    html_parts = [
        '<div class="grid-container">',
        '<div class="grid-row grid-header-row"><div>Data</div><div>ID da Transação</div><div>Cliente</div><div>Tipo</div><div class="valor">Valor</div></div>'
    ]
    for _, row in df_para_mostrar.iterrows():
        try:
            data_obj = pd.to_datetime(row.get('created_at_gmt_minus_3', ''))
            data_str = data_obj.strftime('%d/%m/%Y')
            hora_str = data_obj.strftime('%H:%M:%S')
        except (ValueError, TypeError):
            data_str, hora_str = "Data inválida", ""

        id_str = str(row.get('transaction_id', 'N/A'))
        status_str = str(row.get('status', 'N/A'))
        status_class = f"status-{status_str.replace(' ', '')}"

        cliente_nome = str(row.get('product_name', '')).strip().upper()
        if not cliente_nome or cliente_nome == 'NONE':
            cliente_nome = 'VENDA SEM PEDIDO'

        cliente_doc = str(row.get('customer_document', ''))
        tipo_str = str(row.get('product_capture', 'N/A'))
        valor_str = f"R$ {row.get('amount', 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        row_html = f"""
            <div class="grid-row">
                <div class="grid-col"><div>{data_str}</div><div style="font-size:0.8rem; color:#878787;">{hora_str}</div></div>
                <div class="grid-col" style="font-family: monospace; font-size: 0.8rem; word-break: break-all;">{id_str}</div>
                <div class="grid-col"><div class="status-text {status_class}">{status_str.upper()}</div><div class="client-name">{cliente_nome}</div><div class="client-cnpj">{cliente_doc}</div></div>
                <div class="grid-col"><div>{tipo_str}</div></div>
                <div class="grid-col valor">{valor_str}</div>
            </div>
        """
        html_parts.append(row_html)

    html_parts.append('</div>')
    return "".join(html_parts)