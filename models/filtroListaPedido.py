from typing import List
from dataclasses import dataclass

@dataclass
class filtroListaPedido:
    FILTRO: str
    ORIGEM: str
    STATUS: List[int]
    START: int
