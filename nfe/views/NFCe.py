from typing import List

from base.qBase import qBase
from cfg.config import Config

from infra.repositories.clienteRepository import ClienteRepository
from infra.repositories.empresaRepository import EmpresaRepository
from infra.repositories.enderecoClienteRepository import EnderecoClienteRepository
from infra.repositories.itemPedidoRepository import ItemPedidoRepository
from infra.repositories.pedidoPagamentoRepository import PedidoPagamentoRepository
from infra.repositories.pedidoRepository import PedidoRepository
from infra.repositories.produtoRepository import ProdutoRepository
from infra.repositories.transporteRepository import TransporteRepository
from infra.repositories.tributoRepository import TributoRepository

from nfe.models.dadosEmitente import dadosEmitente
from nfe.models.dadosPedido import dadosPedido
from models.filtroNumeroPedido import filtroNumeroPedido
from nfe.models.pedido import pedido as pedidoNFe
from nfe.models.itemPedido import itemPedido
from nfe.models.pagamentoPedido import pagamentoPedido

from nfe.models.idEmitente import idEmitente

class NFCe:
    def __init__(self):
        self.config = Config()
        self.qBase = qBase()

        self._empresas = EmpresaRepository()
        self._tributos = TributoRepository()
        self._pedidos = PedidoRepository()
        self._itensPedido = ItemPedidoRepository()
        self._pagamentos = PedidoPagamentoRepository()
        self._enderecos = EnderecoClienteRepository()
        self._clientes = ClienteRepository()
        self._transportes = TransporteRepository()
        self._produtos = ProdutoRepository()

    async def getDadosEmitente(self, id: idEmitente) -> dadosEmitente:
        query = self._empresas.listar_todas()

        rec = list(
            filter(lambda e: self.qBase.onlyNumbers(e.CNPJ) == self.qBase.onlyNumbers(id.CNPJ), query)
        )

        if len(rec) == 0:
            raise Exception(f'Não há emitente cadastrado com o CNPJ {id.CNPJ}')

        item = rec[0]

        endereco = item.ENDERECO.split(',')[0]
        numeroEndereco = self.qBase.onlyNumbers(
            item.ENDERECO.split(',')[1]
        )

        retorno = dadosEmitente(
            RAZAO_SOCIAL=item.RAZAO_SOCIAL,
            NOME_FANTASIA =item.NOME_FANTASIA,
            CNPJ = item.CNPJ,
            CODIGO_DE_REGIME_TRIBUTARIO = item.CRT,
            INSCRICAO_ESTADUAL = item.IE,
            INSCRICAO_MUNICIPAL = '',
            CNAE_FISCAL = '',
            ENDERECO_LOGRADOURO = endereco,
            ENDERECO_NUMERO = numeroEndereco,
            ENDERECO_BAIRRO = item.BAIRRO,
            ENDERECO_MUNICIPIO = item.CIDADE,
            ENDERECO_UF = item.UF,
            ENDERECO_CEP = item.CEP,
            ENDERECO_PAIS = 'Brasil'
        )

        return retorno

    async def getRecordTributo(self, ID_TRIBUTO: int, tributos: List) -> object:
        retorno = list(filter(lambda e: e.ID_TRIBUTO == ID_TRIBUTO, tributos))[0]

        if retorno.ALIQ_ICMS is None:
            retorno.ALIQ_ICMS = 0.00

        if retorno.ALIQ_PIS is None:
            retorno.ALIQ_PIS = 0.00

        if retorno.ALIQ_COFINS is None:
            retorno.ALIQ_COFINS = 0.00

        retorno.ALIQ_ICMS = float(retorno.ALIQ_ICMS)
        retorno.ALIQ_PIS = float(retorno.ALIQ_PIS)
        retorno.ALIQ_COFINS = float(retorno.ALIQ_COFINS)

        return retorno

    async def prepareItem(self, item, tributos: List) -> itemPedido:

        recTributo = await self.getRecordTributo(item.ID_TRIBUTO, tributos)

        retorno = itemPedido(
                NUMERO_ITEM=item.NUMERO_ITEM,
                NUMERO_PEDIDO=item.NUMERO_PEDIDO,
                ID_PRODUTO=item.ID_PRODUTO,
                CODIGO_PRODUTO=item.CODIGO_PRODUTO,
                CODIGO_PRODUTO_PDV='',
                ID_TRIBUTO=item.ID_TRIBUTO,
                NCM=recTributo.NCM,
                CFOP=recTributo.CFOP,
                CST_CSOSN=recTributo.CST,
                ALIQ_ICMS=recTributo.ALIQ_ICMS,
                CST_PIS=recTributo.CST_PIS,
                CST_COFINS=recTributo.CST_COFINS,
                ALIQ_PIS=recTributo.ALIQ_PIS,
                ALIQ_COFINS=recTributo.ALIQ_COFINS,
                CEST=recTributo.CEST,
                DESCRICAO_PRODUTO=await self.getItemPedido(item),
                QTDE=int(item.QTDE),
                PRECO_UNITARIO=float(item.PRECO_UNITARIO),
                VALOR_TOTAL=float(item.VALOR_TOTAL),
                OBS_ITEM=item.OBS_ITEM,
                ID_ITEM_LOCAL = 0,
                ID_TERMINAL = 0
            )

        return retorno

    async def getPedidoParaEmissao(self, filtro: filtroNumeroPedido) -> dadosPedido:
        rec = self._pedidos.buscar_por_numero(filtro.NUMERO_PEDIDO)

        if rec is None:
            raise Exception("Pedido não encontrado na base do sistema")

        items = self._itensPedido.listar_por_pedido(filtro.NUMERO_PEDIDO)

        if len(items) == 0:
            raise Exception("O pedido não contém itens para a emissão da NFC-e")

        idsTributo = list(set([item.ID_TRIBUTO for item in items]))

        tributos = self._tributos.listar_por_ids(idsTributo)

        itemsPedido = [await self.prepareItem(item, tributos) for item in items]

        pag = self._pagamentos.listar_por_pedido(filtro.NUMERO_PEDIDO)

        _pagamentos = [
            pagamentoPedido(
                ID_PAGAMENTO=item.ID_PAGAMENTO,
                NUMERO_PEDIDO=item.NUMERO_PEDIDO,
                FORMA_PAGTO=item.FORMA_PAGTO,
                VALOR_PAGO=item.VALOR_PAGO,
                CODIGO_NSU="" if item.CODIGO_NSU is None else item.CODIGO_NSU,
            )
            for item in pag
        ]

        if len(_pagamentos) == 0:
            raise Exception("O pedido não contém registros de pagamento")

        endereco = self._enderecos.buscar_por_id(rec.ID_ENDERECO)

        cliente = self._clientes.buscar_por_id(rec.ID_CLIENTE)

        logradouro = endereco.ENDERECO
        logradouro = logradouro[0: logradouro.index(',')] if ',' in logradouro else logradouro

        _pedido = pedidoNFe(
            NUMERO_PEDIDO=rec.NUMERO_PEDIDO,
            ID_CLIENTE=rec.ID_CLIENTE,
            NOME_CLIENTE=rec.NOME_CLIENTE,
            ID_TRANSPORTE=0 if rec.ID_TRANSPORTE is None else rec.ID_TRANSPORTE,
            NOME_TRANSPORTE=await self.getNomeTransporte(rec.ID_TRANSPORTE),
            ORIGEM=rec.ORIGEM,
            TAXA_ENTREGA=float(rec.TAXA_ENTREGA)
                if rec.TAXA_ENTREGA is not None
                else 0.00,
            VALOR_ADICIONAL=float(rec.ADICIONAL) if rec.ADICIONAL is not None else 0.00,
            VALOR_DESCONTO=float(rec.DESCONTO) if rec.DESCONTO is not None else 0.00,
            INFO_ADICIONAL=rec.INFO_ADICIONAL,
            ID_CAIXA=rec.ID_CAIXA,
            ID_ENDERECO=rec.ID_ENDERECO,
            ENDERECO = logradouro,
            NUMERO_ENDERECO = endereco.NUMERO_ENDERECO,
            COMPLEMENTO_ENDERECO = endereco.COMPLEMENTO_ENDERECO,
            BAIRRO = endereco.BAIRRO,
            CEP = endereco.CEP,
            CIDADE = endereco.MUNICIPIO,
            UF = endereco.UF,
            TELEFONE = cliente.TELEFONE_CLIENTE,
            EMAIL = cliente.EMAIL_CLIENTE
        )

        retorno = dadosPedido(
            Pedido=_pedido,
            Items=itemsPedido,
            pagamentos=_pagamentos
        )

        return retorno

    async def getItemPedido(self, item) -> str:

        obsItem = item.OBS_ITEM if item.OBS_ITEM is not None else ''

        retorno = await self.getDescricaoProduto(item.ID_PRODUTO) + f' {obsItem}'

        return retorno.strip()

    async def getDescricaoProduto(self, ID_PRODUTO) -> str:
        return self._produtos.descricao_por_id_ou_vazio(ID_PRODUTO)

    async def getNomeTransporte(self, ID_TRANSPORTE: int) -> str:
        return self._transportes.nome_por_id(ID_TRANSPORTE)

    async def getNomeCliente(self, ID_CLIENTE: int) -> str:
        return self._clientes.nome_por_id(ID_CLIENTE)
