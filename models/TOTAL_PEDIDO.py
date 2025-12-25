from dataclasses import dataclass

@dataclass
class TOTAL_PEDIDO:
    TOTAL_PRODUTOS: float
    VALOR_ADICIONAL: float
    VALOR_DESCONTO: float
    TAXA_ENTREGA: float
    TOTAL_PEDIDO: float