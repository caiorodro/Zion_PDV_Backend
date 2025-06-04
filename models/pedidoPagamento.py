from pydantic import BaseModel

class pedidoPagamento(BaseModel):

    ID_PAGAMENTO: int
    NUMERO_PEDIDO: int
    DATA_HORA: str
    FORMA_PAGTO: str
    VALOR_PAGO: float
    ID_CAIXA: int
    ORIGEM: str
    ID_PAGAMENTO_LOCAL: int
    ID_TERMINAL: int
    CODIGO_NSU: str
    VALOR_PAGO_STONE: float
    DATA_AUTORIZACAO: str
    BANDEIRA: str
