# 程序的基本配置
APP_NAME = "人事档案软件"
VERSION = "1.0.0"

# 数据库配置
DATABASE = {
    'name': 'personnel.db',
    'path': 'database/'
}

# 文件路径配置
PATHS = {
    'import_dir': 'import/',
    'archive_dir': 'archive/',
    'logs_dir': 'logs/'
}

# 用户配置
USERS = {
    'admin': {
        'password': 'admin123',
        'role': 'admin'
    }
} 