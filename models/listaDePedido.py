from dataclasses import dataclass

@dataclass
class listaDePedido:
    NUMERO_PEDIDO: int
    DATA_HORA: str
    ORIGEM: str
    STATUS_PEDIDO: str
    NOME_CLIENTE: str
    TRANSPORTE: str
    TOTAL_PEDIDO: float
    PAGAMENTOS: str
    ENDERECO: str
    TELEFONE: str
    NF: bool
    DESCRICAO_FORMA: str
    CODIGO_AUTORIZACAO: str
    DADOS_PAGAMENTO: str