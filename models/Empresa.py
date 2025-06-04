from pydantic import BaseModel

class Empresa(BaseModel):
    ID_EMPRESA: int
    NUMERO_NFCE: int
    SERIE_NFCE: str