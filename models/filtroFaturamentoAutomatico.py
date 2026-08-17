from dataclasses import dataclass
from typing import List

@dataclass
class filtroFaturamentoAutomatico:
    VALOR_MAXIMO_MENSAL: float
    FORMAS_PAGTO: List[str]
    ORIGEM: List[str]
