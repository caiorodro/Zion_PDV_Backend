from pydantic import BaseModel

class ResumoOrigem(BaseModel):
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
