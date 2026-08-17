"""Acesso a dados da tabela tb_cliente."""

from types import SimpleNamespace
from typing import List, Optional

from infra import db
from base.mapTable import mapCliente
from models.dadosCliente import dadosCliente

_COLUNAS = (
    "ID_CLIENTE, NOME_CLIENTE, CPF, ENDERECO_CLIENTE, NUMERO_ENDERECO, COMPLEMENTO_ENDERECO, "
    "BAIRRO_CLIENTE, CEP_CLIENTE, MUNICIPIO_CLIENTE, UF_CLIENTE, TELEFONE_CLIENTE, EMAIL_CLIENTE, "
    "ID_EMPRESA, IE, BLACK_LIST, NOME_FANTASIA_CLIENTE, OBS_CLIENTE, TAXA_ENTREGA, NICKNAME, "
    "METADE, UM_TERCO, SENHA_CLIENTE"
)


class ClienteRepository:
    def buscar_por_cpf(self, cpf: str) -> List[mapCliente]:
        sql = f"SELECT {_COLUNAS} FROM tb_cliente WHERE CPF = %s"
        return db.query_all(sql, (cpf,), map_cls=mapCliente)

    def buscar_por_telefone(self, telefone: str) -> List[mapCliente]:
        sql = f"SELECT {_COLUNAS} FROM tb_cliente WHERE TELEFONE_CLIENTE = %s"
        return db.query_all(sql, (telefone,), map_cls=mapCliente)

    def buscar_por_nome(self, nome: str, limite: int = 150) -> List[mapCliente]:
        sql = f"SELECT {_COLUNAS} FROM tb_cliente WHERE NOME_CLIENTE LIKE %s LIMIT %s"
        return db.query_all(sql, (f"%{nome}%", limite), map_cls=mapCliente)

    def buscar_por_id(self, id_cliente: int) -> Optional[mapCliente]:
        sql = f"SELECT {_COLUNAS} FROM tb_cliente WHERE ID_CLIENTE = %s"
        return db.query_one(sql, (id_cliente,), map_cls=mapCliente)

    def buscar_dados_pedido(self, id_cliente: int, id_endereco: int, conn=None) -> Optional[SimpleNamespace]:
        """Junta tb_cliente + tb_endereco_cliente para o cabeçalho de um
        pedido — usado por views/pedido.py (getClientePedido)."""
        sql = (
            "SELECT c.CPF, c.NOME_CLIENTE, e.ENDERECO, e.NUMERO_ENDERECO, e.COMPLEMENTO_ENDERECO, "
            "e.BAIRRO, c.TELEFONE_CLIENTE, e.MUNICIPIO, e.UF, c.EMAIL_CLIENTE "
            "FROM tb_cliente c INNER JOIN tb_endereco_cliente e ON c.ID_CLIENTE = e.ID_CLIENTE "
            "WHERE e.ID_CLIENTE = %s AND e.ID_ENDERECO = %s LIMIT 1"
        )
        params = (id_cliente, id_endereco)
        if conn is not None:
            return db.query_one_in(conn, sql, params, map_cls=SimpleNamespace)
        return db.query_one(sql, params, map_cls=SimpleNamespace)

    def nome_por_id(self, id_cliente: int, conn=None) -> str:
        """Devolve "" se o cliente não existir (não levanta erro) — mesmo
        comportamento do código anterior."""
        sql = "SELECT NOME_CLIENTE FROM tb_cliente WHERE ID_CLIENTE = %s"
        row = db.query_one_in(conn, sql, (id_cliente,)) if conn is not None else db.query_one(sql, (id_cliente,))
        return row["NOME_CLIENTE"] if row else ""

    def buscar_consumidor_final(self, conn=None) -> Optional[mapCliente]:
        sql = f"SELECT {_COLUNAS} FROM tb_cliente WHERE NOME_CLIENTE LIKE %s LIMIT 1"
        params = ("%CONSUMIDOR FINAL%",)
        if conn is not None:
            return db.query_one_in(conn, sql, params, map_cls=mapCliente)
        return db.query_one(sql, params, map_cls=mapCliente)

    def inserir_consumidor_final(
        self,
        endereco_empresa: str,
        numero_endereco_empresa: str,
        complemento_endereco_empresa: str,
        bairro_empresa: str,
        cep_empresa: str,
        municipio_empresa: str,
        uf_empresa: str,
        telefone_empresa: str,
        id_empresa: int,
        conn=None,
    ) -> int:
        sql = (
            "INSERT INTO tb_cliente (NOME_CLIENTE, ENDERECO_CLIENTE, NUMERO_ENDERECO, "
            "COMPLEMENTO_ENDERECO, BAIRRO_CLIENTE, CEP_CLIENTE, MUNICIPIO_CLIENTE, UF_CLIENTE, "
            "TELEFONE_CLIENTE, EMAIL_CLIENTE, ID_EMPRESA, SENHA_CLIENTE, NICKNAME, METADE, UM_TERCO, "
            "CPF, IE, TAXA_ENTREGA) "
            "VALUES ('CONSUMIDOR FINAL', %s, %s, %s, %s, %s, %s, %s, %s, "
            "'consumidorfinal@gmail.com', %s, '', '', 1, 1, 'ISENTO', 'ISENTO', 0)"
        )
        params = (
            endereco_empresa,
            numero_endereco_empresa,
            complemento_endereco_empresa,
            bairro_empresa,
            cep_empresa,
            municipio_empresa,
            uf_empresa,
            telefone_empresa,
            id_empresa,
        )
        if conn is not None:
            return db.execute_in(conn, sql, params)
        return db.execute(sql, params)

    def listar(self, filtro_texto: str = "", limite: int = 200) -> List[mapCliente]:
        if filtro_texto:
            sql = (
                f"SELECT {_COLUNAS} FROM tb_cliente "
                "WHERE NOME_CLIENTE LIKE %s OR NOME_FANTASIA_CLIENTE LIKE %s OR TELEFONE_CLIENTE LIKE %s "
                "LIMIT %s"
            )
            curinga = f"%{filtro_texto}%"
            return db.query_all(sql, (curinga, curinga, curinga, limite), map_cls=mapCliente)

        sql = f"SELECT {_COLUNAS} FROM tb_cliente LIMIT %s"
        return db.query_all(sql, (limite,), map_cls=mapCliente)

    def inserir(self, cliente: dadosCliente) -> int:
        sql = (
            "INSERT INTO tb_cliente (NOME_CLIENTE, CPF, ENDERECO_CLIENTE, NUMERO_ENDERECO, "
            "COMPLEMENTO_ENDERECO, BAIRRO_CLIENTE, CEP_CLIENTE, MUNICIPIO_CLIENTE, UF_CLIENTE, "
            "TELEFONE_CLIENTE, EMAIL_CLIENTE, ID_EMPRESA, IE, BLACK_LIST, NOME_FANTASIA_CLIENTE, "
            "OBS_CLIENTE, TAXA_ENTREGA) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        params = (
            cliente.NOME_CLIENTE,
            cliente.CPF,
            cliente.ENDERECO_CLIENTE,
            cliente.NUMERO_ENDERECO,
            cliente.COMPLEMENTO_ENDERECO,
            cliente.BAIRRO_CLIENTE,
            cliente.CEP_CLIENTE,
            cliente.MUNICIPIO_CLIENTE,
            cliente.UF_CLIENTE,
            cliente.TELEFONE_CLIENTE,
            cliente.EMAIL_CLIENTE,
            cliente.ID_EMPRESA,
            cliente.IE,
            cliente.BLACK_LIST,
            cliente.NOME_FANTASIA_CLIENTE,
            cliente.OBS_CLIENTE,
            cliente.TAXA_ENTREGA,
        )
        return db.execute(sql, params)

    def atualizar(self, cliente: dadosCliente) -> None:
        sql = (
            "UPDATE tb_cliente SET NOME_CLIENTE = %s, CPF = %s, ENDERECO_CLIENTE = %s, "
            "NUMERO_ENDERECO = %s, COMPLEMENTO_ENDERECO = %s, BAIRRO_CLIENTE = %s, CEP_CLIENTE = %s, "
            "MUNICIPIO_CLIENTE = %s, UF_CLIENTE = %s, TELEFONE_CLIENTE = %s, EMAIL_CLIENTE = %s, "
            "ID_EMPRESA = %s, IE = %s, BLACK_LIST = %s, NOME_FANTASIA_CLIENTE = %s, OBS_CLIENTE = %s, "
            "TAXA_ENTREGA = %s WHERE ID_CLIENTE = %s"
        )
        params = (
            cliente.NOME_CLIENTE,
            cliente.CPF,
            cliente.ENDERECO_CLIENTE,
            cliente.NUMERO_ENDERECO,
            cliente.COMPLEMENTO_ENDERECO,
            cliente.BAIRRO_CLIENTE,
            cliente.CEP_CLIENTE,
            cliente.MUNICIPIO_CLIENTE,
            cliente.UF_CLIENTE,
            cliente.TELEFONE_CLIENTE,
            cliente.EMAIL_CLIENTE,
            cliente.ID_EMPRESA,
            cliente.IE,
            cliente.BLACK_LIST,
            cliente.NOME_FANTASIA_CLIENTE,
            cliente.OBS_CLIENTE,
            cliente.TAXA_ENTREGA,
            cliente.ID_CLIENTE,
        )
        db.execute(sql, params)
