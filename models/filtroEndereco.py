from pydantic import BaseModel

class filtroEndereco(BaseModel):
    ID_CLIENTE: int
    FILTRO: str