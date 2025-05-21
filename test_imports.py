import sys
import importlib

def test_imports():
    # 基本功能所需的包
    required = [
        'pandas',
        'openpyxl',
        'PIL',  # Pillow
        'fitz',  # PyMuPDF
        'docx',
        'tkinter'
    ]
    
    # 大型包（可能不需要）
    optional = [
        'torch',
        'transformers',
        'datasets',
        'sklearn',
        'scipy',
        'pyarrow',
        'accelerate'
    ]
    
    print("=== 测试基本导入 ===")
    for pkg in required:
        try:
            importlib.import_module(pkg)
            print(f"✓ {pkg}")
        except ImportError:
            print(f"✗ {pkg} (缺失 - 需要安装)")
    
    print("\n=== 测试可选导入 ===")
    for pkg in optional:
        try:
            importlib.import_module(pkg)
            print(f"✓ {pkg} (已安装，但可能不需要)")
        except ImportError:
            print(f"✗ {pkg} (未安装)")

if __name__ == "__main__":
    test_imports()
