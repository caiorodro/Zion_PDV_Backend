from pydantic import BaseModel

class listaDePagamentos(BaseModel):
    NUMERO_PEDIDO: int
    DATA_HORA: str
    STATUS_PEDIDO: str
    CLIENTE: str
    TOTAL_PEDIDO: float
    TOTAL_PAGO: float
    CODIGO_NSU: str
    ID_PAGAMENTO: int
    VALOR_PAGO_STONE: float