from typing import List

import base.qModel as ctx
from base.qBase import qBase
from models.Cliente_Endereco_Transporte import Cliente_Endereco_Transporte
from models.comboCliente import comboCliente
from models.comboEndereco import comboEndereco
from models.dadosCliente import dadosCliente
from models.dadosEndereco import dadosEndereco
from models.editCliente import editCliente
from models.filtroCliente import filtroCliente
from models.filtroEndereco import filtroEndereco
from models.filtroNumeroPedido import filtroNumeroPedido
from models.fiscalCliente import fiscalCliente
from models.listaDeCliente import listaDeCliente


class Cliente:
    def __init__(self, keep=None, idUser=None):
        self.qBase = qBase(keep)

    async def buscaCliente(self, filtro: filtroCliente) -> List[comboCliente]:
        c = ctx.mapCliente

        filters = [c.CPF == filtro.FILTRO]

        query = ctx.session.query(c).filter(*filters).all()

        if len(query) == 0:
            filters = [c.TELEFONE_CLIENTE == filtro.FILTRO]

            query = ctx.session.query(c).filter(*filters).all()

        if len(query) == 0:
            filters = [c.NOME_CLIENTE.like(f"%{filtro.FILTRO}%")]

            query = ctx.session.query(c).filter(*filters).limit(150).all()

        retorno = [
            comboCliente(
                ID_CLIENTE=item.ID_CLIENTE,
                NOME_CLIENTE=item.NOME_CLIENTE,
                CPF=item.CPF,
                TELEFONE_CLIENTE=item.TELEFONE_CLIENTE,
            ).__dict__
            for item in query
        ]

        return retorno

    async def buscaEndereco(self, filtro: filtroEndereco) -> List[comboEndereco]:
        e = ctx.mapEnderecoCliente

        filters = [
            e.ID_CLIENTE == filtro.ID_CLIENTE,
            e.ENDERECO.like(f"%{filtro.FILTRO}%"),
        ]

        query = ctx.session.query(e).filter(*filters).limit(20).all()

        retorno = [
            comboEndereco(
                ID_ENDERECO=item.ID_ENDERECO,
                ENDERECO=item.ENDERECO,
                NUMERO_ENDERECO=item.NUMERO_ENDERECO,
                COMPLEMENTO_ENDERECO=item.COMPLEMENTO_ENDERECO,
                BAIRRO=item.BAIRRO,
                CEP=item.CEP,
                CIDADE=item.MUNICIPIO,
                UF=item.UF,
            ).__dict__
            for item in query
        ]

        return retorno

    async def get_Dados_Cliente_Endereco_Transporte(
        self, dados: Cliente_Endereco_Transporte
    ) -> Cliente_Endereco_Transporte:
        c = ctx.mapCliente
        e = ctx.mapEnderecoCliente
        t = ctx.mapTransporte

        cliente = (
            ctx.session.query(c.ID_CLIENTE, c.NOME_CLIENTE, c.TELEFONE_CLIENTE)
            .filter(c.ID_CLIENTE == dados.ID_CLIENTE)
            .all()
        )

        endereco = (
            ctx.session.query(
                e.ID_ENDERECO, e.ENDERECO, e.NUMERO_ENDERECO, e.COMPLEMENTO_ENDERECO
            )
            .filter(e.ID_ENDERECO == dados.ID_ENDERECO)
            .all()
        )

        transporte = (
            ctx.session.query(t.ID_TRANSPORTE, t.NOME_TRANSPORTE)
            .filter(t.ID_TRANSPORTE == dados.ID_TRANSPORTE)
            .all()
        )

        e1 = (0, "")
        t1 = (0, "")

        if len(endereco) > 0:
            e1 = (
                endereco[0].ID_ENDERECO,
                " ".join(
                    (
                        endereco[0].ENDERECO,
                        endereco[0].NUMERO_ENDERECO,
                        endereco[0].COMPLEMENTO_ENDERECO,
                    )
                ),
            )

        if len(transporte) > 0:
            t1 = (transporte[0].ID_TRANSPORTE, transporte[0].NOME_TRANSPORTE)

        retorno = Cliente_Endereco_Transporte(
            ID_CLIENTE=cliente[0].ID_CLIENTE,
            NOME_CLIENTE="".join(
                (cliente[0].NOME_CLIENTE, f", Tel: {cliente[0].TELEFONE_CLIENTE}")
            ),
            ID_ENDERECO=e1[0],
            ENDERECO=e1[1],
            ID_TRANSPORTE=t1[0],
            NOME_TRANSPORTE=t1[1],
        )

        return retorno

    async def getFiscalCliente(self, filtro: filtroNumeroPedido) -> fiscalCliente:
        p = ctx.mapPedido

        query = ctx.session.query(p).filter(
            p.NUMERO_PEDIDO == int(filtro.NUMERO_PEDIDO)
        ).all()

        return fiscalCliente(CPF=query[0].CPF if len(query) > 0 else "")

    async def gravaDadosCliente(self, dados: editCliente):
        cliente = dados.cliente
        endereco = dados.endereco[0]

        c = ctx.mapCliente
        e = ctx.mapEnderecoCliente

        cmd = None
        idCliente = cliente.ID_CLIENTE

        if cliente.ID_CLIENTE == 0:
            cmd = ctx.tb_cliente.insert().values(
                ID_CLIENTE=cliente.ID_CLIENTE,
                NOME_CLIENTE=cliente.NOME_CLIENTE,
                CPF=cliente.CPF,
                ENDERECO_CLIENTE=cliente.ENDERECO_CLIENTE,
                NUMERO_ENDERECO=cliente.NUMERO_ENDERECO,
                COMPLEMENTO_ENDERECO=cliente.COMPLEMENTO_ENDERECO,
                BAIRRO_CLIENTE=cliente.BAIRRO_CLIENTE,
                CEP_CLIENTE=cliente.CEP_CLIENTE,
                MUNICIPIO_CLIENTE=cliente.MUNICIPIO_CLIENTE,
                UF_CLIENTE=cliente.UF_CLIENTE,
                TELEFONE_CLIENTE=cliente.TELEFONE_CLIENTE,
                EMAIL_CLIENTE=cliente.EMAIL_CLIENTE,
                ID_EMPRESA=cliente.ID_EMPRESA,
                IE=cliente.IE,
                BLACK_LIST=cliente.BLACK_LIST,
                NOME_FANTASIA_CLIENTE=cliente.NOME_FANTASIA_CLIENTE,
                OBS_CLIENTE=cliente.OBS_CLIENTE,
                TAXA_ENTREGA=cliente.TAXA_ENTREGA,
            )

            result = ctx.session.execute(cmd)

            idCliente = int(result.inserted_primary_key[0])

        elif cliente.ID_CLIENTE > 0:
            cmd = (
                ctx.tb_cliente.update()
                .values(
                    NOME_CLIENTE=cliente.NOME_CLIENTE,
                    CPF=cliente.CPF,
                    ENDERECO_CLIENTE=cliente.ENDERECO_CLIENTE,
                    NUMERO_ENDERECO=cliente.NUMERO_ENDERECO,
                    COMPLEMENTO_ENDERECO=cliente.COMPLEMENTO_ENDERECO,
                    BAIRRO_CLIENTE=cliente.BAIRRO_CLIENTE,
                    CEP_CLIENTE=cliente.CEP_CLIENTE,
                    MUNICIPIO_CLIENTE=cliente.MUNICIPIO_CLIENTE,
                    UF_CLIENTE=cliente.UF_CLIENTE,
                    TELEFONE_CLIENTE=cliente.TELEFONE_CLIENTE,
                    EMAIL_CLIENTE=cliente.EMAIL_CLIENTE,
                    ID_EMPRESA=cliente.ID_EMPRESA,
                    IE=cliente.IE,
                    BLACK_LIST=cliente.BLACK_LIST,
                    NOME_FANTASIA_CLIENTE=cliente.NOME_FANTASIA_CLIENTE,
                    OBS_CLIENTE=cliente.OBS_CLIENTE,
                    TAXA_ENTREGA=cliente.TAXA_ENTREGA,
                )
                .where(c.ID_CLIENTE == cliente.ID_CLIENTE)
            )

            ctx.session.execute(cmd)

        cmd1 = None

        if endereco.ID_ENDERECO == 0:
            cmd1 = ctx.tb_endereco_cliente.insert().values(
                ID_ENDERECO=endereco.ID_ENDERECO,
                ID_CLIENTE=idCliente,
                ENDERECO=endereco.ENDERECO,
                NUMERO_ENDERECO=endereco.NUMERO_ENDERECO,
                COMPLEMENTO_ENDERECO=endereco.COMPLEMENTO_ENDERECO,
                BAIRRO=endereco.BAIRRO,
                CEP=endereco.CEP,
                MUNICIPIO=endereco.MUNICIPIO,
                UF=endereco.UF,
                ID_EMPRESA=endereco.ID_EMPRESA,
                LATITUDE=endereco.LATITUDE,
                LONGITUDE=endereco.LONGITUDE,
            )

        elif endereco.ID_ENDERECO > 0:
            cmd1 = (
                ctx.tb_endereco_cliente.update()
                .values(
                    ID_ENDERECO=endereco.ID_ENDERECO,
                    ID_CLIENTE=idCliente,
                    ENDERECO=endereco.ENDERECO,
                    NUMERO_ENDERECO=endereco.NUMERO_ENDERECO,
                    COMPLEMENTO_ENDERECO=endereco.COMPLEMENTO_ENDERECO,
                    BAIRRO=endereco.BAIRRO,
                    CEP=endereco.CEP,
                    MUNICIPIO=endereco.MUNICIPIO,
                    UF=endereco.UF,
                    ID_EMPRESA=endereco.ID_EMPRESA,
                    LATITUDE=endereco.LATITUDE,
                    LONGITUDE=endereco.LONGITUDE,
                )
                .where(e.ID_ENDERECO == endereco.ID_ENDERECO)
            )

        ctx.session.execute(cmd1)
        ctx.session.commit()

    async def listaCliente(self, filtro: filtroCliente) -> List[listaDeCliente]:
        c = ctx.mapCliente

        filters = []

        if len(filtro.FILTRO) > 0:
            filters.append(
                (c.NOME_CLIENTE.like(f"%{filtro.FILTRO}%"))
                | (c.NOME_FANTASIA_CLIENTE.like(f"%{filtro.FILTRO}%"))
                | (c.TELEFONE_CLIENTE.like(f"%{filtro.FILTRO}%"))
            )

        query = ctx.session.query(c).filter(*filters).limit(200).all()

        retorno = [
            listaDeCliente(
                ID_CLIENTE=item.ID_CLIENTE,
                NOME_CLIENTE=item.NOME_CLIENTE,
                NOME_FANTASIA_CLIENTE=""
                if item.NOME_FANTASIA_CLIENTE is None
                else item.NOME_FANTASIA_CLIENTE,
                TELEFONE_CLIENTE=""
                if item.TELEFONE_CLIENTE is None
                else item.TELEFONE_CLIENTE,
            )
            for item in query
        ]

        return retorno

    async def editCliente(self, filtro: filtroCliente) -> editCliente:
        c = ctx.mapCliente
        e = ctx.mapEnderecoCliente

        query1 = ctx.session.query(c).filter(c.ID_CLIENTE == int(filtro.FILTRO)).all()

        if len(query1) == 0:
            raise Exception("Cliente não encontrado na base")

        rec = query1[0]

        cliente = dadosCliente(
            ID_CLIENTE=rec.ID_CLIENTE,
            NOME_CLIENTE="" if rec.NOME_CLIENTE is None else rec.NOME_CLIENTE,
            CPF="" if rec.CPF is None else rec.CPF,
            ENDERECO_CLIENTE=rec.ENDERECO_CLIENTE,
            NUMERO_ENDERECO="" if rec.NUMERO_ENDERECO is None else rec.NUMERO_ENDERECO,
            COMPLEMENTO_ENDERECO=""
            if rec.COMPLEMENTO_ENDERECO is None
            else rec.COMPLEMENTO_ENDERECO,
            BAIRRO_CLIENTE="" if rec.BAIRRO_CLIENTE is None else rec.BAIRRO_CLIENTE,
            CEP_CLIENTE="" if rec.CEP_CLIENTE is None else rec.CEP_CLIENTE,
            MUNICIPIO_CLIENTE=""
            if rec.MUNICIPIO_CLIENTE is None
            else rec.MUNICIPIO_CLIENTE,
            UF_CLIENTE="" if rec.UF_CLIENTE is None else rec.UF_CLIENTE,
            TELEFONE_CLIENTE=""
            if rec.TELEFONE_CLIENTE is None
            else rec.TELEFONE_CLIENTE,
            EMAIL_CLIENTE="" if rec.EMAIL_CLIENTE is None else rec.EMAIL_CLIENTE,
            ID_EMPRESA=0 if rec.ID_EMPRESA is None else rec.ID_EMPRESA,
            IE="" if rec.IE is None else rec.IE,
            BLACK_LIST=0 if rec.BLACK_LIST is None else rec.BLACK_LIST,
            NOME_FANTASIA_CLIENTE=""
            if rec.NOME_FANTASIA_CLIENTE is None
            else rec.NOME_FANTASIA_CLIENTE,
            OBS_CLIENTE="" if rec.OBS_CLIENTE is None else rec.OBS_CLIENTE,
            TAXA_ENTREGA=0 if rec.TAXA_ENTREGA is None else rec.TAXA_ENTREGA,
        )

        query2 = ctx.session.query(e).filter(e.ID_CLIENTE == int(filtro.FILTRO)).all()

        endereco = [
            dadosEndereco(
                ID_ENDERECO=item.ID_ENDERECO,
                ID_CLIENTE=item.ID_CLIENTE,
                ENDERECO="" if item.ENDERECO is None else item.ENDERECO,
                NUMERO_ENDERECO=""
                if item.NUMERO_ENDERECO is None
                else item.NUMERO_ENDERECO,
                COMPLEMENTO_ENDERECO=""
                if item.COMPLEMENTO_ENDERECO is None
                else item.COMPLEMENTO_ENDERECO,
                BAIRRO="" if item.BAIRRO is None else item.BAIRRO,
                CEP="" if item.CEP is None else item.CEP,
                MUNICIPIO="" if item.MUNICIPIO is None else item.MUNICIPIO,
                UF="" if item.UF is None else item.UF,
                ID_EMPRESA=0 if item.ID_EMPRESA is None else item.ID_EMPRESA,
                LATITUDE=0 if item.LATITUDE is None else item.LATITUDE,
                LONGITUDE=0 if item.LONGITUDE is None else item.LONGITUDE,
            )
            for item in query2
        ]

        return editCliente(cliente=cliente, endereco=endereco)

    def __del__(self):
        ctx.session.close_all()
