from dataclasses import dataclass

@dataclass
class clientePedido:
    CPF: str
    NOME_CLIENTE: str
    ENDERECO: str
    NUMERO_ENDERECO: str
    COMPLEMENTO: str
    BAIRRO: str
    TELEFONE: str
    CIDADE: str
    UF: str
    EMAIL: str
