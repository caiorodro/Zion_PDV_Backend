from dataclasses import dataclass

@dataclass
class notaEntradaResumo:
    ID_NF: int
    NUMERO_NF: int
    CNPJ_FORNECEDOR: str
    NOME_EMITENTE: str
    DATA_EMISSAO: str
