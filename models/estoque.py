from dataclasses import dataclass


@dataclass
class estoque:
    ID_ESTOQUE: int
    DATA_ESTOQUE: str
    ID_PRODUTO: int
    MOVIMENTO: int
    QTDE_ESTOQUE: float
    ID_FORNECEDOR: int
    ID_EMPRESA: int
    SALDO: float
    NUMERO_COMANDA: int
    PRECO_CUSTO: float
    CONTAGEM: int
