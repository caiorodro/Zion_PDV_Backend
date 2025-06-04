from typing import List
from pydantic import BaseModel

class filtroListaPedido(BaseModel):
    FILTRO: str
    ORIGEM: str
    STATUS: List[int]
    START: int
