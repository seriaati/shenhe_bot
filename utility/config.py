import yaml
from pathlib import Path


class Config:
    def __init__(self):
        project_path = Path(__file__).parents[1]
        config_path = project_path.joinpath('config.yaml')
        with open(config_path, encoding='utf-8') as file:
            config = yaml.full_load(file)

        self.main = config['main']
        self.dev = config['dev']
        self.lavalink = config['lavalink']


config = Config()
