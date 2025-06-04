from pydantic import BaseModel

class fechamentoCaixa(BaseModel):
    ID_ABERTURA: int
    FORMA_PAGTO: str
    VALOR_FECHAMENTO: float
    DATA_FECHAMENTO: str
    DIFERENCA: float 
    ID_FECHAMENTO_LOCAL: int
    ID_TERMINAL: int