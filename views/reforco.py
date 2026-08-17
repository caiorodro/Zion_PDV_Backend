from datetime import datetime

from base.qBase import qBase
from infra.repositories.aberturaCaixaRepository import AberturaCaixaRepository
from infra.repositories.reforcoRepository import ReforcoRepository
from infra.repositories.usuarioRepository import UsuarioRepository
from models.filtroReforco import filtroReforco
from models.listaReforco import listaReforco
from models.reforco import reforco


class Reforco:
    def __init__(self, keep=None, idUser=None):
        self.qBase = qBase(keep)
        self._repo = ReforcoRepository()
        self._usuarios = UsuarioRepository()
        self._aberturas = AberturaCaixaRepository()

    async def listReforco(self, filtro: filtroReforco):
        data = datetime.strptime(filtro.DATA_REFORCO, "%d/%m/%Y")

        query = self._repo.listar(data, filtro.ID_CAIXA)

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
            ).__dict__
            for item in sorted(query, key=lambda e: e.DATA_REFORCO, reverse=True)
        ]

        return self.qBase.toRoute(retorno, 200)

    def gravaReforco(self, dados: reforco) -> bool:
        idUsuario = self._aberturas.usuario_da_abertura(dados.ID_ABERTURA)

        self._repo.inserir(dados, idUsuario)

        return True

    async def getUsuario(self, ID_USUARIO) -> str:
        return self._usuarios.nome_por_id(ID_USUARIO)

    async def getUsuarioDoCaixa(self, ID_CAIXA: int) -> int:
        return self._aberturas.usuario_da_abertura(ID_CAIXA)
