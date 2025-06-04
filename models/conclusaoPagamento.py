from pydantic import BaseModel

class conclusaoPagamento(BaseModel):
    NUMERO_PEDIDO: int
    IMPRESSAO: bool
    FISCAL: bool
    NUMERO_IMPRESSORA: int