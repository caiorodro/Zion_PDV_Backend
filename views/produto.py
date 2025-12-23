import base64
from decimal import Decimal
import json
import os
from typing import List

from sqlalchemy import func

import base.qModel as ctx
from base.qBase import qBase
from models.comboProduto import comboProduto
from models.filtroCodigoProduto import filtroCodigoProduto
from models.filtroDescricaoProduto import filtroDescricaoProduto
from models.filtroProduto import filtroProduto
from models.getProduto import getProduto
from models.ItemBalanca import itemBalanca
from models.itemGrade import itemGrade
from models.itemPedidoCaixa import itemPedidoCaixa
from models.listaDeProduto import listaDeProduto
from models.listaProduto import listaProduto
from models.precoAtacado import precoAtacado
from models.produtoBalanca import produtoBalanca
from models.produtoImage import produtoImage
from models.produtoPrecoBalanca import produtoPrecoBalanca

class produto:

    def __init__(self, keep=None, idUser=None):
        self.qBase = qBase(keep)

        self.prefs = self.qBase.getPrefs()

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
            ).__dict__
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
                PRECO_BALCAO=self.getPrecoAtacado(
                    getProduto(ID_PRODUTO=row.ID_PRODUTO, QTDE=filtro.QTDE)
                ),
                ID_TRIBUTO=row.ID_TRIBUTO,
            ).__dict__
            for row in select1
        ]

        return self.qBase.toRoute(lista, 200)

    def getPrecoAtacado(self, filtro: getProduto) -> float:
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
        precoBalcao = self.getPrecoAtacado(filtro)

        return self.qBase.toRoute(
            precoAtacado(PRECO=precoBalcao).__dict__, 200
        )

    def getItemBalanca(self, filtro: filtroCodigoProduto) -> produtoBalanca | produtoPrecoBalanca | None:

        dadosBalanca = itemBalanca(
            TAMANHO_CODIGO_BARRAS=13,
            POSICAO_CODIGO_PRODUTO=[1, 7],
            POSICAO_QTDE_PESO=[7, -1],
            POSICAO_PRECO=[7, -1]
        )

        fileBalanca = 'cfg/itemBalanca.json'

        if os.path.exists(fileBalanca):
            content = ''

            try:
                with open(fileBalanca, 'r') as fi:
                    content = json.loads(fi.read())

                dadosBalanca = itemBalanca(**content)

            except Exception as ex:
                print(f'Error on read Balança file {ex.args[0]}')

        if len(self.qBase.onlyNumbers(filtro.CODIGO)) != dadosBalanca.TAMANHO_CODIGO_BARRAS:
            return None

        codigoBalanca = str(int(
            filtro.CODIGO[dadosBalanca.POSICAO_CODIGO_PRODUTO[0] : dadosBalanca.POSICAO_CODIGO_PRODUTO[1]]
            ))

        p = ctx.mapProduto

        items = ctx.session.query(p).filter(
            p.CODIGO_PRODUTO == codigoBalanca
        ).all()

        itemsBalanca = [
            item
            for item in items
            if item.ID_FAMILIA in self.prefs.FAMILIAS_BALANCA
        ]

        record = None

        if not any(itemsBalanca):
            return record

        if any(dadosBalanca.POSICAO_QTDE_PESO):
            record = produtoBalanca(
                ITEM_PRODUTO=itemsBalanca[0],
                QTDE=float(filtro.CODIGO[
                    dadosBalanca.POSICAO_QTDE_PESO[0]: dadosBalanca.POSICAO_QTDE_PESO[1]
                    ]) / 1000
                )

        if any(dadosBalanca.POSICAO_PRECO):
            record =  produtoPrecoBalanca(
                ITEM_PRODUTO=itemsBalanca[0],
                QTDE = 1,
                PRECO_TOTAL = float(filtro.CODIGO[
                    dadosBalanca.POSICAO_PRECO[0]: dadosBalanca.POSICAO_PRECO[1]
                    ]) / 100
                )

        return record
    
    async def buscaProdutoPorCodigo(self, filtro: filtroCodigoProduto) -> List[itemPedidoCaixa]:

        itemCodigoBalanca = self.getItemBalanca(filtro)

        if isinstance(itemCodigoBalanca, produtoBalanca):
            rec = itemCodigoBalanca.ITEM_PRODUTO

            familiaBalanca = self.qBase.isFamiliaBalanca(rec.ID_FAMILIA) if isinstance(rec.ID_FAMILIA, int) else False

            lista = [
                itemPedidoCaixa(
                    NUMERO_PEDIDO=0,
                    NUMERO_ITEM=0,
                    ID_PRODUTO=rec.ID_PRODUTO,
                    DESCRICAO_PRODUTO=rec.DESCRICAO_PRODUTO,
                    QTDE=itemCodigoBalanca.QTDE,
                    PRECO=float(rec.PRECO_BALCAO),
                    TOTAL=round(float(rec.PRECO_BALCAO) * itemCodigoBalanca.QTDE, 2),
                    ID_TRIBUTO=rec.ID_TRIBUTO,
                    QTDE_FRACIONADA=familiaBalanca,
                    ID_FAMILIA=rec.ID_FAMILIA
                )
            ]

            return lista

        elif isinstance(itemCodigoBalanca, produtoPrecoBalanca):
            rec = itemCodigoBalanca.ITEM_PRODUTO

            lista = [
                itemPedidoCaixa(
                    NUMERO_PEDIDO=0,
                    NUMERO_ITEM=0,
                    ID_PRODUTO=rec.ID_PRODUTO,
                    DESCRICAO_PRODUTO=rec.DESCRICAO_PRODUTO,
                    QTDE=itemCodigoBalanca.QTDE,
                    PRECO=itemCodigoBalanca.PRECO_TOTAL,
                    TOTAL=itemCodigoBalanca.PRECO_TOTAL,
                    ID_TRIBUTO=rec.ID_TRIBUTO,
                    QTDE_FRACIONADA=False,
                    ID_FAMILIA = rec.ID_FAMILIA
                )
            ]

            return lista

        p = ctx.mapProduto
        lista = []

        filters = [
            p.CODIGO_PRODUTO_PDV == filtro.CODIGO,
            p.PRECO_BALCAO > 0.00,
            p.PRODUTO_ATIVO == 1
        ]

        filtro.CODIGO = filtro.CODIGO.strip()

        row = ctx.session.query(
            p.ID_PRODUTO, p.DESCRICAO_PRODUTO, p.PRECO_BALCAO, p.ID_TRIBUTO, p.ID_FAMILIA
        ).filter(*filters)

        if row.first():
            rec = row.first()

            preco = self.getPrecoAtacado(
                getProduto(
                    ID_PRODUTO=rec.ID_PRODUTO,
                    QTDE=filtro.QTDE
                )
            )

            familiaBalanca = self.qBase.isFamiliaBalanca(rec.ID_FAMILIA) if isinstance(rec.ID_FAMILIA, int) else False

            lista = [
                itemPedidoCaixa(
                    NUMERO_PEDIDO=0,
                    NUMERO_ITEM=0,
                    ID_PRODUTO=rec.ID_PRODUTO,
                    DESCRICAO_PRODUTO=rec.DESCRICAO_PRODUTO,
                    QTDE=filtro.QTDE,
                    PRECO=preco,
                    TOTAL=rec.PRECO_BALCAO,
                    ID_TRIBUTO=rec.ID_TRIBUTO,
                    QTDE_FRACIONADA=familiaBalanca
                )
            ]

        elif not row.first():
            filters = [
                p.CODIGO_PRODUTO == filtro.CODIGO,
                p.PRECO_BALCAO > 0.00,
                p.PRODUTO_ATIVO == 1
            ]

            row = ctx.session.query(
                p.ID_PRODUTO, p.DESCRICAO_PRODUTO, p.PRECO_BALCAO, p.ID_TRIBUTO, p.ID_FAMILIA
            ).filter(*filters)

            if row.first():
                rec = row.first()

                preco = self.getPrecoAtacado(
                    getProduto(
                        ID_PRODUTO=rec.ID_PRODUTO,
                        QTDE=filtro.QTDE
                    )
                )

                familiaBalanca = self.qBase.isFamiliaBalanca(rec.ID_FAMILIA) if isinstance(rec.ID_FAMILIA, int) else False

                lista = [
                    itemPedidoCaixa(
                        NUMERO_PEDIDO=0,
                        NUMERO_ITEM=0,
                        ID_PRODUTO=rec.ID_PRODUTO,
                        DESCRICAO_PRODUTO=rec.DESCRICAO_PRODUTO,
                        QTDE=filtro.QTDE,
                        PRECO=preco,
                        TOTAL=rec.PRECO_BALCAO,
                        ID_TRIBUTO=rec.ID_TRIBUTO,
                        QTDE_FRACIONADA=familiaBalanca
                    )
                ]

        if not any(lista):
            pesquisa = self.buscaProdutosSimilares(
                filtroDescricaoProduto(
                    DESCRICAO=filtro.CODIGO,
                    QTDE=filtro.QTDE
                )
            )

            if len(pesquisa) == 1:
                rec = pesquisa[0]

                preco = self.getPrecoAtacado(
                    getProduto(
                        ID_PRODUTO=rec.ID_PRODUTO,
                        QTDE=filtro.QTDE
                    )
                )

                familiaBalanca = self.qBase.isFamiliaBalanca(rec.ID_FAMILIA) if isinstance(rec.ID_FAMILIA, int) else False

                lista = [
                    itemPedidoCaixa(
                        NUMERO_PEDIDO=0,
                        NUMERO_ITEM=0,
                        ID_PRODUTO=rec.ID_PRODUTO,
                        DESCRICAO_PRODUTO=rec.DESCRICAO_PRODUTO,
                        QTDE=filtro.QTDE,
                        PRECO=preco,
                        TOTAL=rec.PRECO_BALCAO,
                        ID_TRIBUTO=rec.ID_TRIBUTO,
                        QTDE_FRACIONADA=familiaBalanca
                    )
                ]

        return lista

    def getSearchList(self, filtro: str) -> List[str]:
        try:
            lista = filtro.split(' ')

            lista = [item.strip() for item in lista]
            lista = [item for item in lista if len(item) > 0]

            return lista
        except:
            return [filtro]

    def buscaProdutosSimilares(
        self, filtro: filtroDescricaoProduto
    ) -> List[listaProduto]:
        lista = []

        p = ctx.mapProduto

        filters = []

        if len(filtro.DESCRICAO) > 0:
            lista = self.getSearchList(filtro.DESCRICAO)

            [filters.append(p.DESCRICAO_PRODUTO.like(f"%{item}%")) for item in lista]

        query = ctx.session.query(p).filter(*filters).limit(50).all()

        lista = [
            listaProduto(
                ID_PRODUTO=row.ID_PRODUTO,
                CODIGO_PRODUTO=row.CODIGO_PRODUTO if row.CODIGO_PRODUTO is not None else '',
                CODIGO_EAN=[row.CODIGO_PRODUTO_PDV] if row.CODIGO_PRODUTO_PDV is not None else [],
                DESCRICAO_PRODUTO=row.DESCRICAO_PRODUTO,
                PRECO_BALCAO=self.getPrecoAtacado(
                    getProduto(
                        ID_PRODUTO=row.ID_PRODUTO,
                        QTDE=filtro.QTDE
                    )
                ) if filtro.QTDE > 1 else float(row.PRECO_BALCAO),
                PRECO_ATACADO=float(row.PRECO_ATACADO) if row.PRECO_ATACADO is not None else 0.00,
                ID_TRIBUTO=row.ID_TRIBUTO,
                SALDO=0,
                CODIGO_ZE="" if row.CODIGO_ZE is None else row.CODIGO_ZE,
                PRODUTO_ATIVO=row.PRODUTO_ATIVO,
                QTDE_FRACIONADA=self.qBase.isFamiliaBalanca(row.ID_FAMILIA) if isinstance(row.ID_FAMILIA, int) else False,
                ID_FAMILIA=row.ID_FAMILIA,
                QTDE=1
            )
            for row in query
        ]

        return [item for item in lista 
                if item.PRODUTO_ATIVO == 1 and item.PRECO_BALCAO > 0.00
                ]

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

        filters = [
            p.PRECO_BALCAO > 0.00, 
            p.PRODUTO_ATIVO == 1
        ]

        select1 = ctx.session.query(p).order_by(p.DESCRICAO_PRODUTO).filter(*filters).all()

        lista = [
            comboProduto(
                ID_PRODUTO=row.ID_PRODUTO,
                DESCRICAO_PRODUTO = f'{row.DESCRICAO_PRODUTO.upper()}, [{row.CODIGO_PRODUTO}]'
            )
            for row in select1
        ]

        return lista

    async def getPrecoBebidaQuente(self, filtro: getProduto) -> float:
        p = ctx.mapProduto

        query = ctx.session.query(
            p.ID_PRODUTO,
            p.PRECO_DELIVERY
        ).filter(
            p.ID_PRODUTO == filtro.ID_PRODUTO
        ).first()

        if query:
            return float(query.PRECO_DELIVERY)

        return 0.0
    
    async def getProductImage(self, filtro: filtroProduto) -> str:
        p = ctx.mapProduto

        record = ctx.session.query(
            p.ID_PRODUTO,
            p.FOTO_PRODUTO
        ).filter(
            p.ID_PRODUTO == filtro.ID_PRODUTO
        ).first()

        fotoValue = record.FOTO_PRODUTO

        if fotoValue is None:
            return ''
        
        retorno = base64.b64encode(fotoValue).decode('utf-8')

        return retorno

    async def getAllProducts(self) -> List[listaProduto]:
        lista = []

        p = ctx.mapProduto

        filters = [
            p.PRECO_BALCAO > 0.00,
            p.PRODUTO_ATIVO == 1
        ]

        query = ctx.session.query(
            p.ID_PRODUTO,
            p.CODIGO_PRODUTO,
            p.CODIGO_PRODUTO_PDV,
            p.DESCRICAO_PRODUTO,
            p.PRECO_BALCAO,
            p.PRECO_ATACADO,
            p.ID_TRIBUTO,
            p.CODIGO_ZE,
            p.PRODUTO_ATIVO,
            p.ID_FAMILIA
        ).filter(*filters).all()

        lista = [
            listaProduto(
                ID_PRODUTO=row.ID_PRODUTO,
                CODIGO_PRODUTO=row.CODIGO_PRODUTO if row.CODIGO_PRODUTO is not None else '',
                CODIGO_EAN=[row.CODIGO_PRODUTO_PDV] if row.CODIGO_PRODUTO_PDV is not None else [],
                DESCRICAO_PRODUTO=row.DESCRICAO_PRODUTO,
                PRECO_BALCAO=float(row.PRECO_BALCAO),
                PRECO_ATACADO=float(row.PRECO_ATACADO) if row.PRECO_ATACADO is not None else 0.00,
                ID_TRIBUTO=row.ID_TRIBUTO,
                SALDO=0,
                CODIGO_ZE="" if row.CODIGO_ZE is None else row.CODIGO_ZE,
                PRODUTO_ATIVO=row.PRODUTO_ATIVO,
                QTDE_FRACIONADA=self.qBase.isFamiliaBalanca(row.ID_FAMILIA) if isinstance(row.ID_FAMILIA, int) else False,
                ID_FAMILIA=row.ID_FAMILIA,
                QTDE=1
            )
            for row in query
        ]

        for item in lista:
            item.CODIGO_EAN.extend(
                self.getEANs(
                    filtroProduto(ID_PRODUTO=item.ID_PRODUTO)
                )
            )

        return lista
    
    def getEANs(self, filtro: filtroProduto) -> List[str]:
        p = ctx.mapCodigoBarrasProduto

        query = ctx.session.query(p).filter(
            p.ID_PRODUTO == filtro.ID_PRODUTO
        ).all()

        lista = [
            row.CODIGO_BARRAS_PRODUTO.strip() if row.CODIGO_BARRAS_PRODUTO is not None else ''
            for row in query
            if row.CODIGO_BARRAS_PRODUTO is not None
        ]

        return lista

    async def getItensGrade(self) -> List[itemGrade]:
        lista = []

        g = ctx.mapGradePreco

        query = ctx.session.query(
            g.ID_PRODUTO,
            g.QTDE_INICIAL,
            g.QTDE_FINAL,
            g.PRECO_VENDA
        ).all()

        lista = [
            itemGrade(
                ID_PRODUTO=row.ID_PRODUTO,
                QTDE_INICIAL=int(row.QTDE_INICIAL),
                QTDE_FINAL=int(row.QTDE_FINAL),
                PRECO_GRADE=float(row.PRECO_VENDA)
            )
            for row in query
        ]

        return lista

    async def getImageProducts(self) -> List[produtoImage]:
        p = ctx.mapProduto

        query = ctx.session.query(
            p.ID_PRODUTO,
            p.FOTO_PRODUTO
        ).filter(
            p.FOTO_PRODUTO != None
        ).all()

        retorno = [
            produtoImage(
                ID_PRODUTO=record.ID_PRODUTO,
                IMAGE_DATA=base64.b64encode(record.FOTO_PRODUTO).decode('utf-8')
            )
            for record in query
        ]

        return retorno

    def __del__(self):
        ctx.session.close_all()
