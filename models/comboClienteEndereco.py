from dataclasses import dataclass
from typing import Optional

@dataclass
class comboClienteEndereco:
    ID_ENDERECO: int
    ID_CLIENTE: int
    NOME_CLIENTE: str
    ENDERECO: str
    NUMERO_ENDERECO: str
    COMPLEMENTO_ENDERECO: str
    BAIRRO: str
    CEP: str
    CIDADE: str
    UF: str
    CPF: Optional[str] = None
    TELEFONE_CLIENTE: Optional[str] = None