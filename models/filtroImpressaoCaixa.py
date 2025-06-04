from pydantic import BaseModel

class filtroImpressaoCaixa(BaseModel):
    ID_CAIXA: int
    MAQUINA: int
    CNPJ: str