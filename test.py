from pathlib import Path

import yaml


def main():
    root = Path(__file__).resolve().parent
    config_path = root / "config.yaml"

    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    model_path = root / config["system"]["model_path"]

    print("Config loaded:", config_path)
    print("Model exists:", model_path.exists(), model_path)
    print("Configured modes:", ", ".join(sorted(config.get("modes", {}).keys())))


if __name__ == "__main__":
    main()
