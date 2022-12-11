class ConfigLoader:
    @classmethod
    def load(cls, path: str):
        if path.endswith('.yml'):
            return cls.load_yaml(path)
        if path.endswith('.json'):
            return cls.load_json(path)
        raise RuntimeError(f'Unknown file type: {path}')

    @classmethod
    def write(cls, path: str, config):
        if path.endswith('.yml'):
            return cls.write_yaml(path, config)
        if path.endswith('.json'):
            return cls.write_json(path, config)
        raise RuntimeError(f'Unknown file type: {path}')

    @staticmethod
    def copy(src: str, dst: str):
        import shutil

        shutil.copyfile(src, dst)

    @staticmethod
    def rename(src: str, dst: str):
        from os import rename

        rename(src, dst)

    @staticmethod
    def load_json(path: str):
        from json import JSONDecodeError, load

        with open(path, "r", encoding="utf-8") as fp:
            try:
                config = load(fp)
            except JSONDecodeError as e:
                raise RuntimeError(f"Unable to parse {path}: {e}")
        return config

    @staticmethod
    def load_yaml(path: str):
        import yaml

        with open(path, "r", encoding="utf-8") as fp:
            try:
                config = yaml.safe_load(fp)
            except yaml.YAMLError as e:
                raise RuntimeError(f"Unable to parse {path}: {e}")
        return config

    @staticmethod
    def write_json(path: str, config):
        import json

        with open(path, "w", encoding="utf-8") as fp:
            fp.write(json.dumps(config, indent=4))

    @classmethod
    def write_yaml(cls, path: str, config):
        with open(path, "w", encoding="utf-8") as fp:
            cls.dump_yaml(fp, config)

    @staticmethod
    def dump_yaml(fp, config):
        import yaml

        return yaml.dump(config, fp, allow_unicode=True, indent=2, sort_keys=False)
