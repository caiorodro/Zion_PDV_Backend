from pydantic import BaseModel

class dadosEndereco(BaseModel):
    ID_ENDERECO: int
    ID_CLIENTE: int
    ENDERECO: str
    NUMERO_ENDERECO: str
    COMPLEMENTO_ENDERECO: str
    BAIRRO: str
    CEP: str
    MUNICIPIO: str
    UF: str
    ID_EMPRESA: int
    LATITUDE: float
    LONGITUDE: float