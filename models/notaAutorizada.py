from dataclasses import dataclass

@dataclass
class notaAutorizada:
    NUMERO_NF: int
    NUMERO_PEDIDO: int
    SERIE_NF: int
    CHAVE_ACESSO: str
    XML_AUTORIZADO: str