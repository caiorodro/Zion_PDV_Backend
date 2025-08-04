from dataclasses import dataclass

@dataclass
class resumoFechamento:
    USUARIO: str
    PERIODO_INICIAL: str
    PERIODO_FINAL: str
    FORMA_PAGTO: str
    ABERTURA: float
    TOTAL: float
    DESCONTO: float
    SANGRIA: float
    REFORCO: float
    TOTAL_GERAL: float
    DIFERENCA: float
    DATA_FECHAMENTO: str
    VALOR_FECHAMENTO: float
    DIFERENCA: float
