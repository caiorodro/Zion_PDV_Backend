from typing import List

from pydantic import BaseModel

from models.FORMAS_PAGTO_IMPRESSAO import FORMAS_PAGTO_IMPRESSAO


class impressaoPedidoBalcao(BaseModel):
    CPF: str
    NUMERO_COMANDA: int
    NUMERO_COMANDA_ATENDIMENTO: int
    MESA: str
    NUMERO_PEDIDO_ZE_DELIVERY: int
    NUMERO_DELIVERY: int
    NUMERO_PEDIDO_IFOOD: str
    DATA_HORA: str
    NOME_CLIENTE: str
    ENDERECO: str
    BAIRRO: str
    CIDADE: str
    FORMA_PAGTO: List[FORMAS_PAGTO_IMPRESSAO]
    PRODUTO: str
    QTDE: str
    PRECO: str
    TOTAL: str
    DESCONTO: str
    TOTAL_QTDE: str
    TOTAL_VALOR: str
    TROCO: str
    COMENTARIOS: str
    CAIXINHA: str
    TELEFONE: str
    CHAVE_PEDIDO: str
    CODIGO_IDENTIFICACAO_IFOOD: str
    ORDER_NUMBER_GOOMER: int
    ORDER_NUMBER_WABIZ: int
    PREPARO_COZINHA: int
    ORIGEM: str
    TRANSPORTE: str
    NOME_MESA: str
    NUMERO_VENDA: int
    NUMERO_PEDIDO_DELIVERY: str
    TAXA_ENTREGA: str
