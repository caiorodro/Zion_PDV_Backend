from pydantic import BaseModel

class filtroSangria(BaseModel):
    DATA_SANGRIA: str
    ID_CAIXA: int