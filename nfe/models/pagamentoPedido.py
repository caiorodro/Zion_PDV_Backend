from dataclasses import dataclass

@dataclass
class pagamentoPedido:
    NUMERO_PEDIDO: int
    ID_PAGAMENTO: int
    FORMA_PAGTO: int
    VALOR_PAGO: float
    CODIGO_NSU: str
