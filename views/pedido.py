from datetime import datetime, timedelta
from typing import List

from dateutil.relativedelta import relativedelta
from sqlalchemy import desc

import base.qModel as ctx
from base.qBase import qBase
from cfg.config import Config
from models.clienteEndereco import clienteEndereco
from models.conclusaoPagamento import conclusaoPagamento
from models.dadosNFCe import dadosNFCe
from models.dadosPedido import dadosPedido
from models.editPedido import editItemPedido, editPedido, editPedidoPagamento
from models.emissaoNFCe import emissaoNFCe
from models.filaComanda import filaComanda
from models.filtroIDPagamento import filtroIDPagamento
from models.filtroImpressaoPedido import filtroImpressaoPedido
from models.filtroListaPedido import filtroListaPedido
from models.filtroNumeroPedido import filtroNumeroPedido
from models.filtroPedido import filtroPedido
from models.FORMAS_PAGTO_IMPRESSAO import FORMAS_PAGTO_IMPRESSAO
from models.impressaoAvulsa import impressaoAvulsa
from models.impressaoPedidoBalcao import impressaoPedidoBalcao
from models.itemPedido import itemPedido
from models.itemPedidoCaixa import itemPedidoCaixa
from models.itemsNFe import itemsNFe
from models.itemTributo import itemTributo
from models.listaDePedido import listaDePedido
from models.listaDeTributo import listaDeTributo
from models.listaDePagamentos import listaDePagamentos
from models.listaFormaPagto import listaFormaPagto
from models.NFCe_Processada import NFCe_Processada
from models.NFe_Finalizada import NFe_Finalizada
from models.numeroItemPedido import numeroItemPedido
from models.numeroPedido import NUM_PEDIDO
from models.Order import Order
from models.pedido import pedido as ped
from models.pagamentoPedido import pagamentoPedido
from models.pedido import pedido
from models.pedidoPagamento import pedidoPagamento
from models.produtoQtde import produtoQtde
from models.TOTAL_PEDIDO import TOTAL_PEDIDO

class pedido:
    def __init__(self, keep=None, idUser=None):
        self.qBase = qBase(keep)
        self.__listOfUsers = []
        self.__idUser = idUser

        self.idPlanoPagtoFuturo = "1.0.2"

    async def preencheConsumidorFinal(self, consumidorFinal: clienteEndereco, _pedido: ped) -> ped:
        c = ctx.mapCliente
        e = ctx.mapEnderecoCliente

        cliente = ctx.session.query(c).filter(
            c.ID_CLIENTE == consumidorFinal.ID_CLIENTE
        ).first()

        endereco = ctx.session.query(e).filter(
            e.ID_ENDERECO == consumidorFinal.ID_ENDERECO
        ).first()

        _pedido.NOME_CLIENTE = cliente.NOME_CLIENTE
        _pedido.ENDERECO_CLIENTE = ' '.join((
            endereco.ENDERECO,
            endereco.NUMERO_ENDERECO,
            endereco.COMPLEMENTO_ENDERECO
            ))
        
        _pedido.BAIRRO_CLIENTE = endereco.BAIRRO 
        _pedido.TELEFONE_CLIENTE = cliente.TELEFONE_CLIENTE

        return _pedido

    async def test_gravaPedido(self, order: Order):

        consumidorFinal = await self.checaConsumidorFinal()

        if not isinstance(consumidorFinal, clienteEndereco):
            raise Exception('Cliente consumidor final não cadastrado')
        
        order.pedido.ID_CLIENTE = consumidorFinal.ID_CLIENTE
        order.pedido.ID_ENDERECO = consumidorFinal.ID_ENDERECO

        order.pedido = await self.preencheConsumidorFinal(
            consumidorFinal,
            order.pedido
        )

        idTransporte = await self.getTransporte()

        if not isinstance(idTransporte, int):
            raise Exception('Transporte não definido')

        order.pedido.ID_TRANSPORTE = idTransporte

        numeroPedido = await self.gravaPedido(order)

        return self.qBase.toRoute(
            NUM_PEDIDO(NUMERO_PEDIDO=numeroPedido).model_dump_json(), 200
        )

    async def gravaPedido(self, order: Order) -> dict:
        numeroPedido = self.insereNovoPedido(order.pedido)

        assert isinstance(numeroPedido, int)

        assert numeroPedido > 0

        for item in order.itemsPedido:
            item.NUMERO_PEDIDO = numeroPedido

        for item in order.pagamento:
            item.NUMERO_PEDIDO = numeroPedido

        [await self.gravaItensPedido(item) for item in order.itemsPedido]
        [await self.gravaPagamentos(item) for item in order.pagamento]

        [await self.test_baixaEstoque(item) for item in order.itemsPedido]

        [
            await self.test_gravaFinanceiro(order.pedido, order.itemsPedido, pagamento)
            for pagamento in order.pagamento
        ]

        if order.impressaoPedido.IMPRESSAO_NAO_FISCAL == 1:
            cmd = ctx.tb_fila_comanda.insert().values(
                ID_FILA=0,
                NUMERO_COMANDA=numeroPedido,
                PROCESSADO=order.impressaoPedido.NUMERO_IMPRESSORA,
            )

            ctx.session.execute(cmd)

        if order.impressaoPedido.IMPRESSAO_FISCAL == 1:
            await self.test_gravaImpressaoFiscal(numeroPedido)

        ctx.session.commit()

        return numeroPedido

    def insereNovoPedido(self, pedido: pedido) -> int:
        cmd = ctx.tb_pedido.insert().values(
            NUMERO_PEDIDO=0,
            DATA_HORA=datetime.strptime(pedido.DATA_HORA, "%d/%m/%Y %H:%M"),
            DATA_ENTREGA=datetime.strptime(pedido.DATA_ENTREGA, "%d/%m/%Y %H:%M"),
            DATA_HORA_AGENDA=datetime.strptime(
                pedido.DATA_HORA_AGENDA, "%d/%m/%Y %H:%M"
            ),
            TEMPO_ENTREGA=pedido.TEMPO_ENTREGA,
            TEMPO_RETIRADA_LOJA=datetime.strptime(
                pedido.TEMPO_RETIRADA_LOJA, "%d/%m/%Y %H:%M"
            ),
            TEMPO_MOTOBOY_CAMINHO=datetime.strptime(
                pedido.TEMPO_MOTOBOY_CAMINHO, "%d/%m/%Y %H:%M"
            ),
            ID_CLIENTE=pedido.ID_CLIENTE,
            ID_ENDERECO=pedido.ID_ENDERECO,
            CPF=pedido.CPF,
            IE=pedido.IE,
            NOME_CLIENTE=pedido.NOME_CLIENTE,
            ENDERECO_CLIENTE=pedido.ENDERECO_CLIENTE,
            BAIRRO_CLIENTE=pedido.BAIRRO_CLIENTE,
            TELEFONE_CLIENTE=pedido.TELEFONE_CLIENTE,
            LATITUDE=pedido.LATITUDE,
            LONGITUDE=pedido.LONGITUDE,
            ORIGEM=pedido.ORIGEM,
            ID_CAIXA=pedido.ID_CAIXA,
            STATUS_PEDIDO=pedido.STATUS_PEDIDO,
            NUMERO_PESSOAS=pedido.NUMERO_PESSOAS,
            NUMERO_VENDA=pedido.NUMERO_VENDA,
            TIPO_ADICIONAL=pedido.TIPO_ADICIONAL,
            TOTAL_PRODUTOS=pedido.TOTAL_PRODUTOS,
            TROCO=pedido.TROCO,
            DESCONTO=pedido.DESCONTO,
            ADICIONAL=pedido.ADICIONAL,
            TAXA_ENTREGA=pedido.TAXA_ENTREGA,
            TOTAL_PEDIDO=pedido.TOTAL_PEDIDO,
            MOTIVO_DEVOLUCAO=pedido.MOTIVO_DEVOLUCAO,
            ID_TRANSPORTE=pedido.ID_TRANSPORTE,
            INFO_ADICIONAL=pedido.INFO_ADICIONAL,
            NUMERO_PEDIDO_ZE_DELIVERY=pedido.NUMERO_PEDIDO_ZE_DELIVERY,
            NUMERO_PEDIDO_DELIVERY=pedido.NUMERO_PEDIDO_DELIVERY,
            NUMERO_PEDIDO_LALAMOVE=pedido.NUMERO_PEDIDO_LALAMOVE,
            NUMERO_PEDIDO_IFOOD=pedido.NUMERO_PEDIDO_IFOOD,
            ID_PEDIDO_IFOOD=pedido.ID_PEDIDO_IFOOD,
            TIPO_PEDIDO_IFOOD=pedido.TIPO_PEDIDO_IFOOD,
            CODIGO_IDENTIFICACAO_IFOOD=pedido.CODIGO_IDENTIFICACAO_IFOOD,
            ORDER_NUMBER_GOOMER=pedido.ORDER_NUMBER_GOOMER,
            ID_PEDIDO_GOOMER=pedido.ID_PEDIDO_GOOMER,
            ORDER_NUMBER_WABIZ=pedido.ORDER_NUMBER_WABIZ,
            INTERNAL_KEY_WABIZ=pedido.INTERNAL_KEY_WABIZ,
            ORDER_NUMBER_RAPPI=pedido.ORDER_NUMBER_RAPPI,
            REQUEST_ID_FATTORINO=pedido.REQUEST_ID_FATTORINO,
            INTERNAL_KEY_ZION=pedido.INTERNAL_KEY_ZION,
            MOTIVO_CANCELAMENTO=pedido.MOTIVO_CANCELAMENTO,
            COMENTARIOS_AVALIACAO=pedido.COMENTARIOS_AVALIACAO,
            NOTA_AVALIACAO=pedido.NOTA_AVALIACAO,
            ORDEM_ROTEIRO=pedido.ORDEM_ROTEIRO,
            TEMPO_ATENDIMENTO_ROBO=datetime.strptime(
                pedido.TEMPO_ATENDIMENTO_ROBO, "%d/%m/%Y %H:%M"
            ),
            TEMPO_ENTREGA_PEDIDO=datetime.strptime(
                pedido.TEMPO_ENTREGA_PEDIDO, "%d/%m/%Y %H:%M"
            ),
            ID_PEDIDO_LOCAL=pedido.ID_PEDIDO_LOCAL,
            ID_TERMINAL=pedido.ID_TERMINAL,
        )

        result = ctx.session.execute(cmd)
        ctx.session.commit()

        return int(result.inserted_primary_key[0])

    async def gravaItensPedido(self, item: itemPedido) -> bool:
        cmd = ctx.tb_item_pedido.insert().values(
            NUMERO_ITEM=0,
            NUMERO_PEDIDO=item.NUMERO_PEDIDO,
            ID_PRODUTO=item.ID_PRODUTO,
            CODIGO_PRODUTO=item.CODIGO_PRODUTO,
            QTDE=item.QTDE,
            PRECO_UNITARIO=item.PRECO_UNITARIO,
            VALOR_TOTAL=item.VALOR_TOTAL,
            ID_TRIBUTO=item.ID_TRIBUTO,
            OBS_ITEM=item.OBS_ITEM,
            ID_ITEM_LOCAL=item.ID_ITEM_LOCAL,
            ID_TERMINAL=item.ID_TERMINAL,
        )

        descricaoProduto = await self.getDescricaoProduto(item.ID_PRODUTO)

        cmd1 = ctx.tb_atendimento_comanda.insert().values(
            ID_ATENDIMENTO=0,
            NUMERO_COMANDA_ATENDIMENTO=0,
            ID_PRODUTO=item.ID_PRODUTO,
            QTDE=item.QTDE,
            PRECO=item.PRECO_UNITARIO,
            NUMERO_COMANDA=item.NUMERO_PEDIDO,
            FECHADO=1,
            DATA_HORA=datetime.today(),
            ID_TRIBUTO=item.ID_TRIBUTO,
            MESA="",
            OBS_ITEM="",
            IMPRESSAO=0,
            AGRUPADOR=0,
            IMPRESSAO_PRECONTA=0,
            DESCONTO=0,
            ADICIONAL=0,
            DESCRICAO_PRODUTO=descricaoProduto,
            QTDE_IMPRESSAO=0,
            ID_ATENDIMENTO_LOCAL=0,
            ID_TERMINAL=0,
            NOME_MESA="",
        )

        [ctx.session.execute(item) for item in (cmd, cmd1)]

    async def gravaPagamentos(self, item: pedidoPagamento) -> bool:
        cmd = ctx.tb_pedido_pagamento.insert().values(
            ID_PAGAMENTO=0,
            NUMERO_PEDIDO=item.NUMERO_PEDIDO,
            DATA_HORA=datetime.strptime(item.DATA_HORA, "%d/%m/%Y %H:%M"),
            FORMA_PAGTO=item.FORMA_PAGTO,
            VALOR_PAGO=item.VALOR_PAGO,
            ID_CAIXA=item.ID_CAIXA,
            ORIGEM=item.ORIGEM,
            ID_PAGAMENTO_LOCAL=item.ID_PAGAMENTO_LOCAL,
            ID_TERMINAL=item.ID_TERMINAL,
            CODIGO_NSU=item.CODIGO_NSU,
            VALOR_PAGO_STONE=item.VALOR_PAGO_STONE,
            DATA_AUTORIZACAO=datetime.strptime(item.DATA_AUTORIZACAO, "%d/%m/%Y %H:%M"),
            BANDEIRA=item.BANDEIRA,
        )

        ctx.session.execute(cmd)

    async def test_baixaEstoque(self, item: itemPedido):
        assert await self.baixaEstoque(item, 1) == True

    async def baixaEstoque(self, item: itemPedido, movimento: int) -> bool:
        tableCombo = ctx.mapComboProduto

        comboProduto = (
            ctx.session.query(
                tableCombo.ID_PRODUTO,
                tableCombo.ID_PRODUTO_COMBO,
                tableCombo.QTDE_COMBO,
            )
            .filter(tableCombo.ID_PRODUTO == item.ID_PRODUTO)
            .all()
        )

        p = ctx.mapProduto

        for combo in comboProduto:
            exists = (
                ctx.session.query(p)
                .filter(p.ID_PRODUTO == combo.ID_PRODUTO_COMBO)
                .all()
            )

            if len(exists) == 0:
                continue

            cmd = ctx.tb_estoque.insert().values(
                ID_ESTOQUE=0,
                DATA_ESTOQUE=datetime.today(),
                ID_PRODUTO=combo.ID_PRODUTO_COMBO,
                MOVIMENTO=movimento,
                QTDE_ESTOQUE=combo.QTDE_COMBO,
                ID_FORNECEDOR=None,
                ID_EMPRESA=1,
                SALDO=combo.QTDE_COMBO,
                NUMERO_COMANDA=item.NUMERO_PEDIDO,
                PRECO_CUSTO=0.00,
                CONTAGEM=0,
            )

            ctx.session.execute(cmd)

        if len(comboProduto) > 0:
            return True

        tableAssociacao = ctx.mapAssociacaoProduto

        associacaoProduto = (
            ctx.session.query(
                tableAssociacao.ID_PRODUTO, tableAssociacao.ID_PRODUTO_ESTOQUE
            )
            .filter(tableAssociacao.ID_PRODUTO == item.ID_PRODUTO)
            .all()
        )

        for item1 in associacaoProduto:
            exists = (
                ctx.session.query(p)
                .filter(p.ID_PRODUTO == item1.ID_PRODUTO_ESTOQUE)
                .all()
            )

            if len(exists) == 0:
                continue

            cmd = ctx.tb_estoque.insert().values(
                ID_ESTOQUE=0,
                DATA_ESTOQUE=datetime.today(),
                ID_PRODUTO=item1.ID_PRODUTO_ESTOQUE,
                MOVIMENTO=movimento,
                QTDE_ESTOQUE=item.QTDE,
                ID_FORNECEDOR=None,
                ID_EMPRESA=1,
                SALDO=item.QTDE,
                NUMERO_COMANDA=item.NUMERO_PEDIDO,
                PRECO_CUSTO=0.00,
                CONTAGEM=0,
            )

            ctx.session.execute(cmd)

        if len(associacaoProduto) > 0:
            return True

        tableDose = ctx.mapDoseProduto

        doseProduto = (
            ctx.session.query(tableDose.ID_PRODUTO, tableDose.ID_PRODUTO_DOSE)
            .filter(tableDose.ID_PRODUTO_DOSE == item.ID_PRODUTO)
            .all()
        )

        for item1 in doseProduto:
            exists = ctx.session.query(p).filter(p.ID_PRODUTO == item1.ID_PRODUTO).all()

            if len(exists) == 0:
                continue

            cmd = ctx.tb_estoque.insert().values(
                ID_ESTOQUE=0,
                DATA_ESTOQUE=datetime.today(),
                ID_PRODUTO=item1.ID_PRODUTO,
                MOVIMENTO=movimento,
                QTDE_ESTOQUE=item1.DOSE_ML,
                ID_FORNECEDOR=None,
                ID_EMPRESA=1,
                SALDO=item1.DOSE_ML,
                NUMERO_COMANDA=item.NUMERO_PEDIDO,
                PRECO_CUSTO=0.00,
                CONTAGEM=0,
            )

            ctx.session.execute(cmd)

        if len(doseProduto) > 0:
            return True

        cmd = ctx.tb_estoque.insert().values(
            ID_ESTOQUE=0,
            DATA_ESTOQUE=datetime.today(),
            ID_PRODUTO=item.ID_PRODUTO,
            MOVIMENTO=movimento,
            QTDE_ESTOQUE=item.QTDE,
            ID_FORNECEDOR=None,
            ID_EMPRESA=1,
            SALDO=item.QTDE,
            NUMERO_COMANDA=item.NUMERO_PEDIDO,
            PRECO_CUSTO=0.00,
            CONTAGEM=0,
        )

        ctx.session.execute(cmd)

        return True

    async def test_gravaFinanceiro(
        self, pedido: pedido, itemsPedido: List[itemPedido], pagamento: pedidoPagamento
    ) -> bool:
        assert await self.gravaFinanceiro(pedido, itemsPedido, pagamento) == True

        return True

    async def gravaFinanceiro(
        self, pedido: pedido, itemsPedido: List[itemPedido], pagamento: pedidoPagamento
    ) -> bool:
        table = ctx.mapFormaPagto

        formaPagto = (
            ctx.session.query(table)
            .filter(table.DESCRICAO_FORMA == pagamento.FORMA_PAGTO)
            .all()
        )

        if len(formaPagto) > 0:
            if formaPagto[0].PAGTO_FUTURO == 1:
                await self.inserePagtoFuturo(pedido, itemsPedido, pagamento)

                return True

            await self.inserePagtoCartao(pedido, itemsPedido, pagamento)

            ctx.session.commit()

        return True

    async def test_gravaImpressaoNaoFiscal(
        self, impressaoNaoFiscal: filaComanda
    ) -> bool:
        assert self.gravaImpressaoNaoFiscal(impressaoNaoFiscal) == True

        return True

    def gravaImpressaoNaoFiscal(self, impressaoNaoFiscal: filaComanda) -> bool:
        cmd = ctx.tb_fila_comanda.insert().values(
            ID_FILA=0, NUMERO_COMANDA=impressaoNaoFiscal.NUMERO_COMANDA, PROCESSADO=0
        )

        ctx.session.execute(cmd)

    async def test_gravaImpressaoFiscal(self, numeroPedido: int) -> bool:
        assert await self.gravaImpressaoFiscal(numeroPedido) == True

        return True

    async def gravaImpressaoFiscal(self, numeroPedido: int) -> bool:
        _nf = await self.buscaProximaNF()

        cmd = ctx.tb_pedido_nfe.insert().values(
            ID_PEDIDO_NFE=0,
            NUMERO_PEDIDO=numeroPedido,
            XML_NOTA="",
            RESPOSTA_SEFAZ="",
            NUMERO_NF=_nf[0],
            SERIE_NF=_nf[1],
            CHAVE_ACESSO_NF="",
            PROTOCOLO_AUTORIZACAO="",
            PROCESSADO=0,
            ASSINATURA_NFCE="",
            DATA_AUTORIZACAO_NFCE="",
            CHAVE_PEDIDO="",
            XML_DEVOLUCAO="",
            NUMERO_NF_DEVOLUCAO=0,
            GERAR_DANFE=0,
            ID_EMPRESA=1,
            CHAVE_NF_DEVOLUCAO="",
            ID_PEDIDO_NFE_LOCAL=0,
            ID_TERMINAL=0
        )

        ctx.session.execute(cmd)

        return True

    async def buscaProximaNF(self):
        _empresa = ctx.session.query(
            ctx.mapEmpresa.ID_EMPRESA,
            ctx.mapEmpresa.NUMERO_NFCE,
            ctx.mapEmpresa.SERIE_NFCE,
        ).all()

        NF = 0 if _empresa[0].NUMERO_NFCE == None else _empresa[0].NUMERO_NFCE

        retorno = [
            NF,
            "1" if _empresa[0].SERIE_NFCE == None else _empresa[0].SERIE_NFCE,
        ]

        return retorno

    async def inserePagtoFuturo(
        self, pedido: pedido, itemsPedido: List[itemPedido], pagamento: pedidoPagamento
    ) -> bool:
        planoConta = (
            ctx.session.query(ctx.mapPlanoConta)
            .filter(ctx.mapPlanoConta.ID_PLANO == self.idPlanoPagtoFuturo)
            .all()
        )

        if len(planoConta) == 0:
            cmd = ctx.tb_plano_conta.insert().values(
                ID_PLANO=self.idPlanoPagtoFuturo,
                DESCRICAO_PLANO="RECEBIMENTO FUTURO",
                PAI_PLANO="1",
                CREDITO_DEBITO=0,
            )

            ctx.session.execute(cmd)

        hoje = datetime.today()

        mes = hoje.month
        ano = hoje.year

        if hoje.day >= 7:
            mes = (hoje + relativedelta(months=1)).month
            ano = (hoje + relativedelta(months=1)).year

        _vencimento = datetime(ano, mes, 7, hoje.hour, hoje.minute, 0)

        delFinanceiro = ctx.tb_financeiro.delete().where(
            ctx.mapFinanceiro.NUMERO_COMANDA == pagamento.ID_PAGAMENTO
        )

        ctx.session.execute(delFinanceiro)

        items = [
            produtoQtde(await self.getDescricaoProduto(item.ID_PRODUTO), item.QTDE)
            for item in itemsPedido
        ]

        strItems = ", ".join(
            [f"[{item.DESCRICAO_PRODUTO}, Qtde: {str(item.QTDE)}]" for item in items]
        )

        descricao = "".join(
            [
                f"Recebimento futuro {pedido.NOME_CLIENTE} - Nr. Pedido {pedido.NUMERO_PEDIDO}",
                f", ITENS: {strItems}",
            ]
        )

        if len(descricao) > 250:
            descricao = descricao[0, 250]

        cmd = ctx.tb_financeiro.insert().values(
            DATA_LANCAMENTO=datetime.today(),
            DATA_VENCIMENTO=_vencimento,
            DATA_PAGAMENTO=datetime(1901, 1, 1),
            HISTORICO=descricao,
            ID_PLANO=self.idPlanoPagtoFuturo,
            VALOR=pagamento.VALOR_PAGO,
            VALOR_DESCONTO=0,
            VALOR_ACRESCIMO=0,
            VALOR_TOTAL=pagamento.VALOR_PAGO,
            CREDITO_DEBITO=0,
            NUMERO_SEQ_NF_ENTRADA=0,
            ID_EMPRESA=1,
            NUMERO_COMANDA=pagamento.ID_PAGAMENTO,
        )

        ctx.session.execute(cmd)

        return True

    async def inserePagtoCartao(
        self, pedido: pedido, itemsPedido: List[itemPedido], pagamento: pedidoPagamento
    ) -> bool:
        formaPagto = (
            ctx.session.query(ctx.mapFormaPagto)
            .filter(ctx.mapFormaPagto.DESCRICAO_FORMA == pagamento.FORMA_PAGTO)
            .all()
        )

        if len(formaPagto) == 0:
            return True

        recPagamento = formaPagto[0]

        if recPagamento.DIAS_PAGAMENTO is None:
            return True

        if recPagamento.DIAS_PAGAMENTO <= 0:
            return True

        planoConta = (
            ctx.session.query(ctx.mapPlanoConta)
            .filter(ctx.mapPlanoConta.ID_PLANO == self.idPlanoPagtoFuturo)
            .all()
        )

        if len(planoConta) == 0:
            cmd = ctx.tb_plano_conta.insert().values(
                ID_PLANO=self.idPlanoPagtoFuturo,
                DESCRICAO_PLANO="RECEBIMENTO FUTURO",
                PAI_PLANO="1",
                CREDITO_DEBITO=0,
            )

            ctx.session.execute(cmd)

        hoje = datetime.today()

        mes = hoje.month
        ano = hoje.year

        if hoje.day >= 7:
            mes = (hoje + relativedelta(months=1)).month
            ano = (hoje + relativedelta(months=1)).year

        _vencimento = datetime(ano, mes, 7, hoje.hour, hoje.minute, 0)

        delFinanceiro = ctx.tb_financeiro.delete().where(
            ctx.mapFinanceiro.NUMERO_COMANDA == pagamento.ID_PAGAMENTO
        )

        ctx.session.execute(delFinanceiro)

        items = [
            produtoQtde(
                **{
                    "DESCRICAO_PRODUTO": await self.getDescricaoProduto(
                        item.ID_PRODUTO
                    ),
                    "QTDE": item.QTDE,
                }
            )
            for item in itemsPedido
        ]

        strItems = ", ".join(
            [f"[{item.DESCRICAO_PRODUTO}, Qtde: {str(item.QTDE)}]" for item in items]
        )

        descricao = "".join(
            [
                f"Recebimento futuro {pedido.NOME_CLIENTE} - Nr. Pedido {pedido.NUMERO_PEDIDO}",
                f", ITENS: {strItems}",
            ]
        )

        if len(descricao) > 250:
            descricao = descricao[0, 250]

        percentualAbatimento = 0.00

        try:
            percentualAbatimento = float(recPagamento.TAXA_PAGAMENTO)
        except:
            pass

        valorPago = float(pagamento.VALOR_PAGO)

        valorAbatimento = round(valorPago * (percentualAbatimento / 100), 2)

        cmd = ctx.tb_financeiro.insert().values(
            DATA_LANCAMENTO=datetime.today(),
            DATA_VENCIMENTO=_vencimento,
            DATA_PAGAMENTO=datetime(1901, 1, 1),
            HISTORICO=descricao,
            ID_PLANO=self.idPlanoPagtoFuturo,
            VALOR=valorPago,
            VALOR_DESCONTO=valorAbatimento,
            VALOR_ACRESCIMO=0,
            VALOR_TOTAL=valorPago - valorAbatimento,
            CREDITO_DEBITO=0,
            NUMERO_SEQ_NF_ENTRADA=0,
            ID_EMPRESA=1,
            NUMERO_COMANDA=pagamento.ID_PAGAMENTO,
        )

        ctx.session.execute(cmd)

        return True

    async def getDescricaoProduto(self, ID_PRODUTO) -> str:
        rec = (
            ctx.session.query(ctx.mapProduto)
            .filter(ctx.mapProduto.ID_PRODUTO == ID_PRODUTO)
            .first()
        )

        descricaoProduto = "" if rec is None else rec.DESCRICAO_PRODUTO

        return descricaoProduto

    async def listaFormaPagto(self):
        select1 = ctx.session.query(ctx.mapFormaPagto).order_by(
            ctx.mapFormaPagto.DESCRICAO_FORMA
        )

        lista = [
            listaFormaPagto(
                ID_FORMA=row.ID_FORMA, DESCRICAO_FORMA=row.DESCRICAO_FORMA
            ).model_dump_json()
            for row in select1
        ]

        return self.qBase.toRoute(lista, 200)

    async def checaConsumidorFinal(self) -> clienteEndereco:
        cliente = (
            ctx.session.query(ctx.mapCliente)
            .filter(ctx.mapCliente.NOME_CLIENTE.like("%{}%".format("CONSUMIDOR FINAL")))
            .all()
        )

        if len(cliente) == 0:
            return None

        ID_CLIENTE = [item for item in cliente][0].ID_CLIENTE

        endereco = (
            ctx.session.query(ctx.mapEnderecoCliente)
            .filter(ctx.mapEnderecoCliente.ID_CLIENTE == ID_CLIENTE)
            .all()
        )

        if len(endereco) == 0:
            return None

        ID_ENDERECO = [item for item in endereco][0].ID_ENDERECO

        return clienteEndereco(ID_CLIENTE=ID_CLIENTE, ID_ENDERECO=ID_ENDERECO)

    async def getTransporte(self) -> int:
        transporte = ctx.session.query(ctx.mapTransporte).all()

        if len(transporte) == 0:
            return None

        ID_TRANSPORTE = [item for item in transporte][0].ID_TRANSPORTE

        return int(ID_TRANSPORTE)

    async def listaAtendimento(self, NUMERO_PEDIDO):
        filters = [
            ctx.mapItemPedido.NUMERO_PEDIDO == NUMERO_PEDIDO,
            ctx.mapItemPedido.ID_PRODUTO == ctx.mapProduto.ID_PRODUTO,
        ]

        select1 = (
            ctx.session.query(
                ctx.mapItemPedido.NUMERO_PEDIDO,
                ctx.mapItemPedido.NUMERO_ITEM,
                ctx.mapItemPedido.ID_PRODUTO,
                ctx.mapProduto.DESCRICAO_PRODUTO,
                ctx.mapItemPedido.QTDE,
                ctx.mapItemPedido.PRECO_UNITARIO,
                ctx.mapItemPedido.VALOR_TOTAL,
            )
            .filter(*filters)
            .all()
        )

        lista = [
            itemPedidoCaixa(
                NUMERO_PEDIDO=row.NUMERO_PEDIDO,
                NUMERO_ITEM=row.NUMERO_ITEM,
                ID_PRODUTO=row.ID_PRODUTO,
                DESCRICAO_PRODUTO=row.DESCRICAO_PRODUTO,
                QTDE=row.QTDE,
                PRECO=row.PRECO_UNITARIO,
                TOTAL=row.VALOR_TOTAL,
            ).model_dump_json()
            for row in select1
        ]

        retorno = self.qBase.toRoute(lista, 200)

        return retorno

    async def get_Pagamentos(self, NUMERO_PEDIDO: int, query: any) -> str:
        retorno = "\n".join(
            [
                f"{item.FORMA_PAGTO}: {self.qBase.currency(item.VALOR_PAGO)}"
                for item in query
                if item.NUMERO_PEDIDO == NUMERO_PEDIDO
            ]
        )

        return retorno

    async def getNomeTransporte(self, ID_TRANSPORTE: int) -> str:
        t = ctx.mapTransporte

        query = ctx.session.query(t).filter(t.ID_TRANSPORTE == ID_TRANSPORTE).all()

        return query[0].NOME_TRANSPORTE if len(query) > 0 else ""

    async def getNomeCliente(self, ID_CLIENTE: int) -> str:
        t = ctx.mapCliente

        query = ctx.session.query(t).filter(t.ID_CLIENTE == ID_CLIENTE).all()

        return query[0].NOME_CLIENTE if len(query) > 0 else ""

    async def listaPedidos(self, filtro: filtroPedido) -> List[listaDePedido]:
        p = ctx.mapPedido

        soNumeros = self.qBase.onlyNumbers(filtro.FILTRO)

        filters = []
        retorno = []

        if len(filtro.FILTRO) == len(soNumeros) and len(soNumeros) > 0:
            filters.extend([p.NUMERO_PEDIDO == filtro.FILTRO])

            retorno = await self.getByNumeroPedido(filtro)

            if len(retorno) == 0 and filtro.ORIGEM == "Zé delivery":
                retorno = await self.getByNumeroZe(filtro)

            if len(retorno) == 0 and filtro.ORIGEM == "IFood":
                retorno = await self.getByNumeroIFood(filtro)

            return retorno

        retorno = await self.getByDataHora(filtro)

        return retorno

    async def getByNumeroPedido(self, filtro: filtroPedido) -> List[listaDePedido]:
        p = ctx.mapPedido
        t = ctx.mapTransporte
        pg = ctx.mapPedidoPagamento

        filters = [
            p.NUMERO_PEDIDO == filtro.FILTRO,
            p.ID_TRANSPORTE == t.ID_TRANSPORTE,
            pg.NUMERO_PEDIDO == p.NUMERO_PEDIDO,
        ]

        query = (
            ctx.session.query(
                pg.NUMERO_PEDIDO,
                pg.DATA_HORA,
                p.STATUS_PEDIDO,
                p.NOME_CLIENTE,
                p.TOTAL_PEDIDO,
                p.ORIGEM,
                p.ID_TRANSPORTE,
                t.NOME_TRANSPORTE,
                p.ID_CLIENTE,
                p.NUMERO_PEDIDO_IFOOD,
                p.ENDERECO_CLIENTE,
                p.TELEFONE_CLIENTE,
                pg.FORMA_PAGTO,
                pg.VALOR_PAGO,
            )
            .filter(*filters)
            .all()
        )

        retorno = await self.retornoQueryPedidos(query)

        return retorno

    async def getByNumeroZe(self, filtro: filtroListaPedido) -> List[listaDePedido]:
        p = ctx.mapPedido
        t = ctx.mapTransporte
        pg = ctx.mapPedidoPagamento

        filters = [
            p.NUMERO_PEDIDO_ZE_DELIVERY == filtro.FILTRO,
            p.ORIGEM == filtro.ORIGEM,
            p.ID_TRANSPORTE == t.ID_TRANSPORTE,
            pg.NUMERO_PEDIDO == p.NUMERO_PEDIDO,
        ]

        query = (
            ctx.session.query()
            .order_by(pg.DATA_HORA)
            .filter(*filters)
            .offset(filtro.START)
            .limit(50)
            .all()
        )

        query = (
            ctx.session.query(
                pg.NUMERO_PEDIDO,
                pg.DATA_HORA,
                p.STATUS_PEDIDO,
                p.NOME_CLIENTE,
                p.TOTAL_PEDIDO,
                p.ORIGEM,
                p.ID_TRANSPORTE,
                t.NOME_TRANSPORTE,
                p.ID_CLIENTE,
                p.NUMERO_PEDIDO_IFOOD,
                p.ENDERECO_CLIENTE,
                p.TELEFONE_CLIENTE,
                pg.FORMA_PAGTO,
                pg.VALOR_PAGO,
            )
            .filter(*filters)
            .all()
        )

        retorno = await self.retornoQueryPedidos(query)

        return retorno

    async def getByNumeroIFood(self, filtro: filtroListaPedido) -> List[listaDePedido]:
        p = ctx.mapPedido
        t = ctx.mapTransporte
        pg = ctx.mapPedidoPagamento

        filters = [
            p.NUMERO_PEDIDO_IFOOD == filtro.FILTRO,
            p.ORIGEM == filtro.ORIGEM,
            p.ID_TRANSPORTE == t.ID_TRANSPORTE,
            pg.NUMERO_PEDIDO == p.NUMERO_PEDIDO,
        ]

        query = (
            ctx.session.query(
                pg.NUMERO_PEDIDO,
                pg.DATA_HORA,
                p.STATUS_PEDIDO,
                p.NOME_CLIENTE,
                p.TOTAL_PEDIDO,
                p.ORIGEM,
                p.ID_TRANSPORTE,
                t.NOME_TRANSPORTE,
                p.ID_CLIENTE,
                p.NUMERO_PEDIDO_IFOOD,
                p.ENDERECO_CLIENTE,
                p.TELEFONE_CLIENTE,
                pg.FORMA_PAGTO,
                pg.VALOR_PAGO,
            )
            .filter(*filters)
            .all()
        )

        retorno = await self.retornoQueryPedidos(query)

        return retorno

    async def getByDataHora(self, filtro: filtroListaPedido) -> List[listaDePedido]:
        p = ctx.mapPedido
        t = ctx.mapTransporte
        pg = ctx.mapPedidoPagamento

        d1 = datetime.today() + timedelta(days=-15)
        d2 = datetime.today() + timedelta(hours=1)

        filters = [p.DATA_HORA >= d1, p.DATA_HORA < d2]

        if len(filtro.FILTRO) > 0:
            filters.append(p.NOME_CLIENTE.like(f"%{filtro.FILTRO}%"))

        if filtro.ORIGEM != "Todos":
            filters.append(p.ORIGEM == filtro.ORIGEM)

        if 0 not in filtro.STATUS:
            filters.append(p.STATUS_PEDIDO.in_(filtro.STATUS))

        filters.extend(
            (p.ID_TRANSPORTE == t.ID_TRANSPORTE, pg.NUMERO_PEDIDO == p.NUMERO_PEDIDO)
        )

        query = (
            ctx.session.query(
                pg.NUMERO_PEDIDO,
                pg.DATA_HORA,
                p.STATUS_PEDIDO,
                p.NOME_CLIENTE,
                p.TOTAL_PEDIDO,
                p.ORIGEM,
                p.ID_TRANSPORTE,
                t.NOME_TRANSPORTE,
                p.ID_CLIENTE,
                p.NUMERO_PEDIDO_IFOOD,
                p.ENDERECO_CLIENTE,
                p.TELEFONE_CLIENTE,
                pg.FORMA_PAGTO,
                pg.VALOR_PAGO,
            )
            .order_by(desc(pg.DATA_HORA))
            .filter(*filters)
            .offset(filtro.START)
            .limit(50)
            .all()
        )

        retorno = await self.retornoQueryPedidos(query)

        return retorno

    async def retornoQueryPedidos(self, query) -> List[listaDePedido]:
        e = ctx.mapEmpresa

        empresa = ctx.session.query(e).all()[0]

        retorno = []

        lista = sorted(query, key=lambda e: e.DATA_HORA, reverse=True)

        for item in lista:
            if (
                len(
                    list(
                        filter(lambda e: e.NUMERO_PEDIDO == item.NUMERO_PEDIDO, retorno)
                    )
                )
                > 0
            ):
                continue

            retorno.append(
                listaDePedido(
                    NUMERO_PEDIDO=item.NUMERO_PEDIDO,
                    DATA_HORA=datetime.strftime(item.DATA_HORA, "%d/%m/%Y %H:%M"),
                    ORIGEM="" if item.ORIGEM is None else item.ORIGEM,
                    STATUS_PEDIDO=Config.getStatus(item),
                    NOME_CLIENTE=item.NOME_CLIENTE,
                    TRANSPORTE=item.NOME_TRANSPORTE,
                    TOTAL_PEDIDO=0.00
                    if item.TOTAL_PEDIDO is None
                    else float(item.TOTAL_PEDIDO),
                    PAGAMENTOS=await self.get_Pagamentos(item.NUMERO_PEDIDO, query),
                    ENDERECO=empresa.ENDERECO
                    if len(item.ENDERECO_CLIENTE) == 0
                    else item.ENDERECO_CLIENTE,
                    TELEFONE=empresa.TELEFONE
                    if len(item.TELEFONE_CLIENTE) == 0
                    else item.TELEFONE_CLIENTE,
                )
            )

        return retorno

    async def getPedido(self, filtro: filtroPedido):
        p = ctx.mapPedido
        ip = ctx.mapItemPedido
        pg = ctx.mapPedidoPagamento

        numeroPedido = 0

        try:
            numeroPedido = int(filtro.FILTRO)
        except:
            pass

        if numeroPedido == 0:
            raise Exception("Numero de pedido inválido")

        filters = [p.NUMERO_PEDIDO == numeroPedido]

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
                p.INFO_ADICIONAL,
            )
            .filter(*filters)
            .all()
        )

        if len(pedido) == 0:
            raise Exception("Pedido não encontrado na base do sistema")

        items = ctx.session.query(ip).filter(ip.NUMERO_PEDIDO == numeroPedido).all()

        itemsPedido = [
            editItemPedido(
                NUMERO_ITEM=item.NUMERO_ITEM,
                NUMERO_PEDIDO=item.NUMERO_PEDIDO,
                ID_PRODUTO=item.ID_PRODUTO,
                ID_TRIBUTO=item.ID_TRIBUTO,
                DESCRICAO_PRODUTO=await self.getDescricaoProduto(item.ID_PRODUTO),
                QTDE=int(item.QTDE),
                PRECO=float(item.PRECO_UNITARIO),
                TOTAL=float(item.VALOR_TOTAL),
            )
            for item in items
        ]

        pag = ctx.session.query(pg).filter(pg.NUMERO_PEDIDO == numeroPedido).all()

        pagamentos = [
            editPedidoPagamento(
                ID_PAGAMENTO=item.ID_PAGAMENTO,
                NUMERO_PEDIDO=item.NUMERO_PEDIDO,
                FORMA_PAGTO=item.FORMA_PAGTO,
                ID_CAIXA=item.ID_CAIXA,
                VALOR_PAGO=item.VALOR_PAGO,
                CODIGO_NSU="" if item.CODIGO_NSU is None else item.CODIGO_NSU,
            )
            for item in pag
        ]

        rec = pedido[0]

        retorno = editPedido(
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
            PAGAMENTOS=pagamentos,
            ID_ENDERECO=rec.ID_ENDERECO,
        )

        return retorno

    async def deletaItemPedido(self, item: numeroItemPedido):
        p = ctx.mapItemPedido

        numeroPedido = (
            ctx.session.query(p)
            .filter(p.NUMERO_ITEM == item.NUMERO_ITEM)
            .all()[0]
            .NUMERO_PEDIDO
        )

        item = ctx.tb_item_pedido.delete().where(p.NUMERO_ITEM == item.NUMERO_ITEM)

        ctx.session.execute(item)
        ctx.session.commit()

        await self.recalculaTotaisPedido(numeroPedido)

    async def deletaPagamento(self, ID_PAGAMENTO: int):
        f = ctx.mapFinanceiro

        cmd = ctx.tb_financeiro.delete().where(f.NUMERO_COMANDA == ID_PAGAMENTO)

        ctx.session.execute(cmd)

    async def cancelaPedido(self, record: listaDePedido):
        ip = ctx.mapItemPedido
        p = ctx.mapPedido
        pg = ctx.mapPedidoPagamento

        itens = (
            ctx.session.query(ip).filter(ip.NUMERO_PEDIDO == record.NUMERO_PEDIDO).all()
        )

        pedido = (
            ctx.session.query(p)
            .filter(p.NUMERO_PEDIDO == record.NUMERO_PEDIDO)
            .all()[0]
        )

        _status = pedido.STATUS_PEDIDO

        cmd = (
            ctx.tb_pedido.update()
            .values(STATUS_PEDIDO=5)
            .where(p.NUMERO_PEDIDO == record.NUMERO_PEDIDO)
        )

        ctx.session.execute(cmd)

        if _status == 3:
            [
                await self.baixaEstoque(
                    itemPedido(
                        NUMERO_ITEM=item.NUMERO_ITEM,
                        NUMERO_PEDIDO=item.NUMERO_PEDIDO,
                        ID_PRODUTO=item.ID_PRODUTO,
                        CODIGO_PRODUTO=item.CODIGO_PRODUTO,
                        QTDE=item.QTDE,
                        PRECO_UNITARIO=item.PRECO_UNITARIO,
                        VALOR_TOTAL=item.VALOR_TOTAL,
                        ID_TRIBUTO=item.ID_TRIBUTO,
                        OBS_ITEM=item.OBS_ITEM,
                        ID_ITEM_LOCAL=0,
                        ID_TERMINAL=0,
                    ),
                    0,
                )
                for item in itens
            ]

        pagamentos = (
            ctx.session.query(pg).filter(pg.NUMERO_PEDIDO == record.NUMERO_PEDIDO).all()
        )

        ids = [item.ID_PAGAMENTO for item in pagamentos]

        [await self.deletaPagamento(id) for id in ids]

        ctx.session.commit()

    async def savePedido(self, record: dadosPedido):
        p = ctx.mapPedido
        pg = ctx.mapPedidoPagamento

        totalPedido = round(
            (record.TOTAL_PRODUTOS + record.TAXA_ENTREGA + record.ADICIONAL)
            - record.DESCONTO,
            2,
        )

        qPg = (
            ctx.session.query(pg.NUMERO_PEDIDO, pg.VALOR_PAGO)
            .filter(pg.NUMERO_PEDIDO == record.NUMERO_PEDIDO)
            .all()
        )

        somaPagamentos = sum(
            [float(item.VALOR_PAGO) for item in qPg if item.VALOR_PAGO is not None]
        )

        troco = 0.00

        if somaPagamentos > totalPedido:
            troco = round(somaPagamentos - totalPedido, 2)

        cmd = (
            ctx.tb_pedido.update()
            .values(
                ID_CLIENTE=record.ID_CLIENTE,
                ID_ENDERECO=record.ID_ENDERECO,
                ID_TRANSPORTE=record.ID_TRANSPORTE,
                TOTAL_PRODUTOS=record.TOTAL_PRODUTOS,
                TAXA_ENTREGA=record.TAXA_ENTREGA,
                ADICIONAL=record.ADICIONAL,
                DESCONTO=record.DESCONTO,
                INFO_ADICIONAL=record.INFO_ADICIONAL,
                TOTAL_PEDIDO=totalPedido,
                TROCO=troco,
            )
            .where(p.NUMERO_PEDIDO == record.NUMERO_PEDIDO)
        )

        ctx.session.execute(cmd)
        ctx.session.commit()

    async def recalculaTotaisPedido(self, NUMERO_PEDIDO: int):
        p = ctx.mapPedido
        pg = ctx.mapPedidoPagamento
        i = ctx.mapItemPedido

        record = ctx.session.query(p).filter(p.NUMERO_PEDIDO == NUMERO_PEDIDO).all()[0]

        items = ctx.session.query(i).filter(i.NUMERO_PEDIDO == NUMERO_PEDIDO).all()

        somaProdutos = 0.00

        try:
            somaProdutos = sum([float(item.VALOR_TOTAL) for item in items])
        except:
            pass

        totalPedido = round(
            (somaProdutos + float(record.TAXA_ENTREGA) + float(record.ADICIONAL))
            - float(record.DESCONTO),
            2,
        )

        qPg = (
            ctx.session.query(pg.NUMERO_PEDIDO, pg.VALOR_PAGO)
            .filter(pg.NUMERO_PEDIDO == record.NUMERO_PEDIDO)
            .all()
        )

        somaPagamentos = sum(
            [float(item.VALOR_PAGO) for item in qPg if item.VALOR_PAGO is not None]
        )

        troco = 0.00

        if somaPagamentos > totalPedido:
            troco = round(somaPagamentos - totalPedido, 2)

        cmd = (
            ctx.tb_pedido.update()
            .values(TOTAL_PRODUTOS=somaProdutos, TOTAL_PEDIDO=totalPedido, TROCO=troco)
            .where(p.NUMERO_PEDIDO == record.NUMERO_PEDIDO)
        )

        ctx.session.execute(cmd)
        ctx.session.commit()

    async def addItem(self, record: itemPedido):
        p = ctx.mapProduto

        produto = (
            ctx.session.query(p).filter(p.ID_PRODUTO == record.ID_PRODUTO).all()[0]
        )

        record.CODIGO_PRODUTO = produto.CODIGO_PRODUTO
        record.ID_TRIBUTO = produto.ID_TRIBUTO
        record.PRECO_UNITARIO = float(produto.PRECO_BALCAO)
        record.VALOR_TOTAL = round(record.QTDE * record.PRECO_UNITARIO, 2)

        await self.gravaItensPedido(record)
        await self.recalculaTotaisPedido(record.NUMERO_PEDIDO)

    async def listaItens(self, filtro: filtroNumeroPedido) -> List[editItemPedido]:
        i = ctx.mapItemPedido

        NUMERO_PEDIDO = filtro.NUMERO_PEDIDO

        query = ctx.session.query(i).filter(i.NUMERO_PEDIDO == NUMERO_PEDIDO).all()

        retorno = [
            editItemPedido(
                NUMERO_ITEM=item.NUMERO_ITEM,
                NUMERO_PEDIDO=item.NUMERO_PEDIDO,
                ID_PRODUTO=item.ID_PRODUTO,
                ID_TRIBUTO=item.ID_TRIBUTO,
                DESCRICAO_PRODUTO=await self.getDescricaoProduto(item.ID_PRODUTO),
                QTDE=item.QTDE,
                PRECO=0.00
                if item.PRECO_UNITARIO is None
                else float(item.PRECO_UNITARIO),
                TOTAL=0.00 if item.VALOR_TOTAL is None else float(item.VALOR_TOTAL),
            )
            for item in query
        ]

        return retorno

    async def getTotalPedido(self, filtro: filtroNumeroPedido) -> TOTAL_PEDIDO:
        p = ctx.mapPedido
        i = ctx.mapItemPedido

        record = (
            ctx.session.query(p)
            .filter(p.NUMERO_PEDIDO == filtro.NUMERO_PEDIDO)
            .all()[0]
        )

        items = (
            ctx.session.query(i).filter(i.NUMERO_PEDIDO == filtro.NUMERO_PEDIDO).all()
        )

        somaProdutos = 0.00

        try:
            somaProdutos = sum([float(item.VALOR_TOTAL) for item in items])
        except:
            pass

        totalPedido = round(
            (somaProdutos + float(record.TAXA_ENTREGA) + float(record.ADICIONAL))
            - float(record.DESCONTO),
            2,
        )

        retorno = TOTAL_PEDIDO(
            TOTAL_PRODUTOS=somaProdutos,
            VALOR_ADICIONAL=float(record.ADICIONAL),
            VALOR_DESCONTO=float(record.DESCONTO),
            TAXA_ENTREGA=float(record.TAXA_ENTREGA),
            TOTAL_PEDIDO=totalPedido,
        )

        return retorno

    async def get_ID_forma_pagamento(self, DESCRICAO: str) -> int:
        f = ctx.mapFormaPagto

        query = ctx.session.query(f).filter(f.DESCRICAO_FORMA == DESCRICAO).all()

        return query[0].ID_FORMA if len(query) > 0 else 0

    async def listaPagamentos(
        self, filtro: filtroNumeroPedido
    ) -> List[pagamentoPedido]:
        pg = ctx.mapPedidoPagamento

        query = (
            ctx.session.query(pg).filter(pg.NUMERO_PEDIDO == filtro.NUMERO_PEDIDO).all()
        )

        retorno = [
            pagamentoPedido(
                NUMERO_PEDIDO=item.NUMERO_PEDIDO,
                ID_PAGAMENTO=item.ID_PAGAMENTO,
                ID_FORMA=await self.get_ID_forma_pagamento(item.FORMA_PAGTO),
                DESCRICAO_FORMA=item.FORMA_PAGTO,
                VALOR_PAGO=0.00 if item.VALOR_PAGO is None else float(item.VALOR_PAGO),
                CODIGO_AUTORIZACAO="" if item.CODIGO_NSU is None else item.CODIGO_NSU,
            )
            for item in query
        ]

        return retorno

    async def deleteItemPagamento(self, filtro: filtroIDPagamento):
        pg = ctx.mapPedidoPagamento

        cmd = ctx.tb_pedido_pagamento.delete().where(
            pg.ID_PAGAMENTO == filtro.ID_PAGAMENTO
        )

        ctx.session.execute(cmd)
        ctx.session.commit()

    async def addItemPagamento(self, dados: pagamentoPedido):
        pg = ctx.mapPedidoPagamento
        p = ctx.mapPedido

        pedido = (
            ctx.session.query(p).filter(p.NUMERO_PEDIDO == dados.NUMERO_PEDIDO).all()[0]
        )

        cmd = ctx.tb_pedido_pagamento.insert().values(
            ID_PAGAMENTO=0,
            NUMERO_PEDIDO=dados.NUMERO_PEDIDO,
            DATA_HORA=datetime.now(),
            FORMA_PAGTO=dados.DESCRICAO_FORMA,
            VALOR_PAGO=dados.VALOR_PAGO,
            ID_CAIXA=pedido.ID_CAIXA,
            ORIGEM=pedido.ORIGEM,
            ID_PAGAMENTO_LOCAL=0,
            ID_TERMINAL=0,
            CODIGO_NSU="",
            VALOR_PAGO_STONE=0,
            DATA_AUTORIZACAO=None,
            BANDEIRA="",
        )

        ctx.session.execute(cmd)
        ctx.session.commit()

    async def concluiPagamento(self, dados: conclusaoPagamento):
        if dados.IMPRESSAO == True:
            cmd = ctx.tb_fila_comanda.insert().values(
                ID_FILA=0,
                NUMERO_COMANDA=dados.NUMERO_PEDIDO,
                PROCESSADO=dados.NUMERO_IMPRESSORA,
            )

            ctx.session.execute(cmd)

        if dados.FISCAL == True:
            cmd = ctx.tb_pedido_nfe.insert().values(
                ID_PEDIDO_NFE=0,
                NUMERO_PEDIDO=dados.NUMERO_PEDIDO,
                XML_NOTA="",
                RESPOSTA_SEFAZ="",
                NUMERO_NF=0,
                SERIE_NF="1",
                CHAVE_ACESSO_NF="",
                PROTOCOLO_AUTORIZACAO="",
                PROCESSADO=0,
                ASSINATURA_NFCE="",
                DATA_AUTORIZACAO_NFCE="",
                CHAVE_PEDIDO="",
                XML_DEVOLUCAO="",
                NUMERO_NF_DEVOLUCAO=0,
                GERAR_DANFE=0,
                ID_EMPRESA=1,
                CHAVE_NF_DEVOLUCAO="",
                ID_PEDIDO_NFE_LOCAL=0,
                ID_TERMINAL="",
            )

            ctx.session.execute(cmd)

        ctx.session.commit()

    async def emiteNFCe(self, dados: emissaoNFCe):
        nf = ctx.mapPedidoNFe
        e = ctx.mapEmpresa
        p = ctx.mapPedido

        filters = [nf.NUMERO_PEDIDO == dados.NUMERO_PEDIDO, nf.PROCESSADO == 0]

        existingQueue = ctx.session.query(nf).filter(*filters).all()

        if len(existingQueue) > 0:
            return

        if len(dados.CPF) > 0:
            cmd = (
                ctx.tb_pedido.update()
                .values(CPF=dados.CPF)
                .where(p.NUMERO_PEDIDO == dados.NUMERO_PEDIDO)
            )

            ctx.session.execute(cmd)

        empresa = ctx.session.query(e).all()

        cmd = ctx.tb_pedido_nfe.insert().values(
            ID_PEDIDO_NFE=0,
            NUMERO_PEDIDO=dados.NUMERO_PEDIDO,
            XML_NOTA="",
            RESPOSTA_SEFAZ="",
            NUMERO_NF=0,
            SERIE_NF=empresa[0].SERIE_NFCE,
            CHAVE_ACESSO_NF="",
            PROTOCOLO_AUTORIZACAO="",
            PROCESSADO=1,
            ASSINATURA_NFCE="",
            DATA_AUTORIZACAO_NFCE="",
            CHAVE_PEDIDO="",
            XML_DEVOLUCAO="",
            NUMERO_NF_DEVOLUCAO=0,
            GERAR_DANFE=0,
            ID_EMPRESA=empresa[0].ID_EMPRESA,
            CHAVE_NF_DEVOLUCAO="",
            ID_PEDIDO_NFE_LOCAL=0,
            ID_TERMINAL=0,
        )

        ctx.session.execute(cmd)
        ctx.session.commit()

    async def checaEmissaoNFCe(self, filtro: filtroNumeroPedido) -> NFCe_Processada:
        nf = ctx.mapPedidoNFe

        query = (
            ctx.session.query(nf)
            .filter(
                *(nf.NUMERO_PEDIDO == filtro.NUMERO_PEDIDO, nf.PROCESSADO.in_((10, 2)))
            )
            .all()
        )

        autorizado = list(filter(lambda e: e.PROCESSADO == 10, query))

        recusada = list(filter(lambda e: e.PROCESSADO == 2, query))

        if len(autorizado) > 0:
            rec = autorizado[0]

            return NFCe_Processada(
                NUMERO_PEDIDO=rec.NUMERO_PEDIDO,
                NUMERO_NF=rec.NUMERO_NF,
                PROTOCOLO_AUTORIZACAO=rec.PROTOCOLO_AUTORIZACAO,
                DATA_AUTORIZACAO=datetime.strftime(
                    rec.DATA_AUTORIZACAO_NFCE, "%d/%m/%Y %H:%M"
                ),
                MENSAGEM=rec.RESPOSTA_SEFAZ,
            )

        if len(recusada) > 0:
            rec = recusada[0]

            return NFCe_Processada(
                NUMERO_PEDIDO=rec.NUMERO_PEDIDO,
                NUMERO_NF=rec.NUMERO_NF,
                PROTOCOLO_AUTORIZACAO="",
                DATA_AUTORIZACAO="",
                MENSAGEM=rec.RESPOSTA_SEFAZ,
            )

        return NFCe_Processada(
            NUMERO_PEDIDO=filtro.NUMERO_PEDIDO,
            NUMERO_NF=0,
            PROTOCOLO_AUTORIZACAO="",
            DATA_AUTORIZACAO="",
            MENSAGEM="Aguardando resposta",
        )

    async def imprimePedido(self, dados: impressaoAvulsa):
        cmd = ctx.tb_fila_comanda.insert().values(
            ID_FILA=0,
            NUMERO_COMANDA=dados.NUMERO_PEDIDO,
            PROCESSADO=dados.NUMERO_IMPRESSORA,
        )

        ctx.session.execute(cmd)
        ctx.session.commit()

    async def buscaPedidoImpressao(
        self, filtro: filtroImpressaoPedido
    ) -> List[impressaoPedidoBalcao]:
        retorno = []

        f = ctx.mapFilaComanda
        p = ctx.mapPedido
        pg = ctx.mapPedidoPagamento
        ip = ctx.mapItemPedido
        c = ctx.mapCliente
        e = ctx.mapEnderecoCliente
        at = ctx.mapAtendimentoComanda
        pr = ctx.mapProduto
        t = ctx.mapTransporte

        filas = ctx.session.query(f).filter(f.PROCESSADO == filtro.MAQUINA).all()

        updated = False

        for fila in filas:
            Pedido = (
                ctx.session.query(p)
                .filter(p.NUMERO_PEDIDO == fila.NUMERO_COMANDA)
                .all()
            )

            items = (
                ctx.session.query(ip)
                .filter(ip.NUMERO_PEDIDO == fila.NUMERO_COMANDA)
                .all()
            )

            pagamento = (
                ctx.session.query(pg)
                .filter(pg.NUMERO_PEDIDO == fila.NUMERO_COMANDA)
                .all()
            )

            if len(Pedido) == 0 or len(items) == 0 or len(pagamento) == 0:
                cmdDelete = ctx.tb_fila_comanda.delete().where(
                    f.NUMERO_COMANDA == fila.NUMERO_COMANDA
                )

                ctx.session.execute(cmdDelete)
                updated = True

        if updated:
            ctx.session.commit()

        pedidos = (
            ctx.session.query(f.NUMERO_COMANDA)
            .distinct()
            .filter(f.PROCESSADO == filtro.MAQUINA)
            .all()
        )

        pedidos = [item[0] for item in pedidos]

        query = ctx.session.query(p).filter(p.NUMERO_PEDIDO.in_(pedidos)).all()

        nComanda = query[0].NUMERO_PEDIDO if len(query) > 0 else 0

        if nComanda == 0:
            return []

        pedido = ctx.session.query(p).filter(p.NUMERO_PEDIDO.in_(pedidos)).first()

        dadosCliente = (
            ctx.session.query(c).filter(c.ID_CLIENTE == pedido.ID_CLIENTE).first()
        )

        dadosEndereco = (
            ctx.session.query(e).filter(e.ID_ENDERECO == pedido.ID_ENDERECO).first()
        )

        pag = (
            ctx.session.query(pg).filter(pg.NUMERO_PEDIDO == pedido.NUMERO_PEDIDO).all()
        )

        formasPagamento = [
            FORMAS_PAGTO_IMPRESSAO(
                DESCRICAO=item.FORMA_PAGTO,
                VALOR=self.qBase.currency(float(item.VALOR_PAGO)),
            )
            for item in pag
        ]

        itemPedido = (
            ctx.session.query(ip).filter(ip.NUMERO_PEDIDO == pedido.NUMERO_PEDIDO).all()
        )

        percentual = (f"% geral", f"% sobre o pagto")

        TOTAL_QTDE = sum([item.QTDE for item in itemPedido])
        TOTAL_VALOR = (
            float(pedido.TOTAL_PRODUTOS) if pedido.TOTAL_PRODUTOS is not None else 0
        )
        TROCO = float(pedido.TROCO) if pedido.TROCO is not None else 0
        DESCONTO = float(pedido.DESCONTO) if pedido.DESCONTO is not None else 0

        adicional = float(pedido.ADICIONAL) if pedido.ADICIONAL is not None else 0
        produtos = (
            float(pedido.TOTAL_PRODUTOS) if pedido.TOTAL_PRODUTOS is not None else 0
        )

        CAIXINHA = (
            produtos * (adicional / 100)
            if pedido.TIPO_ADICIONAL in percentual
            else adicional
        )
        TAXA_ENTREGA = (
            float(pedido.TAXA_ENTREGA) if pedido.TAXA_ENTREGA is not None else 0
        )

        qAtendimento = (
            ctx.session.query(at)
            .filter(at.NUMERO_COMANDA == pedido.NUMERO_PEDIDO)
            .all()
        )

        atendimento = (
            qAtendimento[0].NUMERO_COMANDA_ATENDIMENTO if len(qAtendimento) > 0 else 0
        )
        mesa = qAtendimento[0].MESA if len(qAtendimento) > 0 else ""
        nomeMesa = qAtendimento[0].NOME_MESA if len(qAtendimento) > 0 else ""

        for item in items:
            produto = (
                ctx.session.query(pr).filter(pr.ID_PRODUTO == item.ID_PRODUTO).first()
            )

            descricaoProduto = produto.DESCRICAO_PRODUTO
            obs = item.OBS_ITEM

            endereco = "".join(
                (
                    dadosEndereco.ENDERECO.strip(),
                    ", ",
                    dadosEndereco.NUMERO_ENDERECO.strip(),
                    f"{dadosEndereco.COMPLEMENTO_ENDERECO} - "
                    if dadosEndereco.COMPLEMENTO_ENDERECO is not None
                    else "",
                )
            )

            endereco = self.qBase.cleanSpecialChars(endereco)

            bairro = (
                self.qBase.cleanSpecialChars(dadosEndereco.BAIRRO)
                if dadosEndereco.BAIRRO is not None
                else ""
            )

            if pedido.ORIGEM == "IFood":
                bairro = self.qBase.cleanSpecialChars(pedido.BAIRRO_CLIENTE)

            if isinstance(obs, str):
                if len(obs) > 0:
                    descricaoProduto += f" - {obs}"

            cidade = (
                self.qBase.cleanSpecialChars(dadosEndereco.MUNICIPIO)
                if dadosEndereco.MUNICIPIO is not None
                else ""
            )
            infoAdicional = (
                self.qBase.cleanSpecialChars(pedido.INFO_ADICIONAL)
                if pedido.INFO_ADICIONAL is not None
                else ""
            )

            obs += f" {self.qBase.cleanSpecialChars(dadosCliente.OBS_CLIENTE)}"

            transporte = (
                ctx.session.query(t)
                .filter(t.ID_TRANSPORTE == pedido.ID_TRANSPORTE)
                .all()
            )

            nomeTransporte = (
                transporte[0].NOME_TRANSPORTE if len(transporte) > 0 else ""
            )

            retorno.append(
                impressaoPedidoBalcao(
                    CPF=pedido.CPF,
                    NUMERO_COMANDA=pedido.NUMERO_PEDIDO,
                    NUMERO_COMANDA_ATENDIMENTO=atendimento,
                    MESA=mesa if mesa is not None else "",
                    NUMERO_PEDIDO_ZE_DELIVERY=int(pedido.NUMERO_PEDIDO_ZE_DELIVERY)
                    if pedido.NUMERO_PEDIDO_ZE_DELIVERY is not None
                    else 0,
                    NUMERO_DELIVERY=int(pedido.NUMERO_PEDIDO_DELIVERY)
                    if pedido.NUMERO_PEDIDO_DELIVERY is not None
                    else 0,
                    NUMERO_PEDIDO_IFOOD=pedido.NUMERO_PEDIDO_IFOOD,
                    DATA_HORA=self.qBase.TrataDataHora(pedido.DATA_HORA),
                    NOME_CLIENTE=pedido.NOME_CLIENTE,
                    ENDERECO=endereco,
                    BAIRRO=bairro,
                    CIDADE=cidade,
                    FORMA_PAGTO=formasPagamento,
                    PRODUTO=descricaoProduto,
                    QTDE=str(int(item.QTDE)),
                    PRECO=self.qBase.currency(item.PRECO_UNITARIO),
                    TOTAL=self.qBase.currency(item.VALOR_TOTAL),
                    DESCONTO=self.qBase.currency(DESCONTO),
                    CAIXINHA=self.qBase.currency(CAIXINHA),
                    TOTAL_QTDE=str(int(TOTAL_QTDE)),
                    TOTAL_VALOR=self.qBase.currency(TOTAL_VALOR),
                    TROCO=self.qBase.currency(TROCO),
                    COMENTARIOS=obs,
                    TELEFONE=dadosCliente.TELEFONE_CLIENTE.strip()
                    if dadosCliente.TELEFONE_CLIENTE is not None
                    else "",
                    CHAVE_PEDIDO="",
                    CODIGO_IDENTIFICACAO_IFOOD=pedido.CODIGO_IDENTIFICACAO_IFOOD.strip()
                    if pedido.CODIGO_IDENTIFICACAO_IFOOD is not None
                    else "",
                    ORDER_NUMBER_GOOMER=int(pedido.ORDER_NUMBER_GOOMER)
                    if pedido.CODIGO_IDENTIFICACAO_IFOOD is not None
                    else 0,
                    ORDER_NUMBER_WABIZ=int(pedido.ORDER_NUMBER_WABIZ)
                    if pedido.ORDER_NUMBER_WABIZ is not None
                    else 0,
                    PREPARO_COZINHA=0,
                    ORIGEM=pedido.ORIGEM,
                    TRANSPORTE=nomeTransporte,
                    NOME_MESA=nomeMesa if nomeMesa is not None else "",
                    NUMERO_VENDA=int(pedido.NUMERO_VENDA)
                    if pedido.NUMERO_VENDA is not None
                    else 0,
                    TAXA_ENTREGA=self.qBase.currency(TAXA_ENTREGA),
                    NUMERO_PEDIDO_DELIVERY="",
                )
            )

        return retorno

    async def getDadosNFCe(self, filtro: filtroNumeroPedido) -> List[dadosNFCe]:
        p = ctx.mapPedido
        ip = ctx.mapItemPedido
        pg = ctx.mapPedidoPagamento
        e = ctx.mapEmpresa
        pnf = ctx.mapPedidoNFe
        c = ctx.mapCliente
        en = ctx.mapEnderecoCliente
        pr = ctx.mapProduto
        t = ctx.mapTransporte
        m = ctx.mapMunicipio
        tr = ctx.mapTributo

        retorno = []

        pedido = (
            ctx.session.query(p).filter(p.NUMERO_PEDIDO == filtro.NUMERO_PEDIDO).first()
        )

        itemsPedido = (
            ctx.session.query(ip).filter(ip.NUMERO_PEDIDO == filtro.NUMERO_PEDIDO).all()
        )

        p = (1, 10)

        pedidoNFe = (
            ctx.session.query(pnf)
            .filter(pnf.NUMERO_PEDIDO == filtro.NUMERO_PEDIDO)
            .all()
        )

        if len(pedidoNFe) == 0:
            raise Exception("Pedido não existe")

        ID_CLIENTE = pedido.ID_CLIENTE
        ID_ENDERECO = pedido.ID_ENDERECO
        ID_EMITENTE = pedidoNFe[0].ID_EMPRESA

        dadosEmpresa = ctx.session.query(e).filter(e.ID_EMPRESA == ID_EMITENTE).first()

        dadosCliente = ctx.session.query(c).filter(c.ID_CLIENTE == ID_CLIENTE).first()

        dadosEndereco = (
            ctx.session.query(en).filter(en.ID_ENDERECO == ID_ENDERECO).first()
        )

        if dadosEndereco.ENDERECO is None or len(dadosEndereco.ENDERECO.strip()) == 0:
            dadosEndereco.ENDERECO = dadosEmpresa.ENDERECO
            dadosEndereco.NUMERO_ENDERECO = ""
            dadosEndereco.COMPLEMENTO_ENDERECO = ""
            dadosEndereco.CEP = dadosEmpresa.CEP
            dadosEndereco.BAIRRO = dadosEmpresa.BAIRRO
            dadosEndereco.MUNICIPIO = dadosEmpresa.CIDADE
            dadosEndereco.UF = dadosEmpresa.UF

        formasPagamento = [
            FORMAS_PAGTO_IMPRESSAO(
                DESCRICAO=item.FORMA_PAGTO, VALOR=self.qBase.currency(item.VALOR_PAGO)
            )
            for item in ctx.session.query(pg)
            .filter(pg.NUMERO_PEDIDO == filtro.NUMERO_PEDIDO)
            .all()
        ]

        TOTAL_QTDE = sum([int(item.QTDE) for item in itemsPedido])
        TOTAL_VALOR = float(pedido.TOTAL_PEDIDO) - float(pedido.DESCONTO)
        TROCO = float(pedido.TROCO)
        DESCONTO = float(pedido.DESCONTO)

        if DESCONTO >= pedido.TOTAL_PEDIDO:
            DESCONTO = 0.00

        _nf = []

        qAutorizada = [item for item in pedidoNFe if item.PROCESSADO == 10]

        if len(qAutorizada) > 0:
            _nf.append(str(qAutorizada[0].NUMERO_NF))
        else:
            nNF = 0
            semNumero = pedidoNFe[0].NUMERO_NF == 0

            if pedidoNFe[0].GERAR_DANFE == 1:
                if semNumero:
                    nNF = dadosEmpresa.NUMERO_NF + 1
                else:
                    nNF = dadosEmpresa.NUMERO_NF
            else:
                if semNumero:
                    nNF = dadosEmpresa.NUMERO_NFCE + 1
                else:
                    nNF = dadosEmpresa.NUMERO_NFCE

            _nf.append(str(nNF))

        _nf.append(dadosEmpresa.SERIE_NFCE)

        if pedidoNFe[0].GERAR_DANFE == 1:
            if dadosEmpresa.NUMERO_NF < int(_nf[0]):
                dadosEmpresa.NUMERO_NF = int(_nf[0])
        else:
            if dadosEmpresa.NUMERO_NFCE < int(_nf[0]):
                dadosEmpresa.NUMERO_NFCE = int(_nf[0])

        items = sorted(itemsPedido, key=lambda e: e.NUMERO_ITEM)

        for item in items:
            produto = (
                ctx.session.query(pr).filter(pr.ID_PRODUTO == item.ID_PRODUTO).first()
            )

            descricaoProduto = self.qBase.cleanSpecialChars(produto.DESCRICAO_PRODUTO)

            _endereco = f"{dadosEndereco.ENDERECO.strip()}, {dadosEndereco.NUMERO_ENDERECO.strip()}"

            if len(dadosEndereco.ENDERECO) == 0:
                _endereco = dadosEmpresa.ENDERECO.strip()

            _endereco = self.qBase.cleanSpecialChars(_endereco)

            _bairro = self.qBase.cleanSpecialChars(dadosEndereco.BAIRRO)
            _bairro = self.qBase.cleanSpecialChars(_bairro)
            descricaoProduto = self.qBase.cleanSpecialChars(descricaoProduto)

            if len(descricaoProduto) > 120:
                descricaoProduto = descricaoProduto[0, 120]

            _cidade = (
                dadosEmpresa.CIDADE
                if len(dadosEndereco.MUNICIPIO) == 0
                else dadosEndereco.MUNICIPIO.strip()
            )
            _cidade = self.qBase.cleanSpecialChars(_cidade)

            numeroEndereco = (
                "SN"
                if len(dadosEndereco.NUMERO_ENDERECO) > 0
                else dadosEndereco.NUMERO_ENDERECO
            )
            cep = "00000000" if len(dadosEndereco.CEP) == 0 else dadosEndereco.CEP
            uf = dadosEmpresa.UF
            email_cliente = dadosCliente.EMAIL_CLIENTE

            if ID_EMITENTE is None:
                dadosEmpresa.ID_EMPRESA

            idEmpresa = dadosEmpresa.ID_EMPRESA
            cnpjEmitente = self.qBase.onlyNumbers(dadosEmpresa.CNPJ)
            numeroNF = int(_nf[0])
            serieNF = _nf[1]
            serialProtocolo = dadosEmpresa.SERIAL_PROTOCOLO

            _tr = (
                ctx.session.query(t)
                .filter(t.ID_TRANSPORTE == pedido.ID_TRANSPORTE)
                .first()
            )

            if _tr is None:
                _tr = ctx.session.query(t).first()

            uf1 = dadosEmpresa.UF.upper()
            mun1 = dadosEmpresa.CIDADE.upper()

            qIbge = (
                ctx.session.query(m)
                .filter(*(m.SIGLA_UF == uf1, m.NOME_MUNICIPIO == mun1))
                .all()
            )

            ibgeEmitente = qIbge[0]
            ibgeDestinatario = ibgeEmitente

            _NOME_CLIENTE = self.qBase.maxString(pedido.NOME_CLIENTE, 60)

            if len(_NOME_CLIENTE.strip()) < 6:
                _NOME_CLIENTE = _NOME_CLIENTE.rjust(6, "0")

            _produto = (
                ctx.session.query(pr).filter(pr.ID_PRODUTO == item.ID_PRODUTO).first()
            )

            _CODIGO_PRODUTO = await self.buscaCodigoProduto(_produto.ID_PRODUTO)

            _CODIGO_IBGE_EMITENTE = dadosEmpresa.CODIGO_MUNICIPIO_IBGE

            _CODIGO_IBGE_DESTINATARIO = "".join(
                (
                    str(ibgeDestinatario.ID_UF),
                    str(ibgeDestinatario.ID_MUNICIPIO).rjust(5, "0"),
                )
            )

            CPF = pedido.CPF

            Tributo = (
                ctx.session.query(tr).filter(tr.ID_TRIBUTO == item.ID_TRIBUTO).first()
            )

            qCFOP = (
                ctx.session.query(ctx.mapCFOP)
                .filter(ctx.mapCFOP.CFOP == Tributo.CFOP)
                .all()
            )

            NATUREZA_OPERACAO = (
                qCFOP[0].DESCRICAO_CFOP if len(qCFOP) > 0 else "VENDA DE MERCADORIA"
            )

            protocolo = await self.extraiProtocoloNF(pedidoNFe[0].XML_NOTA)

            rec = dadosNFCe(
                NUMERO_COMANDA=pedido.NUMERO_PEDIDO,
                DATA_HORA=datetime.strftime(
                    pedido.DATA_HORA + timedelta(hours=3), "%d/%m/%Y %H:%M"
                ),
                NOME_CLIENTE=_NOME_CLIENTE.strip(),
                CPF=self.qBase.onlyNumbers(CPF) if len(CPF) > 0 else "ISENTO",
                IE=""
                if dadosCliente.IE is None
                else self.qBase.onlyNumbers(dadosCliente.IE),
                ENDERECO=_endereco,
                BAIRRO=_bairro,
                CIDADE=_cidade,
                FORMA_PAGTO=formasPagamento,
                NCM=Tributo.NCM,
                CFOP=Tributo.CFOP,
                ID_PRODUTO=int(item.ID_PRODUTO),
                ID_TRIBUTO=int(item.ID_TRIBUTO),
                NATUREZA_OPERACAO=NATUREZA_OPERACAO,
                CODIGO_PRODUTO=_CODIGO_PRODUTO,
                PRODUTO=descricaoProduto,
                QTDE=int(item.QTDE),
                PRECO=float(item.PRECO_UNITARIO),
                TOTAL=int(item.QTDE) * float(item.PRECO_UNITARIO),
                DESCONTO=DESCONTO,
                TOTAL_QTDE=TOTAL_QTDE,
                TOTAL_VALOR=TOTAL_VALOR,
                TROCO=TROCO,
                COMENTARIOS=pedido.INFO_ADICIONAL
                if pedido.INFO_ADICIONAL is not None
                else "",
                TELEFONE=pedido.TELEFONE_CLIENTE
                if pedido.TELEFONE_CLIENTE is not None
                else "",
                ID_EMPRESA=idEmpresa,
                NUMERO_NF=numeroNF,
                SERIE_NF=serieNF,
                CNPJ_EMITENTE=cnpjEmitente,
                SERIAL_PROTOCOLO=serialProtocolo,
                PROTOCOLO=protocolo,
                NOME_EMITENTE=dadosEmpresa.RAZAO_SOCIAL,
                NOME_FANTASIA_EMITENTE=dadosEmpresa.NOME_FANTASIA,
                IE_EMITENTE=dadosEmpresa.IE,
                ENDERECO_EMITENTE=dadosEmpresa.ENDERECO.strip(),
                BAIRRO_EMITENTE=dadosEmpresa.BAIRRO.strip(),
                CEP_EMITENTE=dadosEmpresa.CEP,
                CIDADE_EMITENTE=dadosEmpresa.CIDADE.strip(),
                UF_EMITENTE=dadosEmpresa.UF,
                CRT_EMITENTE=dadosEmpresa.CRT,
                TELEFONE_EMITENTE=dadosEmpresa.TELEFONE.strip(),
                NUMERO_ENDERECO="SN" if len(numeroEndereco) == 0 else numeroEndereco,
                CEP=cep,
                UF=uf,
                ENDERECO_TRANSPORTE=self.qBase.cleanSpecialChars(_tr.ENDERECO),
                EMAIL_CLIENTE=email_cliente,
                UF_TRANSPORTE=_tr.UF,
                IE_TRANSPORTE=self.qBase.onlyNumbers(_tr.IE),
                CNPJ_TRANSPORTE=self.qBase.onlyNumbers(_tr.CNPJ),
                CIDADE_TRANSPORTE=self.qBase.cleanSpecialChars(_tr.CIDADE),
                NOME_FANTASIA_TRANSPORTE=self.qBase.cleanSpecialChars(
                    _tr.NOME_TRANSPORTE
                ),
                NOME_TRANSPORTE=self.qBase.cleanSpecialChars(_tr.NOME_TRANSPORTE),
                XML=pedidoNFe[0].XML_NOTA,
                CHAVE=pedidoNFe[0].CHAVE_ACESSO_NF
                if pedidoNFe[0].CHAVE_ACESSO_NF is not None
                else "",
                CODIGO_IBGE_EMITENTE=_CODIGO_IBGE_EMITENTE,
                CODIGO_IBGE_DESTINATARIO=_CODIGO_IBGE_DESTINATARIO,
                DATA_AUTORIZACAO_NFCE=pedidoNFe[0].DATA_AUTORIZACAO_NFCE,
                ASSINATURA_NFCE=pedidoNFe[0].ASSINATURA_NFCE,
                CST=Tributo.CST,
                ALIQ_ICMS=Tributo.ALIQ_ICMS,
                ALIQ_INTERNA_ICMS=Tributo.ALIQ_INTERNA_ICMS,
                MODO_BASE_CALCULO_ICMS_ST=Tributo.MODO_BASE_CALCULO_ICMS_ST,
                IVA=Tributo.IVA,
                CST_IPI=Tributo.CST_IPI,
                ALIQ_IPI=Tributo.ALIQ_IPI,
                CST_PIS=Tributo.CST_PIS,
                ALIQ_PIS=Tributo.ALIQ_PIS,
                CST_COFINS=Tributo.CST_COFINS,
                ALIQ_COFINS=Tributo.ALIQ_COFINS,
                CEST="" if Tributo.CEST is None else Tributo.CEST,
                FATURAR_TAXA_ENTREGA=int(dadosEmpresa.FATURAR_TAXA_ENTREGA),
                pFCP=0.00
                if Tributo.PERCENTUAL_FCP is None
                else float(Tributo.PERCENTUAL_FCP),
                GERAR_DANFE=0
                if pedidoNFe[0].GERAR_DANFE is None
                else int(pedidoNFe[0].GERAR_DANFE),
                DADOS_ADICIONAIS=pedido.INFO_ADICIONAL
                if pedido.INFO_ADICIONAL is not None
                else "",
                DEVOLUCAO=False,
                CHAVE_NF_DEVOLUCAO="",
                TAXA_ENTREGA=float(pedido.TAXA_ENTREGA),
                vBCSTRet=0.00,
                vICMSRet=0.00,
                pST=Tributo.ALIQ_ICMS,
                ID_TRANSPORTE=int(pedido.ID_TRANSPORTE)
                if pedido.ID_TRANSPORTE is not None
                else _tr.ID_TRANSPORTE,
            )

            retorno.append(rec)

        return retorno

    async def extraiProtocoloNF(self, XML: str) -> str:
        try:
            prot = "<nProt>"
            prot1 = "</nProt>"

            retorno = XML[XML.index(prot) :]

            retorno = self.qBase.onlyNumbers(retorno[len(prot) : retorno.index(prot1)])

            return retorno
        except:
            return ""

    async def buscaCodigoProduto(self, ID_PRODUTO: int) -> str:
        retorno = "SEM GTIN"

        p = ctx.mapProduto

        produto = ctx.session.query(p).filter(p.ID_PRODUTO == ID_PRODUTO).first()

        if produto.CODIGO_PRODUTO_PDV is not None:
            retorno = (
                produto.CODIGO_PRODUTO_PDV
                if len(produto.CODIGO_PRODUTO_PDV) >= 8
                else "SEM GTIN"
            )

        return retorno.strip()

    async def finalizaNFCe(self, dados: NFe_Finalizada):
        pnf = ctx.mapPedidoNFe

        q = (
            ctx.session.query(pnf)
            .filter(pnf.NUMERO_PEDIDO == dados.NUMERO_PEDIDO)
            .all()
        )

        if len(q) == 0:
            return

        autorizada = 10 if len(dados.ASSINATURA_NFC) > 0 else 0

        if autorizada == 0:
            return

        cmd = (
            ctx.tb_pedido_nfe.update()
            .values(
                XML_NOTA=dados.XML,
                NUMERO_NF=dados.NUMERO_NF,
                CHAVE_ACESSO_NF=dados.CHAVE_ACESSO,
                ASSINATURA_NFCE=dados.ASSINATURA_NFC,
                DATA_AUTORIZACAO_NFCE=dados.DATA_AUTORIZACAO,
                PROCESSADO=autorizada,
            )
            .where(pnf.NUMERO_PEDIDO == dados.NUMERO_PEDIDO and pnf.PROCESSADO == 1)
        )

        ctx.session.execute(cmd)
        ctx.session.commit()

    async def listTributo(self) -> List[listaDeTributo]:
        tr = ctx.mapTributo

        query = ctx.session.query(tr).all()

        lista = [
            listaDeTributo(
                ID_TRIBUTO=item.ID_TRIBUTO,
                NOME_OPERACAO=item.NOME_OPERACAO
            )
            for item in query
        ]

        retorno = sorted(lista, key=lambda e: e.NOME_OPERACAO)

        return retorno

    async def listItensParaNFe(self, filtro: filtroNumeroPedido) -> List[itemsNFe]:
        tr = ctx.mapItemPedido

        query = ctx.session.query(tr).filter(tr.NUMERO_PEDIDO == filtro.NUMERO_PEDIDO).all()

        lista = [
            itemsNFe(
                NUMERO_ITEM=item.NUMERO_ITEM,
                DESCRICAO_PRODUTO=await self.getDescricaoProduto(item.ID_PRODUTO),
                QTDE=int(item.QTDE),
                PRECO=float(item.PRECO_UNITARIO),
                TOTAL=float(item.VALOR_TOTAL),
                ID_TRIBUTO=int(item.ID_TRIBUTO)
            )
            for item in query
        ]

        return lista

    async def setTributoItemPedido(self, item: itemTributo): 
        cmd = ctx.tb_item_pedido.update().values(
            ID_TRIBUTO = item.ID_TRIBUTO
        ).where(
            ctx.mapItemPedido.NUMERO_ITEM == item.NUMERO_ITEM 
        )

        ctx.session.execute(cmd)
        ctx.session.commit()

    async def conferePagamento(self, record: listaDePagamentos):
        cmd = ctx.tb_pedido_pagamento.update().values(
            VALOR_PAGO_STONE = record.TOTAL_PAGO
        ).where(
            ctx.mapPedidoPagamento.ID_PAGAMENTO == record.ID_PAGAMENTO
        )

        ctx.session.execute(cmd)
        ctx.session.commit()

    def __del__(self):
        ctx.session.close_all()
