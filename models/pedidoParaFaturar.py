from dataclasses import dataclass

@dataclass
class pedidoParaFaturar:
    NUMERO_PEDIDO: int
    DATA_HORA: str
    TOTAL_PEDIDO: float
