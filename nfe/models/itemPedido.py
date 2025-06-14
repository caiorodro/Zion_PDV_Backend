from dataclasses import dataclass

@dataclass
class itemPedido:
    NUMERO_ITEM: int
    NUMERO_PEDIDO: int
    ID_PRODUTO: int
    CODIGO_PRODUTO: str
    CODIGO_PRODUTO_PDV: str
    QTDE: int
    PRECO_UNITARIO: float
    VALOR_TOTAL: float
    ID_TRIBUTO: int
    NCM: str
    CFOP: str
    CST_CSOSN: str
    ALIQ_ICMS: str
    CST_PIS: str
    CST_COFINS: str
    ALIQ_PIS: float
    ALIQ_COFINS: float
    CEST: str
    OBS_ITEM: str
    ID_ITEM_LOCAL: int
    ID_TERMINAL: int
