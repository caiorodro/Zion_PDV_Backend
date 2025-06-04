from pydantic import BaseModel

class listaDeTributo(BaseModel):
    ID_TRIBUTO: int
    NOME_OPERACAO: str