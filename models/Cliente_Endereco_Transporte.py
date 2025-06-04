from pydantic import BaseModel

class Cliente_Endereco_Transporte(BaseModel):
    ID_CLIENTE: int
    NOME_CLIENTE: str
    ID_ENDERECO: int
    ENDERECO: str
    ID_TRANSPORTE: int
    NOME_TRANSPORTE: str