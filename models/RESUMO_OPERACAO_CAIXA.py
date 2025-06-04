from typing import List
from pydantic import BaseModel

class TOTAIS_CAIXA_FORMA_PAGTO(BaseModel):
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

class TOTAIS_CAIXA_ORIGEM(BaseModel):
    ORIGEM: str 
    VALOR: float 
    DESCONTO: float 
    TOTAL: float 

class TOTAIS_CAIXA_FORMA_PAGTO_ORIGEM(BaseModel):
    ORIGEM: str 
    FORMA_PAGTO: str 
    VALOR: float 
    DESCONTO: float 
    TOTAL: float 

class TOTAIS_SANGRIA(BaseModel):
    DATA_HORA: str 
    DESCRICAO: str 
    USUARIO: str 
    VALOR: float 

class TOTAIS_REFORCO(BaseModel):
    DATA_HORA: str 
    DESCRICAO: str 
    USUARIO: str 
    VALOR: float 

class RESUMO_IMPRESSAO_CAIXA(BaseModel):
    DATA1: str
    DATA2: str
    USUARIO: str
    RESUMO_FORMA_PAGTO: List[TOTAIS_CAIXA_FORMA_PAGTO]
    RESUMO_ORIGEM: List[TOTAIS_CAIXA_ORIGEM]
    RESUMO_SANGRIA: List[TOTAIS_SANGRIA]
    RESUMO_FORMA_PAGTO_ORIGEM: List[TOTAIS_CAIXA_FORMA_PAGTO_ORIGEM]
    RESUMO_REFORCO: List[TOTAIS_REFORCO]
