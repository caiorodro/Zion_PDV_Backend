from pydantic import BaseModel

class dadosFechamento(BaseModel):
    ID_FECHAMENTO: int
    FORMA_PAGTO: str
    DATA_FECHAMENTO: str
    VALOR_FECHAMENTO: float
    DIFERENCA: float
