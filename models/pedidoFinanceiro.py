from dataclasses import dataclass

@dataclass
class pedidoFinanceiro:
    NUMERO_PEDIDO: int
    NOME_CLIENTE: str
    ID_CLIENTE: int
    TOTAL_PEDIDO: float
    LIMITE_MENSAL: float