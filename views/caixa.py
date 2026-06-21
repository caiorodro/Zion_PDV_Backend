import asyncio
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
from models.historicoCaixas import HistoricoCaixas
from models.itemCaixa import itemCaixa
from models.listaDeCaixa import listaDeCaixa
from models.listaDePagamentos import listaDePagamentos
from models.listaDeUsuario import listaDeUsuario
from models.nsu import nsu
from models.pedidosPorStatus import pedidosPorStatus
from models.periodoUsuario import periodoUsuario
from models.resumoFechamento import resumoFechamento
from models.resumoOrigemFormaPagto import resumoOrigemFormaPagto

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
from models.senhaReset import senhaReset
from models.totaisPorFormaPagto import totaisPorFormaPagto
from models.ultimosCaixas import ultimosCaixas
from models.usuarioTipo import usuarioTipo

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
        u = ctx.mapUSUARIO

        _filters = [
            a.DATA_ABERTURA >= ontem, 
            a.VALOR_FECHAMENTO == 0,
            a.ID_USUARIO == u.ID_USUARIO
        ]

        query = ctx.session.query(
            a.ID_ABERTURA,
            a.DATA_ABERTURA,
            a.VALOR_ABERTURA,
            a.VALOR_FECHAMENTO,
            u.NOME_USUARIO,
            u.TIPO_USUARIO,
            u.USUARIO_CAIXA
        ).filter(
            *_filters
        ).order_by(a.DATA_ABERTURA).all()

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
                USUARIO=item.NOME_USUARIO,
                DATA_FECHAMENTO=self.buscaFechamento(item.ID_ABERTURA),
                ADMINISTRADOR=item.TIPO_USUARIO == 1,
                USUARIO_CAIXA=item.USUARIO_CAIXA == 1
            ).__dict__
            for item in query
        ]

        return self.qBase.toRoute(retorno, 200)

    def getAdmin(self, ID_USUARIO: int) -> bool:
        admin = ctx.session.query(ctx.mapUSUARIO).filter(
            ctx.mapUSUARIO.ID_USUARIO == ID_USUARIO
        ).first().TIPO_USUARIO == 1

        return admin

    def getUsuario(self, ID_USUARIO) -> str:
        NOME_USUARIO = (
            ctx.session.query(ctx.mapUSUARIO)
            .filter(ctx.mapUSUARIO.ID_USUARIO == ID_USUARIO)
            .first()
            .NOME_USUARIO
        )

        return NOME_USUARIO
    
    def getUsuarioCaixa(self, ID_USUARIO) -> tuple:
        u = ctx.mapUSUARIO

        query = ctx.session.query(
            u.NOME_USUARIO,
            u.USUARIO_CAIXA
        ).filter(
            u.ID_USUARIO == ID_USUARIO
        ).all()

        return (
            query[0].NOME_USUARIO,
            query[0].USUARIO_CAIXA
        )

    def buscaFechamento(self, idAbertura):
        f = ctx.mapFechamentoCaixa

        rec = ctx.session.query(f).filter(f.ID_ABERTURA == idAbertura).all()

        return (
            datetime.strftime(rec[0].DATA_FECHAMENTO, "%d/%m/%Y %H:%M")
            if len(rec) > 0
            else ""
        )

    def gravaAberturaCaixa(self, dados: aberturaCaixa) -> usuarioTipo:
        senhaOk = asyncio.run(self.verificaSenhaAberturaCaixa(
            dadosUsuario(
                ID_USUARIO=dados.ID_USUARIO,
                SENHA_USUARIO=dados.SENHA_CAIXA
            )
        ))

        if not senhaOk:
            return usuarioTipo(
                ID_CAIXA=-1,
                ADMIN=False
            )

        limiteAbertura = datetime.now() - timedelta(hours=24)

        usuario = ctx.mapAberturaCaixa

        aberturaRecente = ctx.session.query(usuario.ID_ABERTURA).filter(*[
            usuario.ID_USUARIO == dados.ID_USUARIO,
            usuario.DATA_ABERTURA >= limiteAbertura,
            usuario.VALOR_FECHAMENTO == 0
        ]).first()

        if aberturaRecente is not None:
            return usuarioTipo(
                ID_CAIXA=-2,
                ADMIN=False
            )

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

        idCaixa = int(result.inserted_primary_key[0])

        u = ctx.mapUSUARIO

        adminUsuario = ctx.session.query(u.TIPO_USUARIO).filter(
            u.ID_USUARIO == dados.ID_USUARIO
        ).first()

        return usuarioTipo(
            ID_CAIXA=idCaixa,
            ADMIN=adminUsuario == 1
        )

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
            ).__dict__
            for item in query
        ]

        return self.qBase.toRoute(retorno, 200)

    async def listSenhaAdministrador(self):
        u = ctx.mapUSUARIO

        query = ctx.session.query(
            u.ID_USUARIO,
            u.SENHA_USUARIO
        ).filter(
            u.TIPO_USUARIO == 1
        ).all()

        retorno = [
            {"SENHA_USUARIO": item.SENHA_USUARIO}
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
            USUARIO=self.getUsuario(rec.ID_USUARIO),
            DATA_FECHAMENTO=self.buscaFechamento(rec.ID_ABERTURA),
            ADMINISTRADOR=self.getAdmin(rec.ID_USUARIO),
            USUARIO_CAIXA=self.getUsuarioCaixa(rec.ID_USUARIO)[1]
        )

        return retorno

    async def calcula_Formas_de_Pagto_no_Caixa(self, filtro: filtroFormasPagtoCaixa) -> List[formaPagtoCaixa]:
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

        retorno = sorted(
            [formaPagtoCaixa(DESCRICAO_FORMA=item) for item in x],
            key=lambda e: e.DESCRICAO_FORMA,
        )

        return retorno

    async def busca_Formas_de_Pagto_no_Caixa(self, filtro: filtroFormasPagtoCaixa):
       
        lista = await self.calcula_Formas_de_Pagto_no_Caixa(filtro)

        retorno = [
            formaPagtoCaixa(DESCRICAO_FORMA=item.DESCRICAO_FORMA).__dict__
            for item in lista
        ]

        return self.qBase.toRoute(retorno, 200)

    async def getPeriodo_e_Usuario(self, ID_CAIXA: int) -> periodoUsuario:
        a = ctx.mapAberturaCaixa
        f = ctx.mapFechamentoCaixa
        u = ctx.mapUSUARIO

        Abertura = ctx.session.query(
            a.DATA_ABERTURA,
            a.ID_USUARIO
            ).filter(
                a.ID_ABERTURA == ID_CAIXA
            ).first()
        
        nomeUsuario = ctx.session.query(u.NOME_USUARIO).filter(
            u.ID_USUARIO == Abertura.ID_USUARIO
        ).first()[0]

        hoje = datetime.strftime(datetime.now(), '%d/%m/%Y %H:%M')

        fechamento = ctx.session.query(f.DATA_FECHAMENTO).filter(
            f.ID_ABERTURA == ID_CAIXA
        ).all()

        dataFechamento = datetime.strftime(fechamento[0][0], '%d/%m/%Y %H:%M') if len(fechamento) > 0 else hoje

        retorno = periodoUsuario(
            USUARIO=nomeUsuario,
            PERIODO_INICIAL=datetime.strftime(Abertura.DATA_ABERTURA, '%d/%m/%Y %H:%M'),
            PERIODO_FINAL=dataFechamento
        )

        return retorno

    def calcula_Totais_Por_Forma_Pagto(self, filtro: filtroFormasPagtoCaixa) -> totaisPorFormaPagto:
        p = ctx.mapPedido
        pg = ctx.mapPedidoPagamento
        s = ctx.mapSangria
        r = ctx.mapReforco
        a = ctx.mapAberturaCaixa
        f = ctx.mapFechamentoCaixa

        _filters = [
            p.STATUS_PEDIDO == 3,
            p.ID_CAIXA == filtro.ID_CAIXA,
            pg.FORMA_PAGTO == filtro.FORMA_PAGTO
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

        totalGeral = self.get_Total_Geral_Caixa(filtro)

        valorAbertura = ctx.session.query(a.VALOR_ABERTURA).filter(
            a.ID_ABERTURA == filtro.ID_CAIXA
        ).first().VALOR_ABERTURA

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
            TOTAL_GERAL=totalGeral,
            VALOR_ABERTURA=float(valorAbertura)
        )

        try:
            retorno = [
                totaisPorFormaPagto(
                    FORMA_PAGTO=item.FORMA_PAGTO,
                    TROCO=float(recTroco.TROCO) if recTroco.TROCO is not None else 0.00,
                    TOTAL_PAGTO=float(item.TOTAL_PAGO) - float(recTroco.TROCO),
                    DESCONTO=float(recTroco.DESCONTO)
                    if recTroco.DESCONTO is not None
                    else 0.00,
                    SANGRIA=0,
                    REFORCO=0,
                    TOTAL_FINAL=0,
                    VALOR_FECHAMENTO=0,
                    DIFERENCA=0,
                    TOTAL_GERAL=totalGeral,
                    VALOR_ABERTURA=float(valorAbertura)
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

            fechamento = ctx.session.query(
                f.DIFERENCA,
                f.VALOR_FECHAMENTO,
                f.DATA_FECHAMENTO
            ).filter(*[
                f.ID_ABERTURA == filtro.ID_CAIXA,
                f.FORMA_PAGTO == filtro.FORMA_PAGTO
            ]).all()

            rec = sangrias[0][0]
            retorno.SANGRIA = float(rec) if rec is not None else 0.00

            rec = reforcos[0][0]
            retorno.REFORCO = float(rec) if rec is not None else 0.00

            retorno.DIFERENCA = float(fechamento[0].DIFERENCA) if len(fechamento) > 0 else 0
            retorno.VALOR_FECHAMENTO = float(fechamento[0].VALOR_FECHAMENTO) if len(fechamento) > 0 else 0

        retorno.TOTAL_FINAL = (
            (retorno.TOTAL_PAGTO + retorno.REFORCO) - retorno.SANGRIA
        )

        retorno.TOTAL_FINAL = round(retorno.TOTAL_FINAL, 2)

        return retorno

    def get_Totais_Por_Forma_Pagto(self, filtro: filtroFormasPagtoCaixa):
        
        retorno = self.calcula_Totais_Por_Forma_Pagto(filtro)

        return self.qBase.toRoute(retorno.__dict__, 200)

    async def verificaCaixaAberto(self, filtro: filtroFormasPagtoCaixa) -> bool:
        a = ctx.mapAberturaCaixa
        f = ctx.mapFechamentoCaixa

        filters = [a.ID_ABERTURA == filtro.ID_CAIXA]

        abertura = ctx.session.query(a).filter(*filters).all()

        fechamento = ctx.session.query(f).filter(*[
            f.ID_ABERTURA == filtro.ID_CAIXA,
            f.FORMA_PAGTO == filtro.FORMA_PAGTO
        ]).all()

        return len(abertura) > 0 and len(fechamento) == 0

    def listaPagamentosPorForma(self, filtro: filtroFormasPagtoCaixa):
        p = ctx.mapPedido
        pg = ctx.mapPedidoPagamento

        _filters = [
            p.ID_CAIXA == filtro.ID_CAIXA, 
            pg.FORMA_PAGTO == filtro.FORMA_PAGTO,
            p.STATUS_PEDIDO == 3
        ]

        query = (
            ctx.session.query(
                p.NUMERO_PEDIDO,
                p.DATA_HORA,
                p.STATUS_PEDIDO,
                p.NOME_CLIENTE,
                p.TOTAL_PEDIDO,
                p.TROCO,
                pg.VALOR_PAGO,
                pg.CODIGO_NSU,
                pg.ID_PAGAMENTO,
                pg.VALOR_PAGO_STONE,
                pg.FORMA_PAGTO
            )
            .join(p, pg.NUMERO_PEDIDO == p.NUMERO_PEDIDO)
            .filter(*_filters)
            .all()
        )

        def calculaValorPago(formaPagto: str, valorPago: any, troco: any) -> float:
            if valorPago is None:
                valorPago = 0.00

            if troco is None:
                troco = 0.00

            retorno = float(valorPago) if valorPago is not None else 0.00

            if "DINHEIRO" in formaPagto.upper():
                try:
                    retorno = round(
                        float(valorPago) - float(troco),
                        2
                    )
                except:
                    pass

            return retorno

        retorno = [
            listaDePagamentos(
                NUMERO_PEDIDO=item.NUMERO_PEDIDO,
                DATA_HORA=datetime.strftime(item.DATA_HORA, "%d/%m/%Y %H:%M"),
                STATUS_PEDIDO=Config.getStatus(item),
                CLIENTE=item.NOME_CLIENTE,
                TOTAL_PEDIDO=0.00
                if item.TOTAL_PEDIDO is None
                else float(item.TOTAL_PEDIDO),
                TOTAL_PAGO=calculaValorPago(item.FORMA_PAGTO, item.VALOR_PAGO, item.TROCO),
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

    def gravaFechamentoCaixa(self, dados: fechamentoCaixa) -> dadosFechamento:
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

    def get_Usuario_Caixa_sem_acesso_fechamento(self, ID_CAIXA: int) -> bool:

        ID_USUARIO = ctx.session.query(ctx.mapAberturaCaixa).filter(
            ctx.mapAberturaCaixa.ID_ABERTURA == ID_CAIXA
        ).first().ID_USUARIO

        query = ctx.session.query(ctx.mapUSUARIO).filter(
            ctx.mapUSUARIO.ID_USUARIO == ID_USUARIO
        ).first()

        usuarioCaixa = query.USUARIO_CAIXA == 1 and query.ACESSO_FECHAMENTO == 0

        return usuarioCaixa

    def get_Total_Geral_Caixa(self, filtro: filtroFormasPagtoCaixa) -> float:
        p = ctx.mapPedido
        pg = ctx.mapPedidoPagamento
        s = ctx.mapSangria
        r = ctx.mapReforco

        usuarioCaixa = self.get_Usuario_Caixa_sem_acesso_fechamento(filtro.ID_CAIXA)

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

        return 0.00 if usuarioCaixa else round(TOTAL_FINAL, 2)

    async def setImpressaoCaixa(self, filtro: filtroFormasPagtoCaixa):
        filtro.NUMERO_IMPRESSORA = 1 if filtro.NUMERO_IMPRESSORA == 0 else filtro.NUMERO_IMPRESSORA
        
        cmd = ctx.tb_abertura_caixa.update().values(
            IMPRESSAO = 1 if filtro.NUMERO_IMPRESSORA == 0 else filtro.NUMERO_IMPRESSORA
        ).where(
            ctx.mapAberturaCaixa.ID_ABERTURA == filtro.ID_CAIXA
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

    def getTrocoOrigem(self, filtro: filtroCAIXA, ORIGEM: str) -> float:
        p = ctx.mapPedido

        _filters = [
            p.STATUS_PEDIDO == 3, 
            p.ID_CAIXA == filtro.ID_CAIXA,
            p.ORIGEM == ORIGEM
        ]

        somaTroco = ctx.session.query(
            p.NUMERO_PEDIDO,
            p.TROCO
        ).filter(*_filters).all()

        return sum(
            [float(item.TROCO) for item in somaTroco]
        )
    
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
                TROCO=self.getTrocoOrigem(filtro, item.ORIGEM)
            )
            for item in totais
        ]

        for item in retorno:
            item.VALOR_VENDA -= item.TROCO

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

        if formaPagto is None:
            return 0.00

        taxaPagamento = formaPagto.TAXA_PAGAMENTO

        if taxaPagamento is None:
            taxaPagamento = 0.00

        return float(taxaPagamento)

    async def checaSenhaReset(self, dados: senhaReset) -> bool:
        u = ctx.mapUSUARIO

        passwordOk = ctx.session.query(u).filter(*[
            u.SENHA_USUARIO == dados.SENHA,
            u.TIPO_USUARIO == 1
        ]).first()

        return passwordOk is not None

    async def getResumoFechamento(self, filtro: filtroCAIXA) -> List[resumoFechamento]:

        formasPagto = await self.calcula_Formas_de_Pagto_no_Caixa(
            filtroFormasPagtoCaixa(
                ID_CAIXA=filtro.ID_CAIXA,
                FORMA_PAGTO='',
                NUMERO_IMPRESSORA=0
            )
        )

        retorno = []

        periodo = await self.getPeriodo_e_Usuario(filtro.ID_CAIXA)

        for item in formasPagto:
            totais = self.calcula_Totais_Por_Forma_Pagto(
                filtroFormasPagtoCaixa(
                    ID_CAIXA=filtro.ID_CAIXA,
                    FORMA_PAGTO=item.DESCRICAO_FORMA,
                    NUMERO_IMPRESSORA=0
                )
            )

            dado = resumoFechamento(
                USUARIO = periodo.USUARIO,
                PERIODO_INICIAL = periodo.PERIODO_INICIAL,
                PERIODO_FINAL = periodo.PERIODO_FINAL,
                FORMA_PAGTO=item.DESCRICAO_FORMA,
                ABERTURA=totais.VALOR_ABERTURA,
                TOTAL=totais.TOTAL_PAGTO,
                DESCONTO=totais.DESCONTO,
                SANGRIA=totais.SANGRIA,
                REFORCO=totais.REFORCO,
                TOTAL_GERAL=totais.TOTAL_GERAL,
                DIFERENCA=totais.DIFERENCA,
                DATA_FECHAMENTO='',
                VALOR_FECHAMENTO=totais.VALOR_FECHAMENTO
            )

            retorno.append(dado)

        return retorno

    async def getResumoFechamentoPorOrigem(self, filtro: filtroCAIXA) -> List[resumoOrigemFormaPagto]:

        totais = await self.calculaCaixaPorFormaPagtoOrigem(
            filtroCAIXA(
                ID_CAIXA=filtro.ID_CAIXA
            )
        )

        retorno = [
            resumoOrigemFormaPagto(
                FORMA_PAGTO=item.FORMA_PAGTO,
                ORIGEM=item.ORIGEM,
                TOTAL=item.VALOR_VENDA
            )
            for item in totais
        ]

        return retorno

    async def listaCaixasAnteriores(self) -> List[HistoricoCaixas]:
        a = ctx.mapAberturaCaixa
        u = ctx.mapUSUARIO

        dt = datetime.today() + relativedelta(days=-30)

        q = ctx.session.query(
            a.ID_ABERTURA, 
            a.DATA_ABERTURA, 
            u.NOME_USUARIO
        ).filter(*[
            a.ID_USUARIO == u.ID_USUARIO,
            a.DATA_ABERTURA > dt,
            a.ID_USUARIO == u.ID_USUARIO
        ]).all()

        dados = [
            HistoricoCaixas(
                ID_CAIXA=item.ID_ABERTURA,
                DATA_HORA=self.qBase.TrataDataHora_Caixa(item.DATA_ABERTURA),
                DT = item.DATA_ABERTURA,
                NOME_USUARIO=item.NOME_USUARIO
            )
            for item in q
        ]

        retorno = sorted(dados, key=lambda x: x.DT, reverse=True)

        return retorno

    async def getCaixaAberto(self, filtro: filtroCAIXA) -> aberturaCaixa:
        a = ctx.mapAberturaCaixa

        q = ctx.session.query(a).filter(
            a.ID_CAIXA == filtro.ID_CAIXA,
            a.STATUS_ABERTURA == 1
        ).first()

        return q

    def __del__(self):
        ctx.session.close_all()
