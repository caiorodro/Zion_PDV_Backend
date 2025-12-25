from dataclasses import dataclass

@dataclass
class listaDeProduto:
    ID_PRODUTO: int
    DESCRICAO_PRODUTO: str
    PRECO_BALCAO: float
    ID_TRIBUTO: int