from datetime import datetime
from dataclasses import dataclass

@dataclass
class HistoricoCaixas:
    ID_CAIXA: int
    DATA_HORA: str
    DT: datetime
    NOME_USUARIO: str