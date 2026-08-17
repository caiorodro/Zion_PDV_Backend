import asyncio
from datetime import datetime, timedelta
from typing import List

from dateutil.relativedelta import relativedelta

from base.qBase import qBase
from cfg.config import Config
from infra.repositories.aberturaCaixaRepository import AberturaCaixaRepository
from infra.repositories.empresaRepository import EmpresaRepository
from infra.repositories.fechamentoCaixaRepository import FechamentoCaixaRepository
from infra.repositories.formaPagtoRepository import FormaPagtoRepository
from infra.repositories.pedidoPagamentoRepository import PedidoPagamentoRepository
from infra.repositories.pedidoRepository import PedidoRepository
from infra.repositories.reforcoRepository import ReforcoRepository
from infra.repositories.sangriaRepository import SangriaRepository
from infra.repositories.usuarioRepository import UsuarioRepository
from models.aberturaCaixa import aberturaCaixa
from models.consistenciasCaixa import consistenciasCaixa
from models.dadosAbertura import dadosAbertura
from models.dadosFechamento import dadosFechamento
from models.dadosUsuario import dadosUsuario
from models.fechamentoCaixa import fechamentoCaixa
from models.filtroCAIXA import filtroCAIXA
from models.filtroFormasPagtoCaixa import filtroFormasPagtoCaixa
from models.filtroImpressaoCaixa import filtroImpressaoCaixa
from models.formaPagtoCaixa import formaPagtoCaixa
from models.historicoCaixas import HistoricoCaixas
from models.itemCaixa import itemCaixa
from models.listaDeCaixa import listaDeCaixa
from models.listaDePagamentos import listaDePagamentos
from models.listaDeUsuario import listaDeUsuario
from models.nsu import nsu
from models.pedidosPorStatus import pedidosPorStatus
from models.periodoUsuario import periodoUsuario
from models.resumoFechamento import resumoFechamento
from models.resumoOrigemFormaPagto import resumoOrigemFormaPagto

from models.RESUMO_OPERACAO_CAIXA import (
    RESUMO_IMPRESSAO_CAIXA,
    TOTAIS_CAIXA_FORMA_PAGTO,
    TOTAIS_CAIXA_FORMA_PAGTO_ORIGEM,
    TOTAIS_CAIXA_ORIGEM,
    TOTAIS_REFORCO,
    TOTAIS_SANGRIA
)
from models.ResumoFormaPagto import ResumoFormaPagto
from models.ResumoFormaPagtoOrigem import ResumoFormaPagtoOrigem
from models.ResumoOrigem import ResumoOrigem
from models.senhaReset import senhaReset
from models.totaisPorFormaPagto import totaisPorFormaPagto
from models.ultimosCaixas import ultimosCaixas
from models.usuarioTipo import usuarioTipo

class Caixa:

    def __init__(self, keep=None, idUser=None):
        self.qBase = qBase(keep)
        self.__listOfUsers = []
        self.__idUser = idUser

        self._aberturas = AberturaCaixaRepository()
        self._fechamentos = FechamentoCaixaRepository()
        self._usuarios = UsuarioRepository()
        self._pedidos = PedidoRepository()
        self._pagamentos = PedidoPagamentoRepository()
        self._sangrias = SangriaRepository()
        self._reforcos = ReforcoRepository()
        self._empresas = EmpresaRepository()
        self._formasPagto = FormaPagtoRepository()

    async def listCaixa(self):
        hoje = datetime(
            datetime.now().year, datetime.now().month, datetime.now().day, 0, 0, 0
        )

        ontem = hoje + relativedelta(days=-1)

        query = self._aberturas.listar_abertos_com_usuario(ontem)

        retorno = [
            listaDeCaixa(
                ID_ABERTURA=item.ID_ABERTURA,
                DATA_ABERTURA=datetime.strftime(item.DATA_ABERTURA, "%d/%m/%Y %H:%M")
                if item.DATA_ABERTURA is not None
                else "",
                VALOR_ABERTURA=float(item.VALOR_ABERTURA),
                VALOR_FECHAMENTO=float(item.VALOR_FECHAMENTO)
                    if item.VALOR_FECHAMENTO is not None
                    else 0.00,
                USUARIO=item.NOME_USUARIO,
                DATA_FECHAMENTO=self.buscaFechamento(item.ID_ABERTURA),
                ADMINISTRADOR=item.TIPO_USUARIO == 1,
                USUARIO_CAIXA=item.USUARIO_CAIXA == 1
            ).__dict__
            for item in query
        ]

        return self.qBase.toRoute(retorno, 200)

    def getAdmin(self, ID_USUARIO: int) -> bool:
        return self._usuarios.buscar_por_id(ID_USUARIO).TIPO_USUARIO == 1

    def getUsuario(self, ID_USUARIO) -> str:
        return self._usuarios.nome_por_id(ID_USUARIO)

    def getUsuarioCaixa(self, ID_USUARIO) -> tuple:
        rec = self._usuarios.nome_e_usuario_caixa(ID_USUARIO)

        return (rec.NOME_USUARIO, rec.USUARIO_CAIXA)

    def buscaFechamento(self, idAbertura):
        rec = self._fechamentos.listar_por_abertura(idAbertura)

        return (
            datetime.strftime(rec[0].DATA_FECHAMENTO, "%d/%m/%Y %H:%M")
            if len(rec) > 0
            else ""
        )

    def gravaAberturaCaixa(self, dados: aberturaCaixa) -> usuarioTipo:
        senhaOk = asyncio.run(self.verificaSenhaAberturaCaixa(
            dadosUsuario(
                ID_USUARIO=dados.ID_USUARIO,
                SENHA_USUARIO=dados.SENHA_CAIXA
            )
        ))

        if not senhaOk:
            return usuarioTipo(
                ID_CAIXA=-1,
                ADMIN=False
            )

        limiteAbertura = datetime.now() - timedelta(hours=24)

        aberturaRecente = self._aberturas.buscar_aberta_recente(dados.ID_USUARIO, limiteAbertura)

        if aberturaRecente is not None:
            return usuarioTipo(
                ID_CAIXA=-2,
                ADMIN=False
            )

        idCaixa = self._aberturas.inserir(
            datetime.strptime(dados.DATA_ABERTURA, "%d/%m/%Y %H:%M"),
            dados.VALOR_ABERTURA,
            dados.ID_USUARIO
        )

        adminUsuario = self._usuarios.buscar_por_id(dados.ID_USUARIO).TIPO_USUARIO

        return usuarioTipo(
            ID_CAIXA=idCaixa,
            ADMIN=adminUsuario == 1
        )

    async def verificaSenhaAberturaCaixa(self, dados: dadosUsuario) -> bool:
        currentPassword = self._usuarios.buscar_por_id(dados.ID_USUARIO).SENHA_USUARIO

        return currentPassword == dados.SENHA_USUARIO

    async def listUsuario(self):
        query = self._usuarios.listar_ativos()

        retorno = [
            listaDeUsuario(
                ID_USUARIO=item.ID_USUARIO, NOME_USUARIO=item.NOME_USUARIO
            ).__dict__
            for item in query
        ]

        return self.qBase.toRoute(retorno, 200)

    async def listSenhaAdministrador(self):
        retorno = [
            {"SENHA_USUARIO": senha}
            for senha in self._usuarios.listar_senhas_admin()
        ]

        return self.qBase.toRoute(retorno, 200)

    async def getUsuarioFromCaixa(self, dados: itemCaixa) -> int:
        return self._aberturas.usuario_da_abertura(dados.ID_ABERTURA)

    async def getCaixa(self, filtro: filtroCAIXA) -> listaDeCaixa:
        rec = self._aberturas.buscar_por_id(filtro.ID_CAIXA)

        retorno = listaDeCaixa(
            ID_ABERTURA=rec.ID_ABERTURA,
            DATA_ABERTURA=datetime.strftime(rec.DATA_ABERTURA, "%d/%m/%Y %H:%M"),
            VALOR_ABERTURA=float(rec.VALOR_ABERTURA),
            VALOR_FECHAMENTO=float(rec.VALOR_FECHAMENTO)
            if rec.VALOR_FECHAMENTO is not None
            else 0,
            USUARIO=self.getUsuario(rec.ID_USUARIO),
            DATA_FECHAMENTO=self.buscaFechamento(rec.ID_ABERTURA),
            ADMINISTRADOR=self.getAdmin(rec.ID_USUARIO),
            USUARIO_CAIXA=self.getUsuarioCaixa(rec.ID_USUARIO)[1]
        )

        return retorno

    async def calcula_Formas_de_Pagto_no_Caixa(self, filtro: filtroFormasPagtoCaixa) -> List[formaPagtoCaixa]:
        x = set(self._pagamentos.formas_pagto_do_caixa(filtro.ID_CAIXA))

        retorno = sorted(
            [formaPagtoCaixa(DESCRICAO_FORMA=item) for item in x],
            key=lambda e: e.DESCRICAO_FORMA,
        )

        return retorno

    async def busca_Formas_de_Pagto_no_Caixa(self, filtro: filtroFormasPagtoCaixa):

        lista = await self.calcula_Formas_de_Pagto_no_Caixa(filtro)

        retorno = [
            formaPagtoCaixa(DESCRICAO_FORMA=item.DESCRICAO_FORMA).__dict__
            for item in lista
        ]

        return self.qBase.toRoute(retorno, 200)

    async def getPeriodo_e_Usuario(self, ID_CAIXA: int) -> periodoUsuario:
        Abertura = self._aberturas.buscar_por_id(ID_CAIXA)

        nomeUsuario = self._usuarios.nome_por_id(Abertura.ID_USUARIO)

        hoje = datetime.strftime(datetime.now(), '%d/%m/%Y %H:%M')

        fechamento = self._fechamentos.listar_por_abertura(ID_CAIXA)

        dataFechamento = datetime.strftime(fechamento[0].DATA_FECHAMENTO, '%d/%m/%Y %H:%M') if len(fechamento) > 0 else hoje

        retorno = periodoUsuario(
            USUARIO=nomeUsuario,
            PERIODO_INICIAL=datetime.strftime(Abertura.DATA_ABERTURA, '%d/%m/%Y %H:%M'),
            PERIODO_FINAL=dataFechamento
        )

        return retorno

    def calcula_Totais_Por_Forma_Pagto(self, filtro: filtroFormasPagtoCaixa) -> totaisPorFormaPagto:
        totaisRow = self._pagamentos.total_por_forma(filtro.ID_CAIXA, filtro.FORMA_PAGTO)
        totais = [totaisRow] if totaisRow is not None else []

        recTroco = self._pedidos.troco_e_desconto_do_caixa(filtro.ID_CAIXA, filtro.FORMA_PAGTO)

        totalGeral = self.get_Total_Geral_Caixa(filtro)

        semAcessoFechamento = self.get_Usuario_Caixa_sem_acesso_fechamento(filtro.ID_CAIXA)

        valorAbertura = self._aberturas.buscar_por_id(filtro.ID_CAIXA).VALOR_ABERTURA

        retorno = totaisPorFormaPagto(
            FORMA_PAGTO="DINHEIRO",
            TROCO=0.00,
            TOTAL_PAGTO=0.00,
            DESCONTO=0.00,
            SANGRIA=0,
            REFORCO=0,
            TOTAL_FINAL=0,
            VALOR_FECHAMENTO=0,
            DIFERENCA=0,
            TOTAL_GERAL=totalGeral,
            VALOR_ABERTURA=float(valorAbertura),
            SEM_ACESSO_FECHAMENTO=semAcessoFechamento
        )

        try:
            retorno = [
                totaisPorFormaPagto(
                    FORMA_PAGTO=item.FORMA_PAGTO,
                    TROCO=float(recTroco.TROCO) if recTroco.TROCO is not None else 0.00,
                    TOTAL_PAGTO=float(item.TOTAL_PAGO) - float(recTroco.TROCO),
                    DESCONTO=float(recTroco.DESCONTO)
                    if recTroco.DESCONTO is not None
                    else 0.00,
                    SANGRIA=0,
                    REFORCO=0,
                    TOTAL_FINAL=0,
                    VALOR_FECHAMENTO=0,
                    DIFERENCA=0,
                    TOTAL_GERAL=totalGeral,
                    VALOR_ABERTURA=float(valorAbertura),
                    SEM_ACESSO_FECHAMENTO=semAcessoFechamento
                )
                for item in totais
            ][0]
        except:
            pass

        if "DINHEIRO" in filtro.FORMA_PAGTO.upper():
            rec = self._sangrias.soma_por_abertura(filtro.ID_CAIXA)
            retorno.SANGRIA = float(rec) if rec is not None else 0.00

            rec = self._reforcos.soma_por_abertura(filtro.ID_CAIXA)
            retorno.REFORCO = float(rec) if rec is not None else 0.00

            fechamento = self._fechamentos.listar(filtro.ID_CAIXA, filtro.FORMA_PAGTO)

            retorno.DIFERENCA = float(fechamento[0].DIFERENCA) if len(fechamento) > 0 else 0
            retorno.VALOR_FECHAMENTO = float(fechamento[0].VALOR_FECHAMENTO) if len(fechamento) > 0 else 0

        retorno.TOTAL_FINAL = (
            (retorno.TOTAL_PAGTO + retorno.REFORCO) - retorno.SANGRIA
        )

        retorno.TOTAL_FINAL = round(retorno.TOTAL_FINAL, 2)

        return retorno

    def get_Totais_Por_Forma_Pagto(self, filtro: filtroFormasPagtoCaixa):

        retorno = self.calcula_Totais_Por_Forma_Pagto(filtro)

        return self.qBase.toRoute(retorno.__dict__, 200)

    async def verificaCaixaAberto(self, filtro: filtroFormasPagtoCaixa) -> bool:
        abertura = self._aberturas.buscar_por_id(filtro.ID_CAIXA)

        fechamento = self._fechamentos.listar(filtro.ID_CAIXA, filtro.FORMA_PAGTO)

        return abertura is not None and len(fechamento) == 0

    def listaPagamentosPorForma(self, filtro: filtroFormasPagtoCaixa):
        query = self._pagamentos.listar_pagamentos_do_caixa(filtro.ID_CAIXA, filtro.FORMA_PAGTO)

        def calculaValorPago(formaPagto: str, valorPago: any, troco: any) -> float:
            if valorPago is None:
                valorPago = 0.00

            if troco is None:
                troco = 0.00

            retorno = float(valorPago) if valorPago is not None else 0.00

            if "DINHEIRO" in formaPagto.upper():
                try:
                    retorno = round(
                        float(valorPago) - float(troco),
                        2
                    )
                except:
                    pass

            return retorno

        retorno = [
            listaDePagamentos(
                NUMERO_PEDIDO=item.NUMERO_PEDIDO,
                DATA_HORA=datetime.strftime(item.DATA_HORA, "%d/%m/%Y %H:%M"),
                STATUS_PEDIDO=Config.getStatus(item),
                CLIENTE=item.NOME_CLIENTE,
                TOTAL_PEDIDO=0.00
                if item.TOTAL_PEDIDO is None
                else float(item.TOTAL_PEDIDO),
                TOTAL_PAGO=calculaValorPago(item.FORMA_PAGTO, item.VALOR_PAGO, item.TROCO),
                CODIGO_NSU="" if item.CODIGO_NSU is None else item.CODIGO_NSU,
                ID_PAGAMENTO=item.ID_PAGAMENTO,
                VALOR_PAGO_STONE=0 if item.VALOR_PAGO_STONE is None else float(item.VALOR_PAGO_STONE)
            )
            for item in query
        ]

        return self.qBase.toRoute(retorno, 200)

    async def gravaNSU(self, dados: nsu):
        self._pagamentos.atualizar_nsu(dados.ID_PAGAMENTO, dados.NSU)

    def gravaFechamentoCaixa(self, dados: fechamentoCaixa) -> dadosFechamento:
        idFechamento = self._fechamentos.gravar_fechamento_e_atualizar_abertura(
            dados.ID_ABERTURA,
            dados.FORMA_PAGTO,
            dados.VALOR_FECHAMENTO,
            datetime.strptime(dados.DATA_FECHAMENTO, "%d/%m/%Y %H:%M"),
            dados.DIFERENCA
        )

        retorno = dadosFechamento(
            ID_FECHAMENTO=idFechamento,
            FORMA_PAGTO=dados.FORMA_PAGTO,
            DATA_FECHAMENTO=dados.DATA_FECHAMENTO,
            VALOR_FECHAMENTO=dados.VALOR_FECHAMENTO,
            DIFERENCA=dados.DIFERENCA
        )

        return retorno

    async def get_Totais_Fechamento(
        self, filtro: filtroFormasPagtoCaixa
    ) -> List[dadosFechamento]:
        query = self._fechamentos.listar(filtro.ID_CAIXA, filtro.FORMA_PAGTO)

        retorno = [
            dadosFechamento(
                ID_FECHAMENTO=record.ID_FECHAMENTO
                    if record.ID_FECHAMENTO is not None
                    else 0,
                FORMA_PAGTO=filtro.FORMA_PAGTO,
                DATA_FECHAMENTO=datetime.strftime(
                    record.DATA_FECHAMENTO, "%d/%m/%Y %H:%M"
                )
                    if record.DATA_FECHAMENTO is not None
                    else "",
                VALOR_FECHAMENTO=float(record.VALOR_FECHAMENTO)
                    if record.VALOR_FECHAMENTO is not None
                    else 0,
                DIFERENCA=float(record.DIFERENCA)
                    if record.DIFERENCA is not None
                    else 0
            )
            for record in query
        ]

        return retorno

    def get_Usuario_Caixa_sem_acesso_fechamento(self, ID_CAIXA: int) -> bool:
        ID_USUARIO = self._aberturas.buscar_por_id(ID_CAIXA).ID_USUARIO

        usuario = self._usuarios.buscar_por_id(ID_USUARIO)

        usuarioCaixa = usuario.USUARIO_CAIXA == 1 and usuario.ACESSO_FECHAMENTO == 0

        return usuarioCaixa

    def get_Total_Geral_Caixa(self, filtro: filtroFormasPagtoCaixa) -> float:
        usuarioCaixa = self.get_Usuario_Caixa_sem_acesso_fechamento(filtro.ID_CAIXA)

        totalDePagamentos = self._pagamentos.soma_pagamentos_do_caixa(filtro.ID_CAIXA)

        try:
            totalDePagamentos = float(totalDePagamentos)
        except:
            totalDePagamentos = 0.00

        Troco = self._pedidos.somar_troco_do_caixa_com_join_pagamento(filtro.ID_CAIXA)

        try:
            Troco = float(Troco)
        except:
            Troco = 0.00

        rec = self._sangrias.soma_por_abertura(filtro.ID_CAIXA)
        SANGRIA = float(rec) if rec is not None else 0.00

        rec = self._reforcos.soma_por_abertura(filtro.ID_CAIXA)
        REFORCO = float(rec) if rec is not None else 0.00

        TOTAL_FINAL = ((totalDePagamentos + REFORCO) - SANGRIA) - Troco

        return 0.00 if usuarioCaixa else round(TOTAL_FINAL, 2)

    async def setImpressaoCaixa(self, filtro: filtroFormasPagtoCaixa):
        filtro.NUMERO_IMPRESSORA = 1 if filtro.NUMERO_IMPRESSORA == 0 else filtro.NUMERO_IMPRESSORA

        self._aberturas.atualizar_impressao(filtro.ID_CAIXA, filtro.NUMERO_IMPRESSORA)

    async def get_Inconsistencias_Caixa(
        self, filtro: filtroFormasPagtoCaixa
    ) -> List[consistenciasCaixa]:
        horaInicial = self._empresas.hora_inicial()

        datahoraInicial = None

        try:
            datahoraInicial = datetime.today() + timedelta(
                hours=int(horaInicial[0:2]), minutes=int(horaInicial[3:5])
            )
        except:
            pass

        if not isinstance(datahoraInicial, datetime):
            raise Exception(
                "Horário inicial de funcionamento da loja não foi cadastrado"
            )

        dataHoraFinal = datetime.now() + timedelta(minutes=1)

        pedidosNoPeriodo = self._pedidos.listar_periodo(datahoraInicial, dataHoraFinal, 3)

        numeroDeCaixas = list(
            dict.fromkeys([item.ID_CAIXA for item in pedidosNoPeriodo])
        )

        retorno = []

        # Correção: o código anterior comparava a lista inteira com um inteiro
        # (`numeroDeCaixas > 1`), o que sempre levantava TypeError em tempo de
        # execução — este método nunca chegava a retornar com sucesso quando
        # alcançava este ponto. Nenhuma rota chama este método hoje, então o
        # bug nunca apareceu em produção; corrigido para `len(...)`.
        if len(numeroDeCaixas) > 1:
            periodo = f'{datetime.strftime(datahoraInicial, "%d/%m/%Y %H:%M")} até {datetime.strftime(dataHoraFinal, "%d/%m/%Y %H:%M")}'

            retorno.append(
                consistenciasCaixa(
                    DATA_HORA=datetime.strftime(datetime.now(), "%d/%m/%Y %H:%M"),
                    DESCRICAO=f"Existem {len(numeroDeCaixas)} caixa(s) aberto(s) no período de {periodo}",
                )
            )

        porStatus = self._pedidos.contar_por_status(filtro.ID_CAIXA, 3)

        grouped = [
            pedidosPorStatus(
                STATUS=Config.getStatus(item), COUNT=item.NUMERO_DE_PEDIDOS
            )
            for item in porStatus
        ]

        if len(grouped) > 1:
            retorno.append(
                consistenciasCaixa(
                    DATA_HORA=datetime.strftime(datetime.now(), "%d/%m/%Y %H:%M"),
                    DESCRICAO="\n".join(
                        [
                            f"{item.STATUS_PEDIDO}: {item.NUMERO_DE_PEDIDOS}"
                            for item in grouped
                        ]
                    ),
                )
            )

        return retorno

    async def listaUltimosCaixas(self) -> List[ultimosCaixas]:
        hoje = datetime(
            datetime.now().year, datetime.now().month, datetime.now().day, 0, 0, 0
        )

        ontem = hoje + relativedelta(days=-7)

        query = self._aberturas.listar_recentes_com_usuario(ontem)

        retorno = [
            ultimosCaixas(
                ID_ABERTURA=item.ID_ABERTURA,
                DATA_ABERTURA=datetime.strftime(item.DATA_ABERTURA, "%d/%m/%Y %H:%M")
                if item.DATA_ABERTURA is not None
                else "",
            )
            for item in query
        ]

        return retorno

    async def resumoTotaisImpressao(
        self, filtro: filtroImpressaoCaixa
    ) -> RESUMO_IMPRESSAO_CAIXA:
        impressao = self._aberturas.buscar_por_impressao(filtro.MAQUINA)

        if impressao is None:
            return []

        DATA1 = self.qBase.TrataDataHora(impressao.DATA_ABERTURA)
        DATA2 = (
            self.qBase.TrataDataHora(impressao.DATA_FECHAMENTO)
            if impressao.DATA_FECHAMENTO is not None
            else self.qBase.TrataDataHora(datetime.now() + timedelta(minutes=1))
        )

        ID_CAIXA = impressao.ID_ABERTURA

        f = filtroCAIXA(ID_CAIXA=ID_CAIXA)

        totaisPorFormaPagto = await self.calculaCaixaPorFormaPagto(f)
        totaisPorOrigem = await self.calculaCaixaPorOrigem(f)
        totaisPorOrigemFormaPagto = await self.calculaCaixaPorFormaPagtoOrigem(f)

        retorno = RESUMO_IMPRESSAO_CAIXA(
            DATA1=DATA1,
            DATA2=DATA2,
            RESUMO_FORMA_PAGTO=[
                TOTAIS_CAIXA_FORMA_PAGTO(
                    FORMA_PAGTO=item.FORMA_PAGTO,
                    ABERTURA=item.ABERTURA,
                    VALOR=item.VALOR_VENDA,
                    DESCONTO=item.DESCONTO,
                    TROCO=item.TROCO,
                    SANGRIA=item.SANGRIA,
                    REFORCO=item.REFORCO,
                    TOTAL=item.TOTAL,
                    VALOR_FECHAMENTO=item.VALOR_FECHAMENTO,
                    DIFERENCA=item.DIFERENCA,
                )
                for item in totaisPorFormaPagto
            ],
            RESUMO_ORIGEM=[
                TOTAIS_CAIXA_ORIGEM(
                    ORIGEM=item.ORIGEM,
                    VALOR=item.VALOR_VENDA,
                    DESCONTO=item.DESCONTO,
                    TOTAL=item.TOTAL,
                )
                for item in totaisPorOrigem
            ],
            RESUMO_FORMA_PAGTO_ORIGEM=[
                TOTAIS_CAIXA_FORMA_PAGTO_ORIGEM(
                    ORIGEM=item.ORIGEM,
                    FORMA_PAGTO=item.FORMA_PAGTO,
                    VALOR=item.VALOR_VENDA,
                    DESCONTO=item.DESCONTO,
                    TOTAL=item.TOTAL,
                )
                for item in totaisPorOrigemFormaPagto
            ],
            RESUMO_REFORCO=await self.operacoesReforco(f),
            RESUMO_SANGRIA=await self.operacoesSangria(f),
            USUARIO=self._usuarios.nome_por_id(impressao.ID_USUARIO),
        )

        self._aberturas.atualizar_impressao(ID_CAIXA, 0)

        return retorno

    async def calculaCaixaPorFormaPagto(
        self, filtro: filtroCAIXA
    ) -> List[ResumoFormaPagto]:
        retorno = []

        dinheiro = "dinheiro"

        totais = self._pagamentos.totais_agrupados_por_forma(filtro.ID_CAIXA)

        dadosDinheiro = await self.getDadosAbertura(filtro)

        trocoTotal = self._pedidos.somar_troco_do_caixa(filtro.ID_CAIXA)
        troco = float(trocoTotal) if trocoTotal is not None else 0.00

        for item in totais:
            total = float(item.TOTAL_PAGO) if item.TOTAL_PAGO is not None else 0

            if item.FORMA_PAGTO == dinheiro:
                total -= troco
                total = (
                    dadosDinheiro.ABERTURA + item.TOTAL_PAGO + dadosDinheiro.REFORCO
                ) - dadosDinheiro.SANGRIA

            fechamento = self._fechamentos.listar(filtro.ID_CAIXA, item.FORMA_PAGTO)

            dHoraFechamento = ""
            valorFechamento = 0

            for item1 in fechamento:
                dHoraFechamento = (
                    self.qBase.TrataDataHora(item1.DATA_FECHAMENTO)
                    if item1.DATA_FECHAMENTO is not None
                    else ""
                )

                valorFechamento = (
                    float(item1.VALOR_FECHAMENTO)
                    if item1.VALOR_FECHAMENTO is not None
                    else 0.00
                )

            diferenca = valorFechamento - total if valorFechamento > 0.00 else 0.00

            retorno.append(
                ResumoFormaPagto(
                    FORMA_PAGTO=item.FORMA_PAGTO,
                    ABERTURA=dadosDinheiro.ABERTURA
                    if item.FORMA_PAGTO == dinheiro
                    else 0,
                    VALOR_VENDA=float(item.TOTAL_PAGO)
                    if item.TOTAL_PAGO is not None
                    else 0,
                    DESCONTO=0,
                    SANGRIA=dadosDinheiro.SANGRIA
                    if item.FORMA_PAGTO == dinheiro
                    else 0,
                    REFORCO=dadosDinheiro.REFORCO
                    if item.FORMA_PAGTO == dinheiro
                    else 0,
                    TOTAL=total,
                    DIFERENCA=diferenca,
                    DATA_HORA_FECHAMENTO=dHoraFechamento,
                    VALOR_FECHAMENTO=valorFechamento,
                    TROCO=troco,
                )
            )

        return retorno

    async def calculaCaixaPorOrigem(self, filtro: filtroCAIXA) -> List[ResumoOrigem]:
        totais = self._pagamentos.totais_agrupados_por_origem(filtro.ID_CAIXA)

        retorno = [
            ResumoOrigem(
                ORIGEM=item.ORIGEM,
                ABERTURA=0,
                VALOR_VENDA=float(item.TOTAL_PAGO)
                if item.TOTAL_PAGO is not None
                else 0,
                DESCONTO=0,
                SANGRIA=0,
                REFORCO=0,
                TOTAL=float(item.TOTAL_PAGO) if item.TOTAL_PAGO is not None else 0,
                DIFERENCA=0,
                DATA_HORA_FECHAMENTO="",
                VALOR_FECHAMENTO=0,
                TROCO=0,
            )
            for item in totais
        ]

        return retorno

    def getTrocoOrigem(self, filtro: filtroCAIXA, ORIGEM: str) -> float:
        rec = self._pedidos.somar_troco_por_origem(filtro.ID_CAIXA, ORIGEM)

        return float(rec) if rec is not None else 0.00

    async def calculaCaixaPorFormaPagtoOrigem(
        self, filtro: filtroCAIXA
    ) -> List[ResumoFormaPagtoOrigem]:
        totais = self._pagamentos.totais_agrupados_por_forma_e_origem(filtro.ID_CAIXA)

        retorno = [
            ResumoFormaPagtoOrigem(
                FORMA_PAGTO=item.FORMA_PAGTO,
                ORIGEM=item.ORIGEM,
                ABERTURA=0,
                VALOR_VENDA=float(item.TOTAL_PAGO)
                if item.TOTAL_PAGO is not None
                else 0,
                DESCONTO=0,
                SANGRIA=0,
                REFORCO=0,
                TOTAL=float(item.TOTAL_PAGO) if item.TOTAL_PAGO is not None else 0,
                DIFERENCA=0,
                DATA_HORA_FECHAMENTO="",
                VALOR_FECHAMENTO=0,
                TROCO=self.getTrocoOrigem(filtro, item.ORIGEM)
            )
            for item in totais
        ]

        for item in retorno:
            item.VALOR_VENDA -= item.TROCO

        return retorno

    async def getDadosAbertura(self, filtro: filtroCAIXA) -> dadosAbertura:
        recA = self._aberturas.buscar_por_id(filtro.ID_CAIXA).VALOR_ABERTURA
        recS = self._sangrias.soma_por_abertura(filtro.ID_CAIXA)
        recR = self._reforcos.soma_por_abertura(filtro.ID_CAIXA)

        retorno = dadosAbertura(
            ABERTURA=float(recA) if recA is not None else 0,
            SANGRIA=float(recS) if recS is not None else 0,
            REFORCO=float(recR) if recR is not None else 0,
        )

        return retorno

    async def operacoesSangria(self, filtro: filtroCAIXA) -> List[TOTAIS_SANGRIA]:
        q2 = self._sangrias.listar_por_abertura(filtro.ID_CAIXA)

        TOTAIS = [
            TOTAIS_SANGRIA(
                DATA_HORA=self.qBase.TrataDataHora(item.DATA_SANGRIA),
                DESCRICAO=item.DESCRICAO_SANGRIA,
                USUARIO=self._usuarios.nome_por_id(item.ID_USUARIO),
                VALOR=float(item.VALOR_SANGRIA)
                if item.VALOR_SANGRIA is not None
                else 0,
            )
            for item in q2
        ]

        return TOTAIS

    async def operacoesReforco(self, filtro: filtroCAIXA) -> TOTAIS_REFORCO:
        q2 = self._reforcos.listar_por_abertura(filtro.ID_CAIXA)

        TOTAIS = [
            TOTAIS_REFORCO(
                DATA_HORA=self.qBase.TrataDataHora(item.DATA_REFORCO),
                DESCRICAO="",
                USUARIO=self._usuarios.nome_por_id(item.ID_USUARIO),
                VALOR=float(item.VALOR_REFORCO)
                if item.VALOR_REFORCO is not None
                else 0,
            )
            for item in q2
        ]

        return TOTAIS

    async def getTaxaPagamento(self, filtro: filtroFormasPagtoCaixa) -> float:
        formaPagto = self._formasPagto.buscar_por_descricao(filtro.FORMA_PAGTO)

        if formaPagto is None:
            return 0.00

        taxaPagamento = formaPagto.TAXA_PAGAMENTO

        if taxaPagamento is None:
            taxaPagamento = 0.00

        return float(taxaPagamento)

    async def checaSenhaReset(self, dados: senhaReset) -> bool:
        return self._usuarios.existe_admin_com_senha(dados.SENHA)

    async def getResumoFechamento(self, filtro: filtroCAIXA) -> List[resumoFechamento]:

        formasPagto = await self.calcula_Formas_de_Pagto_no_Caixa(
            filtroFormasPagtoCaixa(
                ID_CAIXA=filtro.ID_CAIXA,
                FORMA_PAGTO='',
                NUMERO_IMPRESSORA=0
            )
        )

        retorno = []

        periodo = await self.getPeriodo_e_Usuario(filtro.ID_CAIXA)

        for item in formasPagto:
            totais = self.calcula_Totais_Por_Forma_Pagto(
                filtroFormasPagtoCaixa(
                    ID_CAIXA=filtro.ID_CAIXA,
                    FORMA_PAGTO=item.DESCRICAO_FORMA,
                    NUMERO_IMPRESSORA=0
                )
            )

            dado = resumoFechamento(
                USUARIO = periodo.USUARIO,
                PERIODO_INICIAL = periodo.PERIODO_INICIAL,
                PERIODO_FINAL = periodo.PERIODO_FINAL,
                FORMA_PAGTO=item.DESCRICAO_FORMA,
                ABERTURA=totais.VALOR_ABERTURA,
                TOTAL=totais.TOTAL_PAGTO,
                DESCONTO=totais.DESCONTO,
                SANGRIA=totais.SANGRIA,
                REFORCO=totais.REFORCO,
                TOTAL_GERAL=totais.TOTAL_GERAL,
                DIFERENCA=totais.DIFERENCA,
                DATA_FECHAMENTO='',
                VALOR_FECHAMENTO=totais.VALOR_FECHAMENTO
            )

            retorno.append(dado)

        return retorno

    async def getResumoFechamentoPorOrigem(self, filtro: filtroCAIXA) -> List[resumoOrigemFormaPagto]:

        totais = await self.calculaCaixaPorFormaPagtoOrigem(
            filtroCAIXA(
                ID_CAIXA=filtro.ID_CAIXA
            )
        )

        retorno = [
            resumoOrigemFormaPagto(
                FORMA_PAGTO=item.FORMA_PAGTO,
                ORIGEM=item.ORIGEM,
                TOTAL=item.VALOR_VENDA
            )
            for item in totais
        ]

        return retorno

    async def listaCaixasAnteriores(self) -> List[HistoricoCaixas]:
        dt = datetime.today() + relativedelta(days=-30)

        q = self._aberturas.listar_historico_com_usuario(dt)

        dados = [
            HistoricoCaixas(
                ID_CAIXA=item.ID_ABERTURA,
                DATA_HORA=self.qBase.TrataDataHora_Caixa(item.DATA_ABERTURA),
                DT = item.DATA_ABERTURA,
                NOME_USUARIO=item.NOME_USUARIO
            )
            for item in q
        ]

        retorno = sorted(dados, key=lambda x: x.DT, reverse=True)

        return retorno

    async def getCaixaAberto(self, filtro: filtroCAIXA) -> aberturaCaixa:
        # Este método já estava morto/quebrado antes da migração: filtrava por
        # `a.ID_CAIXA` e `a.STATUS_ABERTURA`, colunas que nunca existiram em
        # tb_abertura_caixa (nem na definição SQLAlchemy) — teria levantado
        # AttributeError sempre que chamado. Nenhuma rota chama este método
        # hoje. Mantive a interpretação mais provável (buscar a abertura por
        # ID) sem inventar uma regra de "status" que não existe no schema.
        return self._aberturas.buscar_por_id(filtro.ID_CAIXA)
