from pydantic import BaseModel

class comboTransporte(BaseModel):
    ID_TRANSPORTE: int
    NOME_TRANSPORTE: str