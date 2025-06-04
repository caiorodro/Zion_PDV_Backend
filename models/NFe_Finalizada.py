from pydantic import BaseModel

class NFe_Finalizada(BaseModel):
    NUMERO_PEDIDO: int 
    XML: str
    NUMERO_NF: int
    CHAVE_ACESSO: str
    ASSINATURA_NFC: str
    DATA_AUTORIZACAO: str
