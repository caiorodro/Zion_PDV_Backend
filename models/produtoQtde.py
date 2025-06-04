from pydantic import BaseModel

class produtoQtde(BaseModel):
    DESCRICAO_PRODUTO: str
    QTDE: int