from pydantic import BaseModel

class TOTAL_PEDIDO(BaseModel):
    TOTAL_PRODUTOS: float
    VALOR_ADICIONAL: float
    VALOR_DESCONTO: float
    TAXA_ENTREGA: float
    TOTAL_PEDIDO: float