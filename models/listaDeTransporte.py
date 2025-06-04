from pydantic import BaseModel

class listaDeTransporte(BaseModel):
    ID_TRANSPORTE: int
    NOME_TRANSPORTE: str
