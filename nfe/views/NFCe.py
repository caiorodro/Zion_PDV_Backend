from datetime import datetime, timedelta
from typing import List

import base.qModel as ctx
from base.qBase import qBase
from cfg.config import Config

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
        self.qBase = qBase

    async def getDadosEmitente(self, id: idEmitente) -> dadosEmitente:
        e = ctx.mapEmpresa

        query = ctx.session.query(e).all()

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
    
    async def getRecordTributo(self, ID_TRIBUTO: int, tributos: List[ctx.mapTributo]) -> ctx.mapTributo:
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
    
    async def getPedidoParaEmissao(self, filtro: filtroNumeroPedido) -> dadosPedido:
        p = ctx.mapPedido
        ip = ctx.mapItemPedido
        pg = ctx.mapPedidoPagamento
        t = ctx.mapTributo

        filters = [p.NUMERO_PEDIDO == filtro.NUMERO_PEDIDO]

        pedido = (
            ctx.session.query(
                p.NUMERO_PEDIDO,
                p.ID_CLIENTE,
                p.ID_ENDERECO,
                p.NOME_CLIENTE,
                p.ID_TRANSPORTE,
                p.ID_CAIXA,
                p.ORIGEM,
                p.TAXA_ENTREGA,
                p.ADICIONAL,
                p.DESCONTO,
                p.INFO_ADICIONAL
            )
            .filter(*filters)
            .all()
        )

        if len(pedido) == 0:
            raise Exception("Pedido não encontrado na base do sistema")

        items = ctx.session.query(ip).filter(
            ip.NUMERO_PEDIDO == filtro.NUMERO_PEDIDO
        ).all()

        if len(items) == 0:
            raise Exception("O pedido não contém itens para a emissão da NFC-e")

        idsTributo = set([item.ID_TRIBUTO for item in items])

        tributos = ctx.session.query(t).filter(
            t.ID_TRIBUTO.in_(idsTributo)
        ).all()

        itemsPedido = [
            itemPedido(
                NUMERO_ITEM=item.NUMERO_ITEM,
                NUMERO_PEDIDO=item.NUMERO_PEDIDO,
                ID_PRODUTO=item.ID_PRODUTO,
                CODIGO_PRODUTO=item.CODIGO_PRODUTO,
                CODIGO_PRODUTO_PDV='',
                ID_TRIBUTO=item.ID_TRIBUTO,
                NCM=await self.getRecordTributo(item.ID_TRIBUTO, tributos).NCM,
                CFOP=await self.getRecordTributo(item.ID_TRIBUTO, tributos).CFOP,
                CST_CSOSN=await self.getRecordTributo(item.ID_TRIBUTO, tributos).CST,
                ALIQ_ICMS=await self.getRecordTributo(item.ID_TRIBUTO, tributos).ALIQ_ICMS,
                CST_PIS=await self.getRecordTributo(item.ID_TRIBUTO, tributos).CST_PIS,
                CST_COFINS=await self.getRecordTributo(item.ID_TRIBUTO, tributos).CST_COFINS,
                ALIQ_PIS=await self.getRecordTributo(item.ID_TRIBUTO, tributos).ALIQ_PIS,
                ALIQ_COFINS=await self.getRecordTributo(item.ID_TRIBUTO, tributos).ALIQ_COFINS,
                CEST=await self.getRecordTributo(item.ID_TRIBUTO, tributos).CEST,
                DESCRICAO_PRODUTO=await self.getItemPedido(item),
                QTDE=int(item.QTDE),
                PRECO=float(item.PRECO_UNITARIO),
                TOTAL=float(item.VALOR_TOTAL)
            )
            for item in items
        ]

        pag = ctx.session.query(pg).filter(
            pg.NUMERO_PEDIDO == filtro.NUMERO_PEDIDO
        ).all()

        _pagamentos = [
            pagamentoPedido(
                ID_PAGAMENTO=item.ID_PAGAMENTO,
                NUMERO_PEDIDO=item.NUMERO_PEDIDO,
                FORMA_PAGTO=item.FORMA_PAGTO,
                ID_CAIXA=item.ID_CAIXA,
                VALOR_PAGO=item.VALOR_PAGO,
                CODIGO_NSU="" if item.CODIGO_NSU is None else item.CODIGO_NSU,
            )
            for item in pag
        ]

        if len(_pagamentos) == 0:
            raise Exception("O pedido não contém registros de pagamento")

        rec = pedido[0]

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
            ITEMS=itemsPedido,
            PAGAMENTOS=_pagamentos,
            ID_ENDERECO=rec.ID_ENDERECO
        )

        retorno = dadosPedido(
            Pedido=_pedido,
            Items=itemsPedido,
            pagamentos=_pagamentos
        )

        return retorno

    async def getItemPedido(self, item: ctx.mapItemPedido) -> str:

        obsItem = item.OBS_ITEM if item.OBS_ITEM is not None else ''
        
        retorno = await self.getDescricaoProduto(item.ID_PRODUTO) + f' {obsItem}'

        return retorno
    
    async def getDescricaoProduto(self, ID_PRODUTO) -> str:
        rec = (
            ctx.session.query(ctx.mapProduto)
            .filter(ctx.mapProduto.ID_PRODUTO == ID_PRODUTO)
            .first()
        )

        descricaoProduto = "" if rec is None else rec.DESCRICAO_PRODUTO

        return descricaoProduto