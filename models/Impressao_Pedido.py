from pydantic import BaseModel

class IMPRESSAO_PEDIDO(BaseModel):
        
    IMPRESSAO_NAO_FISCAL: int 
    IMPRESSAO_FISCAL: int
    NUMERO_IMPRESSORA: int
