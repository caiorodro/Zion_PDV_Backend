from pydantic import BaseModel

class impressaoAvulsa(BaseModel):
    NUMERO_PEDIDO: int
    NUMERO_IMPRESSORA: int