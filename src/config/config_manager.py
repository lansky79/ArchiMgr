import configparser
import os

class ConfigManager:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_file = 'config.ini'
        
    def load_config(self):
        # 加载配置文件
        if os.path.exists(self.config_file):
            self.config.read(self.config_file, encoding='utf-8')
        else:
            self.create_default_config()
            
    def create_default_config(self):
        # 创建默认配置
        self.config['Paths'] = {
            'import_dir': 'import/',
            'archive_dir': 'archive/'
        }
        self.save_config()
        
    def save_config(self):
        # 保存配置到文件
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f) 