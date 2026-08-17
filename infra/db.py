"""Camada de infraestrutura de acesso a dados.

Pool de conexões MySQL via mysql-connector-python, com SQL parametrizado.
Substitui, view a view, o antigo base/qModel.py (SQLAlchemy). Nenhum código
de negócio ou SQL específico de tabela deve morar aqui — isso fica em
infra/repositories/.
"""

import os
import threading
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv
from mysql.connector import pooling

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)


def _env_obrigatoria(nome: str) -> str:
    valor = os.getenv(nome)
    if not valor:
        raise RuntimeError(
            f"Variável de ambiente obrigatória '{nome}' não definida. "
            f"Copie .env.example para .env e preencha os valores."
        )
    return valor


DB_HOST = _env_obrigatoria("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = _env_obrigatoria("DB_NAME")
DB_USER = _env_obrigatoria("DB_USER")
DB_PASSWORD = _env_obrigatoria("DB_PASSWORD")

# Pequeno de propósito: o app roda com vários processos worker (uvicorn
# `workers=`), cada um com o seu próprio pool — o total de conexões no MySQL
# é aproximadamente `workers × DB_POOL_SIZE`. Com o padrão antigo (10) e uma
# máquina de muitos núcleos, só o boot já podia estourar o `max_connections`
# do servidor (era exatamente esse o efeito: workers falhando ao importar,
# em processos-filho cujo erro não aparece no terminal principal). Ajuste via
# variável de ambiente se precisar de mais.
_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "3"))

_pool = None
_pool_lock = threading.Lock()


def _get_pool():
    """Cria o pool na primeira vez que uma conexão é realmente pedida, não na
    importação do módulo. Evita que TODO worker abra `DB_POOL_SIZE` conexões
    de uma vez só no boot (e evita derrubar o processo inteiro se o MySQL
    estiver momentaneamente indisponível/sobrecarregado durante o startup)."""
    global _pool

    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = pooling.MySQLConnectionPool(
                    pool_name="zion_pool",
                    pool_size=_POOL_SIZE,
                    pool_reset_session=True,
                    host=DB_HOST,
                    port=DB_PORT,
                    database=DB_NAME,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    autocommit=False,
                    connection_timeout=10,
                    # Força a implementação 100% Python do driver, sem a
                    # extensão nativa em C. A extensão C provocou uma queda
                    # do processo (access violation em MSVCP140.dll, código
                    # 0xc0000005) na primeira query real após o boot, em
                    # produção. Com vários processos worker do uvicorn
                    # acessando o driver ao mesmo tempo, é um cenário
                    # conhecido de instabilidade dessa extensão no Windows.
                    use_pure=True,
                )

    return _pool


@contextmanager
def get_connection():
    """Empresta uma conexão do pool para uma operação isolada (normalmente leitura).

    Testa a conexão antes de entregar (evita erro tipo "MySQL server has gone
    away" quando uma conexão do pool ficou ociosa além do wait_timeout do
    servidor) e devolve ao pool ao sair, com rollback em caso de exceção.
    """
    conn = _get_pool().get_connection()
    conn.ping(reconnect=True, attempts=2, delay=1)
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()  # devolve a conexão ao pool, não a encerra de fato


@contextmanager
def transaction():
    """Para operações que precisam de múltiplos `execute` atômicos.

    Uso:
        with transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(...)
            cursor.execute(...)
        # commit automático ao sair sem exceção; rollback se algo levantar
    """
    conn = _get_pool().get_connection()
    conn.ping(reconnect=True, attempts=2, delay=1)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def query_all(sql, params=(), map_cls=None):
    """Executa um SELECT e devolve todas as linhas.

    Se `map_cls` for informado, cada linha vira `map_cls(**linha)` (pensado
    para reaproveitar as classes já existentes em base/mapTable.py).
    """
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        finally:
            cursor.close()

    if map_cls is None:
        return rows
    return [map_cls(**row) for row in rows]


def query_one(sql, params=(), map_cls=None):
    """Executa um SELECT e devolve a primeira linha (ou None)."""
    rows = query_all(sql, params, map_cls=map_cls)
    return rows[0] if rows else None


def execute(sql, params=()):
    """Executa um INSERT/UPDATE/DELETE isolado, com commit automático.

    Devolve o lastrowid (útil em INSERTs com autoincrement).
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params)
            conn.commit()
            return cursor.lastrowid
        finally:
            cursor.close()


# ---------------------------------------------------------------------------
# Variantes "_in": operam dentro de uma conexão/transação já aberta por quem
# chama (normalmente um `with transaction() as conn:` mais acima na pilha).
# Não abrem conexão própria nem dão commit — quem abriu a transação decide
# quando commitar. Usadas por fluxos de negócio que precisam gravar em várias
# tabelas atomicamente (ex.: salvar um pedido inteiro: cabeçalho + itens +
# pagamentos + baixa de estoque + financeiro, tudo ou nada).
# ---------------------------------------------------------------------------

def query_all_in(conn, sql, params=(), map_cls=None):
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
    finally:
        cursor.close()

    if map_cls is None:
        return rows
    return [map_cls(**row) for row in rows]


def query_one_in(conn, sql, params=(), map_cls=None):
    rows = query_all_in(conn, sql, params, map_cls=map_cls)
    return rows[0] if rows else None


def execute_in(conn, sql, params=()):
    """Como `execute`, mas roda na conexão/transação recebida, sem commit."""
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        return cursor.lastrowid
    finally:
        cursor.close()
