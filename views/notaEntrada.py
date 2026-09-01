from datetime import datetime
from typing import List, Optional

from infra.repositories.notaEntradaRepository import NotaEntradaRepository
from models.filtroNotaEntrada import filtroNotaEntrada
from models.filtroNotaFornecedor import filtroNotaFornecedor
from models.itemNotaEntrada import itemNotaEntrada
from models.notaEntradaResumo import notaEntradaResumo


class NotaEntrada:
    def __init__(self):
        self._notas = NotaEntradaRepository()

    async def listaNotasFornecedor(self, filtro: filtroNotaEntrada) -> List[notaEntradaResumo]:
        dataMinima = datetime.strptime(filtro.DATA_MINIMA, "%d/%m/%Y")

        query = self._notas.listar_distinct(dataMinima, filtro.NOME_FORNECEDOR or "")

        return [
            notaEntradaResumo(
                ID_NF=item.ID_NF,
                NUMERO_NF=item.NUMERO_NF,
                CNPJ_FORNECEDOR=item.CNPJ_FORNECEDOR or "",
                NOME_EMITENTE=item.NOME_EMITENTE or "",
                DATA_EMISSAO=datetime.strftime(item.DATA_EMISSAO, "%d/%m/%Y %H:%M")
                if item.DATA_EMISSAO is not None
                else "",
            )
            for item in query
        ]

    async def buscaXml(self, id_nf: int) -> Optional[str]:
        return self._notas.buscar_xml(id_nf)

    async def buscaItens(self, filtro: filtroNotaFornecedor) -> List[itemNotaEntrada]:
        # ID_PRODUTO de cada item -- é o que liga o item da nota do
        # fornecedor ao cadastro próprio da loja (tributação/CSOSN já
        # usada pra esse produto), pra montar a devolução sem tentar
        # traduzir a tributação do fornecedor (regime fiscal diferente).
        query = self._notas.buscar_itens(filtro.NUMERO_NF, filtro.CNPJ_FORNECEDOR)

        return [
            itemNotaEntrada(
                ID_NF=item.ID_NF,
                ID_PRODUTO=item.ID_PRODUTO or 0,
                DESCRICAO_PRODUTO=item.DESCRICAO_PRODUTO or "",
                PRECO_UNITARIO=float(item.PRECO_UNITARIO) if item.PRECO_UNITARIO is not None else 0.0,
                QTDE_ITEM=float(item.QTDE_ITEM) if item.QTDE_ITEM is not None else 0.0,
            )
            for item in query
        ]
