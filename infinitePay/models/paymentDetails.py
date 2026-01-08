from dataclasses import dataclass
from typing import List

@dataclass
class itemDetail:
    quantity: int
    price: int
    description: str

@dataclass
class paymentDetails:
    handle: str
    items: List[itemDetail]
    order_nsu: str