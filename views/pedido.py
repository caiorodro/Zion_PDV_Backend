import asyncio
from datetime import datetime, timedelta
from typing import List

from dateutil.relativedelta import relativedelta

from base.qBase import qBase
from cfg.config import Config
from infra import db
from infra.repositories.associacaoProdutoRepository import AssociacaoProdutoRepository
from infra.repositories.atendimentoComandaRepository import AtendimentoComandaRepository
from infra.repositories.cfopRepository import CFOPRepository
from infra.repositories.clienteRepository import ClienteRepository
from infra.repositories.comboProdutoRepository import ComboProdutoRepository
from infra.repositories.doseProdutoRepository import DoseProdutoRepository
from infra.repositories.empresaRepository import EmpresaRepository
from infra.repositories.enderecoClienteRepository import EnderecoClienteRepository
from infra.repositories.estoqueRepository import EstoqueRepository
from infra.repositories.filaComandaRepository import FilaComandaRepository
from infra.repositories.financeiroRepository import FinanceiroRepository
from infra.repositories.formaPagtoRepository import FormaPagtoRepository
from infra.repositories.itemPedidoRepository import ItemPedidoRepository
from infra.repositories.municipioRepository import MunicipioRepository
from infra.repositories.numeroNotaRepository import NumeroNotaRepository
from infra.repositories.pedidoNFeRepository import PedidoNFeRepository
from infra.repositories.pedidoPagamentoRepository import PedidoPagamentoRepository
from infra.repositories.pedidoRepository import PedidoRepository
from infra.repositories.planoContaRepository import PlanoContaRepository
from infra.repositories.produtoRepository import ProdutoRepository
from infra.repositories.transporteRepository import TransporteRepository
from infra.repositories.tributoRepository import TributoRepository
from models.clienteEndereco import clienteEndereco
from models.clientePedido import clientePedido
from models.conclusaoPagamento import conclusaoPagamento
from models.comboProduto import comboProduto
from models.dadosEmitente import dadosEmitente
from models.dadosNFCe import dadosNFCe
from models.dadosPedido import dadosPedido
from models.editPedido import editItemPedido, editPedido, editPedidoPagamento
from models.emissaoNFCe import emissaoNFCe
from models.estoque import estoque
from models.filaComanda import filaComanda
from models.filtroCancelamento import filtroCancelamento
from models.filtroIDPagamento import filtroIDPagamento
from models.filtroImpressaoPedido import filtroImpressaoPedido
from models.filtroListaPedido import filtroListaPedido
from models.filtroNFCe import filtroNFCe
from models.filtroNumeroPedido import filtroNumeroPedido
from models.filtroPedido import filtroPedido
from models.filtroProduto import filtroProduto
from models.FORMAS_PAGTO_IMPRESSAO import FORMAS_PAGTO_IMPRESSAO
from models.impressaoAvulsa import impressaoAvulsa
from models.impressaoPedidoBalcao import impressaoPedidoBalcao
from models.itemPedido import itemPedido
from models.itemPedidoFinanceiro import itemPedidoFinanceiro
from models.itemPedidoCaixa import itemPedidoCaixa
from models.itemsNFe import itemsNFe
from models.itemTributo import itemTributo
from models.listaDePedido import listaDePedido
from models.listaDeTributo import listaDeTributo
from models.tributoCompleto import tributoCompleto
from models.filtroFaturamentoAutomatico import filtroFaturamentoAutomatico
from models.pedidoParaFaturar import pedidoParaFaturar
from models.filtroMunicipio import filtroMunicipio
from models.listaDePagamentos import listaDePagamentos
from models.listaFormaPagto import listaFormaPagto
from models.NFCe_Processada import NFCe_Processada
from models.NFe_Finalizada import NFe_Finalizada
from models.notaAutorizada import notaAutorizada
from models.numeroItemPedido import numeroItemPedido
from models.numeroPedido import NUM_PEDIDO
from models.Order import Order
from models.pedido import pedido as ped
from models.pagamentoAutorizado import pagamentoAutorizado
from models.pagamentoPedido import pagamentoPedido
from models.pedido import pedido
from models.pedidoFinanceiro import pedidoFinanceiro
from models.pedidoPagamento import pedidoPagamento
from models.pedidoPagamentoFinanceiro import pedidoPagamentoFinanceiro
from models.produtoQtde import produtoQtde
from models.produtoIDQtde import produtoIDQtde
from models.TOTAL_PEDIDO import TOTAL_PEDIDO


class _ErroNegocioPedido(Exception):
    """Sinaliza uma falha de validação de negócio (não de sistema) dentro da
    transação de gravaPedido — usada só para desfazer a transação (rollback)
    e devolver a mensagem como string, mantendo o mesmo contrato de retorno
    que o código anterior já tinha (int em caso de sucesso, str em caso de
    erro de validação)."""


class pedido:
    def __init__(self, keep=None, idUser=None):
        self.qBase = qBase(keep)

        self.idPlanoPagtoFuturo = "1.0.2"
        self.prefs = self.qBase.getPrefs()

        self._clientes = ClienteRepository()
        self._enderecos = EnderecoClienteRepository()
        self._transportes = TransporteRepository()
        self._produtos = ProdutoRepository()
        self._pedidos = PedidoRepository()
        self._itensPedido = ItemPedidoRepository()
        self._pagamentos = PedidoPagamentoRepository()
        self._estoque = EstoqueRepository()
        self._combos = ComboProdutoRepository()
        self._associacoes = AssociacaoProdutoRepository()
        self._doses = DoseProdutoRepository()
        self._atendimentoComanda = AtendimentoComandaRepository()
        self._formasPagto = FormaPagtoRepository()
        self._planoContas = PlanoContaRepository()
        self._financeiro = FinanceiroRepository()
        self._filaComanda = FilaComandaRepository()
        self._pedidoNFe = PedidoNFeRepository()
        self._empresas = EmpresaRepository()
        self._municipios = MunicipioRepository()
        self._tributos = TributoRepository()
        self._cfops = CFOPRepository()
        self._numerosNota = NumeroNotaRepository()

    async def preencheConsumidorFinal(self, consumidorFinal: clienteEndereco, _pedido: ped) -> ped:
        cliente = self._clientes.buscar_por_id(consumidorFinal.ID_CLIENTE)
        endereco = self._enderecos.buscar_por_id(consumidorFinal.ID_ENDERECO)

        _pedido.NOME_CLIENTE = cliente.NOME_CLIENTE
        _pedido.ENDERECO_CLIENTE = ' '.join((
            endereco.ENDERECO,
            endereco.NUMERO_ENDERECO,
            endereco.COMPLEMENTO_ENDERECO
            ))

        _pedido.BAIRRO_CLIENTE = endereco.BAIRRO
        _pedido.TELEFONE_CLIENTE = cliente.TELEFONE_CLIENTE

        return _pedido

    def test_gravaPedido(self, order: Order):

        consumidorFinal = self.checaConsumidorFinal()

        if not isinstance(consumidorFinal, clienteEndereco):
            raise Exception('Cliente consumidor final não cadastrado')

        order.pedido.ID_CLIENTE = consumidorFinal.ID_CLIENTE if order.pedido.ID_CLIENTE == 0 else order.pedido.ID_CLIENTE
        order.pedido.ID_ENDERECO = consumidorFinal.ID_ENDERECO if order.pedido.ID_ENDERECO == 0 else order.pedido.ID_ENDERECO

        order.pedido = asyncio.run(self.preencheConsumidorFinal(
            consumidorFinal,
            order.pedido
        ))

        idTransporte = asyncio.run(self.getTransporte())

        if not isinstance(idTransporte, int):
            raise Exception('Transporte não definido')

        order.pedido.ID_TRANSPORTE = idTransporte

        numeroPedido = self.gravaPedido(order)

        if isinstance(numeroPedido, str):
            return numeroPedido

        return NUM_PEDIDO(NUMERO_PEDIDO=numeroPedido)        

    def gravaPedido(self, order: Order) -> int | str:
        # Todo o fluxo (cabeçalho + itens + pagamentos + baixa de estoque +
        # financeiro + impressão) roda numa única transação: ou grava tudo, ou
        # não grava nada. Antes da migração, cada etapa usava a mesma sessão
        # global do SQLAlchemy (compartilhada entre requisições concorrentes,
        # já que era um objeto único no processo) e o cabeçalho do pedido era
        # commitado sozinho, antes do resto — uma falha no meio do fluxo podia
        # deixar um pedido gravado sem itens/pagamento. Isso não acontece mais.
        try:
            with db.transaction() as conn:
                cliente = self.getClientePedido(order.pedido.ID_CLIENTE, order.pedido.ID_ENDERECO, conn=conn)

                if 'consumidor final' not in cliente.NOME_CLIENTE.lower():
                    order.pedido.ORIGEM = 'Delivery próprio'

                    for item in order.pagamento:
                        item.ORIGEM = 'Delivery próprio'

                numeroPedido = self.insereNovoPedido(order.pedido, conn=conn)

                assert isinstance(numeroPedido, int)

                assert numeroPedido > 0

                order.pedido.NUMERO_PEDIDO = numeroPedido

                for item in order.itemsPedido:
                    item.NUMERO_PEDIDO = numeroPedido

                for item in order.pagamento:
                    item.NUMERO_PEDIDO = numeroPedido

                [self.gravaItensPedido(item, conn=conn) for item in order.itemsPedido]
                [self.gravaPagamentos(item, conn=conn) for item in order.pagamento]

                [self.test_baixaEstoque(item, conn=conn) for item in order.itemsPedido]

                financeiro = [
                    self.test_gravaFinanceiro(order.pedido, order.itemsPedido, pagamento, conn=conn)
                    for pagamento in order.pagamento
                ]

                erro = list(filter(lambda e: isinstance(e, str), financeiro))

                if any(erro):
                    raise _ErroNegocioPedido(''.join(erro))

                if order.impressaoPedido.IMPRESSAO_NAO_FISCAL == 1:
                    self._filaComanda.inserir(
                        numeroPedido, order.impressaoPedido.NUMERO_IMPRESSORA, conn=conn
                    )

                if order.impressaoPedido.IMPRESSAO_FISCAL == 1:
                    self.test_gravaImpressaoFiscal(numeroPedido, conn=conn)
        except _ErroNegocioPedido as ex:
            # Validação de negócio (ex.: limite de vale funcionário excedido)
            # — não é uma falha de sistema, então a transação já foi desfeita
            # (rollback automático do "with") e devolvemos a mensagem como
            # string, igual ao comportamento anterior.
            return str(ex)

        return numeroPedido

    def insereNovoPedido(self, pedido: pedido, conn=None) -> int:
        cliente = self.getClientePedido(pedido.ID_CLIENTE, pedido.ID_ENDERECO, conn=conn)

        return self._pedidos.inserir(pedido, cliente, conn=conn)

    def gravaItensPedido(self, item: itemPedido, conn=None) -> bool:
        self._itensPedido.inserir(item, conn=conn)

        descricaoProduto = self.getDescricaoProduto(item.ID_PRODUTO, conn=conn)

        self._atendimentoComanda.inserir(
            item.ID_PRODUTO,
            item.QTDE,
            item.PRECO_UNITARIO,
            item.NUMERO_PEDIDO,
            item.ID_TRIBUTO,
            descricaoProduto,
            conn=conn,
        )

    def gravaPagamentos(self, item: pedidoPagamento, conn=None) -> bool:
        self._pagamentos.inserir(item, conn=conn)

    def test_baixaEstoque(self, item: itemPedido, conn=None):
        assert self.baixaEstoque(item, 1, conn=conn) == True

    def gravaEstoque(self, dados: estoque) -> bool:
        self._estoque.inserir(dados)

        return True

    def baixaEstoque(self, item: itemPedido, movimento: int, conn=None) -> bool:
        comboProduto = self._combos.listar_por_produto(item.ID_PRODUTO, conn=conn)

        for combo in comboProduto:
            if not self._produtos.existe(combo.ID_PRODUTO_COMBO, conn=conn):
                continue

            self._estoque.inserir_movimento(
                combo.ID_PRODUTO_COMBO, movimento, combo.QTDE_COMBO,
                item.NUMERO_PEDIDO, combo.QTDE_COMBO, conn=conn
            )

        if len(comboProduto) > 0:
            return True

        associacaoProduto = self._associacoes.listar_por_produto(item.ID_PRODUTO, conn=conn)

        for item1 in associacaoProduto:
            if not self._produtos.existe(item1.ID_PRODUTO_ESTOQUE, conn=conn):
                continue

            self._estoque.inserir_movimento(
                item1.ID_PRODUTO_ESTOQUE, movimento, item.QTDE,
                item.NUMERO_PEDIDO, item.QTDE, conn=conn
            )

        if len(associacaoProduto) > 0:
            return True

        # Correção: a consulta original não trazia DOSE_ML (só ID_PRODUTO e
        # ID_PRODUTO_DOSE), mas o código logo abaixo acessava item1.DOSE_ML —
        # levantava AttributeError sempre que um produto vendido por dose
        # entrava aqui (baixa de estoque quebrava para esses produtos).
        doseProduto = self._doses.listar_por_produto_dose(item.ID_PRODUTO, conn=conn)

        for item1 in doseProduto:
            if not self._produtos.existe(item1.ID_PRODUTO, conn=conn):
                continue

            self._estoque.inserir_movimento(
                item1.ID_PRODUTO, movimento, item1.DOSE_ML,
                item.NUMERO_PEDIDO, item1.DOSE_ML, conn=conn
            )

        if len(doseProduto) > 0:
            return True

        self._estoque.inserir_movimento(
            item.ID_PRODUTO, movimento, item.QTDE, item.NUMERO_PEDIDO, item.QTDE, conn=conn
        )

        return True

    def test_gravaFinanceiro(
        self, pedido: pedido, itemsPedido: List[itemPedido], pagamento: pedidoPagamento, conn=None
    ) -> bool | str:
        result = self.gravaFinanceiro(pedido, itemsPedido, pagamento, conn=conn)

        return result

    def gravaFinanceiro(
        self, _pedido: pedido, itemsPedido: List[itemPedido], pagamento: pedidoPagamento, conn=None
    ) -> bool | str:
        formaPagto = self._formasPagto.buscar_por_descricao(pagamento.FORMA_PAGTO, conn=conn)

        if formaPagto is not None:
            if formaPagto.PAGTO_FUTURO == 1:

                itemsFinanceiro = [
                    itemPedidoFinanceiro(
                        PRODUTO= self.getDescricaoProduto(item.ID_PRODUTO, conn=conn),
                        QTDE=item.QTDE
                    )
                    for item in itemsPedido
                ]

                self.inserePagtoFuturo(
                    pedidoFinanceiro(
                        NUMERO_PEDIDO=_pedido.NUMERO_PEDIDO,
                        NOME_CLIENTE=self.getNomeCliente(_pedido.ID_CLIENTE, conn=conn),
                        ID_CLIENTE=_pedido.ID_CLIENTE,
                        TOTAL_PEDIDO=_pedido.TOTAL_PEDIDO,
                        LIMITE_MENSAL=_pedido.LIMITE_MENSAL
                    ),
                    itemsFinanceiro,
                    pedidoPagamentoFinanceiro(
                        VALOR_PAGO=pagamento.VALOR_PAGO,
                        NUMERO_PEDIDO=pagamento.NUMERO_PEDIDO
                    ),
                    conn=conn
                )

                return True

        valorLimite = 0.00

        if _pedido.LIMITE_MENSAL > 0.00:
            valorLimite = _pedido.LIMITE_MENSAL

        if valorLimite == 0.00 and formaPagto is not None and formaPagto.VALE_FUNCIONARIO == 1:
            valorLimite = formaPagto.VALOR_DIA if formaPagto.VALOR_DIA is not None else 0.00

        if valorLimite > 0.00:
            itemsFinanceiro = [
                itemPedidoFinanceiro(
                    PRODUTO= self.getDescricaoProduto(item.ID_PRODUTO, conn=conn),
                    QTDE=item.QTDE
                )
                for item in itemsPedido
            ]

            result = self.insereValeFuncionario(
                pedidoFinanceiro(
                    NUMERO_PEDIDO=_pedido.NUMERO_PEDIDO,
                    NOME_CLIENTE=self.getNomeCliente(_pedido.ID_CLIENTE, conn=conn),
                    ID_CLIENTE=_pedido.ID_CLIENTE,
                    TOTAL_PEDIDO=_pedido.TOTAL_PEDIDO,
                    LIMITE_MENSAL=_pedido.LIMITE_MENSAL
                ),
                itemsFinanceiro,
                pedidoPagamentoFinanceiro(
                    VALOR_PAGO=pagamento.VALOR_PAGO,
                    NUMERO_PEDIDO=pagamento.NUMERO_PEDIDO
                ),
                conn=conn
            )

            if isinstance(result, str):
                # A transação inteira (gravaPedido) é desfeita pelo chamador
                # quando esta função devolve uma string — não precisa de
                # rollback manual aqui.
                return result

            self.inserePagtoCartao(_pedido, itemsPedido, pagamento, conn=conn)

        return True

    async def test_gravaImpressaoNaoFiscal(
        self, impressaoNaoFiscal: filaComanda
    ) -> bool:
        self.gravaImpressaoNaoFiscal(impressaoNaoFiscal)

        return True

    def gravaImpressaoNaoFiscal(self, impressaoNaoFiscal: filaComanda, conn=None) -> bool:
        self._filaComanda.inserir(impressaoNaoFiscal.NUMERO_COMANDA, 0, conn=conn)

        return True

    def test_gravaImpressaoFiscal(self, numeroPedido: int, conn=None) -> bool:
        assert self.gravaImpressaoFiscal(numeroPedido, conn=conn) == True

        return True

    def gravaImpressaoFiscal(self, numeroPedido: int, conn=None) -> bool:
        _nf = asyncio.run(self.buscaProximaNF(conn=conn))

        self._pedidoNFe.inserir(
            numero_pedido=numeroPedido,
            numero_nf=_nf[0],
            serie_nf=_nf[1],
            processado=1,
            conn=conn,
        )

        return True

    async def buscaProximaNF(self, conn=None):
        _empresa = self._empresas.numero_e_serie_nfce(conn=conn)

        NF = 0 if _empresa["NUMERO_NFCE"] is None else _empresa["NUMERO_NFCE"]

        retorno = [
            NF,
            "1" if _empresa["SERIE_NFCE"] is None else _empresa["SERIE_NFCE"],
        ]

        return retorno

    def inserePagtoFuturo(
        self, pedido: pedidoFinanceiro, itemsPedido: List[itemPedidoFinanceiro], pagamento: pedidoPagamentoFinanceiro,
        conn=None
    ) -> bool:
        if not self._planoContas.existe(self.idPlanoPagtoFuturo, conn=conn):
            self._planoContas.inserir(
                self.idPlanoPagtoFuturo, "RECEBIMENTO FUTURO", "1", 0, conn=conn
            )

        hoje = datetime.today()

        mes = hoje.month
        ano = hoje.year

        if hoje.day >= 7:
            mes = (hoje + relativedelta(months=1)).month
            ano = (hoje + relativedelta(months=1)).year

        _vencimento = datetime(ano, mes, 7, hoje.hour, hoje.minute, 0)

        self._financeiro.deletar_por_comanda(pagamento.NUMERO_PEDIDO, conn=conn)

        items = [
            produtoQtde(
                DESCRICAO_PRODUTO=item.PRODUTO,
                QTDE=item.QTDE
                )
            for item in itemsPedido
        ]

        strItems = ", ".join(
            [f"[{item.DESCRICAO_PRODUTO}, Qtde: {str(item.QTDE)}]" for item in items]
        )

        descricao = "".join(
            [
                f"Recebimento futuro {pedido.NOME_CLIENTE} - Nr. Pedido {pedido.NUMERO_PEDIDO}",
                f", ITENS: {strItems}",
            ]
        )

        if len(descricao) > 250:
            descricao = descricao[0: 250]

        self._financeiro.inserir(
            _vencimento, descricao, self.idPlanoPagtoFuturo,
            pagamento.VALOR_PAGO, 0, pagamento.VALOR_PAGO, pagamento.NUMERO_PEDIDO,
            conn=conn
        )

        return True

    def inserePagtoCartao(
        self, pedido: pedido, itemsPedido: List[itemPedido], pagamento: pedidoPagamento, conn=None
    ) -> bool:
        recPagamento = self._formasPagto.buscar_por_descricao(pagamento.FORMA_PAGTO, conn=conn)

        if recPagamento is None:
            return True

        if recPagamento.DIAS_PAGAMENTO is None:
            return True

        if recPagamento.DIAS_PAGAMENTO <= 0:
            return True

        if not self._planoContas.existe(self.idPlanoPagtoFuturo, conn=conn):
            self._planoContas.inserir(
                self.idPlanoPagtoFuturo, "RECEBIMENTO FUTURO", "1", 0, conn=conn
            )

        hoje = datetime.today()

        mes = hoje.month
        ano = hoje.year

        if hoje.day >= 7:
            mes = (hoje + relativedelta(months=1)).month
            ano = (hoje + relativedelta(months=1)).year

        _vencimento = datetime(ano, mes, 7, hoje.hour, hoje.minute, 0)

        self._financeiro.deletar_por_comanda(pagamento.NUMERO_PEDIDO, conn=conn)

        items = [
            produtoQtde(
                DESCRICAO_PRODUTO=self.getDescricaoProduto(item.ID_PRODUTO, conn=conn),
                QTDE=item.QTDE
            )
            for item in itemsPedido
        ]

        strItems = ", ".join(
            [f"[{item.DESCRICAO_PRODUTO}, Qtde: {str(item.QTDE)}]" for item in items]
        )

        nomeCliente = self.getNomeCliente(pedido.ID_CLIENTE, conn=conn)

        descricao = "".join(
            [
                f"Recebimento futuro {nomeCliente} - Nr. Pedido {pedido.NUMERO_PEDIDO}",
                f", ITENS: {strItems}",
            ]
        )

        if len(descricao) > 250:
            descricao = descricao[0: 250]

        percentualAbatimento = 0.00

        try:
            percentualAbatimento = float(recPagamento.TAXA_PAGAMENTO)
        except:
            pass

        valorPago = float(pagamento.VALOR_PAGO)

        valorAbatimento = round(valorPago * (percentualAbatimento / 100), 2)

        self._financeiro.inserir(
            _vencimento, descricao, self.idPlanoPagtoFuturo,
            valorPago, valorAbatimento, valorPago - valorAbatimento, pagamento.NUMERO_PEDIDO,
            conn=conn
        )

        return True

    def insereValeFuncionario(
        self, pedido: pedidoFinanceiro, itemsPedido: List[itemPedidoFinanceiro],
            pagamento: pedidoPagamentoFinanceiro, conn=None) -> bool | str:

        d1 = datetime(datetime.today().year, datetime.today().month, 1)
        d2 = d1 + relativedelta(months=1)

        soma = self._pedidos.soma_total_pedido_mes(pedido.ID_CLIENTE, d1, d2, conn=conn)

        totalVendas = 0.00 if soma is None else float(soma)

        totalVendas += pedido.TOTAL_PEDIDO

        # Removido: o código anterior ainda buscava a forma de pagamento do
        # pedido e o VALOR_DIA da tb_forma_pagto correspondente só para
        # calcular um `valorMaximoMensal` que era imediatamente sobrescrito
        # pela linha abaixo (pedido.LIMITE_MENSAL) — resultado sempre
        # descartado, sem efeito colateral. Duas consultas a menos.
        valorMaximoMensal = pedido.LIMITE_MENSAL

        if totalVendas > valorMaximoMensal:
            return '\n'.join((
                f"O valor máximo mensal para vale funcionário foi excedido. ",
                f"Valor máximo: {self.qBase.currency(valorMaximoMensal)}. ",
                f"Total de vendas do mês: {self.qBase.currency(totalVendas)}."
            ))

        self.inserePagtoFuturo(
            pedido,
            itemsPedido,
            pagamento,
            conn=conn
        )

        return True

    def getDescricaoProduto(self, ID_PRODUTO, conn=None) -> str:
        return self._produtos.descricao_por_id_ou_vazio(ID_PRODUTO, conn=conn)

    async def lista_FormaPagto(self) -> List[listaFormaPagto]:
        select1 = self._formasPagto.listar()

        lista = [
            listaFormaPagto(
                ID_FORMA=row.ID_FORMA,
                DESCRICAO_FORMA=row.DESCRICAO_FORMA,
                TAXA_PAGAMENTO=0 if row.TAXA_PAGAMENTO is None else float(row.TAXA_PAGAMENTO)
            ).__dict__
            for row in select1
        ]

        return lista

    def checaConsumidorFinal(self) -> clienteEndereco:
        with db.transaction() as conn:
            empresa = self._empresas.buscar_padrao(conn=conn)

            endereco_empresa = "ISENTO"
            numero_endereco_empresa = "SN"
            complemento_endereco_empresa = ""
            bairro_empresa = "ISENTO"
            cep_empresa = ""
            municipio_empresa = ""
            uf_empresa = ""
            telefone_empresa = "11"
            id_empresa = 1

            if empresa is not None:
                endereco_raw = (
                    empresa.ENDERECO.strip()
                    if isinstance(empresa.ENDERECO, str)
                    else ""
                )

                if len(endereco_raw) > 0:
                    partes_endereco = [item.strip() for item in endereco_raw.split(",")]

                    endereco_empresa = partes_endereco[0] if len(partes_endereco[0]) > 0 else "ISENTO"

                    if len(partes_endereco) > 1 and len(partes_endereco[1]) > 0:
                        numero_endereco_empresa = self.qBase.onlyNumbers(partes_endereco[1]).strip()

                    if len(partes_endereco) > 2 and len(partes_endereco[2]) > 0:
                        complemento_endereco_empresa = partes_endereco[2]

                    if len(numero_endereco_empresa) == 0:
                        numero_endereco_empresa = "SN"

                bairro_empresa = (
                    empresa.BAIRRO.strip()
                    if isinstance(empresa.BAIRRO, str) and len(empresa.BAIRRO.strip()) > 0
                    else "ISENTO"
                )
                cep_empresa = "" if empresa.CEP is None else str(empresa.CEP).strip()
                municipio_empresa = "" if empresa.CIDADE is None else str(empresa.CIDADE).strip()
                uf_empresa = "" if empresa.UF is None else str(empresa.UF).strip()
                telefone_empresa = (
                    "11"
                    if empresa.TELEFONE is None or len(str(empresa.TELEFONE).strip()) == 0
                    else str(empresa.TELEFONE).strip()
                )
                id_empresa = 1 if empresa.ID_EMPRESA is None else int(empresa.ID_EMPRESA)

            cliente = self._clientes.buscar_consumidor_final(conn=conn)

            if cliente is None:
                ID_CLIENTE = self._clientes.inserir_consumidor_final(
                    endereco_empresa, numero_endereco_empresa, complemento_endereco_empresa,
                    bairro_empresa, cep_empresa, municipio_empresa, uf_empresa, telefone_empresa,
                    id_empresa, conn=conn
                )
            else:
                ID_CLIENTE = int(cliente.ID_CLIENTE)

            endereco = self._enderecos.buscar_primeiro_por_cliente(ID_CLIENTE, conn=conn)

            if endereco is None:
                ID_ENDERECO = self._enderecos.inserir_endereco_empresa(
                    ID_CLIENTE, endereco_empresa, numero_endereco_empresa, complemento_endereco_empresa,
                    bairro_empresa, cep_empresa, municipio_empresa, uf_empresa, id_empresa,
                    conn=conn
                )
            else:
                ID_ENDERECO = int(endereco.ID_ENDERECO)

        return clienteEndereco(ID_CLIENTE=ID_CLIENTE, ID_ENDERECO=ID_ENDERECO)

    async def getTransporte(self) -> int:
        transporte = self._transportes.buscar_primeiro()

        return None if transporte is None else int(transporte.ID_TRANSPORTE)

    async def listaAtendimento(self, NUMERO_PEDIDO):
        select1 = self._itensPedido.listar_com_produto(NUMERO_PEDIDO)

        lista = [
            itemPedidoCaixa(
                NUMERO_PEDIDO=row.NUMERO_PEDIDO,
                NUMERO_ITEM=row.NUMERO_ITEM,
                ID_PRODUTO=row.ID_PRODUTO,
                DESCRICAO_PRODUTO=row.DESCRICAO_PRODUTO,
                QTDE=row.QTDE,
                PRECO=row.PRECO_UNITARIO,
                TOTAL=row.VALOR_TOTAL,
                ID_TRIBUTO=row.ID_TRIBUTO,
                QTDE_FRACIONADA=self.qBase.isFamiliaBalanca(row.ID_FAMILIA) if isinstance(row.ID_FAMILIA, int) else False
            ).__dict__
            for row in select1
        ]

        retorno = self.qBase.toRoute(lista, 200)

        return retorno

    async def get_Pagamentos(self, NUMERO_PEDIDO: int, query: List) -> str:
        lista = [
            FORMAS_PAGTO_IMPRESSAO(
                DESCRICAO = item.FORMA_PAGTO,
                VALOR = self.qBase.currency(item.VALOR_PAGO)
            )
            for item in query
            if item.NUMERO_PEDIDO == NUMERO_PEDIDO
        ]

        retorno = "\n".join(
            [
                f"{item.DESCRICAO}: {item.VALOR}"
                for item in lista
            ]
        )

        return retorno

    def _campoSeguro(self, valor) -> str:
        """
        Escapa '|' e quebra de linha antes de entrar num campo de
        DADOS_PAGAMENTO. FORMA_PAGTO/CODIGO_NSU são texto livre (ex.:
        MOVILE_PAY, NUBANK, VISA_ELECTRON) e um '|' embutido desloca o
        parsing posicional que o frontend faz em cima desse formato.
        """
        if valor is None:
            return ''

        return str(valor).replace('|', '/').replace('\n', ' ').replace('\r', ' ')

    async def get_DadosPagamentos(self, NUMERO_PEDIDO: int, query: list) -> str:
        lista = [
            '|'.join((
                str(item.ID_PAGAMENTO),
                self._campoSeguro(item.FORMA_PAGTO),
                str(item.VALOR_PAGO),
                self._campoSeguro(item.CODIGO_NSU)
            ))
            for item in query
            if item.NUMERO_PEDIDO == NUMERO_PEDIDO
        ]

        return '\n'.join(lista)

    def getNomeTransporte(self, ID_TRANSPORTE: int, conn=None) -> str:
        return self._transportes.nome_por_id(ID_TRANSPORTE, conn=conn)

    def getNomeCliente(self, ID_CLIENTE: int, conn=None) -> str:
        return self._clientes.nome_por_id(ID_CLIENTE, conn=conn)

    async def listaPedidos(self, filtro: filtroPedido) -> List[listaDePedido]:
        soNumeros = self.qBase.onlyNumbers(filtro.FILTRO)

        retorno = []

        if len(filtro.FILTRO) == len(soNumeros) and len(soNumeros) > 0:
            retorno = await self.getByNumeroPedido(filtro)

            if len(retorno) == 0 and filtro.ORIGEM == "Zé Delivery":
                retorno = await self.getByNumeroZe(filtro)

            if len(retorno) == 0 and filtro.ORIGEM == "IFood":
                retorno = await self.getByNumeroIFood(filtro)

            return retorno

        retorno = await self.getByDataHora(filtro)

        return retorno

    async def getByNumeroPedido(self, filtro: filtroPedido) -> List[listaDePedido]:
        query = self._pedidos.listar_por_numero(filtro.FILTRO)

        retorno = await self.retornoQueryPedidos(query)

        return retorno

    async def getByNumeroZe(self, filtro: filtroListaPedido) -> List[listaDePedido]:
        query = self._pedidos.listar_por_numero_ze(filtro.FILTRO)

        retorno = await self.retornoQueryPedidos(query)

        return retorno

    async def getByNumeroIFood(self, filtro: filtroListaPedido) -> List[listaDePedido]:
        query = self._pedidos.listar_por_numero_ifood(filtro.FILTRO)

        retorno = await self.retornoQueryPedidos(query)

        return retorno

    async def getByDataHora(self, filtro: filtroListaPedido) -> List[listaDePedido]:
        d1 = datetime.today() + timedelta(days=-15)
        d2 = datetime.today() + timedelta(hours=1)

        query = self._pedidos.listar_por_periodo(
            d1, d2, filtro.FILTRO, filtro.ORIGEM, filtro.STATUS, filtro.START
        )

        retorno = await self.retornoQueryPedidos(query)

        return retorno

    async def retornoQueryPedidos(self, query) -> List[listaDePedido]:
        empresa = self._empresas.buscar_padrao()

        retorno = []

        lista = sorted(query, key=lambda e: e.DATA_HORA, reverse=True)

        for item in lista:
            if (
                len(
                    list(
                        filter(lambda e: e.NUMERO_PEDIDO == item.NUMERO_PEDIDO, retorno)
                    )
                )
                > 0
            ):
                continue

            retorno.append(
                listaDePedido(
                    NUMERO_PEDIDO=item.NUMERO_PEDIDO,
                    DATA_HORA=datetime.strftime(item.DATA_HORA, "%d/%m/%Y %H:%M"),
                    ORIGEM="" if item.ORIGEM is None else item.ORIGEM,
                    STATUS_PEDIDO=Config.getStatus(item),
                    NOME_CLIENTE=item.NOME_CLIENTE,
                    TRANSPORTE=item.NOME_TRANSPORTE,

                    TOTAL_PEDIDO=0.00
                    if item.TOTAL_PEDIDO is None
                    else float(item.TOTAL_PEDIDO),

                    PAGAMENTOS=await self.get_Pagamentos(item.NUMERO_PEDIDO, lista),

                    ENDERECO=empresa.ENDERECO
                    if len(item.ENDERECO_CLIENTE) == 0
                    else item.ENDERECO_CLIENTE,

                    TELEFONE=empresa.TELEFONE
                    if len(item.TELEFONE_CLIENTE) == 0
                    else item.TELEFONE_CLIENTE,

                    NF= item.nota == 1,
                    DESCRICAO_FORMA=item.FORMA_PAGTO,
                    CODIGO_AUTORIZACAO=item.CODIGO_NSU,
                    DADOS_PAGAMENTO=await self.get_DadosPagamentos(item.NUMERO_PEDIDO, lista),
                )
            )

        return retorno

    async def getItemPedido(self, item) -> str:

        obsItem = item.OBS_ITEM if item.OBS_ITEM is not None else ''
        
        retorno = self.getDescricaoProduto(item.ID_PRODUTO) + f' {obsItem}'

        return retorno
    
    async def getPedido(self, filtro: filtroPedido):
        numeroPedido = 0

        try:
            numeroPedido = int(filtro.FILTRO)
        except:
            pass

        if numeroPedido == 0:
            raise Exception("Numero de pedido inválido")

        rec = self._pedidos.buscar_resumo_edicao(numeroPedido)

        if rec is None:
            raise Exception("Pedido não encontrado na base do sistema")

        items = self._itensPedido.listar_por_pedido(numeroPedido)

        itemsPedido = [
            editItemPedido(
                NUMERO_ITEM=item.NUMERO_ITEM,
                NUMERO_PEDIDO=item.NUMERO_PEDIDO,
                ID_PRODUTO=item.ID_PRODUTO,
                ID_TRIBUTO=item.ID_TRIBUTO,
                DESCRICAO_PRODUTO=await self.getItemPedido(item),
                QTDE=int(item.QTDE),
                PRECO=float(item.PRECO_UNITARIO),
                TOTAL=float(item.VALOR_TOTAL),
            )
            for item in items
        ]

        pag = self._pagamentos.listar_por_pedido(numeroPedido)

        pagamentos = [
            editPedidoPagamento(
                ID_PAGAMENTO=item.ID_PAGAMENTO,
                NUMERO_PEDIDO=item.NUMERO_PEDIDO,
                FORMA_PAGTO=item.FORMA_PAGTO,
                ID_CAIXA=item.ID_CAIXA,
                VALOR_PAGO=item.VALOR_PAGO,
                CODIGO_NSU="" if item.CODIGO_NSU is None else item.CODIGO_NSU,
            )
            for item in pag
        ]

        retorno = editPedido(
            NUMERO_PEDIDO=rec.NUMERO_PEDIDO,
            ID_CLIENTE=rec.ID_CLIENTE,
            CPF=rec.CPF,
            NOME_CLIENTE=rec.NOME_CLIENTE,
            ID_TRANSPORTE=0 if rec.ID_TRANSPORTE is None else rec.ID_TRANSPORTE,
            NOME_TRANSPORTE=self.getNomeTransporte(rec.ID_TRANSPORTE),
            ORIGEM=rec.ORIGEM,
            TAXA_ENTREGA=float(rec.TAXA_ENTREGA)
            if rec.TAXA_ENTREGA is not None
            else 0.00,
            VALOR_ADICIONAL=float(rec.ADICIONAL) if rec.ADICIONAL is not None else 0.00,
            VALOR_DESCONTO=float(rec.DESCONTO) if rec.DESCONTO is not None else 0.00,
            TOTAL_PRODUTOS=float(rec.TOTAL_PRODUTOS) if rec.TOTAL_PRODUTOS is not None else 0.00,
            VALOR_TOTAL=float(rec.TOTAL_PEDIDO) if rec.TOTAL_PEDIDO is not None else 0.00,
            VALOR_TROCO =float(rec.TROCO) if rec.TROCO is not None else 0.00,
            INFO_ADICIONAL=rec.INFO_ADICIONAL,
            ID_CAIXA=rec.ID_CAIXA,
            ITEMS=itemsPedido,
            PAGAMENTOS=pagamentos,
            ID_ENDERECO=rec.ID_ENDERECO
        )

        return retorno

    async def deletaItemPedido(self, item: numeroItemPedido):
        numeroPedido = self._itensPedido.numero_pedido_do_item(item.NUMERO_ITEM)

        self._itensPedido.deletar_por_numero_item(item.NUMERO_ITEM)

        await self.recalculaTotaisPedido(numeroPedido)

    async def deletaPagamentoFinanceiro(self, NUMERO_PEDIDO: int):
        self._financeiro.deletar_por_comanda(NUMERO_PEDIDO)

    async def cancelaPedido(self, record: filtroCancelamento):
        if not self._usuarios.existe_admin_com_senha(record.SENHA):
            raise Exception('Senha incorreta para cancelar o pedido')

        pedido_atual = self._pedidos.buscar_por_numero(record.NUMERO_PEDIDO)
        _status = pedido_atual.STATUS_PEDIDO

        with db.transaction() as conn:
            itens = self._itensPedido.listar_por_pedido(record.NUMERO_PEDIDO, conn=conn)

            self._pedidos.atualizar_status(record.NUMERO_PEDIDO, 5, conn=conn)

            if _status == 3:
                [
                    self.baixaEstoque(
                        itemPedido(
                            NUMERO_ITEM=item.NUMERO_ITEM,
                            NUMERO_PEDIDO=item.NUMERO_PEDIDO,
                            ID_PRODUTO=item.ID_PRODUTO,
                            CODIGO_PRODUTO=item.CODIGO_PRODUTO,
                            QTDE=item.QTDE,
                            PRECO_UNITARIO=item.PRECO_UNITARIO,
                            VALOR_TOTAL=item.VALOR_TOTAL,
                            ID_TRIBUTO=item.ID_TRIBUTO,
                            OBS_ITEM=item.OBS_ITEM,
                            ID_ITEM_LOCAL=0,
                            ID_TERMINAL=0,
                        ),
                        0,
                        conn=conn,
                    )
                    for item in itens
                ]

            # Simplificação: o código anterior deletava tb_financeiro uma vez
            # por PAGAMENTO do pedido — todos com o mesmo NUMERO_PEDIDO, então
            # repetia o mesmo DELETE (sem efeito nas repetições). Um DELETE já
            # cobre tudo.
            self._financeiro.deletar_por_comanda(record.NUMERO_PEDIDO, conn=conn)

    async def savePedido(self, record: dadosPedido):
        nomeCliente = self._clientes.nome_por_id(record.ID_CLIENTE)
        endereco = self._enderecos.buscar_por_id(record.ID_ENDERECO)

        totalPedido = round(
            (record.TOTAL_PRODUTOS + record.TAXA_ENTREGA + record.ADICIONAL)
            - record.DESCONTO,
            2,
        )

        qPg = self._pagamentos.listar_por_pedido(record.NUMERO_PEDIDO)

        somaPagamentos = sum(
            [float(item.VALOR_PAGO) for item in qPg if item.VALOR_PAGO is not None]
        )

        troco = 0.00

        if somaPagamentos > totalPedido:
            troco = round(somaPagamentos - totalPedido, 2)

        self._pedidos.atualizar_dados_edicao(
            record.NUMERO_PEDIDO,
            record.ID_CLIENTE,
            nomeCliente,
            record.ID_ENDERECO,
            f'{endereco.ENDERECO}, {endereco.NUMERO_ENDERECO} {endereco.COMPLEMENTO_ENDERECO}',
            endereco.BAIRRO,
            record.ID_TRANSPORTE,
            record.TOTAL_PRODUTOS,
            record.TAXA_ENTREGA,
            record.ADICIONAL,
            record.DESCONTO,
            record.INFO_ADICIONAL,
            totalPedido,
            troco,
        )

        await self.refazFinanceiro(
            qPg,
            record
            )

    async def refazFinanceiro(self, pagamentos: List, record: dadosPedido):
        formasPagto = [item.FORMA_PAGTO for item in pagamentos]

        if not self._formasPagto.existe_pagto_futuro_entre(formasPagto):
            return

        if self._financeiro.buscar_por_comanda(record.NUMERO_PEDIDO) is None:
            return

        itemsPedido = self._itensPedido.listar_por_pedido(record.NUMERO_PEDIDO)

        items = [
            produtoQtde(
                DESCRICAO_PRODUTO=self.getDescricaoProduto(item.ID_PRODUTO),
                QTDE=item.QTDE
                )
            for item in itemsPedido
        ]

        strItems = ", ".join(
            [f"[{item.DESCRICAO_PRODUTO}, Qtde: {str(item.QTDE)}]" for item in items]
        )

        nomeCliente = self._clientes.buscar_por_id(record.ID_CLIENTE).NOME_CLIENTE

        descricao = "".join(
            [
                f"Recebimento futuro {nomeCliente} - Nr. Pedido {record.NUMERO_PEDIDO}",
                f", ITENS: {strItems}",
            ]
        )

        if len(descricao) > 250:
            descricao = descricao[0: 250]

        self._financeiro.atualizar_historico(record.NUMERO_PEDIDO, descricao)

    async def isPagtoFuturo(self, DESCRICAO: str) -> List:
        formaPagto = self._formasPagto.buscar_por_descricao(DESCRICAO)

        if formaPagto is not None and formaPagto.PAGTO_FUTURO == 1:
            return [DESCRICAO]

        return []

    async def refazPagamentoFuturo(self, NUMERO_PEDIDO: int):
        pagamentos = self._pagamentos.listar_por_pedido(NUMERO_PEDIDO)

        listaP = [await self.isPagtoFuturo(item.FORMA_PAGTO) for item in pagamentos]

        if not any(listaP):
            await self.deletaPagamentoFinanceiro(NUMERO_PEDIDO)
            return

        recordPagamento = [
            pedidoPagamentoFinanceiro(
                VALOR_PAGO=float(item.VALOR_PAGO),
                NUMERO_PEDIDO=item.NUMERO_PEDIDO
            )
            for item in pagamentos
        ][0]

        # Correção: o código anterior reaproveitava por engano a tabela de
        # pagamento (sem coluna ID_PRODUTO) no lugar da tabela de itens do
        # pedido — levantava AttributeError sempre que este trecho era
        # alcançado, ou seja, sempre que o pedido tinha pagamento do tipo
        # "futuro" (exatamente o caso que esta função existe pra tratar).
        itensPedido = self._itensPedido.listar_por_pedido(NUMERO_PEDIDO)

        itemsPedido = [
            itemPedidoFinanceiro(
                PRODUTO=self.getDescricaoProduto(item.ID_PRODUTO),
                QTDE= float(item.QTDE)
            )
            for item in itensPedido
        ]

        qC = self._pedidos.buscar_cliente_e_total(NUMERO_PEDIDO)

        nomeCliente = qC.NOME_CLIENTE
        idCliente = qC.ID_CLIENTE
        _totalPedido = float(qC.TOTAL_PEDIDO)

        self.inserePagtoFuturo(
            pedidoFinanceiro(
                NUMERO_PEDIDO=NUMERO_PEDIDO,
                NOME_CLIENTE=nomeCliente,
                ID_CLIENTE=idCliente,
                TOTAL_PEDIDO=_totalPedido,
                LIMITE_MENSAL=0
            ),
            itemsPedido,
            recordPagamento
        )

    async def recalculaTotaisPedido(self, NUMERO_PEDIDO: int):
        record = self._pedidos.buscar_por_numero(NUMERO_PEDIDO)

        items = self._itensPedido.listar_por_pedido(NUMERO_PEDIDO)

        somaProdutos = 0.00

        try:
            somaProdutos = sum([float(item.VALOR_TOTAL) for item in items])
        except:
            pass

        totalPedido = round(
            (somaProdutos + float(record.TAXA_ENTREGA) + float(record.ADICIONAL))
            - float(record.DESCONTO),
            2,
        )

        qPg = self._pagamentos.listar_por_pedido(NUMERO_PEDIDO)

        somaPagamentos = sum(
            [float(item.VALOR_PAGO) for item in qPg if item.VALOR_PAGO is not None]
        )

        troco = 0.00

        if somaPagamentos > totalPedido:
            troco = round(somaPagamentos - totalPedido, 2)

        self._pedidos.atualizar_totais(NUMERO_PEDIDO, somaProdutos, totalPedido, troco)

        await self.refazPagamentoFuturo(NUMERO_PEDIDO)

    def addItem(self, record: itemPedido):
        produto = self._produtos.buscar_codigo_tributo_preco(record.ID_PRODUTO)

        record.CODIGO_PRODUTO = produto.CODIGO_PRODUTO
        record.ID_TRIBUTO = produto.ID_TRIBUTO
        record.PRECO_UNITARIO = float(produto.PRECO_BALCAO)
        record.VALOR_TOTAL = round(record.QTDE * record.PRECO_UNITARIO, 2)

        self.gravaItensPedido(record)

        asyncio.run(self.recalculaTotaisPedido(record.NUMERO_PEDIDO))

    async def listaItens(self, filtro: filtroNumeroPedido) -> List[editItemPedido]:
        query = self._itensPedido.listar_por_pedido(filtro.NUMERO_PEDIDO)

        retorno = [
            editItemPedido(
                NUMERO_ITEM=item.NUMERO_ITEM,
                NUMERO_PEDIDO=item.NUMERO_PEDIDO,
                ID_PRODUTO=item.ID_PRODUTO,
                ID_TRIBUTO=item.ID_TRIBUTO,
                DESCRICAO_PRODUTO=self.getDescricaoProduto(item.ID_PRODUTO),
                QTDE=item.QTDE,
                PRECO=0.00
                if item.PRECO_UNITARIO is None
                else float(item.PRECO_UNITARIO),
                TOTAL=0.00 if item.VALOR_TOTAL is None else float(item.VALOR_TOTAL),
            )
            for item in query
        ]

        return retorno

    async def getTotalPedido(self, filtro: filtroNumeroPedido) -> TOTAL_PEDIDO:
        record = self._pedidos.buscar_por_numero(filtro.NUMERO_PEDIDO)

        items = self._itensPedido.listar_por_pedido(filtro.NUMERO_PEDIDO)

        somaProdutos = 0.00

        try:
            somaProdutos = sum([float(item.VALOR_TOTAL) for item in items])
        except:
            pass

        totalPedido = round(
            (somaProdutos + float(record.TAXA_ENTREGA) + float(record.ADICIONAL))
            - float(record.DESCONTO),
            2,
        )

        retorno = TOTAL_PEDIDO(
            TOTAL_PRODUTOS=somaProdutos,
            VALOR_ADICIONAL=float(record.ADICIONAL),
            VALOR_DESCONTO=float(record.DESCONTO),
            TAXA_ENTREGA=float(record.TAXA_ENTREGA),
            TOTAL_PEDIDO=totalPedido,
        )

        return retorno

    async def get_ID_forma_pagamento(self, DESCRICAO: str) -> int:
        forma = self._formasPagto.buscar_por_descricao(DESCRICAO)

        return forma.ID_FORMA if forma is not None else 0

    async def listaPagamentos(
        self, filtro: filtroNumeroPedido
    ) -> List[pagamentoPedido]:
        query = self._pagamentos.listar_por_pedido(filtro.NUMERO_PEDIDO)

        retorno = [
            pagamentoPedido(
                NUMERO_PEDIDO=item.NUMERO_PEDIDO,
                ID_PAGAMENTO=item.ID_PAGAMENTO,
                ID_FORMA=await self.get_ID_forma_pagamento(item.FORMA_PAGTO),
                DESCRICAO_FORMA=item.FORMA_PAGTO,
                VALOR_PAGO=0.00 if item.VALOR_PAGO is None else float(item.VALOR_PAGO),
                CODIGO_AUTORIZACAO="" if item.CODIGO_NSU is None else item.CODIGO_NSU,
                DATA_HORA=item.DATA_HORA
            )
            for item in query
        ]

        return retorno

    async def deleteItemPagamento(self, filtro: filtroIDPagamento):
        rec = self._pagamentos.buscar_por_id(filtro.ID_PAGAMENTO)
        numeroPedido = rec.NUMERO_PEDIDO

        self._pagamentos.deletar_por_id(filtro.ID_PAGAMENTO)

        await self.recalculaTotaisPedido(numeroPedido)

    async def addItemPagamento(self, dados: pagamentoPedido):
        pedido_atual = self._pedidos.buscar_por_numero(dados.NUMERO_PEDIDO)

        self._pagamentos.inserir_avulso(
            dados.NUMERO_PEDIDO,
            pedido_atual.DATA_HORA,
            dados.DESCRICAO_FORMA,
            dados.VALOR_PAGO,
            pedido_atual.ID_CAIXA,
            pedido_atual.ORIGEM,
        )

        await self.recalculaTotaisPedido(dados.NUMERO_PEDIDO)

    async def concluiPagamento(self, dados: conclusaoPagamento):
        with db.transaction() as conn:
            if dados.IMPRESSAO == True:
                self._filaComanda.inserir(dados.NUMERO_PEDIDO, dados.NUMERO_IMPRESSORA, conn=conn)

            if dados.FISCAL == True:
                self._pedidoNFe.inserir(
                    numero_pedido=dados.NUMERO_PEDIDO,
                    numero_nf=0,
                    serie_nf="1",
                    processado=0,
                    conn=conn,
                )

    async def emiteNFCe(self, dados: emissaoNFCe):
        existingQueue = self._pedidoNFe.listar_processadas(dados.NUMERO_PEDIDO, 0)

        if len(existingQueue) > 0:
            return

        if len(dados.CPF) > 0:
            self._pedidos.atualizar_cpf(dados.NUMERO_PEDIDO, dados.CPF)

        empresa = self._empresas.numero_e_serie_nfce()

        self._pedidoNFe.inserir(
            numero_pedido=dados.NUMERO_PEDIDO,
            numero_nf=0,
            serie_nf=empresa["SERIE_NFCE"],
            processado=1,
            id_empresa=empresa["ID_EMPRESA"],
        )

    async def checaEmissaoNFCe(self, filtro: filtroNumeroPedido) -> NFCe_Processada:
        query = self._pedidoNFe.listar_por_status(filtro.NUMERO_PEDIDO, [10, 2])

        autorizado = list(filter(lambda e: e.PROCESSADO == 10, query))

        recusada = list(filter(lambda e: e.PROCESSADO == 2, query))

        if len(autorizado) > 0:
            rec = autorizado[0]

            dataAutorizacao = datetime.strftime(
                    rec.DATA_AUTORIZACAO_NFCE, "%d/%m/%Y %H:%M"
                ) if isinstance(rec.DATA_AUTORIZACAO_NFCE, datetime) else ''

            return NFCe_Processada(
                NUMERO_PEDIDO=rec.NUMERO_PEDIDO,
                NUMERO_NF=rec.NUMERO_NF,
                PROTOCOLO_AUTORIZACAO=rec.PROTOCOLO_AUTORIZACAO,
                DATA_AUTORIZACAO=dataAutorizacao,
                MENSAGEM=rec.RESPOSTA_SEFAZ
            )

        if len(recusada) > 0:
            rec = recusada[0]

            return NFCe_Processada(
                NUMERO_PEDIDO=rec.NUMERO_PEDIDO,
                NUMERO_NF=rec.NUMERO_NF,
                PROTOCOLO_AUTORIZACAO="",
                DATA_AUTORIZACAO="",
                MENSAGEM=rec.RESPOSTA_SEFAZ,
            )

        return NFCe_Processada(
            NUMERO_PEDIDO=filtro.NUMERO_PEDIDO,
            NUMERO_NF=0,
            PROTOCOLO_AUTORIZACAO="",
            DATA_AUTORIZACAO="",
            MENSAGEM="Aguardando resposta",
        )

    async def imprimePedido(self, dados: impressaoAvulsa):
        self._filaComanda.inserir(dados.NUMERO_PEDIDO, dados.NUMERO_IMPRESSORA)

    async def buscaPedidoImpressao(
        self, filtro: filtroImpressaoPedido
    ) -> List[impressaoPedidoBalcao]:
        retorno = []

        filas = self._filaComanda.listar_por_maquina(filtro.MAQUINA)

        for fila in filas:
            Pedido = self._pedidos.buscar_por_numeros([fila.NUMERO_COMANDA])
            items = self._itensPedido.listar_por_pedido(fila.NUMERO_COMANDA)
            pagamento = self._pagamentos.listar_por_pedido(fila.NUMERO_COMANDA)

            if len(Pedido) == 0 or len(items) == 0 or len(pagamento) == 0:
                self._filaComanda.deletar_por_comanda(fila.NUMERO_COMANDA)

        pedidos = self._filaComanda.listar_numeros_distintos_por_maquina(filtro.MAQUINA)

        query = self._pedidos.buscar_por_numeros(pedidos)

        nComanda = query[0].NUMERO_PEDIDO if len(query) > 0 else 0

        if nComanda == 0:
            return []

        # Simplificação: o código anterior rodava a mesma consulta (mesmo
        # filtro `IN`) duas vezes seguidas só pra pegar a primeira linha —
        # `query[0]` já é essa linha.
        pedido = query[0]

        dadosCliente = self._clientes.buscar_por_id(pedido.ID_CLIENTE)

        dadosEndereco = self._enderecos.buscar_por_id(pedido.ID_ENDERECO)

        pag = self._pagamentos.listar_por_pedido(pedido.NUMERO_PEDIDO)

        formasPagamento = [
            FORMAS_PAGTO_IMPRESSAO(
                DESCRICAO=item.FORMA_PAGTO,
                VALOR=self.qBase.currency(float(item.VALOR_PAGO)),
            )
            for item in pag
        ]

        itemPedido = self._itensPedido.listar_por_pedido(pedido.NUMERO_PEDIDO)

        percentual = (f"% geral", f"% sobre o pagto")

        TOTAL_QTDE = sum([item.QTDE for item in itemPedido])
        TOTAL_VALOR = (
            float(pedido.TOTAL_PRODUTOS) if pedido.TOTAL_PRODUTOS is not None else 0
        )
        TROCO = float(pedido.TROCO) if pedido.TROCO is not None else 0
        DESCONTO = float(pedido.DESCONTO) if pedido.DESCONTO is not None else 0

        adicional = float(pedido.ADICIONAL) if pedido.ADICIONAL is not None else 0
        produtos = (
            float(pedido.TOTAL_PRODUTOS) if pedido.TOTAL_PRODUTOS is not None else 0
        )

        CAIXINHA = (
            produtos * (adicional / 100)
            if pedido.TIPO_ADICIONAL in percentual
            else adicional
        )
        TAXA_ENTREGA = (
            float(pedido.TAXA_ENTREGA) if pedido.TAXA_ENTREGA is not None else 0
        )

        qAtendimento = self._atendimentoComanda.listar_por_comanda(pedido.NUMERO_PEDIDO)

        atendimento = (
            qAtendimento[0].NUMERO_COMANDA_ATENDIMENTO if len(qAtendimento) > 0 else 0
        )
        mesa = qAtendimento[0].MESA if len(qAtendimento) > 0 else ""
        nomeMesa = qAtendimento[0].NOME_MESA if len(qAtendimento) > 0 else ""

        for item in items:
            descricaoProduto = self._produtos.descricao_por_id(item.ID_PRODUTO)

            obs = item.OBS_ITEM

            endereco = "".join(
                (
                    dadosEndereco.ENDERECO.strip(),
                    ", ",
                    dadosEndereco.NUMERO_ENDERECO.strip(),
                    f"{dadosEndereco.COMPLEMENTO_ENDERECO} - "
                    if dadosEndereco.COMPLEMENTO_ENDERECO is not None
                    else "",
                )
            )

            endereco = self.qBase.cleanSpecialChars(endereco)

            bairro = (
                self.qBase.cleanSpecialChars(dadosEndereco.BAIRRO)
                if dadosEndereco.BAIRRO is not None
                else ""
            )

            if pedido.ORIGEM == "IFood":
                bairro = self.qBase.cleanSpecialChars(pedido.BAIRRO_CLIENTE)

            if isinstance(obs, str):
                if len(obs) > 0:
                    descricaoProduto += f" - {obs}"

            cidade = (
                self.qBase.cleanSpecialChars(dadosEndereco.MUNICIPIO)
                if dadosEndereco.MUNICIPIO is not None
                else ""
            )
            infoAdicional = (
                self.qBase.cleanSpecialChars(pedido.INFO_ADICIONAL)
                if pedido.INFO_ADICIONAL is not None
                else ""
            )

            obs += f" {self.qBase.cleanSpecialChars(dadosCliente.OBS_CLIENTE)}"

            nomeTransporte = self._transportes.nome_por_id(pedido.ID_TRANSPORTE)

            retorno.append(
                impressaoPedidoBalcao(
                    CPF=pedido.CPF,
                    NUMERO_COMANDA=pedido.NUMERO_PEDIDO,
                    NUMERO_COMANDA_ATENDIMENTO=atendimento,
                    MESA=mesa if mesa is not None else "",
                    NUMERO_PEDIDO_ZE_DELIVERY=int(pedido.NUMERO_PEDIDO_ZE_DELIVERY)
                    if pedido.NUMERO_PEDIDO_ZE_DELIVERY is not None
                    else 0,
                    NUMERO_DELIVERY=int(pedido.NUMERO_PEDIDO_DELIVERY)
                    if pedido.NUMERO_PEDIDO_DELIVERY is not None
                    else 0,
                    NUMERO_PEDIDO_IFOOD=pedido.NUMERO_PEDIDO_IFOOD,
                    DATA_HORA=self.qBase.TrataDataHora(pedido.DATA_HORA),
                    NOME_CLIENTE=pedido.NOME_CLIENTE,
                    ENDERECO=endereco,
                    BAIRRO=bairro,
                    CIDADE=cidade,
                    FORMA_PAGTO=formasPagamento,
                    PRODUTO=descricaoProduto,
                    QTDE=str(int(item.QTDE)),
                    PRECO=self.qBase.currency(item.PRECO_UNITARIO),
                    TOTAL=self.qBase.currency(item.VALOR_TOTAL),
                    DESCONTO=self.qBase.currency(DESCONTO),
                    CAIXINHA=self.qBase.currency(CAIXINHA),
                    TOTAL_QTDE=str(int(TOTAL_QTDE)),
                    TOTAL_VALOR=self.qBase.currency(TOTAL_VALOR),
                    TROCO=self.qBase.currency(TROCO),
                    COMENTARIOS=obs,
                    TELEFONE=dadosCliente.TELEFONE_CLIENTE.strip()
                    if dadosCliente.TELEFONE_CLIENTE is not None
                    else "",
                    CHAVE_PEDIDO="",
                    CODIGO_IDENTIFICACAO_IFOOD=pedido.CODIGO_IDENTIFICACAO_IFOOD.strip()
                    if pedido.CODIGO_IDENTIFICACAO_IFOOD is not None
                    else "",
                    ORDER_NUMBER_GOOMER=int(pedido.ORDER_NUMBER_GOOMER)
                    if pedido.CODIGO_IDENTIFICACAO_IFOOD is not None
                    else 0,
                    ORDER_NUMBER_WABIZ=int(pedido.ORDER_NUMBER_WABIZ)
                    if pedido.ORDER_NUMBER_WABIZ is not None
                    else 0,
                    PREPARO_COZINHA=0,
                    ORIGEM=pedido.ORIGEM,
                    TRANSPORTE=nomeTransporte,
                    NOME_MESA=nomeMesa if nomeMesa is not None else "",
                    NUMERO_VENDA=int(pedido.NUMERO_VENDA)
                    if pedido.NUMERO_VENDA is not None
                    else 0,
                    TAXA_ENTREGA=self.qBase.currency(TAXA_ENTREGA),
                    NUMERO_PEDIDO_DELIVERY="",
                )
            )

        return retorno

    async def getDadosNFCe(self, filtro: filtroNumeroPedido) -> List[dadosNFCe]:
        retorno = []

        pedido = self._pedidos.buscar_por_numero(filtro.NUMERO_PEDIDO)

        itemsPedido = self._itensPedido.listar_por_pedido(filtro.NUMERO_PEDIDO)

        pedidoNFe = self._pedidoNFe.listar_por_pedido(filtro.NUMERO_PEDIDO)

        if len(pedidoNFe) == 0:
            raise Exception("Pedido não existe")

        ID_CLIENTE = pedido.ID_CLIENTE
        ID_ENDERECO = pedido.ID_ENDERECO
        ID_EMITENTE = pedidoNFe[0].ID_EMPRESA

        dadosEmpresa = self._empresas.buscar_por_id(ID_EMITENTE)

        dadosCliente = self._clientes.buscar_por_id(ID_CLIENTE)

        dadosEndereco = self._enderecos.buscar_por_id(ID_ENDERECO)

        if dadosEndereco.ENDERECO is None or len(dadosEndereco.ENDERECO.strip()) == 0:
            dadosEndereco.ENDERECO = dadosEmpresa.ENDERECO
            dadosEndereco.NUMERO_ENDERECO = ""
            dadosEndereco.COMPLEMENTO_ENDERECO = ""
            dadosEndereco.CEP = dadosEmpresa.CEP
            dadosEndereco.BAIRRO = dadosEmpresa.BAIRRO
            dadosEndereco.MUNICIPIO = dadosEmpresa.CIDADE
            dadosEndereco.UF = dadosEmpresa.UF

        formasPagamento = [
            FORMAS_PAGTO_IMPRESSAO(
                DESCRICAO=item.FORMA_PAGTO, VALOR=self.qBase.currency(item.VALOR_PAGO)
            )
            for item in self._pagamentos.listar_por_pedido(filtro.NUMERO_PEDIDO)
        ]

        TOTAL_QTDE = sum([int(item.QTDE) for item in itemsPedido])
        TOTAL_VALOR = float(pedido.TOTAL_PEDIDO) - float(pedido.DESCONTO)
        TROCO = float(pedido.TROCO)
        DESCONTO = float(pedido.DESCONTO)

        if DESCONTO >= pedido.TOTAL_PEDIDO:
            DESCONTO = 0.00

        _nf = []

        qAutorizada = [item for item in pedidoNFe if item.PROCESSADO == 10]

        if len(qAutorizada) > 0:
            _nf.append(str(qAutorizada[0].NUMERO_NF))
        else:
            nNF = 0
            semNumero = pedidoNFe[0].NUMERO_NF == 0

            if pedidoNFe[0].GERAR_DANFE == 1:
                # NUMERO_NF/SERIE_NF (a Nota Fiscal "cheia", separada da
                # NFC-e) existem na tabela real mas não em mapEmpresa —
                # buscadas à parte.
                nfCheia = self._empresas.numero_e_serie_nf(dadosEmpresa.ID_EMPRESA)
                if semNumero:
                    nNF = nfCheia["NUMERO_NF"] + 1
                else:
                    nNF = nfCheia["NUMERO_NF"]
            else:
                if semNumero:
                    nNF = dadosEmpresa.NUMERO_NFCE + 1
                else:
                    nNF = dadosEmpresa.NUMERO_NFCE

            _nf.append(str(nNF))

        _nf.append(dadosEmpresa.SERIE_NFCE)

        items = sorted(itemsPedido, key=lambda e: e.NUMERO_ITEM)

        for item in items:
            produto = self._produtos.buscar_resumo_por_id(item.ID_PRODUTO)

            descricaoProduto = self.qBase.cleanSpecialChars(produto.DESCRICAO_PRODUTO)

            _endereco = f"{dadosEndereco.ENDERECO.strip()}, {dadosEndereco.NUMERO_ENDERECO.strip()}"

            if len(dadosEndereco.ENDERECO) == 0:
                _endereco = dadosEmpresa.ENDERECO.strip()

            _endereco = self.qBase.cleanSpecialChars(_endereco)

            _bairro = self.qBase.cleanSpecialChars(dadosEndereco.BAIRRO)
            _bairro = self.qBase.cleanSpecialChars(_bairro)
            descricaoProduto = self.qBase.cleanSpecialChars(descricaoProduto)

            if len(descricaoProduto) > 120:
                descricaoProduto = descricaoProduto[0: 120]

            _cidade = (
                dadosEmpresa.CIDADE
                if len(dadosEndereco.MUNICIPIO) == 0
                else dadosEndereco.MUNICIPIO.strip()
            )
            _cidade = self.qBase.cleanSpecialChars(_cidade)

            numeroEndereco = (
                "SN"
                if len(dadosEndereco.NUMERO_ENDERECO) > 0
                else dadosEndereco.NUMERO_ENDERECO
            )
            cep = "00000000" if len(dadosEndereco.CEP) == 0 else dadosEndereco.CEP
            uf = dadosEmpresa.UF
            email_cliente = dadosCliente.EMAIL_CLIENTE

            if ID_EMITENTE is None:
                dadosEmpresa.ID_EMPRESA

            idEmpresa = dadosEmpresa.ID_EMPRESA
            cnpjEmitente = self.qBase.onlyNumbers(dadosEmpresa.CNPJ)
            numeroNF = int(_nf[0])
            serieNF = _nf[1]
            serialProtocolo = dadosEmpresa.SERIAL_PROTOCOLO

            _tr = self._transportes.buscar_por_id(pedido.ID_TRANSPORTE)

            if _tr is None:
                _tr = self._transportes.buscar_primeiro()

            uf1 = dadosEmpresa.UF.upper()
            mun1 = dadosEmpresa.CIDADE.upper()

            qIbge = self._municipios.buscar_por_uf_e_nome(uf1, mun1)

            ibgeEmitente = qIbge[0]
            ibgeDestinatario = ibgeEmitente

            _NOME_CLIENTE = self.qBase.maxString(pedido.NOME_CLIENTE, 60)

            if len(_NOME_CLIENTE.strip()) < 6:
                _NOME_CLIENTE = _NOME_CLIENTE.rjust(6, "0")

            # Simplificação: o código anterior buscava o mesmo produto duas
            # vezes seguidas (`produto` e `_produto`, mesma consulta) só pra
            # pegar o ID_PRODUTO de volta — já temos em `item.ID_PRODUTO`.
            _CODIGO_PRODUTO = await self.buscaCodigoProduto(item.ID_PRODUTO)

            _CODIGO_IBGE_EMITENTE = dadosEmpresa.CODIGO_MUNICIPIO_IBGE

            _CODIGO_IBGE_DESTINATARIO = "".join(
                (
                    str(ibgeDestinatario.ID_UF),
                    str(ibgeDestinatario.ID_MUNICIPIO).rjust(5, "0"),
                )
            )

            CPF = pedido.CPF

            Tributo = self._tributos.buscar_por_id(item.ID_TRIBUTO)

            qCFOP = self._cfops.buscar_por_codigo(Tributo.CFOP)

            NATUREZA_OPERACAO = (
                qCFOP[0].DESCRICAO_CFOP if len(qCFOP) > 0 else "VENDA DE MERCADORIA"
            )

            protocolo = await self.extraiProtocoloNF(pedidoNFe[0].XML_NOTA)

            rec = dadosNFCe(
                NUMERO_COMANDA=pedido.NUMERO_PEDIDO,
                DATA_HORA=datetime.strftime(
                    pedido.DATA_HORA + timedelta(hours=3), "%d/%m/%Y %H:%M"
                ),
                NOME_CLIENTE=_NOME_CLIENTE.strip(),
                CPF=self.qBase.onlyNumbers(CPF) if len(CPF) > 0 else "ISENTO",
                IE=""
                if dadosCliente.IE is None
                else self.qBase.onlyNumbers(dadosCliente.IE),
                ENDERECO=_endereco,
                BAIRRO=_bairro,
                CIDADE=_cidade,
                FORMA_PAGTO=formasPagamento,
                NCM=Tributo.NCM,
                CFOP=Tributo.CFOP,
                ID_PRODUTO=int(item.ID_PRODUTO),
                ID_TRIBUTO=int(item.ID_TRIBUTO),
                NATUREZA_OPERACAO=NATUREZA_OPERACAO,
                CODIGO_PRODUTO=_CODIGO_PRODUTO,
                PRODUTO=descricaoProduto,
                QTDE=int(item.QTDE),
                PRECO=float(item.PRECO_UNITARIO),
                TOTAL=int(item.QTDE) * float(item.PRECO_UNITARIO),
                DESCONTO=DESCONTO,
                TOTAL_QTDE=TOTAL_QTDE,
                TOTAL_VALOR=TOTAL_VALOR,
                TROCO=TROCO,
                COMENTARIOS=pedido.INFO_ADICIONAL
                if pedido.INFO_ADICIONAL is not None
                else "",
                TELEFONE=pedido.TELEFONE_CLIENTE
                if pedido.TELEFONE_CLIENTE is not None
                else "",
                ID_EMPRESA=idEmpresa,
                NUMERO_NF=numeroNF,
                SERIE_NF=serieNF,
                CNPJ_EMITENTE=cnpjEmitente,
                SERIAL_PROTOCOLO=serialProtocolo,
                PROTOCOLO=protocolo,
                NOME_EMITENTE=dadosEmpresa.RAZAO_SOCIAL,
                NOME_FANTASIA_EMITENTE=dadosEmpresa.NOME_FANTASIA,
                IE_EMITENTE=dadosEmpresa.IE,
                ENDERECO_EMITENTE=dadosEmpresa.ENDERECO.strip(),
                BAIRRO_EMITENTE=dadosEmpresa.BAIRRO.strip(),
                CEP_EMITENTE=dadosEmpresa.CEP,
                CIDADE_EMITENTE=dadosEmpresa.CIDADE.strip(),
                UF_EMITENTE=dadosEmpresa.UF,
                CRT_EMITENTE=dadosEmpresa.CRT,
                TELEFONE_EMITENTE=dadosEmpresa.TELEFONE.strip(),
                NUMERO_ENDERECO="SN" if len(numeroEndereco) == 0 else numeroEndereco,
                CEP=cep,
                UF=uf,
                ENDERECO_TRANSPORTE=self.qBase.cleanSpecialChars(_tr.ENDERECO),
                EMAIL_CLIENTE=email_cliente,
                UF_TRANSPORTE=_tr.UF,
                IE_TRANSPORTE=self.qBase.onlyNumbers(_tr.IE),
                CNPJ_TRANSPORTE=self.qBase.onlyNumbers(_tr.CNPJ),
                CIDADE_TRANSPORTE=self.qBase.cleanSpecialChars(_tr.CIDADE),
                NOME_FANTASIA_TRANSPORTE=self.qBase.cleanSpecialChars(
                    _tr.NOME_TRANSPORTE
                ),
                NOME_TRANSPORTE=self.qBase.cleanSpecialChars(_tr.NOME_TRANSPORTE),
                XML=pedidoNFe[0].XML_NOTA,
                CHAVE=pedidoNFe[0].CHAVE_ACESSO_NF
                if pedidoNFe[0].CHAVE_ACESSO_NF is not None
                else "",
                CODIGO_IBGE_EMITENTE=_CODIGO_IBGE_EMITENTE,
                CODIGO_IBGE_DESTINATARIO=_CODIGO_IBGE_DESTINATARIO,
                DATA_AUTORIZACAO_NFCE=pedidoNFe[0].DATA_AUTORIZACAO_NFCE,
                ASSINATURA_NFCE=pedidoNFe[0].ASSINATURA_NFCE,
                CST=Tributo.CST,
                ALIQ_ICMS=Tributo.ALIQ_ICMS,
                ALIQ_INTERNA_ICMS=Tributo.ALIQ_INTERNA_ICMS,
                MODO_BASE_CALCULO_ICMS_ST=Tributo.MODO_BASE_CALCULO_ICMS_ST,
                IVA=Tributo.IVA,
                CST_IPI=Tributo.CST_IPI,
                ALIQ_IPI=Tributo.ALIQ_IPI,
                CST_PIS=Tributo.CST_PIS,
                ALIQ_PIS=Tributo.ALIQ_PIS,
                CST_COFINS=Tributo.CST_COFINS,
                ALIQ_COFINS=Tributo.ALIQ_COFINS,
                CEST="" if Tributo.CEST is None else Tributo.CEST,
                CBS=Tributo.CBS if Tributo.CBS is not None else 0,
                IBS=Tributo.IBS if Tributo.IBS is not None else 0,
                ISERV=Tributo.ISERV if Tributo.ISERV is not None else 0,
                FATURAR_TAXA_ENTREGA=int(dadosEmpresa.FATURAR_TAXA_ENTREGA),
                pFCP=0.00
                if Tributo.PERCENTUAL_FCP is None
                else float(Tributo.PERCENTUAL_FCP),
                GERAR_DANFE=0
                if pedidoNFe[0].GERAR_DANFE is None
                else int(pedidoNFe[0].GERAR_DANFE),
                DADOS_ADICIONAIS=pedido.INFO_ADICIONAL
                if pedido.INFO_ADICIONAL is not None
                else "",
                DEVOLUCAO=False,
                CHAVE_NF_DEVOLUCAO="",
                TAXA_ENTREGA=float(pedido.TAXA_ENTREGA),
                vBCSTRet=0.00,
                vICMSRet=0.00,
                pST=Tributo.ALIQ_ICMS,
                ID_TRANSPORTE=int(pedido.ID_TRANSPORTE)
                if pedido.ID_TRANSPORTE is not None
                else _tr.ID_TRANSPORTE,
            )

            retorno.append(rec)

        return retorno

    async def getNumeroNFCe(self, SERIE_NF: str) -> int:
        query = self._numerosNota.buscar_por_serie(SERIE_NF)

        if not any(query):
            self._numerosNota.inserir(SERIE_NF)

            return 1

        retorno = query[0].NUMERO_NF + 1

        return retorno

    async def getNFCe(self, filtro: filtroNFCe) -> List[dadosNFCe]:
        retorno = []

        pedido = self._pedidos.buscar_por_numero(filtro.NUMERO_PEDIDO)

        itemsPedido = self._itensPedido.listar_por_pedido(filtro.NUMERO_PEDIDO)

        pedidoNFe = self._pedidoNFe.listar_dados_autorizados(filtro.NUMERO_PEDIDO)

        dadosEmpresa = self._empresas.buscar_padrao()

        ID_CLIENTE = pedido.ID_CLIENTE
        ID_ENDERECO = pedido.ID_ENDERECO
        ID_EMITENTE = dadosEmpresa.ID_EMPRESA

        dadosCliente = self._clientes.buscar_por_id(ID_CLIENTE)

        dadosEndereco = self._enderecos.buscar_por_id(ID_ENDERECO)

        if dadosEndereco.ENDERECO is None or len(dadosEndereco.ENDERECO.strip()) == 0:
            dadosEndereco.ENDERECO = dadosEmpresa.ENDERECO
            dadosEndereco.NUMERO_ENDERECO = ""
            dadosEndereco.COMPLEMENTO_ENDERECO = ""
            dadosEndereco.CEP = dadosEmpresa.CEP
            dadosEndereco.BAIRRO = dadosEmpresa.BAIRRO
            dadosEndereco.MUNICIPIO = dadosEmpresa.CIDADE
            dadosEndereco.UF = dadosEmpresa.UF

        logradouroEmitente = dadosEmpresa.ENDERECO.split(',')
        numeroEnderecoEmitente = 'SN'
        enderecoEmitente = logradouroEmitente[0].strip()

        if len(logradouroEmitente) > 1:
            numeroEnderecoEmitente = self.qBase.onlyNumbers(logradouroEmitente[1]).strip()

        if len(numeroEnderecoEmitente) == 0:
            numeroEnderecoEmitente = 'SN'

        formasPagamento = [
            FORMAS_PAGTO_IMPRESSAO(
                DESCRICAO=item.FORMA_PAGTO, VALOR=self.qBase.currency(item.VALOR_PAGO)
            )
            for item in self._pagamentos.listar_por_pedido(filtro.NUMERO_PEDIDO)
        ]

        TOTAL_QTDE = sum([int(item.QTDE) for item in itemsPedido])
        TOTAL_VALOR = float(pedido.TOTAL_PEDIDO) - float(pedido.DESCONTO)
        TROCO = float(pedido.TROCO)
        DESCONTO = float(pedido.DESCONTO)

        if DESCONTO >= pedido.TOTAL_PEDIDO:
            DESCONTO = 0.00

        maxNF = await self.getNumeroNFCe(
            str(filtro.SERIE_NF)
        )

        items = sorted(itemsPedido, key=lambda e: e.NUMERO_ITEM)

        for item in items:
            produto = self._produtos.buscar_resumo_por_id(item.ID_PRODUTO)

            descricaoProduto = self.qBase.cleanSpecialChars(produto.DESCRICAO_PRODUTO)

            _endereco = f"{dadosEndereco.ENDERECO.strip()}, {dadosEndereco.NUMERO_ENDERECO.strip()}"

            if len(dadosEndereco.ENDERECO) == 0:
                _endereco = dadosEmpresa.ENDERECO.strip()

            _endereco = self.qBase.cleanSpecialChars(_endereco)

            _bairro = self.qBase.cleanSpecialChars(dadosEndereco.BAIRRO)
            _bairro = self.qBase.cleanSpecialChars(_bairro)
            descricaoProduto = self.qBase.cleanSpecialChars(descricaoProduto)

            if len(descricaoProduto) > 120:
                descricaoProduto = descricaoProduto[0: 120]

            _cidade = (
                dadosEmpresa.CIDADE
                if len(dadosEndereco.MUNICIPIO) == 0
                else dadosEndereco.MUNICIPIO.strip()
            )
            _cidade = self.qBase.cleanSpecialChars(_cidade)

            cep = "00000000" if len(dadosEndereco.CEP) == 0 else dadosEndereco.CEP
            uf = dadosEmpresa.UF
            email_cliente = dadosCliente.EMAIL_CLIENTE

            if ID_EMITENTE is None:
                dadosEmpresa.ID_EMPRESA

            idEmpresa = dadosEmpresa.ID_EMPRESA
            cnpjEmitente = self.qBase.onlyNumbers(dadosEmpresa.CNPJ)
            serialProtocolo = dadosEmpresa.SERIAL_PROTOCOLO

            _tr = self._transportes.buscar_por_id(pedido.ID_TRANSPORTE)

            if _tr is None:
                _tr = self._transportes.buscar_primeiro()

            uf1 = dadosEmpresa.UF.upper()
            mun1 = dadosEmpresa.CIDADE.upper()

            qIbge = self._municipios.buscar_por_uf_e_nome(uf1, mun1)

            ibgeEmitente = qIbge[0]
            ibgeDestinatario = ibgeEmitente

            _NOME_CLIENTE = self.qBase.maxString(pedido.NOME_CLIENTE, 60)

            if len(_NOME_CLIENTE.strip()) < 6:
                _NOME_CLIENTE = _NOME_CLIENTE.rjust(6, "0")

            _CODIGO_PRODUTO = await self.buscaCodigoProduto(item.ID_PRODUTO)

            _CODIGO_IBGE_EMITENTE = dadosEmpresa.CODIGO_MUNICIPIO_IBGE

            _CODIGO_IBGE_DESTINATARIO = "".join(
                (
                    str(ibgeDestinatario.ID_UF),
                    str(ibgeDestinatario.ID_MUNICIPIO).rjust(5, "0"),
                )
            )

            CPF = pedido.CPF

            Tributo = self._tributos.buscar_por_id(item.ID_TRIBUTO)

            qCFOP = self._cfops.buscar_por_codigo(Tributo.CFOP)

            NATUREZA_OPERACAO = (
                qCFOP[0].DESCRICAO_CFOP if len(qCFOP) > 0 else "VENDA DE MERCADORIA"
            )

            recNF = pedidoNFe[0] if any(pedidoNFe) else None

            protocolo = recNF.PROTOCOLO_AUTORIZACAO if recNF is not None else ''

            rec = dadosNFCe(
                NUMERO_COMANDA=pedido.NUMERO_PEDIDO,
                DATA_HORA=datetime.strftime(
                    datetime.now(), "%d/%m/%Y %H:%M"
                ),
                NOME_CLIENTE=_NOME_CLIENTE.strip(),
                CPF=self.qBase.onlyNumbers(CPF) if len(CPF) > 0 else "ISENTO",
                IE=""
                if dadosCliente.IE is None
                else self.qBase.onlyNumbers(dadosCliente.IE),
                ENDERECO=_endereco,
                BAIRRO=_bairro,
                CIDADE=_cidade,
                FORMA_PAGTO=formasPagamento,
                NCM=Tributo.NCM,
                CFOP=Tributo.CFOP,
                ID_PRODUTO=int(item.ID_PRODUTO),
                ID_TRIBUTO=int(item.ID_TRIBUTO),
                NATUREZA_OPERACAO=NATUREZA_OPERACAO,
                CODIGO_PRODUTO=_CODIGO_PRODUTO,
                PRODUTO=descricaoProduto,
                QTDE=int(item.QTDE),
                PRECO=float(item.PRECO_UNITARIO),
                TOTAL=int(item.QTDE) * float(item.PRECO_UNITARIO),
                DESCONTO=DESCONTO,
                TOTAL_QTDE=TOTAL_QTDE,
                TOTAL_VALOR=TOTAL_VALOR,
                TROCO=TROCO,
                COMENTARIOS=pedido.INFO_ADICIONAL
                if pedido.INFO_ADICIONAL is not None
                else "",
                TELEFONE=pedido.TELEFONE_CLIENTE
                if pedido.TELEFONE_CLIENTE is not None
                else "",
                ID_EMPRESA=idEmpresa,
                NUMERO_NF=maxNF,
                SERIE_NF=str(filtro.SERIE_NF),
                CNPJ_EMITENTE=cnpjEmitente,
                SERIAL_PROTOCOLO=serialProtocolo,
                PROTOCOLO=protocolo,
                NOME_EMITENTE=dadosEmpresa.RAZAO_SOCIAL,
                NOME_FANTASIA_EMITENTE=dadosEmpresa.NOME_FANTASIA,
                IE_EMITENTE=dadosEmpresa.IE,
                ENDERECO_EMITENTE=enderecoEmitente,
                BAIRRO_EMITENTE=dadosEmpresa.BAIRRO.strip(),
                CEP_EMITENTE=self.qBase.onlyNumbers(dadosEmpresa.CEP),
                CIDADE_EMITENTE=dadosEmpresa.CIDADE.strip(),
                UF_EMITENTE=dadosEmpresa.UF,
                CRT_EMITENTE=dadosEmpresa.CRT,
                TELEFONE_EMITENTE=dadosEmpresa.TELEFONE.strip(),
                NUMERO_ENDERECO=numeroEnderecoEmitente,
                CEP=cep,
                UF=uf,
                ENDERECO_TRANSPORTE=self.qBase.cleanSpecialChars(_tr.ENDERECO),
                EMAIL_CLIENTE=email_cliente,
                UF_TRANSPORTE=_tr.UF,
                IE_TRANSPORTE=self.qBase.onlyNumbers(_tr.IE),
                CNPJ_TRANSPORTE=self.qBase.onlyNumbers(_tr.CNPJ),
                CIDADE_TRANSPORTE=self.qBase.cleanSpecialChars(_tr.CIDADE),
                NOME_FANTASIA_TRANSPORTE=self.qBase.cleanSpecialChars(
                    _tr.NOME_TRANSPORTE
                ),
                NOME_TRANSPORTE=self.qBase.cleanSpecialChars(_tr.NOME_TRANSPORTE),
                XML=recNF.XML_NOTA if recNF is not None else '',
                CHAVE=recNF.CHAVE_ACESSO_NF if recNF is not None else '',
                CODIGO_IBGE_EMITENTE=_CODIGO_IBGE_EMITENTE,
                CODIGO_IBGE_DESTINATARIO=_CODIGO_IBGE_DESTINATARIO,
                DATA_AUTORIZACAO_NFCE='',
                ASSINATURA_NFCE='',
                CST=Tributo.CST,
                ALIQ_ICMS=Tributo.ALIQ_ICMS,
                ALIQ_INTERNA_ICMS=Tributo.ALIQ_INTERNA_ICMS,
                MODO_BASE_CALCULO_ICMS_ST=Tributo.MODO_BASE_CALCULO_ICMS_ST,
                IVA=Tributo.IVA,
                CST_IPI=Tributo.CST_IPI,
                ALIQ_IPI=Tributo.ALIQ_IPI,
                CST_PIS=Tributo.CST_PIS,
                ALIQ_PIS=Tributo.ALIQ_PIS,
                CST_COFINS=Tributo.CST_COFINS,
                ALIQ_COFINS=Tributo.ALIQ_COFINS,
                CEST="" if Tributo.CEST is None else Tributo.CEST,
                CBS=Tributo.CBS if Tributo.CBS is not None else 0,
                IBS=Tributo.IBS if Tributo.IBS is not None else 0,
                ISERV=Tributo.ISERV if Tributo.ISERV is not None else 0,
                FATURAR_TAXA_ENTREGA=int(dadosEmpresa.FATURAR_TAXA_ENTREGA),
                pFCP=0.00
                if Tributo.PERCENTUAL_FCP is None
                else float(Tributo.PERCENTUAL_FCP),
                GERAR_DANFE=0,
                DADOS_ADICIONAIS=pedido.INFO_ADICIONAL
                if pedido.INFO_ADICIONAL is not None
                else "",
                DEVOLUCAO=False,
                CHAVE_NF_DEVOLUCAO="",
                TAXA_ENTREGA=0.00 if int(dadosEmpresa.FATURAR_TAXA_ENTREGA) == 0 else float(pedido.TAXA_ENTREGA),
                vBCSTRet=0.00,
                vICMSRet=0.00,
                pST=Tributo.ALIQ_ICMS,
                ID_TRANSPORTE=int(pedido.ID_TRANSPORTE)
                if pedido.ID_TRANSPORTE is not None
                else _tr.ID_TRANSPORTE,
            )

            retorno.append(rec)

        return retorno

    async def extraiProtocoloNF(self, XML: str) -> str:
        try:
            prot = "<nProt>"
            prot1 = "</nProt>"

            retorno = XML[XML.index(prot) :]

            retorno = self.qBase.onlyNumbers(retorno[len(prot) : retorno.index(prot1)])

            return retorno
        except:
            return ""

    async def buscaCodigoProduto(self, ID_PRODUTO: int) -> str:
        retorno = "SEM GTIN"

        codigoPdv = self._produtos.codigo_pdv_por_id(ID_PRODUTO)

        if codigoPdv is not None:
            retorno = codigoPdv if len(codigoPdv) >= 8 else "SEM GTIN"

        return retorno.strip()

    async def finalizaNFCe(self, dados: NFe_Finalizada):
        q = self._pedidoNFe.listar_por_pedido(dados.NUMERO_PEDIDO)

        if len(q) == 0:
            return

        autorizada = 10 if len(dados.ASSINATURA_NFC) > 0 else 0

        if autorizada == 0:
            return

        self._pedidoNFe.atualizar_finalizacao(
            dados.NUMERO_PEDIDO,
            dados.XML,
            dados.NUMERO_NF,
            dados.CHAVE_ACESSO,
            dados.ASSINATURA_NFC,
            dados.DATA_AUTORIZACAO,
            autorizada,
        )

    async def listTributo(self) -> List[listaDeTributo]:
        query = self._tributos.listar()

        lista = [
            listaDeTributo(
                ID_TRIBUTO=item.ID_TRIBUTO,
                NOME_OPERACAO=item.NOME_OPERACAO
            )
            for item in query
        ]

        retorno = sorted(lista, key=lambda e: e.NOME_OPERACAO)

        return retorno

    async def listTributoCompleto(self) -> List[tributoCompleto]:
        # Tabela de tributos inteira (NCM/CFOP/CST/alíquotas), sem filtro por
        # pedido — usada pro frontend cachear localmente e montar a NFC-e
        # sem depender de um pedido já salvo (Zeus/nfceZeus.py).
        query = self._tributos.listar()

        return [
            tributoCompleto(
                ID_TRIBUTO=item.ID_TRIBUTO,
                NCM=item.NCM or '',
                CFOP=item.CFOP or '',
                CST=item.CST or '',
                ALIQ_ICMS=float(item.ALIQ_ICMS) if item.ALIQ_ICMS is not None else 0.0,
                CST_PIS=item.CST_PIS or '',
                ALIQ_PIS=float(item.ALIQ_PIS) if item.ALIQ_PIS is not None else 0.0,
                CST_COFINS=item.CST_COFINS or '',
                ALIQ_COFINS=float(item.ALIQ_COFINS) if item.ALIQ_COFINS is not None else 0.0,
                CEST=item.CEST or '',
                NOME_OPERACAO=item.NOME_OPERACAO or ''
            )
            for item in query
        ]

    async def listPedidosParaFaturar(self, filtro: filtroFaturamentoAutomatico) -> List[pedidoParaFaturar]:
        # Usado pelo bot em botFaturamento/ (processo separado do app
        # principal) — devolve só os pedidos que devem ser faturados
        # AGORA, já aplicando: STATUS_PEDIDO=3, dentro do mês corrente,
        # ainda sem NFC-e autorizada, filtro de forma de pagamento/origem,
        # e o teto proporcional ao dia do mês (VALOR_MAXIMO_MENSAL /
        # dias do mês * dia atual, menos o que já foi faturado no mês).
        # Mais antigos primeiro; para no primeiro que não couber no
        # orçamento restante (os que sobrarem voltam no próximo ciclo).
        import calendar

        agora = datetime.now()
        primeiroDiaMes = agora.replace(hour=0, minute=0, second=0, microsecond=0).replace(day=1)
        diasNoMes = calendar.monthrange(agora.year, agora.month)[1]

        candidatos = self._pedidos.listar_candidatos_faturamento(
            primeiroDiaMes, filtro.ORIGEM if filtro.ORIGEM else None
        )

        if filtro.FORMAS_PAGTO:
            permitidas = set(filtro.FORMAS_PAGTO)
            filtrados = []

            for pedidoItem in candidatos:
                formasDoPedido = {
                    item.FORMA_PAGTO
                    for item in self._pagamentos.listar_por_pedido(pedidoItem.NUMERO_PEDIDO)
                }

                # Só entra se TODAS as formas de pagamento desse pedido
                # estiverem na lista permitida (pedido misto com uma forma
                # não-permitida fica de fora).
                if formasDoPedido and formasDoPedido.issubset(permitidas):
                    filtrados.append(pedidoItem)

            candidatos = filtrados

        totalJaFaturado = float(self._pedidos.somar_faturado_no_mes(primeiroDiaMes) or 0)

        valorDiario = filtro.VALOR_MAXIMO_MENSAL / diasNoMes
        tetoAcumulado = valorDiario * agora.day
        orcamentoDisponivel = max(0.0, tetoAcumulado - totalJaFaturado)

        retorno = []
        acumulado = 0.0

        for pedidoItem in candidatos:
            total = float(pedidoItem.TOTAL_PEDIDO or 0)

            if acumulado + total > orcamentoDisponivel:
                break

            acumulado += total

            retorno.append(pedidoParaFaturar(
                NUMERO_PEDIDO=pedidoItem.NUMERO_PEDIDO,
                DATA_HORA=pedidoItem.DATA_HORA.strftime('%d/%m/%Y %H:%M'),
                TOTAL_PEDIDO=total,
            ))

        return retorno

    async def buscaIbgeMunicipio(self, filtro: filtroMunicipio) -> str:
        # Usado pelo Zeus/nfceZeus.py (emissão de NF-e modelo 55) pra
        # resolver o código IBGE do MUNICÍPIO do destinatário — mesma
        # consulta que getNFCe já faz pro emitente, só que devolvendo
        # vazio (não IndexError) quando não encontra, porque aqui é
        # esperado que às vezes não encontre (tb_municipio não é a tabela
        # cheia do IBGE, só o que já foi usado/cadastrado).
        query = self._municipios.buscar_primeiro_por_uf_e_nome(
            filtro.UF.strip().upper(), filtro.MUNICIPIO.strip().upper()
        )

        if query is None:
            return ""

        return f"{int(query.ID_UF)}{str(int(query.ID_MUNICIPIO)).rjust(5, '0')}"

    async def listItensParaNFe(self, filtro: filtroNumeroPedido) -> List[itemsNFe]:
        query = self._itensPedido.listar_por_pedido(filtro.NUMERO_PEDIDO)

        lista = [
            itemsNFe(
                NUMERO_ITEM=item.NUMERO_ITEM,
                DESCRICAO_PRODUTO=self.getDescricaoProduto(item.ID_PRODUTO),
                QTDE=int(item.QTDE),
                PRECO=float(item.PRECO_UNITARIO),
                TOTAL=float(item.VALOR_TOTAL),
                ID_TRIBUTO=int(item.ID_TRIBUTO)
            )
            for item in query
        ]

        return lista

    async def setTributoItemPedido(self, item: itemTributo):
        self._itensPedido.atualizar_tributo(item.NUMERO_ITEM, item.ID_TRIBUTO)

    async def conferePagamento(self, record: listaDePagamentos):
        self._pagamentos.atualizar_valor_pago_stone(record.ID_PAGAMENTO, record.TOTAL_PAGO)

    def getClientePedido(self, idCliente: int, idEndereco: int, conn=None) -> clientePedido:
        cliente = self._clientes.buscar_dados_pedido(idCliente, idEndereco, conn=conn)

        retorno = clientePedido(
            CPF = cliente.CPF,
            NOME_CLIENTE = cliente.NOME_CLIENTE,
            ENDERECO = cliente.ENDERECO,
            NUMERO_ENDERECO = cliente.NUMERO_ENDERECO,
            COMPLEMENTO = cliente.COMPLEMENTO_ENDERECO,
            BAIRRO = cliente.BAIRRO,
            TELEFONE = cliente.TELEFONE_CLIENTE,
            CIDADE = cliente.MUNICIPIO,
            UF = cliente.UF,
            EMAIL = cliente.EMAIL_CLIENTE
        )

        return retorno

    async def getDadosEmitente(self) -> dadosEmitente:
        query = self._empresas.buscar_padrao()

        retorno = dadosEmitente(
            RAZAO_SOCIAL=query.RAZAO_SOCIAL,
            NOME_FANTASIA=query.NOME_FANTASIA,
            ENDERECO = ' '.join((
                query.ENDERECO,
                query.BAIRRO,
                query.CIDADE,
                query.UF
            )),
            TELEFONE = query.TELEFONE
        )

        return retorno

    async def finalizaNFCe_V2(self, nota: notaAutorizada):
        with db.transaction() as conn:
            self._pedidoNFe.inserir(
                numero_pedido=nota.NUMERO_PEDIDO,
                numero_nf=nota.NUMERO_NF,
                serie_nf=nota.SERIE_NF,
                processado=10,
                chave_acesso_nf=nota.CHAVE_ACESSO,
                protocolo_autorizacao=nota.PROTOCOLO_AUTORIZACAO,
                xml_nota=nota.XML_AUTORIZADO,
                conn=conn,
            )

            self._numerosNota.atualizar_numero(nota.SERIE_NF, nota.NUMERO_NF, conn=conn)

    async def getEnderecoDoPedido(self, filtro: filtroNumeroPedido) -> str:
        pedido = self._pedidos.buscar_por_numero(filtro.NUMERO_PEDIDO)

        if pedido is None:
            return ''

        endereco = self._enderecos.buscar_por_id(pedido.ID_ENDERECO)

        retorno = ''

        if endereco is not None:
            retorno = ''.join((
                endereco.ENDERECO, ', \n',
                endereco.NUMERO_ENDERECO, ' - ',
                endereco.COMPLEMENTO_ENDERECO, '\n',
                endereco.BAIRRO, '\n',
                endereco.CEP, '\n',
                endereco.MUNICIPIO, ' - ',
                endereco.UF
            ))

        return retorno

    def confereEstoque(self, items: List[produtoIDQtde]) -> str:
        if not self.prefs.VENDER_SEM_ESTOQUE:
            semEstoque = self.checaEstoqueDopedido(items)

            if len(semEstoque) > 0:
                retorno = 'O item: '

                if ',' in semEstoque:
                    retorno = 'Os items: '
                return f'{retorno}[{semEstoque}] não tem saldo para venda'

        return ''

    def buscaSaldoProduto(self, filtro: filtroProduto) -> float:
        entradas = self._estoque.soma_qtde(filtro.ID_PRODUTO, 0)
        saidas = self._estoque.soma_qtde(filtro.ID_PRODUTO, 1)

        e = 0 if entradas is None else entradas
        s = 0 if saidas is None else saidas

        saldo = float(e) - float(s)

        return saldo

    def getDescricaoProdutos(self, items: List[produtoIDQtde]) -> List[comboProduto]:
        ids = [item.ID_PRODUTO for item in items]

        query = self._produtos.listar_descricoes_por_ids(ids)

        retorno = [
            comboProduto(
                ID_PRODUTO=item.ID_PRODUTO,
                DESCRICAO_PRODUTO=item.DESCRICAO_PRODUTO
            )
            for item in query
        ]

        return retorno

    def checaEstoqueDopedido(self, itemsPedido: List[produtoIDQtde]) -> str:

        retorno = []

        items = self.getDescricaoProdutos(itemsPedido)

        for item in itemsPedido:
            saldo = self.buscaSaldoProduto(
                filtroProduto(
                    ID_PRODUTO=item.ID_PRODUTO
                )
            )

            if saldo < item.QTDE:
                retorno.append(
                    list(filter(lambda e: e.ID_PRODUTO == item.ID_PRODUTO, items))[0].DESCRICAO_PRODUTO
                )

        return ', '.join(retorno)

    def gravaDados_PagamentoAutorizado(self, dados: pagamentoAutorizado):
        dtAutorizacao = datetime.today()

        try:
            dtAutorizacao = datetime.strptime(dados.DATA_AUTORIZACAO, "%Y-%m-%dT%H:%M:%S.%fZ")
        except:
            pass

        self._pagamentos.atualizar_autorizacao(
            dados.NUMERO_PEDIDO,
            dados.VALOR_PAGO,
            dados.NSU,
            dtAutorizacao,
            dados.BANDEIRA,
            dados.ID_TERMINAL,
        )
