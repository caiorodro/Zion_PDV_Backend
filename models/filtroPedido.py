from typing import List
from dataclasses import dataclass

@dataclass
class filtroPedido:
    FILTRO: str
    ORIGEM: str
    STATUS: List[int]