import asyncio
from datetime import datetime
from typing import List

import base.qModel as ctx
from base.qBase import qBase

from models.filtroCAIXA import filtroCAIXA
from models.filtroFormasPagtoCaixa import filtroFormasPagtoCaixa
from models.filtroSangria import filtroSangria
from models.impressaoSangria import impressaoSangria
from models.listaSangria import listaSangria
from models.sangria import sangria

from views.caixa import Caixa

class Sangria:
    def __init__(self, keep=None, idUser=None):
        self.qBase = qBase(keep)

    async def listSangria(self, filtro: filtroSangria):
        data = datetime.strptime(filtro.DATA_SANGRIA, "%d/%m/%Y")

        a = ctx.mapSangria

        _filters = [a.DATA_SANGRIA >= data, a.ID_ABERTURA == filtro.ID_CAIXA]

        query = ctx.session.query(a).filter(*_filters).all()

        query

        retorno = [
            listaSangria(
                ID_SANGRIA=item.ID_SANGRIA,
                DATA_SANGRIA=datetime.strftime(item.DATA_SANGRIA, "%d/%m/%Y %H:%M")
                if item.DATA_SANGRIA is not None
                else "",
                DESCRICAO_SANGRIA=item.DESCRICAO_SANGRIA,
                USUARIO=await self.getUsuario(item.ID_USUARIO),
                VALOR_SANGRIA=float(item.VALOR_SANGRIA)
                if item.VALOR_SANGRIA is not None
                else 0.00,
                ID_SANGRIA_LOCAL=0,
                ID_TERMINAL=0,
                ID_ABERTURA=item.ID_ABERTURA,
            ).__dict__
            for item in sorted(query, key=lambda e: e.DATA_SANGRIA, reverse=True)
        ]

        return self.qBase.toRoute(retorno, 200)

    def gravaSangria(self, dados: sangria) -> bool:

        ha = asyncio.run(
            self.verificaSeHaDinheiroNoCaixa(
                dados.ID_ABERTURA,
                dados.VALOR_SANGRIA
            )
        )

        if not ha:
            raise Exception('Não dinheiro em caixa suficiente para essa sangria')

        idUsuario = asyncio.run(
            self.getUsuarioDoCaixa(dados.ID_ABERTURA)
            )

        cmd = ctx.tb_sangria.insert().values(
            ID_SANGRIA=0,
            DATA_SANGRIA=datetime.strptime(dados.DATA_SANGRIA, "%d/%m/%Y %H:%M"),
            DESCRICAO_SANGRIA=dados.DESCRICAO_SANGRIA,
            ID_USUARIO=idUsuario,
            VALOR_SANGRIA=dados.VALOR_SANGRIA,
            ID_SANGRIA_LOCAL=dados.ID_SANGRIA_LOCAL,
            ID_TERMINAL=dados.ID_TERMINAL,
            ID_ABERTURA=dados.ID_ABERTURA
        )

        ctx.session.execute(cmd)
        ctx.session.commit()

        return True

    async def verificaSeHaDinheiroNoCaixa(self, ID_CAIXA: int, VALOR_SANGRIA: float) -> bool:
        cx = Caixa()

        totais = cx.calcula_Totais_Por_Forma_Pagto(
            filtroFormasPagtoCaixa(
                ID_CAIXA=ID_CAIXA,
                FORMA_PAGTO="DINHEIRO",
                NUMERO_IMPRESSORA=0
            )
        )

        totalEmCaixa = totais.VALOR_ABERTURA + totais.TOTAL_PAGTO + totais.REFORCO
        totalEmCaixa = totalEmCaixa - totais.SANGRIA

        totalEmCaixa += .01
        totalEmCaixa = round(totalEmCaixa, 2)

        return VALOR_SANGRIA < totalEmCaixa

    async def getUsuario(self, ID_USUARIO) -> str:
        NOME_USUARIO = (
            ctx.session.query(ctx.mapUSUARIO)
            .filter(ctx.mapUSUARIO.ID_USUARIO == ID_USUARIO)
            .first()
            .NOME_USUARIO
        )

        return NOME_USUARIO

    async def getUsuarioDoCaixa(self, ID_CAIXA: int) -> int:
        retorno = (
            ctx.session.query(ctx.mapAberturaCaixa)
            .filter(ctx.mapAberturaCaixa.ID_ABERTURA == ID_CAIXA)
            .all()[0]
            .ID_USUARIO
        )

        return retorno

    async def printSangria(self, filtro: filtroCAIXA) -> List[impressaoSangria]:
        s = ctx.mapSangria
        u = ctx.mapUSUARIO
        a = ctx.mapAberturaCaixa

        querySangria = ctx.session.query(
            s.DATA_SANGRIA,
            s.VALOR_SANGRIA,
            s.DESCRICAO_SANGRIA,
            u.NOME_USUARIO,
            a.DATA_ABERTURA
        ).filter(*
            [
                s.ID_ABERTURA == filtro.ID_CAIXA,
                s.ID_USUARIO == u.ID_USUARIO,
                s.ID_ABERTURA == a.ID_ABERTURA
            ]
        ).all()

        retorno = [
            impressaoSangria(
                DATA_SANGRIA=self.qBase.TrataDataHora(item.DATA_SANGRIA),
                DESCRICAO_CAIXA=item.DESCRICAO_SANGRIA,
                VALOR_SANGRIA=round(float(item.VALOR_SANGRIA), 2),
                USUARIO_CAIXA=item.NOME_USUARIO,
                CAIXA_DE=self.qBase.TrataDataHora(item.DATA_ABERTURA)
            )
            for item in querySangria
        ]

        return retorno 
