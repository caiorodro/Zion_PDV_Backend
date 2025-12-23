from pydantic import BaseModel
from typing import List

class listaProduto(BaseModel):
    ID_PRODUTO: int
    CODIGO_PRODUTO: str
    CODIGO_EAN: List[str]
    DESCRICAO_PRODUTO: str
    PRECO_BALCAO: float
    PRECO_ATACADO: float
    ID_TRIBUTO: int
    SALDO: float
    CODIGO_ZE: str
    PRODUTO_ATIVO: int
    QTDE_FRACIONADA: bool
    ID_FAMILIA: int
    QTDE: float
