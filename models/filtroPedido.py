from typing import List
from pydantic import BaseModel

class filtroPedido(BaseModel):
    FILTRO: str
    ORIGEM: str
    STATUS: List[int]