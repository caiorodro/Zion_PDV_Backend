from pydantic import BaseModel

class listaProduto(BaseModel):
    ID_PRODUTO: int
    DESCRICAO_PRODUTO: str
    PRECO_BALCAO: float
    ID_TRIBUTO: int
    SALDO: float
    CODIGO_ZE: str
    PRODUTO_ATIVO: int
    QTDE_FRACIONADA: bool
    ID_FAMILIA: int
