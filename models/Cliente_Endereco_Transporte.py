from dataclasses import dataclass

@dataclass
class Cliente_Endereco_Transporte:
    ID_CLIENTE: int
    NOME_CLIENTE: str
    ID_ENDERECO: int
    ENDERECO: str
    ID_TRANSPORTE: int
    NOME_TRANSPORTE: str