from pydantic import BaseModel

class sangria(BaseModel):
    ID_SANGRIA: int
    DATA_SANGRIA: str
    DESCRICAO_SANGRIA: str
    ID_USUARIO: int
    VALOR_SANGRIA: float
    ID_SANGRIA_LOCAL: int
    ID_TERMINAL: int
    ID_ABERTURA: int
