from pydantic import BaseModel

class aberturaCaixa(BaseModel):
    ID_ABERTURA: int
    DATA_ABERTURA: str
    ID_USUARIO: int
    VALOR_ABERTURA: float
    SENHA_CAIXA: str