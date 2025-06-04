from pydantic import BaseModel

class ResumoFormaPagtoOrigem(BaseModel):
    FORMA_PAGTO: str
    ORIGEM: str
    ABERTURA: float
    VALOR_VENDA: float
    DESCONTO: float
    TROCO: float
    SANGRIA: float
    REFORCO: float
    TOTAL: float
    DIFERENCA: float
    DATA_HORA_FECHAMENTO: str 
    VALOR_FECHAMENTO: float
