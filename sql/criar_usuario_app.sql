-- Cria um usuário de banco dedicado para a aplicação, com privilégio mínimo,
-- em vez de usar a credencial "root" (hoje em cfg/config.py / .env).
--
-- Rode este script manualmente no MySQL de produção (como root ou outro
-- usuário administrador), num horário de sua escolha. Depois de rodar:
--   1. Troque <SENHA_FORTE_AQUI> por uma senha gerada (não reaproveite a do root).
--   2. Atualize DB_USER e DB_PASSWORD no .env real da aplicação.
--   3. Reinicie o serviço da aplicação.
--   4. Considere trocar a senha do usuário "root" também, já que ela está
--      exposta no histórico do git desde o commit inicial do repositório —
--      remover do arquivo atual não desfaz isso.

CREATE USER IF NOT EXISTS 'zion_app'@'%' IDENTIFIED BY '<SENHA_FORTE_AQUI>';

-- Apenas o necessário para a aplicação operar: leitura e escrita de dados.
-- Sem DROP, ALTER, CREATE, GRANT ou acesso a outras bases.
GRANT SELECT, INSERT, UPDATE, DELETE ON zion.* TO 'zion_app'@'%';

-- base/checkDatabase.py hoje roda "CREATE TABLE IF NOT EXISTS" e "ALTER TABLE"
-- no boot da aplicação (migração de schema simplificada). Se esse comportamento
-- for mantido, o usuário da aplicação também precisa de:
-- GRANT CREATE, ALTER ON zion.* TO 'zion_app'@'%';
-- Alternativa mais segura: rodar essas migrações manualmente/uma vez com um
-- usuário administrativo e remover esse privilégio do usuário da aplicação.

FLUSH PRIVILEGES;

-- Para restringir o host de conexão (recomendado, em vez de '%'), troque
-- 'zion_app'@'%' por 'zion_app'@'<IP_DO_SERVIDOR_DA_APLICACAO>' nas linhas acima.
