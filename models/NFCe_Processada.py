from pydantic import BaseModel

class NFCe_Processada(BaseModel):
    NUMERO_PEDIDO: int
    NUMERO_NF: int
    PROTOCOLO_AUTORIZACAO: str
    DATA_AUTORIZACAO: str
    MENSAGEM: str