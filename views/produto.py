import json
from decimal import Decimal
from typing import List

from sqlalchemy import func

import base.qModel as ctx
from base.qBase import qBase
from models.comboProduto import comboProduto
from models.filtroCodigoProduto import filtroCodigoProduto
from models.filtroDescricaoProduto import filtroDescricaoProduto
from models.filtroProduto import filtroProduto
from models.getProduto import getProduto
from models.itemPedidoCaixa import itemPedidoCaixa
from models.listaDeProduto import listaDeProduto
from models.listaProduto import listaProduto
from models.precoAtacado import precoAtacado


class produto:
    def __init__(self, keep=None, idUser=None):
        self.qBase = qBase(keep)
        self.__listOfUsers = []
        self.__idUser = idUser

    async def list(self, NOME) -> List[listaDeProduto]:
        select1 = ctx.session.query(ctx.mapProduto).order_by(
            ctx.mapProduto.DESCRICAO_PRODUTO, ctx.mapProduto.PRODUTO_ATIVO
        )

        filters = [
            ctx.mapProduto.PRECO_BALCAO > 0.00,
            ctx.mapProduto.PRODUTO_ATIVO == 1,
        ]

        if len(NOME) > 0:
            filters.append(ctx.mapProduto.DESCRICAO_PRODUTO.like("%{}%".format(NOME)))

        select1 = select1.filter(*filters)

        if len(NOME) == 0:
            select1 = select1.limit(50)

        lista = [
            listaDeProduto(
                ID_PRODUTO=row.ID_PRODUTO,
                DESCRICAO_PRODUTO=row.DESCRICAO_PRODUTO,
                PRECO_BALCAO=float(row.PRECO_BALCAO)
                if isinstance(row.PRECO_BALCAO, Decimal)
                else 0,
                ID_TRIBUTO=row.ID_TRIBUTO,
            ).model_dump_json()
            for row in select1.all()
        ]

        return lista

    async def get_Produto(self, filtro: getProduto):
        filters = [ctx.mapProduto.ID_PRODUTO == filtro.ID_PRODUTO]

        table = ctx.mapProduto

        select1 = (
            ctx.session.query(
                table.ID_PRODUTO,
                table.DESCRICAO_PRODUTO,
                table.PRECO_BALCAO,
                table.PRODUTO_ATIVO,
                table.ID_TRIBUTO,
            )
            .filter(*filters)
            .all()
        )

        lista = [
            listaDeProduto(
                ID_PRODUTO=row.ID_PRODUTO,
                DESCRICAO_PRODUTO=row.DESCRICAO_PRODUTO,
                PRECO_BALCAO=await self.getPrecoAtacado(
                    getProduto(ID_PRODUTO=row.ID_PRODUTO, QTDE=filtro.QTDE)
                ),
                ID_TRIBUTO=row.ID_TRIBUTO,
            ).model_dump_json()
            for row in select1
        ]

        return self.qBase.toRoute(lista, 200)

    async def getPrecoAtacado(self, filtro: getProduto) -> float:
        preco = (
            ctx.session.query(ctx.mapProduto.ID_PRODUTO, ctx.mapProduto.PRECO_BALCAO)
            .filter(ctx.mapProduto.ID_PRODUTO == filtro.ID_PRODUTO)
            .all()
        )

        if len(preco) == 0:
            return self.qBase.toRoute("Produto não econtrado", 500)

        precoBalcao = float(preco[0].PRECO_BALCAO)

        filters = [
            ctx.mapGradePreco.ID_PRODUTO == filtro.ID_PRODUTO,
            ctx.mapGradePreco.QTDE_INICIAL <= filtro.QTDE,
            ctx.mapGradePreco.QTDE_FINAL > filtro.QTDE,
        ]

        query = (
            ctx.session.query(
                ctx.mapGradePreco.ID_PRODUTO,
                ctx.mapGradePreco.QTDE_INICIAL,
                ctx.mapGradePreco.QTDE_FINAL,
                ctx.mapGradePreco.PRECO_VENDA,
            )
            .filter(*filters)
            .all()
        )

        retorno = precoBalcao

        for item in query:
            if isinstance(item.PRECO_VENDA, Decimal):
                retorno = float(item.PRECO_VENDA)

        return retorno

    async def routePrecoAtacado(self, filtro: getProduto):
        precoBalcao = await self.getPrecoAtacado(filtro)

        return self.qBase.toRoute(
            precoAtacado(PRECO=precoBalcao).model_dump_json(), 200
        )

    async def buscaProdutoPorCodigo(self, filtro: filtroCodigoProduto) -> List[itemPedidoCaixa]:
        p = ctx.mapProduto
        lista = []

        filters = [
            p.CODIGO_PRODUTO_PDV == filtro.CODIGO,
            p.PRECO_BALCAO > 0.00,
            p.PRODUTO_ATIVO == 1,
        ]

        filtro.CODIGO = filtro.CODIGO.strip()

        row = ctx.session.query(
            p.ID_PRODUTO, p.DESCRICAO_PRODUTO, p.PRECO_BALCAO, p.ID_TRIBUTO
        ).filter(*filters)

        if row.first():
            rec = row.first()

            lista = [
                itemPedidoCaixa(
                    NUMERO_PEDIDO=0,
                    NUMERO_ITEM=0,
                    ID_PRODUTO=rec.ID_PRODUTO,
                    DESCRICAO_PRODUTO=rec.DESCRICAO_PRODUTO,
                    QTDE=1,
                    PRECO=await self.getPrecoAtacado(
                        getProduto(
                            ID_PRODUTO=rec.ID_PRODUTO,
                            QTDE=1
                        )
                    ),
                    TOTAL=rec.PRECO_BALCAO,
                    ID_TRIBUTO=rec.ID_TRIBUTO,
                )
            ]

        elif not row.first():
            filters = [
                p.CODIGO_PRODUTO == filtro.CODIGO,
                p.PRECO_BALCAO > 0.00,
                p.PRODUTO_ATIVO == 1,
            ]

            row = ctx.session.query(
                p.ID_PRODUTO, p.DESCRICAO_PRODUTO, p.PRECO_BALCAO, p.ID_TRIBUTO
            ).filter(*filters)

            if row.first():
                rec = row.first()

                lista = [
                    itemPedidoCaixa(
                        NUMERO_PEDIDO=0,
                        NUMERO_ITEM=0,
                        ID_PRODUTO=rec.ID_PRODUTO,
                        DESCRICAO_PRODUTO=rec.DESCRICAO_PRODUTO,
                        QTDE=1,
                        PRECO=await self.getPrecoAtacado(
                            getProduto(
                                rec.ID_PRODUTO,
                                1)
                        ),
                        TOTAL=rec.PRECO_BALCAO,
                        ID_TRIBUTO=rec.ID_TRIBUTO,
                    )
                ]

        return lista

    async def buscaProdutosSimilares(
        self, filtro: filtroDescricaoProduto
    ) -> List[listaProduto]:
        lista = []

        p = ctx.mapProduto

        select1 = ctx.session.query(p).order_by(p.DESCRICAO_PRODUTO, p.PRODUTO_ATIVO)

        filters = [p.PRECO_BALCAO > 0.00, p.PRODUTO_ATIVO == 1]

        if len(filtro.DESCRICAO) > 0:
            filters.append(p.DESCRICAO_PRODUTO.like(f"%{filtro.DESCRICAO}%"))

        select1 = select1.filter(*filters)

        if len(filtro.DESCRICAO) == 0:
            select1 = select1.limit(50)

        lista = [
            listaProduto(
                ID_PRODUTO=row.ID_PRODUTO,
                DESCRICAO_PRODUTO=row.DESCRICAO_PRODUTO,
                PRECO_BALCAO=0 if row.PRECO_BALCAO is None else float(row.PRECO_BALCAO),
                ID_TRIBUTO=row.ID_TRIBUTO,
                SALDO=await self.buscaSaldoProduto(
                    filtroProduto(ID_PRODUTO=row.ID_PRODUTO)
                ),
                CODIGO_ZE="" if row.CODIGO_ZE is None else row.CODIGO_ZE,
            )
            for row in select1.all()
        ]

        return lista

    async def buscaSaldoProduto(self, filtro: filtroProduto) -> float:
        e = ctx.mapEstoque

        filters = [e.ID_PRODUTO == filtro.ID_PRODUTO, e.MOVIMENTO == 0]

        entradas = (
            ctx.session.query(func.sum(e.QTDE_ESTOQUE).label("ENTRADAS"))
            .filter(*filters)
            .first()
        )

        filters = [e.ID_PRODUTO == filtro.ID_PRODUTO, e.MOVIMENTO == 1]

        saidas = (
            ctx.session.query(func.sum(e.QTDE_ESTOQUE).label("SAIDAS"))
            .filter(*filters)
            .first()
        )

        e = entradas[0]
        s = saidas[0]

        if e is None:
            e = 0

        if s is None:
            s = 0

        saldo = float(e) - float(s)

        return saldo

    async def get_Lista_de_Produtos(self) -> List[comboProduto]:
        lista = []

        p = ctx.mapProduto

        filters = [p.PRECO_BALCAO > 0.00, p.PRODUTO_ATIVO == 1]

        select1 = (
            ctx.session.query(p).order_by(p.DESCRICAO_PRODUTO).filter(*filters).all()
        )

        lista = [
            comboProduto(
                ID_PRODUTO=row.ID_PRODUTO, DESCRICAO_PRODUTO=row.DESCRICAO_PRODUTO
            )
            for row in select1
        ]

        return lista

    def __del__(self):
        ctx.session.close_all()
