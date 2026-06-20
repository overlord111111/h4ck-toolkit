#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scanner de Portas TCP
---------------------
Ferramenta simples para escanear portas TCP abertas em um host alvo.
Utiliza conexão socket com timeout para determinar se a porta está aberta.

Uso:
    python scanner/port_scanner.py --host 192.168.1.1 --ports 1-1000
    python scanner/port_scanner.py --host scanme.nmap.org --ports 22,80,443
    python scanner/port_scanner.py --host example.com --ports 1-1024 --timeout 2
"""

import argparse
import socket
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


RESET = "\033[0m"
VERDE = "\033[92m"
VERMELHO = "\033[91m"
AMARELO = "\033[93m"
CIANO = "\033[96m"
NEGRITO = "\033[1m"


def parse_port_range(port_str):
    """Interpreta string de portas no formato '1-1000' ou '22,80,443' ou misto."""
    ports = set()
    for part in port_str.split(","):
        part = part.strip()
        if "-" in part:
            try:
                inicio, fim = part.split("-", 1)
                for p in range(int(inicio.strip()), int(fim.strip()) + 1):
                    if 1 <= p <= 65535:
                        ports.add(p)
            except ValueError:
                continue
        else:
            try:
                p = int(part)
                if 1 <= p <= 65535:
                    ports.add(p)
            except ValueError:
                continue
    return sorted(ports)


def scan_port(host, port, timeout):
    """Tenta conectar a uma porta TCP e retorna (porta, estado, serviço)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        resultado = sock.connect_ex((host, port))
        if resultado == 0:
            try:
                servico = socket.getservbyport(port, "tcp")
            except OSError:
                servico = "desconhecido"
            sock.close()
            return (port, "aberta", servico)
        sock.close()
        return (port, "fechada", "")
    except socket.gaierror:
        return (port, "erro_dns", "")
    except socket.timeout:
        return (port, "timeout", "")
    except OSError as e:
        return (port, "erro", str(e))


def banner():
    """Exibe banner da ferramenta."""
    print(f"{CIANO}{NEGRITO}")
    print("  ╔══════════════════════════════════════╗")
    print("  ║       h4ck-toolkit — Port Scanner    ║")
    print("  ║       Scanner de Portas TCP v1.0     ║")
    print("  ╚══════════════════════════════════════╝")
    print(f"{RESET}")


def main():
    parser = argparse.ArgumentParser(
        prog="port_scanner.py",
        description="Scanner de portas TCP — h4ck-toolkit",
        epilog="Exemplo: python scanner/port_scanner.py --host scanme.nmap.org --ports 22,80,443",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--host", "-H",
        required=True,
        help="Endereço IP ou hostname do alvo (obrigatório)",
    )
    parser.add_argument(
        "--ports", "-p",
        required=True,
        help="Portas a escanear. Formatos: '1-1000', '22,80,443', ou '1-100,443,8080-8090'",
    )
    parser.add_argument(
        "--timeout", "-t",
        type=float,
        default=1.0,
        help="Timeout em segundos para cada conexão (padrão: 1.0)",
    )
    parser.add_argument(
        "--threads", "-T",
        type=int,
        default=100,
        help="Número de threads simultâneas (padrão: 100)",
    )

    args = parser.parse_args()

    portas = parse_port_range(args.ports)
    if not portas:
        print(f"{VERMELHO}[ERRO]{RESET} Nenhuma porta válida encontrada em '{args.ports}'.")
        sys.exit(1)

    banner()

    print(f"  {AMARELO}Alvo:{RESET}        {args.host}")
    print(f"  {AMARELO}Portas:{RESET}       {len(portas)} ({portas[0]}-{portas[-1]})")
    print(f"  {AMARELO}Timeout:{RESET}      {args.timeout}s")
    print(f"  {AMARELO}Threads:{RESET}      {args.threads}")
    print(f"  {AMARELO}Início:{RESET}       {datetime.now().strftime('%H:%M:%S')}")
    print()

    # Resolver DNS primeiro
    try:
        ip_real = socket.gethostbyname(args.host)
        print(f"  {CIANO}[*]{RESET} Resolvido: {args.host} -> {ip_real}")
        print()
    except socket.gaierror:
        print(f"  {VERMELHO}[ERRO]{RESET} Não foi possível resolver o hostname '{args.host}'.")
        sys.exit(1)

    abertas = []
    total = len(portas)
    processadas = 0

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futuros = {
            executor.submit(scan_port, args.host, port, args.timeout): port
            for port in portas
        }
        for futuro in as_completed(futuros):
            processadas += 1
            port, estado, info = futuro.result()
            if estado == "aberta":
                abertas.append((port, info))
                print(f"    {VERDE}✓ PORTA {port:>5}/tcp  ABERTA  [{info}]{RESET}")
            elif estado == "erro_dns":
                print(f"    {VERMELHO}✗ PORTA {port:>5}/tcp  ERRO DNS{RESET}")
                break
            # Barra de progresso a cada 10%
            if processadas % max(1, total // 10) == 0:
                pct = processadas * 100 // total
                print(f"  {CIANO}[{pct:>3}%]{RESET} Progresso: {processadas}/{total} portas escaneadas")

    print()
    print(f"  {CIANO}{NEGRITO}═══ RESUMO ═══{RESET}")
    print(f"  {AMARELO}Total escaneado:{RESET} {total} portas")
    print(f"  {VERDE}Portas abertas:{RESET}  {len(abertas)}")
    print(f"  {AMARELO}Fim:{RESET}           {datetime.now().strftime('%H:%M:%S')}")

    if abertas:
        print()
        print(f"  {NEGRITO}Portas abertas encontradas:{RESET}")
        for port, servico in sorted(abertas):
            print(f"    {VERDE}{port:>5}/tcp{RESET}  {servico}")
    print()


if __name__ == "__main__":
    main()
