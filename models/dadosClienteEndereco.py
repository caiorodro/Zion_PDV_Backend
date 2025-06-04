from pydantic import BaseModel

from models.dadosCliente import dadosCliente
from models.dadosEndereco import dadosEndereco


class dadosClienteEndereco(BaseModel):
    cliente: dadosCliente
    endereco: dadosEndereco
