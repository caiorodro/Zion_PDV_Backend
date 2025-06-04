from pydantic import BaseModel

class listaDeUsuario(BaseModel):
    ID_USUARIO: int
    NOME_USUARIO: str
