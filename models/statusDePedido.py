from pydantic import BaseModel

class statusDePedido(BaseModel):
    ID_STATUS: int
    DESCRICAO: str