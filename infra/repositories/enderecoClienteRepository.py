"""Acesso a dados da tabela tb_endereco_cliente."""

from typing import List, Optional

from infra import db
from base.mapTable import mapEnderecoCliente
from models.dadosEndereco import dadosEndereco

_COLUNAS = (
    "ID_ENDERECO, ID_CLIENTE, ENDERECO, NUMERO_ENDERECO, COMPLEMENTO_ENDERECO, BAIRRO, CEP, "
    "MUNICIPIO, UF, ID_EMPRESA, LATITUDE, LONGITUDE"
)


class EnderecoClienteRepository:
    def buscar(self, id_cliente: int, filtro_texto: str, limite: int = 20) -> List[mapEnderecoCliente]:
        sql = (
            f"SELECT {_COLUNAS} FROM tb_endereco_cliente "
            "WHERE ID_CLIENTE = %s AND ENDERECO LIKE %s LIMIT %s"
        )
        return db.query_all(sql, (id_cliente, f"%{filtro_texto}%", limite), map_cls=mapEnderecoCliente)

    def listar_por_cliente(self, id_cliente: int) -> List[mapEnderecoCliente]:
        sql = f"SELECT {_COLUNAS} FROM tb_endereco_cliente WHERE ID_CLIENTE = %s"
        return db.query_all(sql, (id_cliente,), map_cls=mapEnderecoCliente)

    def buscar_por_id(self, id_endereco: int) -> Optional[mapEnderecoCliente]:
        sql = f"SELECT {_COLUNAS} FROM tb_endereco_cliente WHERE ID_ENDERECO = %s"
        return db.query_one(sql, (id_endereco,), map_cls=mapEnderecoCliente)

    def buscar_primeiro_por_cliente(self, id_cliente: int, conn=None) -> Optional[mapEnderecoCliente]:
        sql = f"SELECT {_COLUNAS} FROM tb_endereco_cliente WHERE ID_CLIENTE = %s LIMIT 1"
        if conn is not None:
            return db.query_one_in(conn, sql, (id_cliente,), map_cls=mapEnderecoCliente)
        return db.query_one(sql, (id_cliente,), map_cls=mapEnderecoCliente)

    def inserir_endereco_empresa(
        self,
        id_cliente: int,
        endereco_empresa: str,
        numero_endereco_empresa: str,
        complemento_endereco_empresa: str,
        bairro_empresa: str,
        cep_empresa: str,
        municipio_empresa: str,
        uf_empresa: str,
        id_empresa: int,
        conn=None,
    ) -> int:
        """Mesmo formato do endereço do consumidor final, criado junto com o
        cliente em checaConsumidorFinal()."""
        sql = (
            "INSERT INTO tb_endereco_cliente (ID_CLIENTE, ENDERECO, NUMERO_ENDERECO, "
            "COMPLEMENTO_ENDERECO, BAIRRO, CEP, MUNICIPIO, UF, ID_EMPRESA, LATITUDE, LONGITUDE) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0, 0)"
        )
        params = (
            id_cliente,
            endereco_empresa,
            numero_endereco_empresa,
            complemento_endereco_empresa,
            bairro_empresa,
            cep_empresa,
            municipio_empresa,
            uf_empresa,
            id_empresa,
        )
        if conn is not None:
            return db.execute_in(conn, sql, params)
        return db.execute(sql, params)

    def listar_todos_com_cliente(self) -> List[dict]:
        sql = (
            "SELECT e.ID_ENDERECO, e.ID_CLIENTE, c.NOME_CLIENTE, c.CPF, c.TELEFONE_CLIENTE, "
            "e.ENDERECO, e.NUMERO_ENDERECO, e.COMPLEMENTO_ENDERECO, e.BAIRRO, e.CEP, e.MUNICIPIO, e.UF "
            "FROM tb_endereco_cliente e "
            "INNER JOIN tb_cliente c ON e.ID_CLIENTE = c.ID_CLIENTE"
        )
        return db.query_all(sql)

    def inserir(self, endereco: dadosEndereco, id_cliente: int) -> int:
        sql = (
            "INSERT INTO tb_endereco_cliente (ID_CLIENTE, ENDERECO, NUMERO_ENDERECO, "
            "COMPLEMENTO_ENDERECO, BAIRRO, CEP, MUNICIPIO, UF, ID_EMPRESA, LATITUDE, LONGITUDE) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        params = (
            id_cliente,
            endereco.ENDERECO,
            endereco.NUMERO_ENDERECO,
            endereco.COMPLEMENTO_ENDERECO,
            endereco.BAIRRO,
            endereco.CEP,
            endereco.MUNICIPIO,
            endereco.UF,
            endereco.ID_EMPRESA,
            endereco.LATITUDE,
            endereco.LONGITUDE,
        )
        return db.execute(sql, params)

    def atualizar(self, endereco: dadosEndereco, id_cliente: int) -> None:
        sql = (
            "UPDATE tb_endereco_cliente SET ID_CLIENTE = %s, ENDERECO = %s, NUMERO_ENDERECO = %s, "
            "COMPLEMENTO_ENDERECO = %s, BAIRRO = %s, CEP = %s, MUNICIPIO = %s, UF = %s, "
            "ID_EMPRESA = %s, LATITUDE = %s, LONGITUDE = %s WHERE ID_ENDERECO = %s"
        )
        params = (
            id_cliente,
            endereco.ENDERECO,
            endereco.NUMERO_ENDERECO,
            endereco.COMPLEMENTO_ENDERECO,
            endereco.BAIRRO,
            endereco.CEP,
            endereco.MUNICIPIO,
            endereco.UF,
            endereco.ID_EMPRESA,
            endereco.LATITUDE,
            endereco.LONGITUDE,
            endereco.ID_ENDERECO,
        )
        db.execute(sql, params)
