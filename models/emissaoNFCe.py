from pydantic import BaseModel

class emissaoNFCe(BaseModel):
    NUMERO_PEDIDO: int
    CPF: str
