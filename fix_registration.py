import os
import sys

def create_registration():
    """创建注册文件"""
    try:
        # 确保配置目录存在
        config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
        os.makedirs(config_dir, exist_ok=True)
        
        # 注册信息
        reg_info = "2xdqzr5zyghj|新都区自然资源规划局"
        
        # 简单加密（每个字符ASCII码+1）
        encrypted = ''.join(chr(ord(c) + 1) for c in reg_info)
        
        # 写入文件
        with open(os.path.join(config_dir, 'registration.dat'), 'w', encoding='utf-8') as f:
            f.write(encrypted)
            
        print("注册文件已创建！")
        return True
        
    except Exception as e:
        print(f"创建注册文件失败: {e}")
        return False

if __name__ == "__main__":
    if create_registration():
        sys.exit(0)
    else:
        sys.exit(1)
