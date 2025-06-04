from pydantic import BaseModel

class listaSangria(BaseModel):
    ID_SANGRIA: int
    DATA_SANGRIA: str
    DESCRICAO_SANGRIA: str
    USUARIO: str
    VALOR_SANGRIA: float
    ID_SANGRIA_LOCAL: int
    ID_TERMINAL: int
    ID_ABERTURA: int
