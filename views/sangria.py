import asyncio
from datetime import datetime
from typing import List

from base.qBase import qBase

from infra.repositories.aberturaCaixaRepository import AberturaCaixaRepository
from infra.repositories.sangriaRepository import SangriaRepository
from infra.repositories.usuarioRepository import UsuarioRepository

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
        self._repo = SangriaRepository()
        self._usuarios = UsuarioRepository()
        self._aberturas = AberturaCaixaRepository()

    async def listSangria(self, filtro: filtroSangria):
        data = datetime.strptime(filtro.DATA_SANGRIA, "%d/%m/%Y")

        query = self._repo.listar(data, filtro.ID_CAIXA)

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

        idUsuario = self._aberturas.usuario_da_abertura(dados.ID_ABERTURA)

        self._repo.inserir(dados, idUsuario)

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
        return self._usuarios.nome_por_id(ID_USUARIO)

    async def getUsuarioDoCaixa(self, ID_CAIXA: int) -> int:
        return self._aberturas.usuario_da_abertura(ID_CAIXA)

    async def printSangria(self, filtro: filtroCAIXA) -> List[impressaoSangria]:
        querySangria = self._repo.listar_para_impressao(filtro.ID_CAIXA)

        retorno = [
            impressaoSangria(
                DATA_SANGRIA=self.qBase.TrataDataHora(item["DATA_SANGRIA"]),
                DESCRICAO_CAIXA=item["DESCRICAO_SANGRIA"],
                VALOR_SANGRIA=round(float(item["VALOR_SANGRIA"]), 2),
                USUARIO_CAIXA=item["NOME_USUARIO"],
                CAIXA_DE=self.qBase.TrataDataHora(item["DATA_ABERTURA"])
            )
            for item in querySangria
        ]

        return retorno
