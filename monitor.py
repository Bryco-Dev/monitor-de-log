import random
from datetime import datetime, timedelta

IP_FORCA_BRUTA = '45.33.32.156'
IP_BOT         = '66.249.66.1'
NOME_ARQUIVO   = 'log.txt'

# ============================================================
# PARTE 1 - GERAR LOGS
# ============================================================

def gerar_logs(quantidade):
    with open(NOME_ARQUIVO, 'w', encoding='UTF-8') as arq:
        for i in range(quantidade):
            recurso   = escolher_recurso(i, quantidade)
            status    = escolher_status(i, quantidade, recurso)
            ip        = escolher_ip(i, quantidade)
            metodo    = 'POST' if recurso == '/login' and random.randint(1,3) != 1 else 'GET'
            tempo     = escolher_tempo(i, quantidade, status)
            tamanho   = random.randint(500,5000) if status == 200 else random.randint(100,500)
            protocolo = ['HTTP/1.0','HTTP/1.0','HTTP/1.1','HTTP/1.1','HTTP/2','HTTP/2'][i % 6]
            agente    = 'Bot' if IP_BOT == ip else ['Chrome','Chrome','Firefox','Firefox','Script','Script'][i % 6]
            data      = datetime(2026, 3, 1, 8, 0, 0) + timedelta(minutes=i * 3)
            data_str  = '[' + data.strftime('%d/%m/%Y %H:%M:%S') + ']'

            linha = (data_str + ' ' + ip + ' - ' + metodo + ' - ' + str(status) +
                     ' - ' + recurso + ' - ' + str(tempo) + 'ms - ' +
                     str(tamanho) + 'B - ' + protocolo + ' - ' + agente + ' - /home')

            arq.write(linha + '\n')

    print('Arquivo gerado com ' + str(quantidade) + ' logs.')


def escolher_recurso(i, total):
    if i % 15 == 7:  return '/admin'
    if i % 20 == 13: return '/backup'
    if i % 25 == 17: return '/config'
    if i % 30 == 23: return '/private'

    inicio_fb = total // 4
    if inicio_fb <= i < inicio_fb + 6:
        return '/login'

    return ['/home', '/login', '/produtos', '/contato'][i % 4]


def escolher_status(i, total, recurso):
    inicio_500 = total // 3
    if inicio_500 <= i < inicio_500 + 4:
        return 500

    inicio_fb = total // 4
    if inicio_fb <= i < inicio_fb + 6:
        return 403

    if recurso in ('/admin', '/backup', '/config', '/private'):
        return random.choice([403, 403, 404])

    n = random.randint(1, 100)
    if n <= 65: return 200
    if n <= 78: return 403
    if n <= 90: return 404
    return 500


def escolher_ip(i, total):
    inicio_fb = total // 4
    if inicio_fb <= i < inicio_fb + 6:
        return IP_FORCA_BRUTA

    inicio_bot = total // 2
    if inicio_bot <= i < inicio_bot + 7:
        return IP_BOT

    return (str(random.randint(1, 254)) + '.' +
            str(random.randint(0, 255)) + '.' +
            str(random.randint(0, 255)) + '.' +
            str(random.randint(1, 254)))


def escolher_tempo(i, total, status):
    inicio_deg = total // 5
    if inicio_deg <= i < inicio_deg + 5:
        return 100 + (i - inicio_deg) * 380 + random.randint(0, 40)

    if status == 500:
        return random.randint(1200, 2000)

    return random.randint(50, 1999)


# ============================================================
# PARTE 2 - ANALISAR LOGS
# ============================================================

def analisar_logs():
    total = total_200 = total_403 = total_404 = total_500 = 0
    rapidos = normais = lentos = 0
    soma_tempos = maior_tempo = 0
    menor_tempo = 999999

    ips       = {}
    ips_erros = {}
    recursos  = {}

    ev_forca_bruta = ev_falha_critica = ev_degradacao = ev_bot = 0
    ip_forca_bruta = ip_bot = ''

    seq_fb_ip = ''; seq_fb   = 0
    seq_500   = 0
    seq_deg   = 0;  tempo_ant = -1
    seq_bot_ip = ''; seq_bot  = 0

    admin_indevido = rotas_sens = falhas_sens = 0

    with open(NOME_ARQUIVO, 'r', encoding='UTF-8') as arq:
        for linha in arq:
            linha = linha.strip()
            if not linha:
                continue

            campos = extrair_campos(linha)
            if campos is None:
                continue

            ip      = campos['ip']
            status  = campos['status']
            recurso = campos['recurso']
            tempo   = campos['tempo']
            agente  = campos['agente']

            total += 1

            if   status == '200': total_200 += 1
            elif status == '403': total_403 += 1
            elif status == '404': total_404 += 1
            elif status == '500': total_500 += 1

            ips[ip] = ips.get(ip, 0) + 1
            if status != '200':
                ips_erros[ip] = ips_erros.get(ip, 0) + 1

            recursos[recurso] = recursos.get(recurso, 0) + 1

            soma_tempos += tempo
            maior_tempo  = max(maior_tempo, tempo)
            menor_tempo  = min(menor_tempo, tempo)

            if   tempo < 200: rapidos += 1
            elif tempo < 800: normais += 1
            else:             lentos  += 1

            if ip == seq_fb_ip and recurso == '/login' and status == '403':
                seq_fb += 1
                if seq_fb == 3:
                    ev_forca_bruta += 1
                    ip_forca_bruta  = ip
                    seq_fb          = 0
            elif recurso == '/login' and status == '403':
                seq_fb_ip = ip
                seq_fb    = 1
            else:
                seq_fb_ip = ''
                seq_fb    = 0

            if status == '500':
                seq_500 += 1
                if seq_500 == 3:
                    ev_falha_critica += 1
                    seq_500           = 0
            else:
                seq_500 = 0

            if tempo_ant != -1:
                if tempo > tempo_ant:
                    seq_deg += 1
                    if seq_deg == 3:
                        ev_degradacao += 1
                        seq_deg        = 0
                else:
                    seq_deg = 0
            tempo_ant = tempo

            if ip == seq_bot_ip:
                seq_bot += 1
                if seq_bot == 5:
                    ev_bot   += 1
                    ip_bot    = ip
                    seq_bot   = 0
            else:
                seq_bot_ip = ip
                seq_bot    = 1

            if 'Bot' in agente or 'Crawler' in agente:
                ev_bot += 1
                if not ip_bot:
                    ip_bot = ip

            if recurso == '/admin' and status != '200':
                admin_indevido += 1

            if recurso in ('/admin', '/backup', '/config', '/private'):
                rotas_sens += 1
                if status != '200':
                    falhas_sens += 1

    total_erros = total_403 + total_404 + total_500
    disponib    = (total_200 / total) * 100 if total else 0
    taxa_erro   = (total_erros / total) * 100 if total else 0
    tempo_medio = soma_tempos / total if total else 0

    ip_top       = max(ips,       key=ips.get,       default='')
    ip_top_erros = max(ips_erros, key=ips_erros.get, default='')
    recurso_top  = max(recursos,  key=recursos.get,  default='')

    perc_lentos = (lentos / total) * 100 if total else 0
    if ev_falha_critica >= 1 or disponib < 70:
        estado = 'CRITICO'
    elif disponib < 85 or perc_lentos > 30:
        estado = 'INSTAVEL'
    elif disponib < 95 or ev_bot > 0 or ev_forca_bruta > 0:
        estado = 'ATENCAO'
    else:
        estado = 'SAUDAVEL'

    print('\n' + '=' * 52)
    print('          RELATORIO - MONITOR LOGPY')
    print('=' * 52)
    print('VISAO GERAL')
    print('  Total de acessos:          ' + str(total))
    print('  Sucessos (200):            ' + str(total_200))
    print('  Total de erros:            ' + str(total_erros))
    print('  Erros criticos (500):      ' + str(total_500))
    print('  Disponibilidade:           ' + str(round(disponib, 2)) + '%')
    print('  Taxa de erro:              ' + str(round(taxa_erro, 2)) + '%')
    print('\nDESEMPENHO')
    print('  Tempo medio:               ' + str(round(tempo_medio, 2)) + 'ms')
    print('  Maior tempo:               ' + str(maior_tempo) + 'ms')
    print('  Menor tempo:               ' + str(menor_tempo) + 'ms')
    print('  Rapidos (<200ms):          ' + str(rapidos))
    print('  Normais (200-799ms):       ' + str(normais))
    print('  Lentos (>=800ms):          ' + str(lentos))
    print('\nDISTRIBUICAO DE STATUS')
    print('  200: ' + str(total_200) + '  |  403: ' + str(total_403) +
          '  |  404: ' + str(total_404) + '  |  500: ' + str(total_500))
    print('\nRANKINGS')
    print('  Recurso mais acessado:     ' + recurso_top)
    print('  IP mais ativo:             ' + ip_top)
    print('  IP com mais erros:         ' + ip_top_erros)
    print('\nSEGURANCA')
    print('  Forca bruta detectada:     ' + str(ev_forca_bruta) + 'x  |  IP: ' + ip_forca_bruta)
    print('  Acessos indevidos /admin:  ' + str(admin_indevido))
    print('  Suspeitas de bot:          ' + str(ev_bot) + 'x  |  IP: ' + ip_bot)
    print('  Rotas sensiveis acessadas: ' + str(rotas_sens))
    print('  Falhas em rotas sensiveis: ' + str(falhas_sens))
    print('\nINCIDENTES')
    print('  Degradacao de desempenho:  ' + str(ev_degradacao) + 'x')
    print('  Falhas criticas (500x3):   ' + str(ev_falha_critica) + 'x')
    print('\nESTADO DO SISTEMA:          ' + estado)
    print('=' * 52)


def extrair_campos(linha):
    try:
        fim_data = linha.find(']')
        resto    = linha[fim_data + 2:]
        partes   = resto.split(' - ')

        return {
            'ip'      : partes[0],
            'metodo'  : partes[1],
            'status'  : partes[2],
            'recurso' : partes[3],
            'tempo'   : int(partes[4].replace('ms', '')),
            'agente'  : partes[7],
        }
    except:
        return None


# ============================================================
# PARTE 3 - MENU
# ============================================================

def menu():
    while True:
        print('\n=== Monitor LogPy ===')
        print('1 - Gerar logs')
        print('2 - Analisar logs')
        print('3 - Gerar e analisar')
        print('4 - Sair')

        opcao = input('Escolha: ')

        if opcao == '1':
            try:
                qtd = int(input('Quantidade de logs: '))
                gerar_logs(qtd)
            except:
                print('Quantidade invalida.')

        elif opcao == '2':
            analisar_logs()

        elif opcao == '3':
            try:
                qtd = int(input('Quantidade de logs: '))
                gerar_logs(qtd)
                analisar_logs()
            except:
                print('Quantidade invalida.')

        elif opcao == '4':
            print('Ate mais!')
            break

        else:
            print('Opcao invalida.')

menu()
