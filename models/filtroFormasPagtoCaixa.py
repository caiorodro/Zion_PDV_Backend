from pydantic import BaseModel

class filtroFormasPagtoCaixa(BaseModel):
    ID_CAIXA: int
    FORMA_PAGTO: str
