from dataclasses import dataclass

from models.dadosCliente import dadosCliente
from models.dadosEndereco import dadosEndereco

@dataclass
class dadosClienteEndereco:
    cliente: dadosCliente
    endereco: dadosEndereco
