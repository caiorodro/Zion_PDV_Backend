from typing import List

from base.qBase import qBase
from infra.repositories.clienteRepository import ClienteRepository
from infra.repositories.enderecoClienteRepository import EnderecoClienteRepository
from infra.repositories.pedidoRepository import PedidoRepository, PEDIDO_NAO_ENCONTRADO
from infra.repositories.transporteRepository import TransporteRepository
from models.Cliente_Endereco_Transporte import Cliente_Endereco_Transporte
from models.comboCliente import comboCliente
from models.comboClienteEndereco import comboClienteEndereco
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
        self._clientes = ClienteRepository()
        self._enderecos = EnderecoClienteRepository()
        self._transportes = TransporteRepository()
        self._pedidos = PedidoRepository()

    async def buscaCliente(self, filtro: filtroCliente) -> List[comboCliente]:
        query = self._clientes.buscar_por_cpf(filtro.FILTRO)

        if len(query) == 0:
            query = self._clientes.buscar_por_telefone(filtro.FILTRO)

        if len(query) == 0:
            query = self._clientes.buscar_por_nome(filtro.FILTRO)

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
        query = self._enderecos.buscar(filtro.ID_CLIENTE, filtro.FILTRO)

        retorno = [
            comboEndereco(
                ID_CLIENTE=item.ID_CLIENTE,
                ID_ENDERECO=item.ID_ENDERECO,
                ENDERECO=item.ENDERECO,
                NUMERO_ENDERECO=item.NUMERO_ENDERECO,
                COMPLEMENTO_ENDERECO=item.COMPLEMENTO_ENDERECO,
                BAIRRO=item.BAIRRO,
                CEP=item.CEP,
                CIDADE=item.MUNICIPIO,
                UF=item.UF
            ).__dict__
            for item in query
        ]

        return retorno

    async def getAllAddresses(self) -> List[comboClienteEndereco]:
        query = self._enderecos.listar_todos_com_cliente()

        retorno = [
            comboClienteEndereco(
                ID_ENDERECO=item["ID_ENDERECO"],
                ID_CLIENTE=item["ID_CLIENTE"],
                NOME_CLIENTE=item["NOME_CLIENTE"],
                CPF=item["CPF"] if item["CPF"] is not None else "",
                TELEFONE_CLIENTE=item["TELEFONE_CLIENTE"] if item["TELEFONE_CLIENTE"] is not None else "",
                ENDERECO=item["ENDERECO"],
                NUMERO_ENDERECO=item["NUMERO_ENDERECO"],
                COMPLEMENTO_ENDERECO=item["COMPLEMENTO_ENDERECO"],
                BAIRRO=item["BAIRRO"],
                CEP=item["CEP"],
                CIDADE=item["MUNICIPIO"],
                UF=item["UF"]
            ).__dict__
            for item in query
        ]

        retorno = sorted(retorno, key=lambda e: e['NOME_CLIENTE'])

        return retorno

    async def get_Dados_Cliente_Endereco_Transporte(
        self, dados: Cliente_Endereco_Transporte
    ) -> Cliente_Endereco_Transporte:
        cliente = self._clientes.buscar_por_id(dados.ID_CLIENTE)
        endereco = self._enderecos.buscar_por_id(dados.ID_ENDERECO)
        transporte = self._transportes.buscar_por_id(dados.ID_TRANSPORTE)

        e1 = (0, "")
        t1 = (0, "")

        if endereco is not None:
            e1 = (
                endereco.ID_ENDERECO,
                " ".join(
                    (
                        endereco.ENDERECO,
                        endereco.NUMERO_ENDERECO,
                        endereco.COMPLEMENTO_ENDERECO,
                    )
                ),
            )

        if transporte is not None:
            t1 = (transporte.ID_TRANSPORTE, transporte.NOME_TRANSPORTE)

        retorno = Cliente_Endereco_Transporte(
            ID_CLIENTE=cliente.ID_CLIENTE,
            NOME_CLIENTE="".join(
                (cliente.NOME_CLIENTE, f", Tel: {cliente.TELEFONE_CLIENTE}")
            ),
            ID_ENDERECO=e1[0],
            ENDERECO=e1[1],
            ID_TRANSPORTE=t1[0],
            NOME_TRANSPORTE=t1[1],
        )

        return retorno

    async def getFiscalCliente(self, filtro: filtroNumeroPedido) -> fiscalCliente:
        cpf = self._pedidos.cpf_por_numero_pedido(int(filtro.NUMERO_PEDIDO))

        return fiscalCliente(CPF="" if cpf is PEDIDO_NAO_ENCONTRADO else cpf)

    async def gravaDadosCliente(self, dados: editCliente):
        cliente = dados.cliente
        endereco = dados.endereco[0]

        idCliente = cliente.ID_CLIENTE

        if cliente.ID_CLIENTE == 0:
            idCliente = self._clientes.inserir(cliente)
        elif cliente.ID_CLIENTE > 0:
            self._clientes.atualizar(cliente)

        if endereco.ID_ENDERECO == 0:
            self._enderecos.inserir(endereco, idCliente)
        elif endereco.ID_ENDERECO > 0:
            self._enderecos.atualizar(endereco, idCliente)

    async def listaCliente(self, filtro: filtroCliente) -> List[listaDeCliente]:
        query = self._clientes.listar(filtro.FILTRO)

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
        rec = self._clientes.buscar_por_id(int(filtro.FILTRO))

        if rec is None:
            raise Exception("Cliente não encontrado na base")

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

        query2 = self._enderecos.listar_por_cliente(int(filtro.FILTRO))

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
