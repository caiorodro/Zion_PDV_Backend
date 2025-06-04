from pydantic import BaseModel

class listaDeCliente(BaseModel):
    ID_CLIENTE: int
    NOME_CLIENTE: str
    NOME_FANTASIA_CLIENTE: str
    TELEFONE_CLIENTE: str