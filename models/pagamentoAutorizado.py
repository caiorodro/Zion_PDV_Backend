from dataclasses import dataclass

@dataclass
class pagamentoAutorizado:
    NUMERO_PEDIDO: int
    DATA_PEDIDO: str
    FORMA_PAGTO: str
    VALOR_PAGO: float
    DATA_AUTORIZACAO: str
    NSU: str
    BANDEIRA: str
    PAYMENT_UNIQUEID: str
    ID_TERMINAL: int