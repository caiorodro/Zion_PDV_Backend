from dataclasses import dataclass

@dataclass
class itemNotaEntrada:
    ID_NF: int
    ID_PRODUTO: int
    DESCRICAO_PRODUTO: str
    PRECO_UNITARIO: float
    QTDE_ITEM: float
