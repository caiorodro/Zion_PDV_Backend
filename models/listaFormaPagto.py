from pydantic import BaseModel

class listaFormaPagto(BaseModel):
    ID_FORMA: int
    DESCRICAO_FORMA: str