from dataclasses import dataclass
from typing import List

@dataclass
class itemBalanca:
    TAMANHO_CODIGO_BARRAS: int
    POSICAO_CODIGO_PRODUTO: List[int]
    POSICAO_QTDE_PESO: List[int]
    POSICAO_PRECO: List[int]