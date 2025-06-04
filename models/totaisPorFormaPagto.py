from pydantic import BaseModel

class totaisPorFormaPagto(BaseModel):
    FORMA_PAGTO: str
    TROCO: float
    TOTAL_PAGTO: float
    DESCONTO: float
    SANGRIA: float
    REFORCO: float 
    TOTAL_FINAL: float
    VALOR_FECHAMENTO: float
    DIFERENCA: float
    TOTAL_GERAL: float