from sqlalchemy import (
    DECIMAL,
    Column,
    DateTime,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    create_engine,
)
from sqlalchemy.orm import mapper, sessionmaker

from base.mapTable import (
    mapAberturaCaixa,
    mapAssociacaoProduto,
    mapAtendimentoComanda,
    mapCFOP,
    mapCliente,
    mapCodigoBarrasProduto,
    mapComboProduto,
    mapDoseProduto,
    mapEmpresa,
    mapEnderecoCliente,
    mapEstoque,
    mapFechamentoCaixa,
    mapFilaComanda,
    mapFinanceiro,
    mapFormaPagto,
    mapGradePreco,
    mapItemPedido,
    mapMunicipio,
    mapPedido,
    mapPedidoNFe,
    mapPedidoPagamento,
    mapPlanoConta,
    mapProduto,
    mapReforco,
    mapSangria,
    mapTransporte,
    mapTributo,
    mapUSUARIO,
    mapMESA
)
from cfg.config import Config

strConn = "".join(
    (
        Config.DB_USERNAME,
        ":",
        Config.DB_PASSWORD,
        "@",
        Config.DB_SERVER_NAME,
        "/",
        Config.DB_NAME,
    )
)

engine = create_engine(
    'mysql+pymysql://' + strConn, isolation_level="READ UNCOMMITTED", 
    pool_recycle=900,
    pool_pre_ping=True
    )

metadata = MetaData()
Session = sessionmaker(bind=engine)
session = Session()

tables = []

tb_usuario = Table(
    "tb_usuario",
    metadata,
    Column("ID_USUARIO", Integer, primary_key=True, autoincrement="auto"),
    Column("NOME_USUARIO", String(100), nullable=False),
    Column("SENHA_USUARIO", String(250), nullable=True),
    Column("EMAIL_USUARIO", String(150), nullable=True),
    Column("USUARIO_ATIVO", Integer, nullable=True),
    Column("TIPO_USUARIO", Integer, nullable=True),
)

tb_produto = Table(
    "tb_produto",
    metadata,
    Column("ID_PRODUTO", Integer, primary_key=True, autoincrement="auto"),
    Column("CODIGO_PRODUTO", String(25), nullable=True),
    Column("CODIGO_PRODUTO_PDV", String(25), nullable=True),
    Column("DESCRICAO_PRODUTO", String(150), nullable=True),
    Column("PRECO_BALCAO", Numeric(12, 4), nullable=True),
    Column("PRODUTO_ATIVO", Integer, nullable=True),
    Column("ID_TRIBUTO", Integer, nullable=False),
    Column("CODIGO_ZE", String(20), nullable=True),
)

tb_grade_produto = Table(
    "tb_grade_produto",
    metadata,
    Column("ID_PRODUTO", Integer, primary_key=True),
    Column("QTDE_INICIAL", Integer, primary_key=True),
    Column("QTDE_FINAL", Integer, primary_key=True),
    Column("PRECO_VENDA", DECIMAL, nullable=True),
)

tb_pedido = Table(
    "tb_pedido",
    metadata,
    Column("NUMERO_PEDIDO", Integer, primary_key=True, autoincrement="auto"),
    Column("DATA_HORA", DateTime, nullable=True),
    Column("DATA_ENTREGA", DateTime, nullable=True),
    Column("DATA_HORA_AGENDA", DateTime, nullable=True),
    Column("TEMPO_ENTREGA", String(5), nullable=True),
    Column("TEMPO_RETIRADA_LOJA", DateTime, nullable=True),
    Column("TEMPO_MOTOBOY_CAMINHO", DateTime, nullable=True),
    Column("ID_CLIENTE", Integer, nullable=True),
    Column("ID_ENDERECO", Integer, nullable=True),
    Column("CPF", String(15), nullable=True),
    Column("IE", String(15), nullable=True),
    Column("NOME_CLIENTE", String(120), nullable=True),
    Column("ENDERECO_CLIENTE", String(200), nullable=True),
    Column("BAIRRO_CLIENTE", String(150), nullable=True),
    Column("TELEFONE_CLIENTE", String(20), nullable=True),
    Column("LATITUDE", DECIMAL, nullable=True),
    Column("LONGITUDE", DECIMAL, nullable=True),
    Column("ORIGEM", String(30), nullable=True),
    Column("ID_CAIXA", Integer, nullable=True),
    Column("STATUS_PEDIDO", Integer, nullable=True),
    Column("NUMERO_PESSOAS", Integer, nullable=True),
    Column("NUMERO_VENDA", Integer, nullable=True),
    Column("TIPO_ADICIONAL", String(20), nullable=True),
    Column("TOTAL_PRODUTOS", DECIMAL, nullable=True),
    Column("TROCO", DECIMAL, nullable=True),
    Column("DESCONTO", DECIMAL, nullable=True),
    Column("ADICIONAL", DECIMAL, nullable=True),
    Column("TAXA_ENTREGA", DECIMAL, nullable=True),
    Column("TOTAL_PEDIDO", DECIMAL, nullable=True),
    Column("MOTIVO_DEVOLUCAO", String(100), nullable=True),
    Column("ID_TRANSPORTE", Integer, nullable=True),
    Column("INFO_ADICIONAL", String(3000), nullable=True),
    Column("NUMERO_PEDIDO_ZE_DELIVERY", Integer, nullable=True),
    Column("NUMERO_PEDIDO_DELIVERY", Integer, nullable=True),
    Column("NUMERO_PEDIDO_LALAMOVE", String(40), nullable=True),
    Column("NUMERO_PEDIDO_IFOOD", String(50), nullable=True),
    Column("ID_PEDIDO_IFOOD", String(100), nullable=True),
    Column("TIPO_PEDIDO_IFOOD", Integer, nullable=True),
    Column("CODIGO_IDENTIFICACAO_IFOOD", String(30), nullable=True),
    Column("ORDER_NUMBER_GOOMER", Integer, nullable=True),
    Column("ID_PEDIDO_GOOMER", Integer, nullable=True),
    Column("ORDER_NUMBER_WABIZ", Integer, nullable=True),
    Column("INTERNAL_KEY_WABIZ", String(150), nullable=True),
    Column("ORDER_NUMBER_RAPPI", Integer, nullable=True),
    Column("REQUEST_ID_FATTORINO", String(25), nullable=True),
    Column("INTERNAL_KEY_ZION", String(150), nullable=True),
    Column("MOTIVO_CANCELAMENTO", String(500), nullable=True),
    Column("COMENTARIOS_AVALIACAO", String(1000), nullable=True),
    Column("NOTA_AVALIACAO", DECIMAL, nullable=True),
    Column("ORDEM_ROTEIRO", DECIMAL, nullable=True),
    Column("TEMPO_ATENDIMENTO_ROBO", DateTime, nullable=True),
    Column("TEMPO_ENTREGA_PEDIDO", DateTime, nullable=True),
    Column("ID_PEDIDO_LOCAL", Integer, nullable=True),
    Column("ID_TERMINAL", Integer, nullable=True),
)

tb_item_pedido = Table(
    "tb_item_pedido",
    metadata,
    Column("NUMERO_ITEM", Integer, primary_key=True, autoincrement="auto"),
    Column("NUMERO_PEDIDO", Integer, nullable=False),
    Column("ID_PRODUTO", Integer, nullable=True),
    Column("CODIGO_PRODUTO", String(25), nullable=True),
    Column("QTDE", DECIMAL, nullable=True),
    Column("PRECO_UNITARIO", DECIMAL, nullable=True),
    Column("VALOR_TOTAL", DECIMAL, nullable=True),
    Column("ID_TRIBUTO", Integer, nullable=True),
    Column("OBS_ITEM", String(200), nullable=True),
    Column("ID_ITEM_LOCAL", Integer, nullable=True),
    Column("ID_TERMINAL", Integer, nullable=True)
)

tb_pedido_pagamento = Table(
    "tb_pedido_pagamento",
    metadata,
    Column("ID_PAGAMENTO", Integer, primary_key=True, autoincrement="auto"),
    Column("NUMERO_PEDIDO", Integer, nullable=False),
    Column("DATA_HORA", DateTime, nullable=True),
    Column("FORMA_PAGTO", String(30), nullable=True),
    Column("VALOR_PAGO", DECIMAL, nullable=True),
    Column("ID_PAGAMENTO_LOCAL", Integer, nullable=True),
    Column("ID_TERMINAL", Integer, nullable=True),
    Column("ID_CAIXA", Integer, nullable=True),
    Column("ORIGEM", String(30), nullable=True),
    Column("CODIGO_NSU", String(100), nullable=True),
    Column("VALOR_PAGO_STONE", DECIMAL, nullable=True),
    Column("DATA_AUTORIZACAO", DateTime, nullable=True),
    Column("BANDEIRA", String(50), nullable=True)
)

tb_combo_produto = Table(
    "tb_combo_produto",
    metadata,
    Column("ID_PRODUTO", Integer, primary_key=True, nullable=False),
    Column("ID_PRODUTO_COMBO", Integer, primary_key=True, nullable=False),
    Column("QTDE_COMBO", DECIMAL, nullable=True),
    Column("PRECO_COMBO", DECIMAL, nullable=True),
)

tb_associacao_produto = Table(
    "tb_associacao_produto",
    metadata,
    Column("ID_ASSOCIACAO", Integer, primary_key=True, autoincrement="auto"),
    Column("ID_PRODUTO_ESTOQUE", Integer, nullable=True),
    Column("ID_PRODUTO", Integer, nullable=True),
)

tb_dose_produto = Table(
    "tb_dose_produto",
    metadata,
    Column("ID_PRODUTO_DOSE", Integer, primary_key=True, nullable=False),
    Column("ID_PRODUTO", Integer, nullable=False),
    Column("DOSE_ML", DECIMAL, nullable=True),
)

tb_estoque = Table(
    "tb_estoque",
    metadata,
    Column("ID_ESTOQUE", Integer, primary_key=True, autoincrement="auto"),
    Column("DATA_ESTOQUE", DateTime, nullable=False),
    Column("ID_PRODUTO", Integer, nullable=False),
    Column("MOVIMENTO", Integer, nullable=False),
    Column("QTDE_ESTOQUE", DECIMAL, nullable=False),
    Column("ID_FORNECEDOR", Integer, nullable=False),
    Column("ID_EMPRESA", Integer, nullable=False),
    Column("SALDO", DECIMAL, nullable=False),
    Column("NUMERO_COMANDA", Integer, nullable=False),
    Column("PRECO_CUSTO", DECIMAL, nullable=False),
    Column("CONTAGEM", Integer, nullable=False),
)

tb_financeiro = Table(
    "tb_financeiro",
    metadata,
    Column("ID_FINANCEIRO", Integer, primary_key=True, autoincrement="auto"),
    Column("CREDITO_DEBITO", Integer, nullable=True),
    Column("DATA_LANCAMENTO", DateTime, nullable=True),
    Column("DATA_VENCIMENTO", DateTime, nullable=True),
    Column("DATA_PAGAMENTO", DateTime, nullable=True),
    Column("NUMERO_SEQ_NF_SAIDA", Integer, nullable=True),
    Column("NUMERO_SEQ_NF_ENTRADA", Integer, nullable=True),
    Column("VALOR", DECIMAL, nullable=True),
    Column("VALOR_DESCONTO", DECIMAL, nullable=True),
    Column("VALOR_ACRESCIMO", DECIMAL, nullable=True),
    Column("VALOR_TOTAL", DECIMAL, nullable=True),
    Column("HISTORICO", String(250), nullable=True),
    Column("ID_EMPRESA", Integer, nullable=True),
    Column("ID_PLANO", String(10), nullable=True),
    Column("NUMERO_COMANDA", Integer, nullable=True),
    Column("ID_FINANCEIRO_LOCAL", Integer, nullable=True),
    Column("ID_TERMINAL", Integer, nullable=True),
)

tb_forma_pagto = Table(
    "tb_forma_pagto",
    metadata,
    Column("ID_FORMA", Integer, primary_key=True, autoincrement="auto"),
    Column("DESCRICAO_FORMA", String(30), nullable=True),
    Column("PAGTO_FUTURO", Integer, nullable=True),
    Column("VALE_FUNCIONARIO", Integer, nullable=True),
    Column("VALOR_DIA", DECIMAL, nullable=True),
    Column("TAXA_PAGAMENTO", DECIMAL, nullable=True),
    Column("DIAS_PAGAMENTO", Integer, nullable=True),
)

tb_plano_conta = Table(
    "tb_plano_conta",
    metadata,
    Column("ID_PLANO", String(10), primary_key=True),
    Column("DESCRICAO_PLANO", String(100), nullable=True),
    Column("CREDITO_DEBITO", Integer, nullable=True),
    Column("PAI_PLANO", String(10), nullable=True),
)

tb_atendimento_comanda = Table(
    "tb_atendimento_comanda",
    metadata,
    Column("ID_ATENDIMENTO", Integer, primary_key=True, autoincrement="auto"),
    Column("NUMERO_COMANDA_ATENDIMENTO", Integer, nullable=True),
    Column("ID_PRODUTO", Integer, nullable=True),
    Column("QTDE", Integer, nullable=True),
    Column("PRECO", DECIMAL, nullable=True),
    Column("NUMERO_COMANDA", Integer, nullable=True),
    Column("FECHADO", Integer, nullable=True),
    Column("DATA_HORA", DateTime, nullable=True),
    Column("ID_TRIBUTO", Integer, nullable=True),
    Column("MESA", String(5), nullable=True),
    Column("OBS_ITEM", String(200), nullable=True),
    Column("IMPRESSAO", Integer, nullable=True),
    Column("AGRUPADOR", Integer, nullable=True),
    Column("IMPRESSAO_PRECONTA", Integer, nullable=True),
    Column("DESCONTO", DECIMAL, nullable=True),
    Column("ADICIONAL", DECIMAL, nullable=True),
    Column("DESCRICAO_PRODUTO", String(180), nullable=True),
    Column("QTDE_IMPRESSAO", Integer, nullable=True),
    Column("ID_ATENDIMENTO_LOCAL", Integer, nullable=True),
    Column("ID_TERMINAL", Integer, nullable=True),
    Column("NOME_MESA", String(50), nullable=True),
)

tb_abertura_caixa = Table(
    "tb_abertura_caixa",
    metadata,
    Column("ID_ABERTURA", Integer, primary_key=True, autoincrement="auto"),
    Column("ID_EMPRESA", Integer, nullable=True),
    Column("DATA_ABERTURA", DateTime, nullable=True),
    Column("VALOR_ABERTURA", DECIMAL, nullable=True),
    Column("VALOR_FECHAMENTO", DECIMAL, nullable=True),
    Column("ID_USUARIO", Integer, nullable=True),
    Column("DATA_FECHAMENTO", DateTime, nullable=True),
    Column("IMPRESSAO", Integer, nullable=True),
)

tb_fechamento_caixa = Table(
    "tb_fechamento_caixa",
    metadata,
    Column("ID_FECHAMENTO", Integer, primary_key=True, autoincrement="auto"),
    Column("ID_ABERTURA", Integer, nullable=True),
    Column("FORMA_PAGTO", String(30), nullable=True),
    Column("VALOR_FECHAMENTO", DECIMAL, nullable=True),
    Column("DATA_FECHAMENTO", DateTime, nullable=True),
    Column("DIFERENCA", DECIMAL, nullable=True),
    Column("ID_FECHAMENTO_LOCAL", Integer, nullable=True),
    Column("ID_TERMINAL", Integer, nullable=True),
)

tb_cliente = Table(
    "tb_cliente",
    metadata,
    Column("ID_CLIENTE", Integer, primary_key=True, autoincrement="auto"),
    Column("NOME_CLIENTE", String(120), nullable=True),
    Column("CPF", String(15), nullable=True),
    Column("ENDERECO_CLIENTE", String(200), nullable=True),
    Column("NUMERO_ENDERECO", String(12), nullable=True),
    Column("COMPLEMENTO_ENDERECO", String(12), nullable=True),
    Column("BAIRRO_CLIENTE", String(150), nullable=True),
    Column("CEP_CLIENTE", String(10), nullable=True),
    Column("MUNICIPIO_CLIENTE", String(80), nullable=True),
    Column("UF_CLIENTE", String(2), nullable=True),
    Column("TELEFONE_CLIENTE", String(20), nullable=True),
    Column("EMAIL_CLIENTE", String(120), nullable=True),
    Column("ID_EMPRESA", Integer, nullable=True),
    Column("IE", String(15), nullable=True),
    Column("BLACK_LIST", DECIMAL, nullable=True),
    Column("NOME_FANTASIA_CLIENTE", String(35), nullable=True),
    Column("OBS_CLIENTE", String(400), nullable=True),
    Column("TAXA_ENTREGA", DECIMAL, nullable=True),
)

tb_endereco_cliente = Table(
    "tb_endereco_cliente",
    metadata,
    Column("ID_ENDERECO", Integer, primary_key=True, autoincrement="auto"),
    Column("ID_CLIENTE", Integer, nullable=True),
    Column("ENDERECO", String(200), nullable=True),
    Column("NUMERO_ENDERECO", String(12), nullable=True),
    Column("COMPLEMENTO_ENDERECO", String(50), nullable=True),
    Column("BAIRRO", String(150), nullable=True),
    Column("CEP", String(12), nullable=True),
    Column("MUNICIPIO", String(80), nullable=True),
    Column("UF", String(2), nullable=True),
    Column("ID_EMPRESA", Integer, nullable=True),
    Column("LATITUDE", DECIMAL, nullable=True),
    Column("LONGITUDE", DECIMAL, nullable=True),
)

tb_transporte = Table(
    "tb_transporte",
    metadata,
    Column("ID_TRANSPORTE", Integer, primary_key=True, autoincrement="auto"),
    Column("NOME_TRANSPORTE", String(80), nullable=True),
    Column("CNPJ", String(20), nullable=True),
    Column("IE", String(15), nullable=True),
    Column("ENDERECO", String(80), nullable=True),
    Column("CIDADE", String(100), nullable=True),
    Column("UF", String(2), nullable=True),
    Column("PLACA", String(15), nullable=True),
    Column("EMAIL", String(100), nullable=True),
)

tb_fila_comanda = Table(
    "tb_fila_comanda",
    metadata,
    Column("ID_FILA", Integer, primary_key=True, autoincrement="auto"),
    Column("NUMERO_COMANDA", Integer, nullable=True),
    Column("PROCESSADO", Integer, nullable=True),
)

tb_pedido_nfe = Table(
    "tb_pedido_nfe",
    metadata,
    Column("ID_PEDIDO_NFE", Integer, primary_key=True, autoincrement="auto"),
    Column("NUMERO_PEDIDO", Integer, nullable=True),
    Column("XML_NOTA", String(10000), nullable=True),
    Column("RESPOSTA_SEFAZ", String(10000), nullable=True),
    Column("NUMERO_NF", Integer, nullable=True),
    Column("SERIE_NF", String(10), nullable=True),
    Column("CHAVE_ACESSO_NF", String(50), nullable=True),
    Column("PROTOCOLO_AUTORIZACAO", String(25), nullable=True),
    Column("PROCESSADO", Integer, nullable=True),
    Column("ASSINATURA_NFCE", String(10000), nullable=True),
    Column("DATA_AUTORIZACAO_NFCE", String(20), nullable=True),
    Column("CHAVE_PEDIDO", String(15), nullable=True),
    Column("XML_DEVOLUCAO", String(10000), nullable=True),
    Column("NUMERO_NF_DEVOLUCAO", Integer, nullable=True),
    Column("GERAR_DANFE", Integer, nullable=True),
    Column("ID_EMPRESA", Integer, nullable=True),
    Column("CHAVE_NF_DEVOLUCAO", String(50), nullable=True),
    Column("ID_PEDIDO_NFE_LOCAL", Integer, nullable=True),
    Column("ID_TERMINAL", String(50), nullable=True),
)

tb_empresa = Table(
    "tb_empresa",
    metadata,
    Column("ID_EMPRESA", Integer, primary_key=True, autoincrement="auto"),
    Column("NOME_FANTASIA", String(30), nullable=True),
    Column("RAZAO_SOCIAL", String(80), nullable=True),
    Column("CNPJ", String(20), nullable=True),
    Column("IE", String(15), nullable=True),
    Column("ENDERECO", String(80), nullable=True),
    Column("BAIRRO", String(60), nullable=True),
    Column("CEP", String(10), nullable=True),
    Column("CIDADE", String(60), nullable=True),
    Column("UF", String(2), nullable=True),
    Column("NUMERO_NFCE", Integer, nullable=True),
    Column("SERIE_NFCE", String(10), nullable=True),
    Column("TELEFONE", String(15), nullable=True),
    Column("CLIENT_ID_IFOOD", String(100), nullable=True),
    Column("CLIENT_SECRET_IFOOD", String(200), nullable=True),
    Column("GRANT_TYPE_IFOOD", String(100), nullable=True),
    Column("MERCHANT_ID_IFOOD", String(150), nullable=True),
    Column("MAQUINA_IMPRESSAO", Integer, nullable=True),
    Column("EMAIL_LOGIN_ZE", String(100), nullable=True),
    Column("SENHA_LOGIN_ZE", String(100), nullable=True),
    Column("VIAS_IMPRESSAO", String(1), nullable=True),
    Column("SERIAL_PROTOCOLO", String(25), nullable=True),
    Column("CODIGO_MUNICIPIO_IBGE", String(8), nullable=True),
    Column("CRT", String(1), nullable=True),
    Column("FATURAR_TAXA_ENTREGA", Integer, nullable=True),
)

tb_sangria = Table(
    "tb_sangria",
    metadata,
    Column("ID_SANGRIA", Integer, primary_key=True, autoincrement="auto"),
    Column("DATA_SANGRIA", DateTime, nullable=True),
    Column("DESCRICAO_SANGRIA", String(120), nullable=True),
    Column("ID_USUARIO", Integer, nullable=True),
    Column("VALOR_SANGRIA", DECIMAL, nullable=True),
    Column("ID_SANGRIA_LOCAL", Integer, nullable=True),
    Column("ID_TERMINAL", Integer, nullable=True),
    Column("ID_ABERTURA", Integer, nullable=True),
)

tb_reforco_caixa = Table(
    "tb_reforco_caixa",
    metadata,
    Column("ID_REFORCO", Integer, primary_key=True, autoincrement="auto"),
    Column("DATA_REFORCO", DateTime, nullable=True),
    Column("DESCRICAO_REFORCO", String(120), nullable=True),
    Column("ID_USUARIO", Integer, nullable=True),
    Column("VALOR_REFORCO", DECIMAL, nullable=True),
    Column("ID_REFORCO_LOCAL", Integer, nullable=True),
    Column("ID_TERMINAL", Integer, nullable=True),
    Column("ID_ABERTURA", Integer, nullable=True),
)

tb_municipio = Table(
    "tb_municipio",
    metadata,
    Column("ID_IBGE", Integer, primary_key=True, autoincrement="auto"),
    Column("ID_UF", Integer, nullable=True),
    Column("ID_MUNICIPIO", Integer, nullable=True),
    Column("NOME_MUNICIPIO", String(100), nullable=True),
    Column("SIGLA_UF", String(2), nullable=True),
)

tb_codigo_barras_produto = Table(
    "tb_codigo_barras_produto",
    metadata,
    Column("ID_BARRAS", Integer, primary_key=True, autoincrement="auto"),
    Column("ID_PRODUTO", Integer, nullable=True),
    Column("CODIGO_BARRAS", String(30), nullable=True),
)

tb_tributo = Table(
    "tb_tributo",
    metadata,
    Column("ID_TRIBUTO", Integer, primary_key=True, autoincrement="auto"),
    Column("NCM", String(10), nullable=True),
    Column("UF_DESTINO", String(2), nullable=True),
    Column("CFOP", String(5), nullable=True),
    Column("CST", String(5), nullable=True),
    Column("ALIQ_ICMS", DECIMAL, nullable=True),
    Column("ALIQ_INTERNA_ICMS", DECIMAL, nullable=True),
    Column("MODO_BASE_CALCULO_ICMS_ST", String(2), nullable=True),
    Column("IVA", DECIMAL, nullable=True),
    Column("CST_IPI", String(3), nullable=True),
    Column("ALIQ_IPI", DECIMAL, nullable=True),
    Column("CST_PIS", String(3), nullable=True),
    Column("ALIQ_PIS", DECIMAL, nullable=True),
    Column("CST_COFINS", String(3), nullable=True),
    Column("ALIQ_COFINS", DECIMAL, nullable=True),
    Column("NOME_OPERACAO", String(50), nullable=True),
    Column("CEST", String(15), nullable=True),
    Column("PERCENTUAL_RED_BASE_ICMS", DECIMAL, nullable=True),
    Column("CODIGO_GENERO", String(30), nullable=True),
    Column("ID_EMPRESA", Integer, nullable=True),
    Column("PERCENTUAL_FCP", DECIMAL, nullable=True),
)

tb_cfop = Table(
    "tb_cfop",
    metadata,
    Column("CFOP", String(5), primary_key=True, nullable=False),
    Column("DESCRICAO_CFOP", String(15), nullable=True),
    Column("VENDA", Integer, nullable=True),
    Column("DEVOLUCAO", Integer, nullable=True),
)

tb_mesa = Table('tb_mesa', metadata,
    Column('ID_MESA', Integer, primary_key=True, autoincrement="auto"),
    Column('NUMERO_MESA', String(10), nullable=True),
    Column('NOME_MESA', String(30), nullable=True),
    Column('MESA_FECHADA', Integer, nullable=True),
    Column('NUMERO_PEDIDO', Integer, nullable=True)
)

tables = [
    [mapProduto, tb_produto],
    [mapGradePreco, tb_grade_produto],
    [mapUSUARIO, tb_usuario],
    [mapPedido, tb_pedido],
    [mapItemPedido, tb_item_pedido],
    [mapPedidoPagamento, tb_pedido_pagamento],
    [mapComboProduto, tb_combo_produto],
    [mapAssociacaoProduto, tb_associacao_produto],
    [mapDoseProduto, tb_dose_produto],
    [mapEstoque, tb_estoque],
    [mapFinanceiro, tb_financeiro],
    [mapFormaPagto, tb_forma_pagto],
    [mapPlanoConta, tb_plano_conta],
    [mapAtendimentoComanda, tb_atendimento_comanda],
    [mapAberturaCaixa, tb_abertura_caixa],
    [mapFechamentoCaixa, tb_fechamento_caixa],
    [mapCliente, tb_cliente],
    [mapEnderecoCliente, tb_endereco_cliente],
    [mapTransporte, tb_transporte],
    [mapFilaComanda, tb_fila_comanda],
    [mapPedidoNFe, tb_pedido_nfe],
    [mapEmpresa, tb_empresa],
    [mapSangria, tb_sangria],
    [mapReforco, tb_reforco_caixa],
    [mapMunicipio, tb_municipio],
    [mapCodigoBarrasProduto, tb_codigo_barras_produto],
    [mapTributo, tb_tributo],
    [mapCFOP, tb_cfop],
    [mapMESA, tb_mesa]
]

def mapAllTables():
    [mapper(table[0], table[1]) for table in tables]


def connect():
    try:
        return engine.connect()
    except Exception as e:
        raise e
        raise Exception("Cannot connect on database")


def close():
    conn.close()
    engine.dispose()
    session.close()


conn = connect()
mapAllTables()
