from dataclasses import dataclass
from typing import List

from nfe.models.pedido import pedido
from nfe.models.itemPedido import itemPedido
from nfe.models.pagamentoPedido import pagamentoPedido

@dataclass
class dadosPedido:
    Pedido: pedido
    Items: List[itemPedido]
    pagamentos: List[pagamentoPedido]
