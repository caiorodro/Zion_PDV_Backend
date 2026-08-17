from dataclasses import dataclass

@dataclass
class tributoCompleto:
    ID_TRIBUTO: int
    NCM: str
    CFOP: str
    CST: str
    ALIQ_ICMS: float
    CST_PIS: str
    ALIQ_PIS: float
    CST_COFINS: str
    ALIQ_COFINS: float
    CEST: str
    NOME_OPERACAO: str
