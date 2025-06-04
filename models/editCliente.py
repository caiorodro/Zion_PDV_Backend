from typing import List

from pydantic import BaseModel

from models.dadosCliente import dadosCliente
from models.dadosEndereco import dadosEndereco


class editCliente(BaseModel):
    cliente: dadosCliente
    endereco: List[dadosEndereco]
