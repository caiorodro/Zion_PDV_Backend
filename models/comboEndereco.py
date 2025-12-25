from dataclasses import dataclass

@dataclass
class comboEndereco:
    ID_ENDERECO: int
    ENDERECO: str
    NUMERO_ENDERECO: str
    COMPLEMENTO_ENDERECO: str
    BAIRRO: str
    CIDADE: str
    UF: str