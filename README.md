# 🛡️ h4ck-toolkit

Kit de ferramentas de **segurança ofensiva** para reconhecimento e scanning, escritas em Python puro. Focado em simplicidade, funcionalidade e aprendizado prático de técnicas de penetration testing.

## 📦 Instalação

```bash
# Clone o repositório
git clone https://github.com/Master/h4ck-toolkit.git
cd h4ck-toolkit

# Instale as dependências
pip install -r requirements.txt

# Ou instale como pacote
pip install -e .
```

## 🔧 Ferramentas

### 1. Port Scanner — `scanner/port_scanner.py`

Scanner de portas TCP multi-threaded. Conecta a cada porta alvo e identifica quais estão abertas, com detecção automática do serviço associado.

**Características:**
- Range de portas flexível (`1-1000`, `22,80,443`, ou misto)
- Resolução DNS automática
- Threading para escaneamento rápido
- Detecção de serviço via `socket.getservbyport`
- Barra de progresso em tempo real
- Cores no terminal para output bonito

**Uso:**

```bash
# Escanear um range de portas
python scanner/port_scanner.py --host scanme.nmap.org --ports 1-1000

# Escanear portas específicas
python scanner/port_scanner.py --host 192.168.1.1 --ports 22,80,443,8080

# Com timeout e threads customizados
python scanner/port_scanner.py --host example.com --ports 1-1024 --timeout 2 --threads 200

# Ajuda completa
python scanner/port_scanner.py --help
```

**Exemplo de output:**
```
  ╔══════════════════════════════════════╗
  ║       h4ck-toolkit — Port Scanner    ║
  ║       Scanner de Portas TCP v1.0     ║
  ╚══════════════════════════════════════╝

  Alvo:        scanme.nmap.org
  Portas:      10 (22-3306)
  Timeout:     1.0s
  Threads:     100
  Início:      14:30:00

  [*] Resolvido: scanme.nmap.org -> 45.33.32.156

    ✓ PORTA    22/tcp  ABERTA  [ssh]
    ✓ PORTA    80/tcp  ABERTA  [http]
    ✓ PORTA   443/tcp  ABERTA  [https]
  [ 60%] Progresso: 6/10 portas escaneadas
    ✓ PORTA  3306/tcp  ABERTA  [mysql]
  [100%] Progresso: 10/10 portas escaneadas

  ═══ RESUMO ═══
  Total escaneado: 10 portas
  Portas abertas:  4
  Fim:           14:30:02

  Portas abertas encontradas:
      22/tcp  ssh
      80/tcp  http
     443/tcp  https
    3306/tcp  mysql
```

---

### 2. Subdomain Finder — `recon/subdomain_finder.py`

Ferramenta de descoberta de subdomínios via DNS e requisições HTTP. Usa wordlist embutida com mais de **200 subdomínios comuns** ou wordlist personalizada.

**Características:**
- Wordlist embutida com mais de 200 subdomínios
- Suporte a wordlist externa personalizada
- Multi-threading para alta performance
- User-Agent customizável
- Identificação de redirecionamentos
- Exibição colorida dos resultados

**Uso:**

```bash
# Scan básico com wordlist embutida
python recon/subdomain_finder.py --domain example.com

# Com wordlist personalizada
python recon/subdomain_finder.py --domain example.com --wordlist meus_subdominios.txt

# Aumentando threads e timeout
python recon/subdomain_finder.py --domain exemplo.com.br --threads 50 --timeout 5

# User-Agent personalizado
python recon/subdomain_finder.py --domain site.com --ua "MyCustomAgent/1.0"

# Ajuda completa
python recon/subdomain_finder.py --help
```

**Exemplo de output:**
```
  ╔══════════════════════════════════════════╗
  ║    h4ck-toolkit — Subdomain Finder      ║
  ║    Descoberta de Subdomínios v1.0       ║
  ╚══════════════════════════════════════════╝

  Domínio:      example.com
  Subdomínios:  210
  Timeout:      3.0s
  Threads:      20
  Início:       14:31:00

  [+] www.example.com                         200                 1.2KB
  [+] mail.example.com                        200                 850B
  [+] api.example.com                         302                 240B
  [ 30%] Progresso: 63/210  Encontrados: 3
  [+] admin.example.com                       403                 450B
  [100%] Progresso: 210/210  Encontrados: 4

  ═══ RESUMO ═══
  Total testados:  210
  Encontrados:    4
  Fim:            14:31:15

  Subdomínios encontrados:
  Host                                               Status               Tamanho
  -------------------------------------------------- -------------------- ----------
  admin.example.com                                  403 (Proibido)       450B
  api.example.com                                    302                  240B
  mail.example.com                                   200                  850B
  www.example.com                                    200                  1.2KB
```

---

### 3. Directory Brute Forcer — `recon/dir_brute.py`

Ferramenta de força bruta de diretórios e arquivos em servidores web. Testa centenas de caminhos com extensões automáticas para descobrir endpoints ocultos.

**Características:**
- Wordlist embutida com mais de **200 caminhos** (diretórios + arquivos)
- Extensões automáticas (php, asp, txt, zip, bak, etc.)
- Wordlist externa personalizada
- Filtro por código de status HTTP
- Detecção de redirecionamentos
- Multi-threading com pool de conexões
- Identificação de endpoints comuns (admin, api, .git, .env, etc.)

**Uso:**

```bash
# Scan básico com wordlist embutida
python recon/dir_brute.py --url http://example.com

# Com extensões específicas
python recon/dir_brute.py --url http://exemplo.com.br --extensions php,asp,txt

# Sem adicionar extensões automaticamente
python recon/dir_brute.py --url http://example.com --no-extensions

# Wordlist personalizada
python recon/dir_brute.py --url http://example.com --wordlist lista_dirs.txt

# Filtrar apenas certos status HTTP
python recon/dir_brute.py --url http://example.com --status-filter 200,403

# Ajuda completa
python recon/dir_brute.py --help
```

**Exemplo de output:**
```
  ╔══════════════════════════════════════════╗
  ║   h4ck-toolkit — Directory Brute Force  ║
  ║    Força Bruta de Diretórios Web v1.0   ║
  ╚══════════════════════════════════════════╝

  URL alvo:     http://example.com
  Caminhos:     200
  Extensões:    .php .asp .aspx .txt .zip .bak .old .html .htm
  Timeout:      3.0s
  Threads:      20
  Início:       14:32:00

  [✓] Alvo acessível: http://example.com -> 200

  [+] http://example.com/admin                           403 (Proibido)       1.2KB
  [+] http://example.com/robots.txt                      200                 450B
  [+] http://example.com/.git/config                     403                 240B
  [+] http://example.com/backup                          301                 320B
  [ 50%] Progresso: 100/200  Encontrados: 4
  [+] http://example.com/wp-admin                        302                 180B
  [+] http://example.com/.env                            403                 120B
  [100%] Progresso: 200/200  Encontrados: 6

  ═══ RESUMO ═══
  Total testados:  200
  Encontrados:    6
  Fim:            14:32:10

  Diretórios/Arquivos encontrados:
  Caminho                            Status                    Tamanho    Palavras
  -------------------------------------------------- -------------------- ---------- ----------
  .env                               403 (Proibido)           120B       18
  .git/config                        403 (Proibido)           240B       32
  admin                              403 (Proibido)           1.2KB      184
  backup                             301                      320B       12
  robots.txt                         200                      450B       28
  wp-admin                           302                      180B       8
```

---

## ⚙️ Instalação como comandos globais

```bash
pip install -e .

# Agora os comandos estarão disponíveis:
h4ck-portscan --host scanme.nmap.org --ports 22,80
h4ck-subfinder --domain example.com
h4ck-dirbrute --url http://example.com
```

## 📋 Dependências

- **requests** — Requisições HTTP para as ferramentas de recon
- **colorama** — Output colorido no terminal (cross-platform)

## ⚠️ Aviso Legal

Este kit foi criado **exclusivamente para fins educacionais e testes de segurança autorizados**. O uso inadequado destas ferramentas contra sistemas sem autorização prévia é **ilegal** e antiético. O autor não se responsabiliza pelo mau uso.

## 📄 Licença

MIT
