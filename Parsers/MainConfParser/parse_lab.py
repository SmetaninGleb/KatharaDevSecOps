# parse_lab.py
import yaml
import os
from jinja2 import Environment, FileSystemLoader

def generate_lab_conf(meta, devices):
    lines = []
    # Scenario metadata
    for field in ["LAB_NAME", "LAB_DESCRIPTION", "LAB_VERSION", "LAB_AUTHOR", "LAB_EMAIL", "LAB_WEB"]:
        if field in meta:
            lines.append(f'{field}="{meta[field]}"')

    if lines:
        lines.append("")  # Blank line after metadata

    # Device configurations
    for dev_name, dev in devices.items():
        # Interfaces
        for idx, iface in enumerate(dev.get("interfaces", [])):
            net = iface["network"]
            mac = iface.get("mac")
            entry = f'{dev_name}[{idx}]="{net}'
            if mac:
                entry += f'/{mac}'
            entry += '"'
            lines.append(entry)

        # Kathara options (field=value)
        kathara_fields = ["image", "mem", "cpus", "port", "bridged", "ipv6", "exec", "shell", "num_terms", "ulimit"]
        for field in kathara_fields:
            if field in dev:
                val = str(dev[field]).lower() if isinstance(dev[field], bool) else dev[field]
                lines.append(f'{dev_name}[{field}]="{val}"')

        # Repeated fields
        for field in ["sysctl", "env"]:
            if field in dev:
                values = dev[field] if isinstance(dev[field], list) else [dev[field]]
                for v in values:
                    lines.append(f'{dev_name}[{field}]="{v}"')

        lines.append("")  # Blank line between devices

    return "\n".join(lines).strip()

def detect_cycle_util(node, visited, rec_stack, graph):
    visited.add(node)
    rec_stack.add(node)
    for neighbor in graph.get(node, []):
        if neighbor not in visited:
            if detect_cycle_util(neighbor, visited, rec_stack, graph):
                return True
        elif neighbor in rec_stack:
            return True
    rec_stack.remove(node)
    return False

def detect_cycles(graph):
    visited = set()
    rec_stack = set()
    for node in graph:
        if node not in visited:
            if detect_cycle_util(node, visited, rec_stack, graph):
                return True
    return False

def generate_lab_dep(dependencies):
    if detect_cycles(dependencies):
        raise ValueError("Cycle detected in dependencies!")
    lines = []
    for dev, deps in dependencies.items():
        if isinstance(deps, list) and deps:
            dep_list = " ".join(deps)
            lines.append(f"{dev}: {dep_list}")
    return "\n".join(lines)

def write_startup_file(dev_name, dev, templates_dir, out_dir):
    startup_path = os.path.join(out_dir, f"{dev_name}.startup")

    if "custom_startup" in dev:
        with open(startup_path, "w") as f:
            f.write(dev["custom_startup"])
    elif "startup_file" in dev:
        from shutil import copyfile
        copyfile(dev["startup_file"], startup_path)
    elif "template" in dev:
        env = Environment(loader=FileSystemLoader(templates_dir))
        from datetime import datetime
        env.globals["now"] = datetime.now
        template = env.get_template(f"{dev['template']}.startup.j2")
        with open(startup_path, "w") as f:
            f.write(template.render(**dev))

def main(config_path, output_dir="kathara_conf", templates_dir="templates"):
    os.makedirs(output_dir, exist_ok=True)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    meta = config.get("lab", {})
    devices = config.get("devices", {})
    dependencies = config.get("dependencies", {})

    lab_conf = generate_lab_conf(meta, devices)
    with open(os.path.join(output_dir, "lab.conf"), "w") as f:
        f.write(lab_conf)

    if dependencies:
        lab_dep = generate_lab_dep(dependencies)
        with open(os.path.join(output_dir, "lab.dep"), "w") as f:
            f.write(lab_dep)

    for dev_name, dev in devices.items():
        write_startup_file(dev_name, dev, templates_dir, output_dir)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Path to YAML configuration")
    parser.add_argument("--output", default="kathara_conf", help="Output directory")
    parser.add_argument("--templates", default="templates", help="Templates directory")
    args = parser.parse_args()

    main(args.config, args.output, args.templates)
