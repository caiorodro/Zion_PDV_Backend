from dataclasses import dataclass

@dataclass
class NFe_Finalizada:
    NUMERO_PEDIDO: int 
    XML: str
    NUMERO_NF: int
    CHAVE_ACESSO: str
    ASSINATURA_NFC: str
    DATA_AUTORIZACAO: str
