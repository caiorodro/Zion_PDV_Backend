from pydantic import BaseModel

class dadosPedido(BaseModel):
    NUMERO_PEDIDO: int
    ID_CLIENTE: int
    ID_ENDERECO: int
    ID_TRANSPORTE: int
    TAXA_ENTREGA: float
    ADICIONAL: float
    DESCONTO: float
    INFO_ADICIONAL: str
    TOTAL_PRODUTOS: float
