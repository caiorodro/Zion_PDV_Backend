from typing import List

from models.Impressao_Pedido import IMPRESSAO_PEDIDO
from models.itemPedido import itemPedido
from models.pedido import pedido
from models.pedidoPagamento import pedidoPagamento

from dataclasses import dataclass

@dataclass
class Order:
    pedido: pedido
    itemsPedido: List[itemPedido]
    pagamento: List[pedidoPagamento]
    impressaoPedido: IMPRESSAO_PEDIDO
