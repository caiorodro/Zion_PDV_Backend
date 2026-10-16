from dataclasses import dataclass
from typing import Optional

@dataclass
class listaDeUsuario:
    ID_USUARIO: int
    NOME_USUARIO: str
    USUARIO_CAIXA: Optional[int] = None
    ACESSO_FECHAMENTO: Optional[int] = None
