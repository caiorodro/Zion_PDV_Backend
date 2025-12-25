from dataclasses import dataclass

@dataclass
class conclusaoPagamento:
    NUMERO_PEDIDO: int
    IMPRESSAO: bool
    FISCAL: bool
    NUMERO_IMPRESSORA: int