from pydantic import BaseModel

class comboCliente(BaseModel):
    ID_CLIENTE: int
    NOME_CLIENTE: str
    CPF: str
    TELEFONE_CLIENTE: str