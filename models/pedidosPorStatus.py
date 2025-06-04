from pydantic import BaseModel

class pedidosPorStatus(BaseModel):
    STATUS: str
    COUNT: int