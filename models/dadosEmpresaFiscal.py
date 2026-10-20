from dataclasses import dataclass

@dataclass
class dadosEmpresaFiscal:
    """
    Dados de tb_empresa já no formato/nomenclatura exigido pelos nós
    Emitente/EnderecoEmitente/CfgServico-cUF/ConfiguracaoCsc do
    Zeus/configuracao.xml -- quem consome isso (aba Fiscal,
    views/caixa.py) só grava campo por campo no XML, sem repetir a
    lógica de separar logradouro/número ou derivar cUF a partir do
    CODIGO_MUNICIPIO_IBGE (isso já vem pronto daqui, mesma lógica que
    getNFCe() já usa pro emitente).
    """
    CNPJ: str
    xNome: str
    xFant: str
    IE: str
    CRT: str
    xLgr: str
    nro: str
    xBairro: str
    cMun: str
    xMun: str
    UF: str
    CEP: str
    fone: str
    cUF: str
    CIdToken: str
    Csc: str
