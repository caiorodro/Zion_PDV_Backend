from dataclasses import dataclass

@dataclass
class dadosTransporte:
    ID_TRANSPORTE: int
    NOME_TRANSPORTE: str
    CNPJ: str
    IE: str
    ENDERECO: str
    CIDADE: str
    UF: str
    PLACA: str
    EMAIL: str
