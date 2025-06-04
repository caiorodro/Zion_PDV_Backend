from pydantic import BaseModel

class dadosCliente(BaseModel):
        
    ID_CLIENTE: int
    NOME_CLIENTE: str
    CPF: str
    ENDERECO_CLIENTE: str
    NUMERO_ENDERECO: str
    COMPLEMENTO_ENDERECO: str
    BAIRRO_CLIENTE: str
    CEP_CLIENTE: str
    MUNICIPIO_CLIENTE: str
    UF_CLIENTE: str
    TELEFONE_CLIENTE: str
    EMAIL_CLIENTE: str
    ID_EMPRESA: int
    IE: str
    BLACK_LIST: int
    NOME_FANTASIA_CLIENTE: str
    OBS_CLIENTE: str
    TAXA_ENTREGA: float
