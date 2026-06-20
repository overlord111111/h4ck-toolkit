#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Directory Brute Forcer
----------------------
Ferramenta para brute force de diretórios e arquivos em servidores web.
Testa caminhos de uma wordlist contra uma URL alvo e reporta os que existem.

Uso:
    python recon/dir_brute.py --url http://example.com
    python recon/dir_brute.py --url http://exemplo.com.br --ext php,txt,zip
    python recon/dir_brute.py --url http://example.com --wordlist lista.txt --threads 50
"""

import argparse
import sys
import concurrent.futures
from datetime import datetime
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    print("[ERRO] requests não instalado. Execute: pip install requests")
    sys.exit(1)

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        RED = GREEN = YELLOW = CYAN = MAGENTA = RESET = ""
    class Style:
        BRIGHT = ""
        RESET_ALL = ""


# Wordlist embutida de diretórios e arquivos comuns
WORDLIST_PADRAO = [
    # Diretórios comuns
    "admin", "administrator", "adm", "backup", "backups", "bak",
    "cache", "cgi-bin", "cgi", "config", "configuration", "conf",
    "css", "data", "database", "db", "dev", "development",
    "docs", "documentacao", "download", "downloads",
    "error", "errors", "example", "examples", "export",
    "files", "forms", "forum", "foto", "fotos", "galeria",
    "home", "html", "htdocs", "httpdocs", "httpsdocs",
    "images", "img", "include", "includes", "index",
    "install", "js", "json", "lib", "library", "log", "logs",
    "mail", "media", "misc", "modules", "news", "old",
    "painel", "panel", "phpmyadmin", "phpPgAdmin",
    "photos", "pic", "pics", "plugins", "portal",
    "private", "public", "public_html", "public_ftp",
    "restrito", "restricted", "root", "sistema",
    "sql", "sqlite", "src", "stats", "status",
    "suporte", "support", "swf", "sys", "system",
    "templates", "test", "tests", "tmp", "tools",
    "upload", "uploads", "user", "users", "var",
    "web", "webapp", "webroot", "webservice", "www",
    "wwwroot", "xml", "api", "v1", "v2", "v3",
    "graphql", "rest", "soap", "wsdl",
    # Arquivos comuns
    "index.php", "index.html", "index.htm", "index.asp",
    "default.aspx", "default.asp", "default.php", "default.html",
    "home.php", "home.html", "main.php", "main.html",
    "login.php", "login.html", "logon.aspx",
    "wp-login.php", "wp-admin", "wp-content", "wp-includes",
    "administrator/index.php", "admin.php", "admin.html",
    "config.php", "config.php.bak", "config.php.old",
    "config.inc", "config.inc.php", "configuration.php",
    ".htaccess", ".htpasswd", "htaccess.txt",
    "robots.txt", "sitemap.xml", "crossdomain.xml",
    "web.config", "web.config.bak",
    ".env", "env.php", ".env.example",
    "composer.json", "composer.lock", "package.json",
    "package-lock.json", "yarn.lock", "Gemfile", "Gemfile.lock",
    "Dockerfile", "docker-compose.yml", "Makefile",
    "README.md", "readme.html", "LICENSE", "CHANGELOG",
    "CHANGELOG.md", "TODO", "CONTRIBUTING.md",
    ".git/config", ".git/HEAD", ".svn/entries",
    "info.php", "phpinfo.php", "test.php", "shell.php",
    "cmd.php", "exec.php", "upload.php", "connector.php",
    "server-status", "server-info",
    "actuator", "actuator/health", "actuator/info",
    "swagger", "swagger-ui", "api-docs", "api/swagger",
    "docs/api", "openapi.json", "swagger.json",
    "wsdl", "?wsdl",
]


def carregar_wordlist(arquivo=None):
    """Carrega wordlist de arquivo externo ou usa a embutida."""
    if arquivo:
        try:
            with open(arquivo, "r", encoding="utf-8", errors="ignore") as f:
                caminhos = [linha.strip() for linha in f if linha.strip()]
            print(f"  {Fore.CYAN}[*]{Fore.RESET} Wordlist carregada: {arquivo} ({len(caminhos)} caminhos)")
            return caminhos
        except FileNotFoundError:
            print(f"  {Fore.RED}[ERRO]{Fore.RESET} Arquivo '{arquivo}' não encontrado.")
            sys.exit(1)
    else:
        print(f"  {Fore.CYAN}[*]{Fore.RESET} Usando wordlist embutida ({len(WORDLIST_PADRAO)} caminhos)")
        return WORDLIST_PADRAO


def gerar_variacoes(caminho, extensoes):
    """Gera variações com extensões para um caminho base."""
    variacoes = [caminho]
    # Se já tem extensão, não adiciona outra
    if "." not in caminho.split("/")[-1]:
        for ext in extensoes:
            variacoes.append(f"{caminho}.{ext}")
    return variacoes


def testar_url(url_base, caminho, timeout, user_agent, extensoes):
    """Testa um caminho na URL base."""
    # Garantir que url_base termine com /
    if not url_base.endswith("/"):
        url_base += "/"

    caminho = caminho.lstrip("/")
    url = url_base + caminho

    cabecalhos = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        resp = requests.get(url, headers=cabecalhos, timeout=timeout, allow_redirects=False)
        status = resp.status_code
        tamanho = len(resp.content)
        palavras = len(resp.text.split())

        if status in (200, 204, 301, 302, 303, 307, 308, 401, 403, 500):
            return (caminho, url, status, tamanho, palavras)
        else:
            return (caminho, url, status, None, None)
    except requests.exceptions.ConnectionError:
        return (caminho, url, 0, None, None)
    except requests.exceptions.Timeout:
        return (caminho, url, -1, None, None)
    except Exception:
        return (caminho, url, -3, None, None)


def mostrar_status(status):
    """Retorna representação textual colorida do status HTTP."""
    if status == 0:
        return f"{Fore.RED}Sem conexão{Fore.RESET}"
    elif status == -1:
        return f"{Fore.YELLOW}Timeout{Fore.RESET}"
    elif status == -3:
        return f"{Fore.RED}Erro{Fore.RESET}"
    elif status == 200:
        return f"{Fore.GREEN}{status}{Fore.RESET}"
    elif status == 204:
        return f"{Fore.CYAN}{status}{Fore.RESET}"
    elif status in (301, 302, 303, 307, 308):
        return f"{Fore.MAGENTA}{status}{Fore.RESET}"
    elif status == 401:
        return f"{Fore.YELLOW}{status} (Não autorizado){Fore.RESET}"
    elif status == 403:
        return f"{Fore.YELLOW}{status} (Proibido){Fore.RESET}"
    elif status == 500:
        return f"{Fore.RED}{status} (Erro interno){Fore.RESET}"
    else:
        return str(status)


def formatar_tamanho(tamanho):
    """Formata tamanho em bytes."""
    if tamanho < 1024:
        return f"{tamanho}B"
    elif tamanho < 1024 * 1024:
        return f"{tamanho/1024:.1f}KB"
    else:
        return f"{tamanho/(1024*1024):.1f}MB"


def banner():
    print(f"{Fore.CYAN}{Style.BRIGHT}")
    print("  ╔══════════════════════════════════════════╗")
    print("  ║   h4ck-toolkit — Directory Brute Force  ║")
    print("  ║    Força Bruta de Diretórios Web v1.0   ║")
    print("  ╚══════════════════════════════════════════╝")
    print(f"{Style.RESET_ALL}")


def main():
    parser = argparse.ArgumentParser(
        prog="dir_brute.py",
        description="Ferramenta de brute force de diretórios web — h4ck-toolkit",
        epilog="Exemplo: python recon/dir_brute.py --url http://example.com",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--url", "-u",
        required=True,
        help="URL alvo (ex: http://example.com ou http://exemplo.com.br/pasta)",
    )
    parser.add_argument(
        "--wordlist", "-w",
        help="Arquivo de wordlist personalizado (um caminho por linha)",
    )
    parser.add_argument(
        "--extensions", "-e",
        default="php,asp,aspx,txt,zip,tar.gz,bak,old,html,htm,jsp,do,action",
        help="Extensões para testar (separadas por vírgula). Padrão: php,asp,aspx,txt,zip",
    )
    parser.add_argument(
        "--timeout", "-t",
        type=float,
        default=3.0,
        help="Timeout em segundos para cada requisição (padrão: 3.0)",
    )
    parser.add_argument(
        "--threads", "-T",
        type=int,
        default=20,
        help="Número de threads simultâneas (padrão: 20)",
    )
    parser.add_argument(
        "--no-extensions", "-ne",
        action="store_true",
        help="Não adicionar extensões automaticamente aos caminhos",
    )
    parser.add_argument(
        "--user-agent", "-ua",
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        help="User-Agent personalizado",
    )
    parser.add_argument(
        "--status-filter", "-sf",
        help="Filtrar por códigos de status (ex: 200,301,403)",
    )

    args = parser.parse_args()

    # Validar URL
    url_base = args.url.rstrip("/")
    parsed = urlparse(url_base)
    if not parsed.scheme:
        url_base = "http://" + url_base
    elif parsed.scheme not in ("http", "https"):
        print(f"{Fore.RED}[ERRO]{Fore.RESET} Esquema inválido: '{parsed.scheme}'. Use http ou https.")
        sys.exit(1)

    # Extensões
    extensoes = []
    if not args.no_extensions:
        extensoes = [e.strip().lstrip(".") for e in args.extensions.split(",") if e.strip()]
    else:
        print(f"  {Fore.YELLOW}[!]{Fore.RESET} Modo sem extensões ativado")

    # Filtro de status
    status_filter = None
    if args.status_filter:
        try:
            status_filter = set(int(s.strip()) for s in args.status_filter.split(","))
        except ValueError:
            print(f"{Fore.RED}[ERRO]{Fore.RESET} Filtro de status inválido. Use números separados por vírgula.")
            sys.exit(1)

    caminhos = carregar_wordlist(args.wordlist)
    if not caminhos:
        print(f"{Fore.RED}[ERRO]{Fore.RESET} Nenhum caminho para testar.")
        sys.exit(1)

    banner()

    print(f"  {Fore.YELLOW}URL alvo:{Fore.RESET}     {url_base}")
    print(f"  {Fore.YELLOW}Caminhos:{Fore.RESET}     {len(caminhos)}")
    if extensoes:
        print(f"  {Fore.YELLOW}Extensões:{Fore.RESET}    .{' .'.join(extensoes)}")
    print(f"  {Fore.YELLOW}Timeout:{Fore.RESET}       {args.timeout}s")
    print(f"  {Fore.YELLOW}Threads:{Fore.RESET}       {args.threads}")
    print(f"  {Fore.YELLOW}Início:{Fore.RESET}        {datetime.now().strftime('%H:%M:%S')}")
    print()

    # Testar conectividade básica primeiro
    try:
        resp = requests.get(url_base, timeout=5)
        print(f"  {Fore.GREEN}[✓]{Fore.RESET} Alvo acessível: {url_base} -> {resp.status_code}")
    except Exception as e:
        print(f"  {Fore.YELLOW}[!]{Fore.RESET} Alvo pode não estar acessível: {e}")
    print()

    encontrados = []
    testados = 0
    total = len(caminhos)
    erros_conexao = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
        futuros = {}
        for caminho in caminhos:
            variacoes = gerar_variacoes(caminho, extensoes)
            for var in variacoes:
                futuros[executor.submit(
                    testar_url, url_base, var, args.timeout, args.user_agent, extensoes
                )] = var

        for futuro in concurrent.futures.as_completed(futuros):
            testados += 1

            try:
                caminho, url, status, tamanho, palavras = futuro.result()
            except Exception:
                continue

            if status == 0:
                erros_conexao += 1
                continue

            # Aplicar filtro de status se definido
            if status_filter and status not in status_filter:
                continue

            if status in (200, 204, 301, 302, 303, 307, 308, 401, 403, 500):
                encontrados.append((caminho, url, status, tamanho, palavras))
                tam = formatar_tamanho(tamanho) if tamanho else "?"
                print(
                    f"  {Fore.GREEN}[+] {url:<65}{Fore.RESET} "
                    f"{mostrar_status(status):<25} {tam:<10}"
                )

            # Progresso
            if testados % max(1, total // 10) == 0 or testados == total:
                pct = testados * 100 // total
                print(
                    f"  {Fore.CYAN}[{pct:>3}%]{Fore.RESET} "
                    f"Progresso: {testados}/{total}  "
                    f"Encontrados: {len(encontrados)}"
                )

    print()
    print(f"  {Fore.CYAN}{Style.BRIGHT}═══ RESUMO ═══{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}Total testados:{Fore.RESET}  {testados}")
    print(f"  {Fore.GREEN}Encontrados:{Fore.RESET}    {len(encontrados)}")
    if erros_conexao > 0:
        print(f"  {Fore.RED}Erros conexão:{Fore.RESET} {erros_conexao}")
    print(f"  {Fore.YELLOW}Fim:{Fore.RESET}            {datetime.now().strftime('%H:%M:%S')}")

    if encontrados:
        print()
        print(f"  {Style.BRIGHT}Diretórios/Arquivos encontrados:{Style.RESET_ALL}")
        print(f"  {'Caminho':<55} {'Status':<25} {'Tamanho':<10} {'Palavras'}")
        print(f"  {'-'*55} {'-'*25} {'-'*10} {'-'*10}")
        for caminho, url, status, tamanho, palavras in sorted(encontrados, key=lambda x: x[1]):
            tam = formatar_tamanho(tamanho) if tamanho else "?"
            print(f"  {caminho:<55} {mostrar_status(status):<25} {tam:<10} {palavras or '?'}")
    print()


if __name__ == "__main__":
    main()
