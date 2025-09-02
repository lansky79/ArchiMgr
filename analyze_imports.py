import sys
import importlib
from collections import defaultdict
import pkgutil
import os

def get_imports_in_file(filepath):
    """分析单个Python文件中的导入语句"""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    imports = set()
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        # 跳过注释和空行
        if not line or line.startswith('#'):
            continue
            
        # 匹配 import xxx
        if line.startswith('import '):
            for pkg in line[7:].split(','):
                pkg = pkg.strip().split(' ')[0].split('.')[0]
                if pkg and not pkg.startswith('_'):
                    imports.add(pkg)
        # 匹配 from xxx import yyy
        elif line.startswith('from '):
            parts = line[5:].split(' import ')
            if len(parts) == 2:
                pkg = parts[0].strip().split(' ')[0].split('.')[0]
                if pkg and not pkg.startswith('_'):
                    imports.add(pkg)
    
    return imports

def scan_project_imports(root_dir):
    """扫描项目中的所有Python文件，分析导入的包"""
    imports = set()
    
    for root, _, files in os.walk(root_dir):
        # 排除虚拟环境和构建目录
        if any(x in root.lower() for x in ['venv', 'env', 'build', 'dist', '.git', '__pycache__', '.idea']):
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    file_imports = get_imports_in_file(filepath)
                    if file_imports:
                        imports.update(file_imports)
                except Exception as e:
                    print(f"[警告] 分析 {filepath} 时出错: {e}")
    
    return sorted(imports)

def get_installed_packages():
    """获取已安装的包及其大小"""
    packages = {}
    for pkg in pkgutil.iter_modules():
        try:
            module = importlib.import_module(pkg.name)
            if hasattr(module, '__file__') and module.__file__:
                try:
                    size = os.path.getsize(module.__file__) / (1024 * 1024)  # MB
                    packages[pkg.name] = round(size, 2)
                except (OSError, FileNotFoundError):
                    continue
        except (ImportError, ModuleNotFoundError):
            continue
    return packages

def main():
    print("正在分析项目导入...")
    project_imports = scan_project_imports('src')
    
    print("\n=== 项目导入的包 ===")
    for pkg in project_imports:
        print(f"- {pkg}")
    
    print("\n=== 已安装的大型包（>5MB）===")
    installed = get_installed_packages()
    large_pkgs = {k: v for k, v in installed.items() if v > 5}
    
    if not large_pkgs:
        print("没有找到大于5MB的包")
    else:
        for pkg, size in sorted(large_pkgs.items(), key=lambda x: x[1], reverse=True):
            print(f"- {pkg}: {size}MB")
    
    print("\n=== 可能不需要的包 ===")
    common_unused = ['torch', 'tensorflow', 'transformers', 'datasets', 'sklearn', 'scipy', 'numpy', 'pandas']
    for pkg in common_unused:
        if pkg in installed and pkg not in project_imports:
            print(f"- {pkg} (已安装但未在项目中使用)")

if __name__ == "__main__":
    main()
