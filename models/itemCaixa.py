from dataclasses import dataclass

@dataclass
class itemCaixa:
    ID_ABERTURA: int
    DATA_ABERTURA: str
    USUARIO: str
    VALOR_ABERTURA: float
    DATA_FECHAMENTO: str
    ADMINISTRADOR: bool