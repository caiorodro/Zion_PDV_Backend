from dataclasses import dataclass

@dataclass
class dadosEmitente:
    RAZAO_SOCIAL: str
    NOME_FANTASIA: str
    CNPJ: str
    CODIGO_DE_REGIME_TRIBUTARIO: str
    INSCRICAO_ESTADUAL: str
    INSCRICAO_MUNICIPAL: str
    CNAE_FISCAL: str
    ENDERECO_LOGRADOURO: str
    ENDERECO_NUMERO: str
    ENDERECO_BAIRRO: str
    ENDERECO_MUNICIPIO: str
    ENDERECO_UF: str
    ENDERECO_CEP: str
    ENDERECO_PAIS: str