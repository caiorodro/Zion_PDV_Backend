from pydantic import BaseModel

class listaDeCaixa(BaseModel):
    ID_ABERTURA: int
    DATA_ABERTURA: str
    VALOR_ABERTURA: float
    VALOR_FECHAMENTO: float
    USUARIO: str
    DATA_FECHAMENTO: str
    ADMINISTRADOR: bool
