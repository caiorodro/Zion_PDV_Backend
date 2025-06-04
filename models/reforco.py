from pydantic import BaseModel

class reforco(BaseModel):
    ID_REFORCO: int
    DATA_REFORCO: str
    DESCRICAO_REFORCO: str
    ID_USUARIO: int
    VALOR_REFORCO: float
    ID_REFORCO_LOCAL: int
    ID_TERMINAL: int
    ID_ABERTURA: int