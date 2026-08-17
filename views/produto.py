import base64
from decimal import Decimal
import json
import os
from typing import List

from base.qBase import qBase
from infra.repositories.codigoBarrasProdutoRepository import CodigoBarrasProdutoRepository
from infra.repositories.estoqueRepository import EstoqueRepository
from infra.repositories.gradePrecoRepository import GradePrecoRepository
from infra.repositories.produtoRepository import ProdutoRepository
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

        self._produtos = ProdutoRepository()
        self._grades = GradePrecoRepository()
        self._estoque = EstoqueRepository()
        self._codigosBarras = CodigoBarrasProdutoRepository()

    async def list(self, NOME) -> List[listaDeProduto]:
        select1 = self._produtos.listar_ativos(NOME)

        lista = [
            listaDeProduto(
                ID_PRODUTO=row.ID_PRODUTO,
                DESCRICAO_PRODUTO=row.DESCRICAO_PRODUTO,
                PRECO_BALCAO=float(row.PRECO_BALCAO)
                if isinstance(row.PRECO_BALCAO, Decimal)
                else 0,
                ID_TRIBUTO=row.ID_TRIBUTO,
            ).__dict__
            for row in select1
        ]

        return lista

    async def get_Produto(self, filtro: getProduto):
        select1 = self._produtos.buscar_resumo_por_id(filtro.ID_PRODUTO)

        rows = [select1] if select1 is not None else []

        lista = [
            listaDeProduto(
                ID_PRODUTO=row.ID_PRODUTO,
                DESCRICAO_PRODUTO=row.DESCRICAO_PRODUTO,
                PRECO_BALCAO=self.getPrecoAtacado(
                    getProduto(ID_PRODUTO=row.ID_PRODUTO, QTDE=filtro.QTDE)
                ),
                ID_TRIBUTO=row.ID_TRIBUTO,
            ).__dict__
            for row in rows
        ]

        return self.qBase.toRoute(lista, 200)

    def getPrecoAtacado(self, filtro: getProduto) -> float:
        preco = self._produtos.preco_balcao_por_id(filtro.ID_PRODUTO)

        if preco is None:
            return self.qBase.toRoute("Produto não econtrado", 500)

        precoBalcao = float(preco.PRECO_BALCAO)

        query = self._grades.buscar_faixa(filtro.ID_PRODUTO, filtro.QTDE)

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

        items = self._produtos.buscar_por_codigo_produto(codigoBalanca)

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

        lista = []

        filtro.CODIGO = filtro.CODIGO.strip()

        rec = self._produtos.buscar_ativo_por_codigo_pdv(filtro.CODIGO)

        if rec is None:
            rec = self._produtos.buscar_ativo_por_codigo(filtro.CODIGO)

        if rec is not None:
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
        termos = []

        if len(filtro.DESCRICAO) > 0:
            termos = self.getSearchList(filtro.DESCRICAO)

        query = self._produtos.buscar_similares(termos, limite=50)

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
        entradas = self._estoque.soma_qtde(filtro.ID_PRODUTO, 0)
        saidas = self._estoque.soma_qtde(filtro.ID_PRODUTO, 1)

        e = 0 if entradas is None else entradas
        s = 0 if saidas is None else saidas

        saldo = float(e) - float(s)

        return saldo

    async def get_Lista_de_Produtos(self) -> List[comboProduto]:
        select1 = self._produtos.listar_ativos_completo()

        lista = [
            comboProduto(
                ID_PRODUTO=row.ID_PRODUTO,
                DESCRICAO_PRODUTO = f'{row.DESCRICAO_PRODUTO.upper()}, [{row.CODIGO_PRODUTO}]'
            )
            for row in select1
        ]

        return lista

    async def getPrecoBebidaQuente(self, filtro: getProduto) -> float:
        query = self._produtos.preco_delivery_por_id(filtro.ID_PRODUTO)

        if query:
            return float(query.PRECO_DELIVERY)

        return 0.0

    async def getProductImage(self, filtro: filtroProduto) -> str:
        record = self._produtos.foto_por_id(filtro.ID_PRODUTO)

        fotoValue = record.FOTO_PRODUTO

        if fotoValue is None:
            return ''

        retorno = base64.b64encode(fotoValue).decode('utf-8')

        return retorno

    async def getAllProducts(self) -> List[listaProduto]:
        query = self._produtos.listar_para_venda()

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
        query = self._codigosBarras.listar_por_produto(filtro.ID_PRODUTO)

        lista = [
            row.CODIGO_BARRAS_PRODUTO.strip() if row.CODIGO_BARRAS_PRODUTO is not None else ''
            for row in query
            if row.CODIGO_BARRAS_PRODUTO is not None
        ]

        return lista

    async def getItensGrade(self) -> List[itemGrade]:
        query = self._grades.listar_todas()

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
        query = self._produtos.listar_com_foto()

        retorno = [
            produtoImage(
                ID_PRODUTO=record.ID_PRODUTO,
                IMAGE_DATA=base64.b64encode(record.FOTO_PRODUTO).decode('utf-8')
            )
            for record in query
        ]

        return retorno
