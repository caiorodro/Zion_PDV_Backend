# Setup do backend em máquina nova (Windows)

Guia para colocar o backend do Zion PDV rodando do zero numa máquina Windows,
**sem `.venv`** — instalado direto no Python global da máquina, como sempre
foi feito. Sem isso, cada máquina nova tende a reproduzir os mesmos problemas
(pacote de driver conflitante, venv não portável entre PCs, `.env` esquecido).

## 1. Pré-requisitos

- Python 3.10 instalado e no PATH (`python --version` no cmd deve responder).
- Acesso ao MySQL onde está o schema `zion` (local nessa máquina ou remoto).
- O usuário de banco `zion_app` já criado nesse MySQL (ver seção 4).

## 2. Copiar o projeto

Clone ou copie a pasta `backend` inteira para a máquina (ex.: `git clone` se
houver um remoto configurado, ou copiando a pasta já preparada).

## 3. Instalar as dependências (sem venv)

Abra o **cmd** (não PowerShell) na pasta `backend`:

```cmd
cd C:\caminho\para\o\backend
pip install -r requirements.txt
```

## 4. Configurar o banco de dados

**4.1. Criar o usuário do banco (se ainda não existir nesse MySQL):**

Verifique primeiro:
```sql
SELECT user, host FROM mysql.user WHERE user='zion_app';
```
Se vier vazio, rode o script [sql/criar_usuario_app.sql](sql/criar_usuario_app.sql)
nesse MySQL (com uma senha real no lugar do placeholder — nunca deixe a senha
real escrita nesse arquivo, ele é versionado no git).

**4.2. Criar o arquivo `.env`**

Não existe `.env` no repositório (é ignorado pelo git de propósito — precisa
ser criado manualmente em cada máquina). Copie o modelo:

```cmd
copy .env.example .env
notepad .env
```
> Atenção ao criar pelo Bloco de Notas: confirme que o nome ficou `.env`
> exatamente, sem sobrar `.txt` no final.

Preencha com os valores reais dessa máquina:
```
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=zion
DB_USER=zion_app
DB_PASSWORD=<senha real do zion_app>
```
(`DB_HOST` é o endereço do MySQL — `127.0.0.1` se for local nessa máquina,
ou o IP do servidor de banco caso contrário)

## 5. Conferir a porta do serviço

O backend abre por padrão na porta **1199**. Se existir um arquivo
`cfg/prefServer.json` na máquina, ele **sobrescreve** essa porta — confira
se o valor de `PORT` ali bate com o que o frontend espera (`cfg/prefServer.json`
do lado do frontend). Se não precisar de porta customizada, pode simplesmente
não ter esse arquivo (aí vale o padrão 1199).

## 6. Testar manualmente antes de instalar como serviço

```cmd
python main.py
```
Deve aparecer `Uvicorn running on http://0.0.0.0:1199` e uma série de linhas
`Started server process [PID]`, uma por worker, sem erro. Confirme acessando
`http://127.0.0.1:1199/docs` no navegador, e depois teste o frontend de fato
contra esse backend antes de seguir pro passo do serviço.

Se algo falhar, veja a seção **Troubleshooting** no final.

Encerre esse teste manual (`Ctrl+C`) antes de instalar como serviço, pra não
disputar a porta 1199 com o `nssm`.

## 7. Instalar como Windows Service (nssm)

O projeto já traz o `nssm.exe` na raiz do backend. Os comandos abaixo criam o
serviço `ZionPDV` — ajuste o caminho do `python.exe` para o da máquina atual
(confira com `where python` no cmd):

```cmd
nssm.exe install ZionPDV "C:\Users\<usuario>\AppData\Local\Programs\Python\Python310\python.exe" "C:\caminho\para\o\backend\main.py"
nssm.exe set ZionPDV AppDirectory C:\caminho\para\o\backend
nssm.exe set ZionPDV Description Service for Zion PDV Nativo
nssm.exe set ZionPDV Start SERVICE_AUTO_START
nssm.exe start ZionPDV
```

(esses comandos também estão salvos em [nssm_instructions.txt](nssm_instructions.txt)
com o caminho de uma máquina específica de referência — ajuste para a máquina atual)

**Comandos úteis de manutenção:**
```cmd
nssm.exe restart ZionPDV
nssm.exe stop ZionPDV
nssm.exe status ZionPDV
nssm.exe remove ZionPDV confirm
nssm.exe edit ZionPDV
```
`nssm.exe edit ZionPDV` abre uma janela gráfica com todas as opções
(diretório, variáveis de ambiente, redirecionamento de log em
`I/O` etc.) — útil se quiser capturar stdout/stderr do serviço em arquivo,
já que rodando como serviço não tem console visível.

## 8. Verificação pós-instalação

- `services.msc` → confira que `ZionPDV` está "Em execução".
- `http://127.0.0.1:1199/docs` deve abrir normalmente.
- Teste o fluxo real pelo frontend.

## Troubleshooting

**"Too many connections" no MySQL:**
Cada worker abre seu próprio pool de conexões (`DB_POOL_SIZE`, padrão 3).
Se a máquina tiver muitos núcleos, o total pode ficar alto — ajuste via
variável de ambiente no `.env`: `DB_POOL_SIZE=2`, por exemplo.

**Backend cai com erro tipo "Connection aborted" no frontend, e sem
traceback Python no console:**
Verifique o Visualizador de Eventos do Windows (`eventvwr.msc` → Logs do
Windows → Aplicativo) por uma entrada de falha do `python.exe`. Se o módulo
com falha for algo como `MSVCP140.dll` com código `0xc0000005`, é uma queda
nativa do driver MySQL (extensão C) — já mitigado neste projeto com
`use_pure=True` em [infra/db.py](infra/db.py). Confirme que essa linha está
presente no arquivo dessa máquina.

**Frontend não conecta / timeout, mas o backend parece rodando:**
Confira a porta real que apareceu no console (`Uvicorn running on
http://0.0.0.0:XXXX`) contra o `cfg/prefServer.json` do frontend — ver
seção 5.

**Erro de variável de ambiente obrigatória não definida:**
Falta o `.env` ou algum campo dele — ver seção 4.2.
