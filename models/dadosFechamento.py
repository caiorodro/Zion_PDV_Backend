from dataclasses import dataclass

@dataclass
class dadosFechamento:
    ID_FECHAMENTO: int
    FORMA_PAGTO: str
    DATA_FECHAMENTO: str
    VALOR_FECHAMENTO: float
    DIFERENCA: float
