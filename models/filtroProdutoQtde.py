from pydantic import BaseModel

class filtroProdutoQtde(BaseModel):
    ID_PRODUTO: int
    QTDE: int