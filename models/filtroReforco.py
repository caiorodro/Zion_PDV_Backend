from pydantic import BaseModel

class filtroReforco(BaseModel):
    DATA_REFORCO: str
    ID_CAIXA: int