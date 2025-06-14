from datetime import datetime, timedelta
from typing import List

from dateutil.relativedelta import relativedelta
from sqlalchemy import func

import base.qModel as ctx
from base.qBase import qBase
from cfg.config import Config
from models.aberturaCaixa import aberturaCaixa
from models.consistenciasCaixa import consistenciasCaixa
from models.dadosAbertura import dadosAbertura
from models.dadosFechamento import dadosFechamento
from models.dadosUsuario import dadosUsuario
from models.fechamentoCaixa import fechamentoCaixa
from models.filtroCAIXA import filtroCAIXA
from models.filtroFormasPagtoCaixa import filtroFormasPagtoCaixa
from models.filtroImpressaoCaixa import filtroImpressaoCaixa
from models.formaPagtoCaixa import formaPagtoCaixa
from models.itemCaixa import itemCaixa
from models.listaDeCaixa import listaDeCaixa
from models.listaDePagamentos import listaDePagamentos
from models.listaDeUsuario import listaDeUsuario
from models.nsu import nsu
from models.pedidosPorStatus import pedidosPorStatus
from models.RESUMO_OPERACAO_CAIXA import (
    RESUMO_IMPRESSAO_CAIXA,
    TOTAIS_CAIXA_FORMA_PAGTO,
    TOTAIS_CAIXA_FORMA_PAGTO_ORIGEM,
    TOTAIS_CAIXA_ORIGEM,
    TOTAIS_REFORCO,
    TOTAIS_SANGRIA
)
from models.ResumoFormaPagto import ResumoFormaPagto
from models.ResumoFormaPagtoOrigem import ResumoFormaPagtoOrigem
from models.ResumoOrigem import ResumoOrigem
from models.totaisPorFormaPagto import totaisPorFormaPagto
from models.ultimosCaixas import ultimosCaixas

class Caixa:
    def __init__(self, keep=None, idUser=None):
        self.qBase = qBase(keep)
        self.__listOfUsers = []
        self.__idUser = idUser

    async def listCaixa(self):
        hoje = datetime(
            datetime.now().year, datetime.now().month, datetime.now().day, 0, 0, 0
        )

        ontem = hoje + relativedelta(days=-1)

        a = ctx.mapAberturaCaixa

        _filters = [
            a.DATA_ABERTURA >= ontem, 
            a.VALOR_FECHAMENTO == 0
        ]

        query = ctx.session.query(a).filter(*_filters).all()

        retorno = [
            listaDeCaixa(
                ID_ABERTURA=item.ID_ABERTURA,
                DATA_ABERTURA=datetime.strftime(item.DATA_ABERTURA, "%d/%m/%Y %H:%M")
                if item.DATA_ABERTURA is not None
                else "",
                VALOR_ABERTURA=float(item.VALOR_ABERTURA),
                VALOR_FECHAMENTO=float(item.VALOR_FECHAMENTO)
                if item.VALOR_FECHAMENTO is not None
                else 0.00,
                USUARIO=await self.getUsuario(item.ID_USUARIO),
                DATA_FECHAMENTO=await self.buscaFechamento(item.ID_ABERTURA),
                ADMINISTRADOR=await self.getAdmin(item.ID_USUARIO)
            ).model_dump_json()
            for item in query
        ]

        return self.qBase.toRoute(retorno, 200)

    async def getAdmin(self, ID_USUARIO: int) -> bool:
        admin = ctx.session.query(ctx.mapUSUARIO).filter(
            ctx.mapUSUARIO.ID_USUARIO == ID_USUARIO
        ).first().TIPO_USUARIO == 1

        return admin

    async def getUsuario(self, ID_USUARIO) -> str:
        NOME_USUARIO = (
            ctx.session.query(ctx.mapUSUARIO)
            .filter(ctx.mapUSUARIO.ID_USUARIO == ID_USUARIO)
            .first()
            .NOME_USUARIO
        )

        return NOME_USUARIO

    async def buscaFechamento(self, idAbertura):
        f = ctx.mapFechamentoCaixa

        rec = ctx.session.query(f).filter(f.ID_ABERTURA == idAbertura).all()

        return (
            datetime.strftime(rec[0].DATA_FECHAMENTO, "%d/%m/%Y %H:%M")
            if len(rec) > 0
            else ""
        )

    async def gravaAberturaCaixa(self, dados: aberturaCaixa) -> int:
        senhaOk = await self.verificaSenhaAberturaCaixa(
            dadosUsuario(
                ID_USUARIO=dados.ID_USUARIO,
                SENHA_USUARIO=dados.SENHA_CAIXA
            )
        )

        if not senhaOk:
            return -1

        cmd = ctx.tb_abertura_caixa.insert().values(
            ID_ABERTURA=0,
            DATA_ABERTURA=datetime.strptime(dados.DATA_ABERTURA, "%d/%m/%Y %H:%M"),
            VALOR_ABERTURA=dados.VALOR_ABERTURA,
            VALOR_FECHAMENTO=0,
            ID_USUARIO=dados.ID_USUARIO,
            DATA_FECHAMENTO=None
        )

        result = ctx.session.execute(cmd)

        ctx.session.commit()

        return int(result.inserted_primary_key[0])

    async def verificaSenhaAberturaCaixa(self, dados: dadosUsuario) -> bool:
        u = ctx.mapUSUARIO

        currentPassword = ctx.session.query(u).filter(
            u.ID_USUARIO == dados.ID_USUARIO
        ).first().SENHA_USUARIO

        return currentPassword == dados.SENHA_USUARIO

    async def listUsuario(self):
        _filters = [ctx.mapUSUARIO.USUARIO_ATIVO == 1]

        query = (
            ctx.session.query(ctx.mapUSUARIO)
            .order_by(ctx.mapUSUARIO.NOME_USUARIO)
            .filter(*_filters)
            .all()
        )

        retorno = [
            listaDeUsuario(
                ID_USUARIO=item.ID_USUARIO, NOME_USUARIO=item.NOME_USUARIO
            ).model_dump_json()
            for item in query
        ]

        return self.qBase.toRoute(retorno, 200)

    async def getUsuarioFromCaixa(self, dados: itemCaixa) -> int:
        a = ctx.mapAberturaCaixa
    
        idUsuario = ctx.session.query(a).filter(
            a.ID_ABERTURA == dados.ID_ABERTURA
        ).first().ID_USUARIO

        return idUsuario
    
    async def getCaixa(self, filtro: filtroCAIXA) -> listaDeCaixa:
        rec = (
            ctx.session.query(ctx.mapAberturaCaixa)
            .filter(ctx.mapAberturaCaixa.ID_ABERTURA == filtro.ID_CAIXA)
            .first()
        )

        retorno = listaDeCaixa(
            ID_ABERTURA=rec.ID_ABERTURA,
            DATA_ABERTURA=datetime.strftime(rec.DATA_ABERTURA, "%d/%m/%Y %H:%M"),
            VALOR_ABERTURA=float(rec.VALOR_ABERTURA),
            VALOR_FECHAMENTO=float(rec.VALOR_FECHAMENTO)
            if rec.VALOR_FECHAMENTO is not None
            else 0,
            USUARIO=await self.getUsuario(rec.ID_USUARIO),
            DATA_FECHAMENTO=await self.buscaFechamento(rec.ID_ABERTURA),
            ADMINISTRADOR=await self.getAdmin(rec.ID_USUARIO)
        )

        return retorno

    async def busca_Formas_de_Pagto_no_Caixa(self, filtro: filtroFormasPagtoCaixa):
        p = ctx.mapPedido
        a = ctx.mapPedidoPagamento

        _filters = [p.STATUS_PEDIDO == 3, p.ID_CAIXA == filtro.ID_CAIXA]

        query = (
            ctx.session.query(
                p.NUMERO_PEDIDO, p.STATUS_PEDIDO, p.ID_CAIXA, a.FORMA_PAGTO
            )
            .join(p, a.NUMERO_PEDIDO == p.NUMERO_PEDIDO)
            .filter(*_filters)
            .all()
        )

        x = set([item.FORMA_PAGTO for item in query])

        lista = sorted(
            [formaPagtoCaixa(DESCRICAO_FORMA=item) for item in x],
            key=lambda e: e.DESCRICAO_FORMA,
        )

        retorno = [
            formaPagtoCaixa(DESCRICAO_FORMA=item.DESCRICAO_FORMA).model_dump_json()
            for item in lista
        ]

        return self.qBase.toRoute(retorno, 200)

    async def get_Totais_Por_Forma_Pagto(self, filtro: filtroFormasPagtoCaixa):
        p = ctx.mapPedido
        pg = ctx.mapPedidoPagamento
        s = ctx.mapSangria
        r = ctx.mapReforco

        _filters = [
            p.STATUS_PEDIDO == 3,
            p.ID_CAIXA == filtro.ID_CAIXA,
            pg.FORMA_PAGTO == filtro.FORMA_PAGTO,
        ]

        totais = (
            ctx.session.query(
                pg.FORMA_PAGTO, func.sum(pg.VALOR_PAGO).label("TOTAL_PAGO")
            )
            .join(p, pg.NUMERO_PEDIDO == p.NUMERO_PEDIDO)
            .filter(*_filters)
            .group_by(pg.FORMA_PAGTO)
            .all()
        )

        descontos_e_Troco = (
            ctx.session.query(
                func.sum(p.TROCO).label("TROCO"), func.sum(p.DESCONTO).label("DESCONTO")
            )
            .join(pg, p.NUMERO_PEDIDO == pg.NUMERO_PEDIDO)
            .filter(*_filters)
            .all()
        )

        recTroco = descontos_e_Troco[0]

        totalGeral = await self.get_Total_Geral_Caixa(filtro)

        retorno = totaisPorFormaPagto(
            FORMA_PAGTO="DINHEIRO",
            TROCO=0.00,
            TOTAL_PAGTO=0.00,
            DESCONTO=0.00,
            SANGRIA=0,
            REFORCO=0,
            TOTAL_FINAL=0,
            VALOR_FECHAMENTO=0,
            DIFERENCA=0,
            TOTAL_GERAL=totalGeral
        )

        try:
            retorno = [
                totaisPorFormaPagto(
                    FORMA_PAGTO=item.FORMA_PAGTO,
                    TROCO=float(recTroco.TROCO) if recTroco.TROCO is not None else 0.00,
                    TOTAL_PAGTO=item.TOTAL_PAGO,
                    DESCONTO=float(recTroco.DESCONTO)
                    if recTroco.DESCONTO is not None
                    else 0.00,
                    SANGRIA=0,
                    REFORCO=0,
                    TOTAL_FINAL=0,
                    VALOR_FECHAMENTO=0,
                    DIFERENCA=0,
                    TOTAL_GERAL=totalGeral
                )
                for item in totais
            ][0]
        except:
            pass

        if "DINHEIRO" in filtro.FORMA_PAGTO.upper():
            sangrias = (
                ctx.session.query(func.sum(s.VALOR_SANGRIA))
                .filter(s.ID_ABERTURA == filtro.ID_CAIXA)
                .all()
            )

            reforcos = (
                ctx.session.query(func.sum(r.VALOR_REFORCO))
                .filter(r.ID_ABERTURA == filtro.ID_CAIXA)
                .all()
            )

            rec = sangrias[0][0]
            retorno.SANGRIA = float(rec) if rec is not None else 0.00

            rec = reforcos[0][0]
            retorno.REFORCO = float(rec) if rec is not None else 0.00

        retorno.TOTAL_FINAL = (
            (retorno.TOTAL_PAGTO + retorno.REFORCO) - retorno.SANGRIA
        ) - retorno.TROCO

        return self.qBase.toRoute(retorno.model_dump_json(), 200)

    async def verificaCaixaAberto(self, filtro: filtroCAIXA) -> bool:
        a = ctx.mapAberturaCaixa
        f = ctx.mapFechamentoCaixa

        filters = [a.ID_ABERTURA == filtro.ID_CAIXA, a.VALOR_FECHAMENTO == 0.00]

        abertura = ctx.session.query(a).filter(*filters).all()

        fechamento = ctx.session.query(f).filter(f.ID_ABERTURA == filtro.ID_CAIXA).all()

        return len(abertura) > 0 and len(fechamento) == 0

    async def listaPagamentosPorForma(self, filtro: filtroFormasPagtoCaixa):
        p = ctx.mapPedido
        pg = ctx.mapPedidoPagamento

        _filters = [p.ID_CAIXA == filtro.ID_CAIXA, pg.FORMA_PAGTO == filtro.FORMA_PAGTO]

        query = (
            ctx.session.query(
                p.NUMERO_PEDIDO,
                p.DATA_HORA,
                p.STATUS_PEDIDO,
                p.NOME_CLIENTE,
                p.TOTAL_PEDIDO,
                pg.VALOR_PAGO,
                pg.CODIGO_NSU,
                pg.ID_PAGAMENTO,
                pg.VALOR_PAGO_STONE
            )
            .join(p, pg.NUMERO_PEDIDO == p.NUMERO_PEDIDO)
            .filter(*_filters)
            .all()
        )

        retorno = [
            listaDePagamentos(
                NUMERO_PEDIDO=item.NUMERO_PEDIDO,
                DATA_HORA=datetime.strftime(item.DATA_HORA, "%d/%m/%Y %H:%M"),
                STATUS_PEDIDO=Config.getStatus(item),
                CLIENTE=item.NOME_CLIENTE,
                TOTAL_PEDIDO=0.00
                if item.TOTAL_PEDIDO is None
                else float(item.TOTAL_PEDIDO),
                TOTAL_PAGO=0.00 if item.VALOR_PAGO is None else float(item.VALOR_PAGO),
                CODIGO_NSU="" if item.CODIGO_NSU is None else item.CODIGO_NSU,
                ID_PAGAMENTO=item.ID_PAGAMENTO,
                VALOR_PAGO_STONE=0 if item.VALOR_PAGO_STONE is None else float(item.VALOR_PAGO_STONE)
            )
            for item in query
        ]

        return self.qBase.toRoute(retorno, 200)

    async def gravaNSU(self, dados: nsu):
        cmd = (
            ctx.tb_pedido_pagamento.update()
            .values(CODIGO_NSU=dados.NSU)
            .where(ctx.mapPedidoPagamento.ID_PAGAMENTO == dados.ID_PAGAMENTO)
        )

        ctx.session.execute(cmd)
        ctx.session.commit()

    async def gravaFechamentoCaixa(self, dados: fechamentoCaixa) -> dadosFechamento:
        cmd = ctx.tb_fechamento_caixa.insert().values(
            ID_FECHAMENTO=0,
            ID_ABERTURA=dados.ID_ABERTURA,
            FORMA_PAGTO=dados.FORMA_PAGTO,
            VALOR_FECHAMENTO=dados.VALOR_FECHAMENTO,
            DATA_FECHAMENTO=datetime.strptime(dados.DATA_FECHAMENTO, "%d/%m/%Y %H:%M"),
            DIFERENCA=dados.DIFERENCA,
            ID_FECHAMENTO_LOCAL=0,
            ID_TERMINAL=0,
        )

        fechamento = ctx.session.execute(cmd)

        idFechamento = int(fechamento.inserted_primary_key[0])

        abertura = (
            ctx.tb_abertura_caixa.update()
            .values(
                VALOR_FECHAMENTO=dados.VALOR_FECHAMENTO,
                DATA_FECHAMENTO=datetime.strptime(
                    dados.DATA_FECHAMENTO, "%d/%m/%Y %H:%M"
                ),
            )
            .where(ctx.mapAberturaCaixa.ID_ABERTURA == dados.ID_ABERTURA)
        )

        ctx.session.execute(abertura)
        ctx.session.commit()

        retorno = dadosFechamento(
            ID_FECHAMENTO=idFechamento,
            FORMA_PAGTO=dados.FORMA_PAGTO,
            DATA_FECHAMENTO=dados.DATA_FECHAMENTO,
            VALOR_FECHAMENTO=dados.VALOR_FECHAMENTO,
            DIFERENCA=dados.DIFERENCA
        )

        return retorno

    async def get_Totais_Fechamento(
        self, filtro: filtroFormasPagtoCaixa
    ) -> List[dadosFechamento]:
        f = ctx.mapFechamentoCaixa

        filters = [
            f.ID_ABERTURA == filtro.ID_CAIXA,
            f.FORMA_PAGTO == filtro.FORMA_PAGTO,
        ]

        query = ctx.session.query(f).filter(*filters).all()

        retorno = [
            dadosFechamento(
                ID_FECHAMENTO=record.ID_FECHAMENTO
                    if record.ID_FECHAMENTO is not None
                    else 0,
                FORMA_PAGTO=filtro.FORMA_PAGTO,
                DATA_FECHAMENTO=datetime.strftime(
                    record.DATA_FECHAMENTO, "%d/%m/%Y %H:%M"
                )
                    if record.DATA_FECHAMENTO is not None
                    else "",
                VALOR_FECHAMENTO=float(record.VALOR_FECHAMENTO)
                    if record.VALOR_FECHAMENTO is not None
                    else 0,
                DIFERENCA=float(record.DIFERENCA)
                    if record.DIFERENCA is not None
                    else 0
            )
            for record in query
        ]

        return retorno

    async def get_Total_Geral_Caixa(self, filtro: filtroFormasPagtoCaixa) -> float:
        p = ctx.mapPedido
        pg = ctx.mapPedidoPagamento
        s = ctx.mapSangria
        r = ctx.mapReforco

        _filters = [
            p.STATUS_PEDIDO == 3,
            p.ID_CAIXA == filtro.ID_CAIXA
        ]

        totalDePagamentos = ctx.session.query(
            func.sum(pg.VALOR_PAGO).label("VALOR_PAGO")
        ).join(
            p, pg.NUMERO_PEDIDO == p.NUMERO_PEDIDO
        ).filter(
            *_filters
        ).all()[0]

        try:
            totalDePagamentos = float(totalDePagamentos[0])
        except:
            totalDePagamentos = 0.00

        Troco = (
            ctx.session.query(
                func.sum(p.TROCO).label("TROCO")
            )
            .join(pg, p.NUMERO_PEDIDO == pg.NUMERO_PEDIDO)
            .filter(*_filters)
            .all()
        )

        try:
            Troco = float(Troco[0][0])
        except:
            Troco = 0.00

        sangrias = ctx.session.query(
            func.sum(s.VALOR_SANGRIA)
        ).filter(
            s.ID_ABERTURA == filtro.ID_CAIXA
        ).all()

        reforcos = ctx.session.query(
            func.sum(r.VALOR_REFORCO)
        ).filter(
            r.ID_ABERTURA == filtro.ID_CAIXA
        ).all()

        rec = sangrias[0][0]
        SANGRIA = float(rec) if rec is not None else 0.00

        rec = reforcos[0][0]
        REFORCO = float(rec) if rec is not None else 0.00

        TOTAL_FINAL = ((totalDePagamentos + REFORCO) - SANGRIA) - Troco

        return TOTAL_FINAL

    async def setImpressaoCaixa(self, filtro: filtroFormasPagtoCaixa):
        cmd = (
            ctx.tb_abertura_caixa.update()
            .values(IMPRESSAO=1)
            .where(ctx.mapAberturaCaixa.ID_ABERTURA == filtro.ID_CAIXA)
        )

        ctx.session.execute(cmd)
        ctx.session.commit()

    async def get_Inconsistencias_Caixa(
        self, filtro: filtroFormasPagtoCaixa
    ) -> List[consistenciasCaixa]:
        e = ctx.mapEmpresa
        p = ctx.mapPedido

        horaInicial = ctx.session.query(e).first().HORA_INICIAL

        datahoraInicial = None

        try:
            datahoraInicial = datetime.today() + timedelta(
                hours=int(horaInicial[0:2]), minutes=int(horaInicial[3:2])
            )
        except:
            pass

        if not isinstance(datahoraInicial, datetime):
            raise Exception(
                "Horário inicial de funcionamento da loja não foi cadastrado"
            )

        dataHoraFinal = datetime.now() + timedelta(minutes=1)

        filters = [
            p.DATA_HORA >= datahoraInicial,
            p.DATA_HORA < dataHoraFinal,
            p.STATUS_PEDIDO == 3,
        ]

        pedidosNoPeriodo = ctx.session.query(p).filter(*filters).all()

        filters = [p.ID_CAIXA == filtro.ID_CAIXA, p.STATUS_PEDIDO == 3]

        pedidosDoCaixa = ctx.session.query(p).filter(*filters).all()

        numeroDeCaixas = list(
            dict.fromkeys([item.ID_CAIXA for item in pedidosNoPeriodo])
        )

        retorno = []

        if numeroDeCaixas > 1:
            periodo = f'{datetime.strftime(datahoraInicial, "%d/%m/%Y %H:%M")} até {datetime.strftime(dataHoraFinal, "%d/%m/%Y %H:%M")}'

            retorno.append(
                consistenciasCaixa(
                    DATA_HORA=datetime.strftime(datetime.now(), "%d/%m/%Y %H:%M"),
                    DESCRICAO=f"Existem {numeroDeCaixas} caixa(s) aberto(s) no período de {periodo}",
                )
            )

        filters = [p.ID_CAIXA == filtro.ID_CAIXA, p.STATUS_PEDIDO == 3]

        porStatus = (
            ctx.session.query(
                p.STATUS_PEDIDO, func.count(p.NUMERO_PEDIDO).label("NUMERO_DE_PEDIDOS")
            )
            .filter(*filters)
            .group_by(p.STATUS_PEDIDO)
            .all()
        )

        grouped = [
            pedidosPorStatus(
                STATUS=Config.getStatus(item), COUNT=item.NUMERO_DE_PEDIDOS
            )
            for item in porStatus
        ]

        if len(grouped) > 1:
            retorno.append(
                consistenciasCaixa(
                    DATA_HORA=datetime.strftime(datetime.now(), "%d/%m/%Y %H:%M"),
                    DESCRICAO="\n".join(
                        [
                            f"{item.STATUS_PEDIDO}: {item.NUMERO_DE_PEDIDOS}"
                            for item in grouped
                        ]
                    ),
                )
            )

        return retorno

    async def listaUltimosCaixas(self) -> List[ultimosCaixas]:
        hoje = datetime(
            datetime.now().year, datetime.now().month, datetime.now().day, 0, 0, 0
        )

        ontem = hoje + relativedelta(days=-7)

        a = ctx.mapAberturaCaixa
        u = ctx.mapUSUARIO

        _filters = [a.DATA_ABERTURA >= ontem, a.ID_USUARIO == u.ID_USUARIO]

        query = (
            ctx.session.query(
                a.ID_ABERTURA,
                a.DATA_ABERTURA,
                a.VALOR_ABERTURA,
                a.VALOR_FECHAMENTO,
                u.NOME_USUARIO,
                a.DATA_FECHAMENTO,
            )
            .filter(*_filters)
            .all()
        )

        retorno = [
            ultimosCaixas(
                ID_ABERTURA=item.ID_ABERTURA,
                DATA_ABERTURA=datetime.strftime(item.DATA_ABERTURA, "%d/%m/%Y %H:%M")
                if item.DATA_ABERTURA is not None
                else "",
            )
            for item in query
        ]

        return retorno

    async def resumoTotaisImpressao(
        self, filtro: filtroImpressaoCaixa
    ) -> RESUMO_IMPRESSAO_CAIXA:
        a = ctx.mapAberturaCaixa
        u = ctx.mapUSUARIO

        impressao = ctx.session.query(a).filter(a.IMPRESSAO == filtro.MAQUINA).first()

        if impressao is None:
            return []

        DATA1 = self.qBase.TrataDataHora(impressao.DATA_ABERTURA)
        DATA2 = (
            self.qBase.TrataDataHora(impressao.DATA_FECHAMENTO)
            if impressao.DATA_FECHAMENTO is not None
            else self.qBase.TrataDataHora(datetime.now() + timedelta(minutes=1))
        )

        ID_CAIXA = impressao.ID_ABERTURA

        f = filtroCAIXA(ID_CAIXA=ID_CAIXA)

        totaisPorFormaPagto = await self.calculaCaixaPorFormaPagto(f)
        totaisPorOrigem = await self.calculaCaixaPorOrigem(f)
        totaisPorOrigemFormaPagto = await self.calculaCaixaPorFormaPagtoOrigem(f)

        retorno = RESUMO_IMPRESSAO_CAIXA(
            DATA1=DATA1,
            DATA2=DATA2,
            RESUMO_FORMA_PAGTO=[
                TOTAIS_CAIXA_FORMA_PAGTO(
                    FORMA_PAGTO=item.FORMA_PAGTO,
                    ABERTURA=item.ABERTURA,
                    VALOR=item.VALOR_VENDA,
                    DESCONTO=item.DESCONTO,
                    TROCO=item.TROCO,
                    SANGRIA=item.SANGRIA,
                    REFORCO=item.REFORCO,
                    TOTAL=item.TOTAL,
                    VALOR_FECHAMENTO=item.VALOR_FECHAMENTO,
                    DIFERENCA=item.DIFERENCA,
                )
                for item in totaisPorFormaPagto
            ],
            RESUMO_ORIGEM=[
                TOTAIS_CAIXA_ORIGEM(
                    ORIGEM=item.ORIGEM,
                    VALOR=item.VALOR_VENDA,
                    DESCONTO=item.DESCONTO,
                    TOTAL=item.TOTAL,
                )
                for item in totaisPorOrigem
            ],
            RESUMO_FORMA_PAGTO_ORIGEM=[
                TOTAIS_CAIXA_FORMA_PAGTO_ORIGEM(
                    ORIGEM=item.ORIGEM,
                    FORMA_PAGTO=item.FORMA_PAGTO,
                    VALOR=item.VALOR_VENDA,
                    DESCONTO=item.DESCONTO,
                    TOTAL=item.TOTAL,
                )
                for item in totaisPorOrigemFormaPagto
            ],
            RESUMO_REFORCO=await self.operacoesReforco(f),
            RESUMO_SANGRIA=await self.operacoesSangria(f),
            USUARIO=ctx.session.query(u)
            .filter(u.ID_USUARIO == impressao.ID_USUARIO)
            .first()
            .NOME_USUARIO,
        )

        cmd = (
            ctx.tb_abertura_caixa.update()
            .values(IMPRESSAO=0)
            .where(a.ID_ABERTURA == ID_CAIXA)
        )

        ctx.session.execute(cmd)
        ctx.session.commit()

        return retorno

    async def calculaCaixaPorFormaPagto(
        self, filtro: filtroCAIXA
    ) -> List[ResumoFormaPagto]:
        retorno = []

        p = ctx.mapPedido
        pg = ctx.mapPedidoPagamento
        f = ctx.mapFechamentoCaixa

        dinheiro = "dinheiro"

        _filters = [p.STATUS_PEDIDO == 3, p.ID_CAIXA == filtro.ID_CAIXA]

        totais = (
            ctx.session.query(
                pg.FORMA_PAGTO, func.sum(pg.VALOR_PAGO).label("TOTAL_PAGO")
            )
            .join(p, pg.NUMERO_PEDIDO == p.NUMERO_PEDIDO)
            .filter(*_filters)
            .group_by(pg.FORMA_PAGTO)
            .all()
        )

        dadosDinheiro = await self.getDadosAbertura(filtro)

        troco = sum(
            [
                float(item[0])
                for item in ctx.session.query(p.TROCO).filter(*_filters).all()
            ]
        )

        if not isinstance(troco, float):
            troco = 0.00

        for item in totais:
            total = float(item.TOTAL_PAGO) if item.TOTAL_PAGO is not None else 0

            if item.FORMA_PAGTO == dinheiro:
                total -= troco
                total = (
                    dadosDinheiro.ABERTURA + item.TOTAL_PAGO + dadosDinheiro.REFORCO
                ) - dadosDinheiro.SANGRIA

            fechamento = (
                ctx.session.query(f)
                .filter(
                    *(
                        f.ID_ABERTURA == filtro.ID_CAIXA,
                        f.FORMA_PAGTO == item.FORMA_PAGTO,
                    )
                )
                .all()
            )

            dHoraFechamento = ""
            valorFechamento = 0

            for item1 in fechamento:
                dHoraFechamento = (
                    self.qBase.TrataDataHora(item1.DATA_FECHAMENTO)
                    if item1.DATA_FECHAMENTO is not None
                    else ""
                )

                valorFechamento = (
                    item1.VALOR_FECHAMENTO
                    if item1.VALOR_FECHAMENTO is not None
                    else 0.00
                )

            diferenca = valorFechamento - total if valorFechamento > 0.00 else 0.00

            retorno.append(
                ResumoFormaPagto(
                    FORMA_PAGTO=item.FORMA_PAGTO,
                    ABERTURA=dadosDinheiro.ABERTURA
                    if item.FORMA_PAGTO == dinheiro
                    else 0,
                    VALOR_VENDA=float(item.TOTAL_PAGO)
                    if item.TOTAL_PAGO is not None
                    else 0,
                    DESCONTO=0,
                    SANGRIA=dadosDinheiro.SANGRIA
                    if item.FORMA_PAGTO == dinheiro
                    else 0,
                    REFORCO=dadosDinheiro.REFORCO
                    if item.FORMA_PAGTO == dinheiro
                    else 0,
                    TOTAL=total,
                    DIFERENCA=diferenca,
                    DATA_HORA_FECHAMENTO=dHoraFechamento,
                    VALOR_FECHAMENTO=valorFechamento,
                    TROCO=troco,
                )
            )

        return retorno

    async def calculaCaixaPorOrigem(self, filtro: filtroCAIXA) -> List[ResumoOrigem]:
        p = ctx.mapPedido
        pg = ctx.mapPedidoPagamento

        _filters = [p.STATUS_PEDIDO == 3, p.ID_CAIXA == filtro.ID_CAIXA]

        totais = (
            ctx.session.query(pg.ORIGEM, func.sum(pg.VALOR_PAGO).label("TOTAL_PAGO"))
            .join(p, pg.NUMERO_PEDIDO == p.NUMERO_PEDIDO)
            .filter(*_filters)
            .group_by(pg.ORIGEM)
            .all()
        )

        retorno = [
            ResumoOrigem(
                ORIGEM=item.ORIGEM,
                ABERTURA=0,
                VALOR_VENDA=float(item.TOTAL_PAGO)
                if item.TOTAL_PAGO is not None
                else 0,
                DESCONTO=0,
                SANGRIA=0,
                REFORCO=0,
                TOTAL=float(item.TOTAL_PAGO) if item.TOTAL_PAGO is not None else 0,
                DIFERENCA=0,
                DATA_HORA_FECHAMENTO="",
                VALOR_FECHAMENTO=0,
                TROCO=0,
            )
            for item in totais
        ]

        return retorno

    async def calculaCaixaPorFormaPagtoOrigem(
        self, filtro: filtroCAIXA
    ) -> List[ResumoFormaPagtoOrigem]:
        p = ctx.mapPedido
        pg = ctx.mapPedidoPagamento

        _filters = [p.STATUS_PEDIDO == 3, p.ID_CAIXA == filtro.ID_CAIXA]

        totais = (
            ctx.session.query(
                pg.FORMA_PAGTO, pg.ORIGEM, func.sum(pg.VALOR_PAGO).label("TOTAL_PAGO")
            )
            .join(p, pg.NUMERO_PEDIDO == p.NUMERO_PEDIDO)
            .filter(*_filters)
            .group_by(pg.FORMA_PAGTO, pg.ORIGEM)
            .all()
        )

        retorno = [
            ResumoFormaPagtoOrigem(
                FORMA_PAGTO=item.FORMA_PAGTO,
                ORIGEM=item.ORIGEM,
                ABERTURA=0,
                VALOR_VENDA=float(item.TOTAL_PAGO)
                if item.TOTAL_PAGO is not None
                else 0,
                DESCONTO=0,
                SANGRIA=0,
                REFORCO=0,
                TOTAL=float(item.TOTAL_PAGO) if item.TOTAL_PAGO is not None else 0,
                DIFERENCA=0,
                DATA_HORA_FECHAMENTO="",
                VALOR_FECHAMENTO=0,
                TROCO=0,
            )
            for item in totais
        ]

        return retorno

    async def getDadosAbertura(self, filtro: filtroCAIXA) -> dadosAbertura:
        a = ctx.mapAberturaCaixa
        s = ctx.mapSangria
        r = ctx.mapReforco

        recA = (
            ctx.session.query(a)
            .filter(a.ID_ABERTURA == filtro.ID_CAIXA)
            .first()
            .VALOR_ABERTURA
        )

        recS = sum(
            [
                item.VALOR_SANGRIA
                for item in ctx.session.query(s)
                .filter(s.ID_ABERTURA == filtro.ID_CAIXA)
                .all()
            ]
        )

        recR = sum(
            [
                item.VALOR_REFORCO
                for item in ctx.session.query(r)
                .filter(r.ID_ABERTURA == filtro.ID_CAIXA)
                .all()
            ]
        )

        retorno = dadosAbertura(
            ABERTURA=float(recA) if recA is not None else 0,
            SANGRIA=float(recS) if recS is not None else 0,
            REFORCO=float(recR) if recR is not None else 0,
        )

        return retorno

    async def operacoesSangria(self, filtro: filtroCAIXA) -> List[TOTAIS_SANGRIA]:
        s = ctx.mapSangria
        u = ctx.mapUSUARIO

        q2 = ctx.session.query(s).filter(s.ID_ABERTURA == filtro.ID_CAIXA).all()

        TOTAIS = [
            TOTAIS_SANGRIA(
                DATA_HORA=self.qBase.TrataDataHora(item.DATA_SANGRIA),
                DESCRICAO=item.DESCRICAO_SANGRIA,
                USUARIO=ctx.session.query(u)
                .filter(u.ID_USUARIO == item.ID_USUARIO)
                .first()
                .NOME_USUARIO,
                VALOR=float(item.VALOR_SANGRIA)
                if item.VALOR_SANGRIA is not None
                else 0,
            )
            for item in q2
        ]

        return TOTAIS

    async def operacoesReforco(self, filtro: filtroCAIXA) -> TOTAIS_REFORCO:
        r = ctx.mapReforco
        u = ctx.mapUSUARIO

        q2 = ctx.session.query(r).filter(r.ID_ABERTURA == filtro.ID_CAIXA).all()

        TOTAIS = [
            TOTAIS_REFORCO(
                DATA_HORA=self.qBase.TrataDataHora(item.DATA_REFORCO),
                DESCRICAO="",
                USUARIO=ctx.session.query(u)
                .filter(u.ID_USUARIO == item.ID_USUARIO)
                .first()
                .NOME_USUARIO,
                VALOR=float(item.VALOR_REFORCO)
                if item.VALOR_REFORCO is not None
                else 0,
            )
            for item in q2
        ]

        return TOTAIS

    async def getTaxaPagamento(self, filtro: filtroFormasPagtoCaixa) -> float:
        f = ctx.mapFormaPagto

        formaPagto = ctx.session.query(f).filter(
            f.DESCRICAO_FORMA == filtro.FORMA_PAGTO
        ).first()

        taxaPagamento = formaPagto.TAXA_PAGAMENTO

        if taxaPagamento is None:
            taxaPagamento = 0.00

        return float(taxaPagamento)

    def __del__(self):
        ctx.session.close_all()
