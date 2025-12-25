from typing import List
from dataclasses import dataclass

@dataclass
class TOTAIS_CAIXA_FORMA_PAGTO:
    FORMA_PAGTO: str
    ABERTURA: float 
    VALOR: float 
    DESCONTO: float 
    TROCO: float 
    SANGRIA: float 
    REFORCO: float 
    TOTAL: float 
    VALOR_FECHAMENTO: float 
    DIFERENCA: float 

@dataclass
class TOTAIS_CAIXA_ORIGEM:
    ORIGEM: str 
    VALOR: float 
    DESCONTO: float 
    TOTAL: float 

@dataclass
class TOTAIS_CAIXA_FORMA_PAGTO_ORIGEM:
    ORIGEM: str 
    FORMA_PAGTO: str 
    VALOR: float 
    DESCONTO: float 
    TOTAL: float 

@dataclass
class TOTAIS_SANGRIA:
    DATA_HORA: str 
    DESCRICAO: str 
    USUARIO: str 
    VALOR: float 

@dataclass
class TOTAIS_REFORCO:
    DATA_HORA: str 
    DESCRICAO: str 
    USUARIO: str 
    VALOR: float 

@dataclass
class RESUMO_IMPRESSAO_CAIXA:
    DATA1: str
    DATA2: str
    USUARIO: str
    RESUMO_FORMA_PAGTO: List[TOTAIS_CAIXA_FORMA_PAGTO]
    RESUMO_ORIGEM: List[TOTAIS_CAIXA_ORIGEM]
    RESUMO_SANGRIA: List[TOTAIS_SANGRIA]
    RESUMO_FORMA_PAGTO_ORIGEM: List[TOTAIS_CAIXA_FORMA_PAGTO_ORIGEM]
    RESUMO_REFORCO: List[TOTAIS_REFORCO]
