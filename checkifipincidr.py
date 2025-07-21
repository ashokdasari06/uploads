import ipaddress

cidrs = [
    "10.0.0.0/16",
    "10.1.252.0/24",
    "172.31.252.0/24",
    "192.168.100.0/22"
]

target_suffix = ".252.212"
matching = []

for cidr in cidrs:
    net = ipaddress.ip_network(cidr)
    for ip in net.hosts():
        if str(ip).endswith(target_suffix):
            matching.append(cidr)
            break

for cidr in matching:
    print(f"{cidr} contains an IP ending with {target_suffix}")
