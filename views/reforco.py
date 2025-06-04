from datetime import datetime

import base.qModel as ctx
from base.qBase import qBase
from models.filtroReforco import filtroReforco
from models.listaReforco import listaReforco
from models.reforco import reforco


class Reforco:
    def __init__(self, keep=None, idUser=None):
        self.qBase = qBase(keep)

    async def listReforco(self, filtro: filtroReforco):
        data = datetime.strptime(filtro.DATA_REFORCO, "%d/%m/%Y")

        a = ctx.mapReforco

        _filters = [a.DATA_REFORCO >= data, a.ID_ABERTURA == filtro.ID_CAIXA]

        query = ctx.session.query(a).filter(*_filters).all()

        query

        retorno = [
            listaReforco(
                ID_REFORCO=item.ID_REFORCO,
                DATA_REFORCO=datetime.strftime(item.DATA_REFORCO, "%d/%m/%Y %H:%M")
                if item.DATA_REFORCO is not None
                else "",
                DESCRICAO_REFORCO=item.DESCRICAO_REFORCO,
                USUARIO=await self.getUsuario(item.ID_USUARIO),
                VALOR_REFORCO=float(item.VALOR_REFORCO)
                if item.VALOR_REFORCO is not None
                else 0.00,
                ID_REFORCO_LOCAL=0,
                ID_TERMINAL=0,
                ID_ABERTURA=item.ID_ABERTURA,
            ).model_dump_json()
            for item in sorted(query, key=lambda e: e.DATA_REFORCO, reverse=True)
        ]

        return self.qBase.toRoute(retorno, 200)

    async def gravaReforco(self, dados: reforco) -> bool:
        idUsuario = await self.getUsuarioDoCaixa(dados.ID_ABERTURA)

        cmd = ctx.tb_reforco_caixa.insert().values(
            ID_REFORCO=0,
            DATA_REFORCO=datetime.strptime(dados.DATA_REFORCO, "%d/%m/%Y %H:%M"),
            DESCRICAO_REFORCO=dados.DESCRICAO_REFORCO,
            ID_USUARIO=idUsuario,
            VALOR_REFORCO=dados.VALOR_REFORCO,
            ID_REFORCO_LOCAL=dados.ID_REFORCO_LOCAL,
            ID_TERMINAL=dados.ID_TERMINAL,
            ID_ABERTURA=dados.ID_ABERTURA,
        )

        ctx.session.execute(cmd)
        ctx.session.commit()

        return True

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
