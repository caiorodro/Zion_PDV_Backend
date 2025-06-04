from pydantic import BaseModel

class listaDePedido(BaseModel):
    NUMERO_PEDIDO: int
    DATA_HORA: str
    ORIGEM: str
    STATUS_PEDIDO: str
    NOME_CLIENTE: str
    TRANSPORTE: str
    TOTAL_PEDIDO: float
    PAGAMENTOS: str
    ENDERECO: str
    TELEFONE: str