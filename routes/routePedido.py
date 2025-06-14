import traceback

from fastapi import APIRouter
from fastapi.security import HTTPBearer

from base.authentication import authentication
#from base.checkDatabase import checkTables
from cfg.config import Config
from models.aberturaCaixa import aberturaCaixa
from models.Cliente_Endereco_Transporte import Cliente_Endereco_Transporte
from models.conclusaoPagamento import conclusaoPagamento
from models.dadosPedido import dadosPedido
from models.dadosTransporte import dadosTransporte
from models.dadosUsuario import dadosUsuario
from models.editCliente import editCliente
from models.emissaoNFCe import emissaoNFCe
from models.fechamentoCaixa import fechamentoCaixa
from models.filtroCAIXA import filtroCAIXA
from models.filtroCliente import filtroCliente
from models.filtroCodigoProduto import filtroCodigoProduto
from models.filtroDescricaoProduto import filtroDescricaoProduto
from models.filtroEndereco import filtroEndereco
from models.filtroFormasPagtoCaixa import filtroFormasPagtoCaixa
from models.filtroIDPagamento import filtroIDPagamento
from models.filtroImpressaoCaixa import filtroImpressaoCaixa
from models.filtroImpressaoPedido import filtroImpressaoPedido
from models.filtroListaPedido import filtroListaPedido
from models.filtroListaProduto import filtroListaProduto
from models.filtroNumeroPedido import filtroNumeroPedido
from models.filtroPedido import filtroPedido
from models.filtroReforco import filtroReforco
from models.filtroSangria import filtroSangria
from models.filtroTransporte import filtroTransporte
from models.getProduto import getProduto
from models.impressaoAvulsa import impressaoAvulsa
from models.itemCaixa import itemCaixa
from models.itemPedido import itemPedido
from models.itemTributo import itemTributo
from models.listaDePagamentos import listaDePagamentos
from models.listaDePedido import listaDePedido
from models.NFe_Finalizada import NFe_Finalizada
from models.nsu import nsu
from models.numeroItemPedido import numeroItemPedido
from models.Order import Order
from models.pagamentoPedido import pagamentoPedido
from models.reforco import reforco
from models.sangria import sangria
from models.TOTAL_PEDIDO import TOTAL_PEDIDO
from views.caixa import Caixa
from views.cliente import Cliente
from views.CupomFiscal import cupomFiscal
from views.pedido import pedido
from views.produto import produto
from views.reforco import Reforco
from views.sangria import Sangria
from views.transporte import Transporte

router = APIRouter()

security = HTTPBearer()

@router.post("/saveOrder")
async def saveOrder(order: Order):
    result = None
    _pedido = pedido()

    try:
        result = await _pedido.test_gravaPedido(order)
    except Exception as ex:
        raise ex
    finally:
        del _pedido

    return result

@router.get("/listCaixa")
async def listCaixa():
    _caixa = Caixa()
    result = None

    try:
        result = await _caixa.listCaixa()
    except Exception as ex:
        raise ex
    finally:
        del _caixa

    return result


@router.get("/listFormaPagto")
async def listFormaPagto():
    _pedido = pedido()
    result = None

    try:
        result = await _pedido.listaFormaPagto()
    except Exception as ex:
        raise ex
    finally:
        del _pedido

    return result


@router.get("/listProduto")
async def listProduto(filtro: filtroListaProduto):
    _produto = produto()
    result = None

    try:
        result = await _produto.list(filtro.NOME)
    except Exception as ex:
        raise ex
    finally:
        del _produto

    return result


@router.get("/getProduto")
async def get_Produto(filtro: getProduto):
    _produto = produto()
    result = None
    try:
        result = await _produto.get_Produto(filtro)

    except Exception as ex:
        raise ex
    finally:
        del _produto

    return result


@router.get("/getPrecoAtacado")
async def getPrecoAtacado(filtro: getProduto):
    _produto = produto()
    retorno = None

    try:
        retorno = await _produto.routePrecoAtacado(filtro)
    except Exception as ex:
        raise ex
    finally:
        del _produto

    return retorno


@router.get("/getNewToken")
async def getNewToken():
    au = authentication()

    auth = au.generateNewToken()

    return auth


@router.get("/listaAtendimento")
async def listaAtendimento(filtro: filtroNumeroPedido):
    _pedido = pedido()
    retorno = None

    try:
        retorno = await _pedido.listaAtendimento(filtro.NUMERO_PEDIDO)
    except Exception as ex:
        raise ex
    finally:
        del _pedido

    return retorno


@router.get("/buscaProdutoPorCodigo")
async def buscaProdutoPorCodigo(filtro: filtroCodigoProduto):
    _produto = produto()
    retorno = None

    try:
        retorno = await _produto.buscaProdutoPorCodigo(filtro)
    except Exception as ex:
        raise ex
    finally:
        del _produto

    return retorno


@router.get("/buscaProdutosSimilares")
async def buscaProdutosSimilares(filtro: filtroDescricaoProduto):
    _produto = produto()
    retorno = None

    try:
        retorno = await _produto.buscaProdutosSimilares(filtro)
    except Exception as ex:
        raise ex
    finally:
        del _produto

    return retorno


@router.post("/gravaAberturaCaixa")
async def gravaAberturaCaixa(dados: aberturaCaixa):
    _caixa = Caixa()
    retorno = None

    try:
        retorno = await _caixa.gravaAberturaCaixa(dados)
    except Exception as ex:
        raise ex
    finally:
        del _caixa

    return retorno


@router.get("/listUsuario")
async def listUsuario():
    _caixa = Caixa()
    result = None

    try:
        result = await _caixa.listUsuario()
    except Exception as ex:
        raise ex
    finally:
        del _caixa

    return result


@router.get("/getCaixa")
async def getCaixa(filtro: filtroCAIXA):
    _caixa = Caixa()
    result = None

    try:
        result = await _caixa.getCaixa(filtro)
    except Exception as ex:
        raise ex
    finally:
        del _caixa

    return result


@router.get("/listaSangria")
async def listaSangria(filtro: filtroSangria):
    _sangria = Sangria()
    result = None

    try:
        result = await _sangria.listSangria(filtro)
    except Exception as ex:
        raise ex
    finally:
        del _sangria

    return result


@router.post("/gravaSangria")
async def gravaSangria(dados: sangria):
    _sangria = Sangria()
    retorno = None
    try:
        retorno = await _sangria.gravaSangria(dados)
    except Exception as ex:
        raise ex
    finally:
        del _sangria

    return retorno


@router.get("/listaReforco")
async def listaReforco(filtro: filtroReforco):
    _reforco = Reforco()
    result = None
    try:
        result = await _reforco.listReforco(filtro)
    except Exception as ex:
        raise ex
    finally:
        del _reforco

    return result


@router.post("/gravaReforco")
async def gravaReforco(dados: reforco):
    _reforco = Reforco()
    retorno = None
    try:
        retorno = await _reforco.gravaReforco(dados)
    except Exception as ex:
        raise ex
    finally:
        del _reforco

    return retorno


@router.get("/busca_Formas_de_Pagto_no_Caixa")
async def busca_Formas_de_Pagto_no_Caixa(filtro: filtroFormasPagtoCaixa):
    _caixa = Caixa()
    retorno = None

    try:
        retorno = await _caixa.busca_Formas_de_Pagto_no_Caixa(filtro)
    except Exception as ex:
        raise ex
    finally:
        del _caixa

    return retorno


@router.get("/get_Totais_Por_Forma_Pagto")
async def get_Totais_Por_Forma_Pagto(filtro: filtroFormasPagtoCaixa):
    _caixa = Caixa()
    retorno = None
    try:
        retorno = await _caixa.get_Totais_Por_Forma_Pagto(filtro)
    except Exception as ex:
        raise ex
    finally:
        del _caixa

    return retorno


@router.get("/verificaCaixaAberto")
async def verificaCaixaAberto(filtro: filtroCAIXA):
    _caixa = Caixa()
    retorno = None

    try:
        retorno = await _caixa.verificaCaixaAberto(filtro)
    except Exception as ex:
        raise ex
    finally:
        del _caixa

    return retorno


@router.get("/listaPagamentosPorForma")
async def listaPagamentosPorForma(filtro: filtroFormasPagtoCaixa):
    _caixa = Caixa()
    retorno = None

    try:
        retorno = await _caixa.listaPagamentosPorForma(filtro)
    except Exception as ex:
        raise ex
    finally:
        del _caixa

    return retorno


@router.post("/gravaNSU")
async def gravaNSU(dados: nsu):
    _caixa = Caixa()

    try:
        await _caixa.gravaNSU(dados)
    except Exception as ex:
        raise ex
    finally:
        del _caixa


@router.post("/gravaFechamentoCaixa")
async def gravaFechamentoCaixa(dados: fechamentoCaixa):
    _caixa = Caixa()
    result = None

    try:
        result = await _caixa.gravaFechamentoCaixa(dados)
    except Exception as ex:
        raise ex
    finally:
        del _caixa

    return result


@router.get("/get_Totais_Fechamento")
async def get_Totais_Fechamento(filtro: filtroFormasPagtoCaixa):
    _caixa = Caixa()
    result = None

    try:
        result = await _caixa.get_Totais_Fechamento(filtro)
    except Exception as ex:
        raise ex
    finally:
        del _caixa

    return result


@router.post("/setImpressaoCaixa")
async def setImpressaoCaixa(filtro: filtroFormasPagtoCaixa):
    _caixa = Caixa()
    result = None

    try:
        result = await _caixa.setImpressaoCaixa(filtro)
    except Exception as ex:
        raise ex
    finally:
        del _caixa

    return result


@router.get("/listaPedidos")
async def listaPedidos(filtro: filtroListaPedido):
    _pedido = pedido()
    result = None

    try:
        result = await _pedido.listaPedidos(filtro)
    except Exception as ex:
        raise ex
    finally:
        del _pedido

    return result


@router.get("/getOrigem")
async def getOrigem():
    return Config.ORIGEM


@router.get("/getStatusPedido")
async def getStatusPedido():
    return Config.STATUS


@router.get("/get_Lista_de_Produtos")
async def get_Lista_de_Produtos():
    _produto = produto()
    result = None

    try:
        result = await _produto.get_Lista_de_Produtos()
    except Exception as ex:
        raise ex

    finally:
        del _produto

    return result


@router.get("/getPedido")
async def getPedido(filtro: filtroPedido):
    _pedido = pedido()
    result = None

    try:
        result = await _pedido.getPedido(filtro)
    except Exception as ex:
        raise ex

    finally:
        del _pedido

    return result


@router.post("/deletaItemPedido")
async def deletaItemPedido(item: numeroItemPedido):
    _pedido = pedido()
    result = None

    try:
        result = await _pedido.deletaItemPedido(item)
    except Exception as ex:
        raise ex

    finally:
        del _pedido

    return result


@router.get("/buscaCliente")
async def buscaCliente(filtro: filtroCliente):
    _cliente = Cliente()
    result = None

    try:
        result = await _cliente.buscaCliente(filtro)
    except Exception as ex:
        raise ex

    finally:
        del _cliente

    return result


@router.get("/buscaTransporte")
async def buscaTransporte(filtro: filtroTransporte):
    _cliente = Transporte()
    result = None

    try:
        result = await _cliente.buscaTransporte(filtro)
    except Exception as ex:
        raise ex

    finally:
        del _cliente

    return result


@router.get("/buscaEndereco")
async def buscaEndereco(filtro: filtroEndereco):
    _cliente = Cliente()
    result = None

    try:
        result = await _cliente.buscaEndereco(filtro)
    except Exception as ex:
        raise ex

    finally:
        del _cliente

    return result


@router.post("/cancelaPedido")
async def cancelaPedido(record: listaDePedido):
    _cliente = pedido()
    result = None

    try:
        result = await _cliente.cancelaPedido(record)
    except Exception as ex:
        raise ex

    finally:
        del _cliente

    return result


@router.post("/savePedido")
async def savePedido(record: dadosPedido):
    _cliente = pedido()

    try:
        await _cliente.savePedido(record)
    except Exception as ex:
        raise ex

    finally:
        del _cliente


@router.get("/get_Dados_Cliente_Endereco_Transporte")
async def get_Dados_Cliente_Endereco_Transporte(dados: Cliente_Endereco_Transporte):
    _cliente = Cliente()

    retorno = None

    try:
        retorno = await _cliente.get_Dados_Cliente_Endereco_Transporte(dados)
    except Exception as ex:
        raise ex

    finally:
        del _cliente

    return retorno


@router.post("/addItem")
async def addItem(record: itemPedido):
    _cliente = pedido()

    try:
        await _cliente.addItem(record)
    except Exception as ex:
        raise ex

    finally:
        del _cliente


@router.get("/listaItens")
async def listaItens(filtro: filtroNumeroPedido):
    _cliente = pedido()
    retorno = None

    try:
        retorno = await _cliente.listaItens(filtro)
    except Exception as ex:
        raise ex

    finally:
        del _cliente

    return retorno


@router.get("/getTotalPedido")
async def getTotalPedido(filtro: filtroNumeroPedido) -> TOTAL_PEDIDO:
    _cliente = pedido()
    retorno = None

    try:
        retorno = await _cliente.getTotalPedido(filtro)
    except Exception as ex:
        raise ex

    finally:
        del _cliente

    return retorno


@router.get("/listaPagamentos")
async def listaPagamentos(filtro: filtroNumeroPedido):
    _cliente = pedido()
    retorno = None

    try:
        retorno = await _cliente.listaPagamentos(filtro)
    except Exception as ex:
        raise ex

    finally:
        del _cliente

    return retorno


@router.post("/deleteItemPagamento")
async def deleteItemPagamento(filtro: filtroIDPagamento):
    _cliente = pedido()

    try:
        await _cliente.deleteItemPagamento(filtro)
    except Exception as ex:
        raise ex

    finally:
        del _cliente


@router.post("/addItemPagamento")
async def addItemPagamento(dados: pagamentoPedido):
    _cliente = pedido()

    try:
        await _cliente.addItemPagamento(dados)
    except Exception as ex:
        raise ex

    finally:
        del _cliente


@router.post("/concluiPagamento")
async def concluiPagamento(dados: conclusaoPagamento):
    _cliente = pedido()

    try:
        await _cliente.concluiPagamento(dados)
    except Exception as ex:
        raise ex

    finally:
        del _cliente


@router.post("/emiteNFCe")
async def emiteNFCe(dados: emissaoNFCe):
    _cliente = pedido()

    try:
        await _cliente.emiteNFCe(dados)
    except Exception as ex:
        raise ex

    finally:
        del _cliente


@router.get("/checaEmissaoNFCe")
async def checaEmissaoNFCe(filtro: filtroNumeroPedido):
    _cliente = pedido()

    result = None

    try:
        result = await _cliente.checaEmissaoNFCe(filtro)
    except Exception as ex:
        raise ex

    finally:
        del _cliente

    return result


@router.get("/getFiscalCliente")
async def getFiscalCliente(filtro: filtroNumeroPedido):
    _cliente = Cliente()

    result = None

    try:
        result = await _cliente.getFiscalCliente(filtro)
    except Exception as ex:
        raise ex

    finally:
        del _cliente

    return result


@router.get("/listaCliente")
async def listaCliente(filtro: filtroCliente):
    _cliente = Cliente()

    result = None

    try:
        result = await _cliente.listaCliente(filtro)
    except Exception as ex:
        raise ex

    finally:
        del _cliente

    return result


@router.post("/gravaDadosCliente")
async def gravaDadosCliente(dados: editCliente):
    _cliente = Cliente()

    try:
        await _cliente.gravaDadosCliente(dados)
    except Exception as ex:
        raise ex

    finally:
        del _cliente


@router.get("/editCliente1")
async def editCliente1(filtro: filtroCliente):
    _cliente = Cliente()

    result = None

    try:
        result = await _cliente.editCliente(filtro)
    except Exception as ex:
        raise ex

    finally:
        del _cliente

    return result


@router.get("/listaTransporte")
async def listaTransporte(filtro: filtroTransporte):
    _cliente = Transporte()

    result = None

    try:
        result = await _cliente.listaTransporte(filtro)
    except Exception as ex:
        raise ex

    finally:
        del _cliente

    return result


@router.post("/gravaDadosTransporte")
async def gravaDadosTransporte(dados: dadosTransporte):
    _cliente = Transporte()

    try:
        await _cliente.gravaDadosTransporte(dados)
    except Exception as ex:
        raise ex

    finally:
        del _cliente


@router.get("/editTransporte")
async def editTransporte(filtro: filtroTransporte):
    _cliente = Transporte()

    result = None

    try:
        result = await _cliente.editTransporte(filtro)
    except Exception as ex:
        raise ex

    finally:
        del _cliente

    return result


@router.post("/imprimePedido")
async def imprimePedido(dados: impressaoAvulsa):
    _cliente = pedido()

    try:
        await _cliente.imprimePedido(dados)
    except Exception as ex:
        raise ex

    finally:
        del _cliente


@router.get("/listaUltimosCaixas")
async def listaUltimosCaixas():
    _cliente = Caixa()

    try:
        await _cliente.listaUltimosCaixas()
    except Exception as ex:
        raise ex

    finally:
        del _cliente


@router.get("/buscaPedidoImpressao")
async def buscaPedidoImpressao(filtro: filtroImpressaoPedido):
    _cliente = pedido()

    retorno = []

    try:
        retorno = await _cliente.buscaPedidoImpressao(filtro)
    except Exception as ex:
        raise ex

    finally:
        del _cliente

    return retorno


@router.get("/resumoTotaisImpressao")
async def resumoTotaisImpressao(filtro: filtroImpressaoCaixa):
    _cliente = Caixa()

    retorno = []

    try:
        retorno = await _cliente.resumoTotaisImpressao(filtro)
    except Exception as ex:
        raise ex

    finally:
        del _cliente

    return retorno


@router.get("/getDadosNFCe")
async def getDadosNFCe(filtro: filtroNumeroPedido):
    _cliente = pedido()

    retorno = []

    try:
        retorno = await _cliente.getDadosNFCe(filtro)
    except Exception as ex:
        raise ex

    finally:
        del _cliente

    return retorno


@router.post("/finalizaNFCe")
async def finalizaNFCe(dados: NFe_Finalizada):
    _cliente = pedido()

    try:
        await _cliente.finalizaNFCe(dados)
    except Exception as ex:
        raise ex

    finally:
        del _cliente

@router.get('/getCupomFiscal')
async def getCupomFiscal(filtro: filtroPedido):
    _cliente = cupomFiscal()

    try:
        pdf = await _cliente.getPDF(filtro)
    except Exception as ex:
        raise ex

    finally:
        del _cliente

    return pdf

@router.get('/getTaxaPagamento')
async def getTaxaPagamento(filtro: filtroFormasPagtoCaixa):
    _cliente = Caixa()

    retorno = 0.00    

    try:
        retorno = await _cliente.getTaxaPagamento(filtro)
    except Exception as ex:
        raise ex

    finally:
        del _cliente

    return retorno

@router.get('/listTributo')
async def listTributo():
    ped = pedido()

    retorno = []

    try:
        retorno = await ped.listTributo()
    except Exception as ex:
        raise ex

    finally:
        del ped

    return retorno

@router.get('/listItensParaNFe')
async def listItensParaNFe(filtro: filtroNumeroPedido):
    ped = pedido()

    retorno = []

    try:
        retorno = await ped.listItensParaNFe(filtro)
    except Exception as ex:
        raise ex

    finally:
        del ped

    return retorno

@router.post('/setTributoItemPedido')
async def setTributoItemPedido(item: itemTributo):
    ped = pedido()

    try:
        await ped.setTributoItemPedido(item)
    except Exception as ex:
        raise ex

    finally:
        del ped

@router.post('/conferePagamento')
async def conferePagamento(record: listaDePagamentos):
    ped = pedido()

    try:
        await ped.conferePagamento(record)
    except Exception as ex:
        raise ex

    finally:
        del ped

@router.get('/buscaPrecoGrade')
async def buscaPrecoGrade(filtro: getProduto):
    ped = produto()

    retorno = 0

    try:
        retorno = await ped.getPrecoAtacado(filtro)

        if not isinstance(retorno, float):
            retorno = 0.00

    except Exception as ex:
        raise ex

    finally:
        del ped

    return retorno

@router.get('/verificaSenhaAberturaCaixa')
async def verificaSenhaAberturaCaixa(dados: dadosUsuario):
    ped = Caixa()

    retorno = False

    try:
        retorno = await ped.verificaSenhaAberturaCaixa(dados)

    except Exception as ex:
        raise ex

    finally:
        del ped

    return retorno

@router.get('/getUsuarioFromCaixa')
async def getUsuarioFromCaixa(dados: itemCaixa):
    ped = Caixa()

    retorno = 0

    try:
        retorno = await ped.getUsuarioFromCaixa(dados)

    except Exception as ex:
        raise ex

    finally:
        del ped

    return retorno
# @router.post('/verifyTables')
# async def verifyTables():
#     ct = checkTables()
#     await ct.verifyNewTables()
#     del ct
