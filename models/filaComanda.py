from pydantic import BaseModel

class filaComanda(BaseModel):
    ID_FILA: int
    NUMERO_COMANDA: int
    PROCESSADO: int
