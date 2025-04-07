import os
import yaml
import ipaddress
import subprocess

folder_path = "./kathara_config"
ip_mask = "/24"
ip_addresses = ipaddress.ip_network(f"192.168.1.0{ip_mask}")
next_ip_addr_ind = 2

def parse_docker_compose_to_kathara(docker_compose_file):
    global next_ip_addr_ind
    with open(docker_compose_file, 'r') as f:
        docker_compose = yaml.safe_load(f)

    kathara_config = []

    for service_name, service_data in docker_compose['services'].items():
        kathara_service = {}

        # Имя сервиса
        kathara_service['name'] = service_name.replace('-', '')

        kathara_service['build'] = service_data.get('build', None)

        # Образ Docker
        kathara_service['image'] = service_data.get('image', None)

        if (kathara_service['build'] != None and kathara_service['image'] == None):
            docker_build_command = ["sudo", "docker", "build", "-t", f"katharasectemp/{service_name}", kathara_service['build']]
            subprocess.run(docker_build_command, check=True)
            kathara_service['image'] = f"katharasectemp/{service_name}"

        kathara_service['ip'] = ip_addresses[next_ip_addr_ind]
        next_ip_addr_ind += 1

        # Перевод портов
        if 'ports' in service_data:
            ports = []
            for port_mapping in service_data['ports']:
                host_port, container_port = port_mapping.split(':')
                ports.append(f"{container_port}:{host_port}")
            kathara_service['ports'] = ports

        # Перевод переменных окружения
        if 'environment' in service_data:
            environment_vars = []
            for env_str in service_data['environment']:
                key, value = env_str.split("=", 1)
                environment_vars.append(f"{key}={value}")
            kathara_service['environment'] = environment_vars

        kathara_config.append(kathara_service)

    return kathara_config

def add_to_file_dns(file_to_write):
        file_to_write.write(f"dnsmasq[0]=\"A\"\n")
        file_to_write.write(f"dnsmasq[image]=\"katharasec/dnsmasq\"\n")
        file_to_write.write("\n")

def gen_startup_dns(services):
    with open(f"{folder_path}/dnsmasq.startup", 'w') as f:
        f.write(f"ip address add {ip_addresses[1]}{ip_mask} dev eth0\n")
        dns_conf_command = f"echo -e \"no-dhcp-interface=\\ninterface=lo0\\ninterface=eth0\\nserver=8.8.8.8\\n"
        for service in services:
            dns_conf_command += f"address=/{service['name']}/{service['ip']}\\n"
        dns_conf_command += "\" > /etc/dnsmasq.conf\n"
        f.write(dns_conf_command)
        f.write("dnsmasq --conf-file=/etc/dnsmasq.conf -d")

def gen_startup_file(service):
    with open(f"{folder_path}/{service['name']}.startup", 'w') as f:
        f.write(f"ip address add {service['ip']}{ip_mask} dev eth0\n")
        f.write(f"echo \"nameserver {ip_addresses[1]}\" | tee /etc/resolv.conf")

def generate_kathara_config(docker_compose_file, output_file):
    kathara_config = parse_docker_compose_to_kathara(docker_compose_file)

    with open(output_file, 'w') as f:
        gen_startup_dns(kathara_config)
        add_to_file_dns(f)
        for service in kathara_config:
            # f.write(f"# Service: {service['name']}\n")
            gen_startup_file(service)
            f.write(f"{service['name']}[0]=\"A\"\n")
            f.write(f"{service['name']}[image]=\"{service['image']}\"\n")
            if 'ports' in service:
                for port in service['ports']:
                    f.write(f"{service['name']}[port]=\"{port}\"\n")
            if 'environment' in service:
                for env in service['environment']:
                    f.write(f"{service['name']}[env]=\"{env}\"\n")
            f.write("\n")

# Использование программы
os.makedirs(folder_path, exist_ok=True)
docker_compose_file = 'docker-compose.yml'
output_file = f'{folder_path}/lab.conf'

generate_kathara_config(docker_compose_file, output_file)
print(f"Kathara конфигурация была сохранена в {output_file}")

