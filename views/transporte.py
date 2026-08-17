from typing import List

from base.qBase import qBase
from infra.repositories.transporteRepository import TransporteRepository
from models.comboTransporte import comboTransporte
from models.dadosTransporte import dadosTransporte
from models.filtroTransporte import filtroTransporte
from models.listaDeTransporte import listaDeTransporte


class Transporte:
    def __init__(self, keep=None, idUser=None):
        self.qBase = qBase(keep)
        self._repo = TransporteRepository()

    async def buscaTransporte(self, filtro: filtroTransporte) -> List[comboTransporte]:
        query = self._repo.buscar_por_nome(filtro.FILTRO)

        retorno = [
            comboTransporte(
                ID_TRANSPORTE=item.ID_TRANSPORTE, NOME_TRANSPORTE=item.NOME_TRANSPORTE
            ).__dict__
            for item in query
        ]

        return retorno

    async def gravaDadosTransporte(self, dados: dadosTransporte):
        if dados.ID_TRANSPORTE == 0:
            self._repo.inserir(dados)
        elif dados.ID_TRANSPORTE > 0:
            self._repo.atualizar(dados)

    async def listaTransporte(
        self, filtro: filtroTransporte
    ) -> List[listaDeTransporte]:
        query = self._repo.listar(filtro.FILTRO)

        retorno = [
            listaDeTransporte(
                ID_TRANSPORTE=item.ID_TRANSPORTE, NOME_TRANSPORTE=item.NOME_TRANSPORTE
            )
            for item in query
        ]

        return retorno

    async def editTransporte(self, filtro: filtroTransporte) -> dadosTransporte:
        rec = self._repo.buscar_por_id(int(filtro.FILTRO))

        if rec is None:
            raise Exception("Transporte não encontrado na base")

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
