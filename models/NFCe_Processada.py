from dataclasses import dataclass

@dataclass
class NFCe_Processada:
    NUMERO_PEDIDO: int
    NUMERO_NF: int
    PROTOCOLO_AUTORIZACAO: str
    DATA_AUTORIZACAO: str
    MENSAGEM: str