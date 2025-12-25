from typing import List

from dataclasses import dataclass

from models.dadosCliente import dadosCliente
from models.dadosEndereco import dadosEndereco

@dataclass
class editCliente:
    cliente: dadosCliente
    endereco: List[dadosEndereco]
