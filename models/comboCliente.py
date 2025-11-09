from dataclasses import dataclass
from typing import Optional

@dataclass
class comboCliente:
    ID_CLIENTE: int
    NOME_CLIENTE: str
    CPF: Optional[str] = None
    TELEFONE_CLIENTE: Optional[str] = None