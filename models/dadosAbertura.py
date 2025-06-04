from pydantic import BaseModel

class dadosAbertura(BaseModel):
    ABERTURA: int
    SANGRIA: float
    REFORCO: float
