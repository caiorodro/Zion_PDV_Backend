from pydantic import BaseModel

class comboEndereco(BaseModel):
    ID_ENDERECO: int
    ENDERECO: str
    NUMERO_ENDERECO: str
    COMPLEMENTO_ENDERECO: str
    BAIRRO: str
    CIDADE: str
    UF: str