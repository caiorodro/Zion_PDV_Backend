from dataclasses import dataclass

@dataclass
class listaDeCaixa:
    ID_ABERTURA: int
    DATA_ABERTURA: str
    VALOR_ABERTURA: float
    VALOR_FECHAMENTO: float
    USUARIO: str
    DATA_FECHAMENTO: str
    ADMINISTRADOR: bool
    USUARIO_CAIXA: int
