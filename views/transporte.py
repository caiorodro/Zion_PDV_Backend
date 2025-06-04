from typing import List

import base.qModel as ctx
from base.qBase import qBase
from models.comboTransporte import comboTransporte
from models.dadosTransporte import dadosTransporte
from models.filtroTransporte import filtroTransporte
from models.listaDeTransporte import listaDeTransporte


class Transporte:
    def __init__(self, keep=None, idUser=None):
        self.qBase = qBase(keep)

    async def buscaTransporte(self, filtro: filtroTransporte) -> List[comboTransporte]:
        c = ctx.mapTransporte

        filters = [c.NOME_TRANSPORTE.like(f"%{filtro.FILTRO}%")]

        query = ctx.session.query(c).filter(*filters).limit(150).all()

        retorno = [
            comboTransporte(
                ID_TRANSPORTE=item.ID_TRANSPORTE, NOME_TRANSPORTE=item.NOME_TRANSPORTE
            ).__dict__
            for item in query
        ]

        return retorno

    async def gravaDadosTransporte(self, dados: dadosTransporte):
        c = ctx.mapTransporte

        cmd = None
        idTransporte = dados.ID_TRANSPORTE

        if idTransporte == 0:
            cmd = ctx.tb_transporte.insert().values(
                ID_TRANSPORTE=0,
                NOME_TRANSPORTE=dados.NOME_TRANSPORTE,
                CNPJ=dados.CNPJ,
                IE=dados.IE,
                ENDERECO=dados.ENDERECO,
                CIDADE=dados.CIDADE,
                UF=dados.UF,
                PLACA=dados.PLACA,
                EMAIL=dados.EMAIL,
            )

        elif idTransporte > 0:
            cmd = (
                ctx.tb_transporte.update()
                .values(
                    NOME_TRANSPORTE=dados.NOME_TRANSPORTE,
                    CNPJ=dados.CNPJ,
                    IE=dados.IE,
                    ENDERECO=dados.ENDERECO,
                    CIDADE=dados.CIDADE,
                    UF=dados.UF,
                    PLACA=dados.PLACA,
                    EMAIL=dados.EMAIL,
                )
                .where(c.ID_TRANSPORTE == idTransporte)
            )

        ctx.session.execute(cmd)
        ctx.session.commit()

    async def listaTransporte(
        self, filtro: filtroTransporte
    ) -> List[listaDeTransporte]:
        c = ctx.mapTransporte

        filters = []

        if len(filtro.FILTRO) > 0:
            filters.append((c.NOME_TRANSPORTE.like(f"%{filtro.FILTRO}%")))

        query = ctx.session.query(c).filter(*filters).limit(200).all()

        retorno = [
            listaDeTransporte(
                ID_TRANSPORTE=item.ID_TRANSPORTE, NOME_TRANSPORTE=item.NOME_TRANSPORTE
            )
            for item in query
        ]

        return retorno

    async def editTransporte(self, filtro: filtroTransporte) -> dadosTransporte:
        c = ctx.mapTransporte

        query1 = (
            ctx.session.query(c).filter(c.ID_TRANSPORTE == int(filtro.FILTRO)).all()
        )

        if len(query1) == 0:
            raise Exception("Transporte não encontrado na base")

        rec = query1[0]

        cliente = dadosTransporte(
            ID_TRANSPORTE=rec.ID_TRANSPORTE,
            NOME_TRANSPORTE="" if rec.NOME_TRANSPORTE is None else rec.NOME_TRANSPORTE,
            CNPJ="" if rec.CNPJ is None else rec.CNPJ,
            IE="" if rec.IE is None else rec.IE,
            ENDERECO="" if rec.ENDERECO is None else rec.ENDERECO,
            CIDADE="" if rec.CIDADE is None else rec.CIDADE,
            UF="" if rec.UF is None else rec.UF,
            PLACA="" if rec.PLACA is None else rec.PLACA,
            EMAIL="" if rec.EMAIL is None else rec.EMAIL,
        )

        return cliente

    def __del__(self):
        ctx.session.close_all()
