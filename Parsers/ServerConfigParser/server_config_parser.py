import os
import argparse
from jinja2 import Template

def main():
    parser = argparse.ArgumentParser(description="Генерация server-config.json из шаблона и списка инструментов.")
    parser.add_argument("--template", required=True, help="Путь к шаблону server-config.json.template")
    parser.add_argument("--tools", required=True, help="Путь к файлу tool_ids.txt")
    parser.add_argument("--output", required=True, help="Путь к выходному файлу server-config.json")
    parser.add_argument("--dd-ip", help="IP адрес DefectDojo")
    parser.add_argument("--dd-port", help="Порт DefectDojo")
    parser.add_argument("--dd-token", help="Token DefectDojo")

    args = parser.parse_args()

    # Считываем список инструментов
    with open(args.tools, "r") as f:
        tools = [line.strip() for line in f if line.strip()]

    # Считываем шаблон
    with open(args.template, "r") as f:
        template = Template(f.read())

    # Формируем контекст: сначала берём из аргументов, потом из окружения, потом пусто
    context = {
        "tools": tools,
        "DEFECTDOJO_IP": args.dd_ip or os.environ.get("DEFECTDOJO_IP", ""),
        "DEFECTDOJO_PORT": args.dd_port or os.environ.get("DEFECTDOJO_PORT", ""),
        "DEFECTDOJO_TOKEN": args.dd_token or os.environ.get("DEFECTDOJO_TOKEN", "")
    }

    # Рендер шаблона
    rendered = template.render(**context)

    # Сохраняем в файл
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        f.write(rendered)

    print(f"✅ Конфигурация сгенерирована: {args.output}")

if __name__ == "__main__":
    main()
