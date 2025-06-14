from dataclasses import dataclass

@dataclass
class pagamentoPedido:
    NUMERO_PEDIDO: int
    ID_PAGAMENTO: int
    ID_FORMA: int
    DESCRICAO_FORMA: str
    VALOR_PAGO: float
    CODIGO_AUTORIZACAO: str
