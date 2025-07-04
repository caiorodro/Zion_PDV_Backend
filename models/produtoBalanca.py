from dataclasses import dataclass
from base.mapTable import mapProduto

@dataclass
class produtoBalanca:
    ITEM_PRODUTO: mapProduto
    QTDE: float