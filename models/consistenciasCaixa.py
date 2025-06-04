from pydantic import BaseModel

class consistenciasCaixa(BaseModel):
    DATA_HORA: str
    DESCRICAO: str