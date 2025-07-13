from dataclasses import dataclass

@dataclass
class pedido:
    NUMERO_PEDIDO: int
    ID_CLIENTE: int
    NOME_CLIENTE: str
    ID_TRANSPORTE: int
    NOME_TRANSPORTE: str
    ORIGEM: str
    TAXA_ENTREGA: float
    VALOR_ADICIONAL: float
    VALOR_DESCONTO: float
    INFO_ADICIONAL: str
    ID_CAIXA: int
    ID_ENDERECO:int
