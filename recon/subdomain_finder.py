#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subdomain Finder
----------------
Ferramenta para descoberta de subdomínios usando wordlist embutida e requests.
Testa subdomínios contra um domínio alvo e reporta quais resolvem (HTTP 200/301/302).

Uso:
    python recon/subdomain_finder.py --domain example.com
    python recon/subdomain_finder.py --domain exemplo.com.br --wordlist extra.txt
    python recon/subdomain_finder.py --domain example.com --threads 50 --timeout 3
"""

import argparse
import sys
import concurrent.futures
from datetime import datetime

try:
    import requests
except ImportError:
    print("[ERRO] requests não instalado. Execute: pip install requests")
    sys.exit(1)

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    # Fallback se colorama não estiver disponível
    class Fore:
        RED = GREEN = YELLOW = CYAN = RESET = ""
    class Style:
        BRIGHT = ""
        RESET_ALL = ""


# Wordlist embutida com subdomínios comuns
WORDLIST_PADRAO = [
    "www", "mail", "ftp", "admin", "blog", "webmail", "vpn", "support",
    "dev", "test", "api", "app", "m", "mobile", "email", "portal",
    "smtp", "pop3", "imap", "ssh", "remote", "intranet", "cpanel",
    "whm", "server", "ns1", "ns2", "dns", "mx", "owa", "exchange",
    "autodiscover", "lyncdiscover", "sip", "web", "www2", "www1",
    "ftp2", "mail2", "cdn", "static", "assets", "images", "img",
    "download", "uploads", "files", "cloud", "svn", "git", "jenkins",
    "wiki", "confluence", "jira", "redmine", "mantis", "bugzilla",
    "phpmyadmin", "phpPgAdmin", "adminer", "mysql", "db", "database",
    "backup", "backups", "logs", "monitor", "status", "help", "helpdesk",
    "ticket", "tickets", "chat", "forum", "community", "news", "info",
    "register", "login", "signup", "painel", "sistema", "sistemaweb",
    "erp", "rh", "financeiro", "compras", "vendas", "estoque", "pedidos",
    "clientes", "fornecedores", "agenda", "calendario", "webmail2",
    "hospedagem", "ssl", "certificado", "bkp", "homolog", "homologacao",
    "hml", "stage", "staging", "beta", "alpha", "sandbox", "demo",
    "corporativo", "webdisk", "webdav", "dav", "radius", "ldap",
    "radius2", "sms", "sms2", "billing", "invoice", "payment", "loja",
    "shop", "store", "carrinho", "checkout", "produto", "produtos",
    "catalogo", "categoria", "sac", "ouvidoria", "faleconosco",
    "contato", "sobre", "empresa", "trabalheconosco", "vagas",
    "parceiros", "representantes", "revenda", "afiliados",
    "docs", "documentacao", "manual", "faq", "tutorial", "suporte",
    "dev-api", "api-docs", "swagger", "docs-api", "graphql",
    "websocket", "stream", "proxy", "gateway", "firewall", "waf",
    "correio", "zimbra", "roundcube", "squirrelmail", "rainloop",
    "webmail3", "webmail4", "webmail5", "moodle", "ead", "ava",
    "ensino", "ensinar", "aluno", "professor", "secretaria",
    "biblioteca", "academico", "graduacao", "pos", "extensao",
    "wordpress", "wp", "wp-admin", "wp-content", "wp-includes",
    "joomla", "administrator", "drupal", "magento", "opencart",
    "shopify", "prestashop", "whmcs", "vestacp", "vesta",
    "cwp", "centoswebpanel", "ispconfig", "plesk", "directadmin",
    "cpanel2", "webmail6", "cpcalendars", "cpcontacts", "webdisk2",
    "ns3", "ns4", "ns5", "mail1", "mail3", "relay", "lists",
    "newsletter", "marketing", "pesquisa", "surveys", "enquete",
    "votacao", "eleicao", "resultados", "premiacao", "eventos",
    "certame", "concurso", "processoseletivo", "inscricao",
    "cadastro", "recadastro", "atualizacao", "valida", "validacao",
    "confirmacao", "ativacao", "cancelamento", "bloqueio",
]


def carregar_wordlist(arquivo=None):
    """Carrega wordlist de arquivo externo ou usa a embutida."""
    if arquivo:
        try:
            with open(arquivo, "r", encoding="utf-8", errors="ignore") as f:
                subdominios = [linha.strip().lower() for linha in f if linha.strip()]
            print(f"  {Fore.CYAN}[*]{Fore.RESET} Wordlist carregada: {arquivo} ({len(subdominios)} subdomínios)")
            return subdominios
        except FileNotFoundError:
            print(f"  {Fore.RED}[ERRO]{Fore.RESET} Arquivo '{arquivo}' não encontrado.")
            sys.exit(1)
    else:
        print(f"  {Fore.CYAN}[*]{Fore.RESET} Usando wordlist embutida ({len(WORDLIST_PADRAO)} subdomínios)")
        return WORDLIST_PADRAO


def testar_subdominio(dominio, subdominio, timeout, user_agent):
    """Testa um subdomínio e retorna resultado."""
    host = f"{subdominio}.{dominio}"
    url = f"http://{host}"
    cabecalhos = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    try:
        resp = requests.get(url, headers=cabecalhos, timeout=timeout, allow_redirects=True)
        status = resp.status_code
        tamanho = len(resp.content)
        if status in (200, 301, 302, 303, 307, 308):
            return (subdominio, host, status, tamanho, resp.url)
        elif status in (401, 403):
            return (subdominio, host, status, tamanho, url)
        elif status == 404:
            return (subdominio, host, status, tamanho, None)
        else:
            return (subdominio, host, status, tamanho, None)
    except requests.exceptions.ConnectionError:
        return (subdominio, host, 0, 0, None)
    except requests.exceptions.Timeout:
        return (subdominio, host, -1, 0, None)
    except requests.exceptions.TooManyRedirects:
        return (subdominio, host, -2, 0, None)
    except Exception:
        return (subdominio, host, -3, 0, None)


def formatar_tamanho(tamanho):
    """Formata tamanho em bytes para exibição amigável."""
    if tamanho < 1024:
        return f"{tamanho}B"
    elif tamanho < 1024 * 1024:
        return f"{tamanho/1024:.1f}KB"
    else:
        return f"{tamanho/(1024*1024):.1f}MB"


def mostrar_status(status):
    """Retorna representação textual do status."""
    if status == 0:
        return f"{Fore.RED}Sem conexão{Fore.RESET}"
    elif status == -1:
        return f"{Fore.YELLOW}Timeout{Fore.RESET}"
    elif status == -2:
        return f"{Fore.YELLOW}Muitos redirects{Fore.RESET}"
    elif status == -3:
        return f"{Fore.RED}Erro{Fore.RESET}"
    elif status == 200:
        return f"{Fore.GREEN}{status}{Fore.RESET}"
    elif status in (301, 302, 303, 307, 308):
        return f"{Fore.CYAN}{status}{Fore.RESET}"
    elif status in (401, 403):
        return f"{Fore.YELLOW}{status}{Fore.RESET}"
    else:
        return str(status)


def banner():
    print(f"{Fore.CYAN}{Style.BRIGHT}")
    print("  ╔══════════════════════════════════════════╗")
    print("  ║    h4ck-toolkit — Subdomain Finder      ║")
    print("  ║    Descoberta de Subdomínios v1.0       ║")
    print("  ╚══════════════════════════════════════════╝")
    print(f"{Style.RESET_ALL}")


def main():
    parser = argparse.ArgumentParser(
        prog="subdomain_finder.py",
        description="Ferramenta de descoberta de subdomínios — h4ck-toolkit",
        epilog="Exemplo: python recon/subdomain_finder.py --domain example.com",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--domain", "-d",
        required=True,
        help="Domínio alvo para buscar subdomínios (obrigatório)",
    )
    parser.add_argument(
        "--wordlist", "-w",
        help="Arquivo de wordlist personalizado (um subdomínio por linha)",
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
        "--user-agent", "-ua",
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        help="User-Agent personalizado para as requisições",
    )

    args = parser.parse_args()

    # Validação básica do domínio
    dominio = args.domain.lower().strip()
    if not dominio or "." not in dominio:
        print(f"{Fore.RED}[ERRO]{Fore.RESET} Domínio inválido: '{dominio}'")
        sys.exit(1)

    subdominios = carregar_wordlist(args.wordlist)
    if not subdominios:
        print(f"{Fore.RED}[ERRO]{Fore.RESET} Nenhum subdomínio para testar.")
        sys.exit(1)

    banner()

    print(f"  {Fore.YELLOW}Domínio:{Fore.RESET}      {dominio}")
    print(f"  {Fore.YELLOW}Subdomínios:{Fore.RESET}  {len(subdominios)}")
    print(f"  {Fore.YELLOW}Timeout:{Fore.RESET}      {args.timeout}s")
    print(f"  {Fore.YELLOW}Threads:{Fore.RESET}      {args.threads}")
    print(f"  {Fore.YELLOW}Início:{Fore.RESET}       {datetime.now().strftime('%H:%M:%S')}")
    print()

    encontrados = []
    testados = 0
    total = len(subdominios)

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
        futuros = {
            executor.submit(
                testar_subdominio, dominio, sub, args.timeout, args.user_agent
            ): sub
            for sub in subdominios
        }
        for futuro in concurrent.futures.as_completed(futuros):
            testados += 1
            subdominio, host, status, tamanho, url_final = futuro.result()

            if status in (200, 301, 302, 303, 307, 308, 401, 403):
                encontrados.append((host, status, tamanho, url_final))
                tam = formatar_tamanho(tamanho)
                print(
                    f"  {Fore.GREEN}[+] {host:<40}{Fore.RESET} "
                    f"{mostrar_status(status):<20} {tam:<10}"
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
    print(f"  {Fore.YELLOW}Fim:{Fore.RESET}            {datetime.now().strftime('%H:%M:%S')}")

    if encontrados:
        print()
        print(f"  {Style.BRIGHT}Subdomínios encontrados:{Style.RESET_ALL}")
        print(f"  {'Host':<50} {'Status':<20} {'Tamanho'}")
        print(f"  {'-'*50} {'-'*20} {'-'*10}")
        for host, status, tamanho, url_final in sorted(encontrados, key=lambda x: x[0]):
            tam = formatar_tamanho(tamanho)
            print(f"  {host:<50} {mostrar_status(status):<20} {tam:<10}")
            if url_final and url_final != f"http://{host}":
                print(f"  {'↳ ' + url_final:<70}")
    print()


if __name__ == "__main__":
    main()
