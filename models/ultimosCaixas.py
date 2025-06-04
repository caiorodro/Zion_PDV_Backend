from pydantic import BaseModel

class ultimosCaixas(BaseModel):
    ID_ABERTURA: int
    DATA_ABERTURA: str