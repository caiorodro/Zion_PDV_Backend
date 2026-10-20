from datetime import datetime, timedelta

import jwt
from fastapi import HTTPException, status
from werkzeug.security import check_password_hash, generate_password_hash

from cfg.config import Config
from models.Token import Token


class authentication:
    def __init__(self):
        self.config = Config()

    def generateNewToken(self) -> str:
        palavraPasse = "zionPDV"

        passe = generate_password_hash(palavraPasse)

        if not check_password_hash(passe, palavraPasse):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Credenciais inválidas para autenticação",
            )

        auth = authentication.encode_auth_token(passe)

        return Token(token=auth).__dict__

    # Prefixos de hash do Werkzeug -- mesma lista usada pelo Zion ADM
    # (base/authentication.py de lá), pra reconhecer um valor já com hash
    # sem precisar tentar check_password_hash em cima de texto puro (o que
    # levantaria/engoliria exceção à toa).
    _PREFIXOS_HASH = ("pbkdf2:", "scrypt:", "argon2")

    @staticmethod
    def verificar_senha(senha_informada: str, senha_armazenada: str | None) -> bool:
        """Confere a senha aceitando tanto hash Werkzeug (gravado pelo Zion
        ADM ao criar/editar um usuário) quanto texto puro legado (como
        tb_usuario ainda guarda pra quem nunca teve a senha regravada por
        lá). Mesma lógica de Zion_Adm/backend/base/authentication.py --
        precisa ser idêntica aqui porque os dois sistemas leem/gravam a
        mesma tb_usuario.
        """
        if senha_armazenada is None:
            return False

        if senha_armazenada.startswith(authentication._PREFIXOS_HASH):
            try:
                return check_password_hash(senha_armazenada, senha_informada)
            except Exception:
                return False

        return senha_informada == senha_armazenada

    @staticmethod
    def verify_Token_Is_Active(token: str):
        b1 = bytes(token, encoding="raw_unicode_escape")
        result = authentication.decode_auth_token(b1)

        if result == False:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Token inválido"
            )

    @staticmethod
    def encode_auth_token(user_id):
        try:
            payload = {
                "exp": datetime.now() + timedelta(days=2),
                "iat": datetime.now(),
                "sub": user_id,
            }

            return jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Falha na criação do token de autenticação",
            )

    @staticmethod
    def decode_auth_token(auth_token):
        try:
            payload = jwt.decode(auth_token, Config.SECRET_KEY, algorithms=["HS256"])

            return payload["sub"]

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Falha na autenticação de credenciais",
            )

        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token de autenticação inválido",
            )
