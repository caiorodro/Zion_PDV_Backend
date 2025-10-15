from dataclasses import dataclass
from base.mapTable import mapProduto

@dataclass
class produtoPrecoBalanca:
    ITEM_PRODUTO: mapProduto
    QTDE: int
    PRECO_TOTAL: float