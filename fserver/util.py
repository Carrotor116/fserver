DEBUG = True


def debug(*args, sep=' ', end='\n', file=None):
    if DEBUG:
        print(*args, sep=sep, end=end, file=file)


def get_ip_v4():
    import os
    ips = []
    if os.name == 'nt':
        import re
        ip_cmd = os.popen('ipconfig').read().split('\n')
        ip6_re = re.compile(r'(([0-9a-fA-F]{0,4}:){5}[0-9a-fA-F]{0,4})')
        for ind, s in enumerate(ip_cmd):
            if re.search(ip6_re, s):
                ips.append(ip_cmd[ind + 1][ip_cmd[ind + 1].index(':') + 2:])
    elif os.name == 'posix':
        sh = """ip -4 add | awk 'BEGIN{print"succeed"}/[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}..[0-9]{1,3}/{print $2}'"""
        ip_cmd = os.popen(sh).read()
        if 'succeed' in ip_cmd:
            ips.extend([i[:i.index('/')] for i in ip_cmd.split('\n') if i != '' and i != 'succeed'])
        else:
            sh = """ifconfig | awk '/inet addr/{print $2}' | awk -F: 'BEGIN{print "succeed"}{print $2}'"""
            ip_cmd = os.popen(sh).read()
            if 'succeed' in ip_cmd:
                ips.extend([i for i in ip_cmd.split('\n') if i != '' and i != 'succeed'])
    for ip in [i for i in ips]:
        if ip.startswith('169.254.'):
            ips.remove(ip)
    if '127.0.0.1' not in ips:
        ips.append('127.0.0.1')
    return ips


if __name__ == '__main__':
    print(get_ip_v4())
