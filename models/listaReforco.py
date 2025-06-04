from pydantic import BaseModel

class listaReforco(BaseModel):
    ID_REFORCO: int
    DATA_REFORCO: str
    DESCRICAO_REFORCO: str
    USUARIO: str
    VALOR_REFORCO: float
    ID_REFORCO_LOCAL: int
    ID_TERMINAL: int
    ID_ABERTURA: int