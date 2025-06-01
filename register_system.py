import os
import sys

def generate_registration_file():
    """生成注册文件"""
    try:
        # 创建配置目录
        config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
        
        # 读取有效注册信息
        valid_reg_file = os.path.join(config_dir, 'valid_registration.dat')
        
        if not os.path.exists(valid_reg_file):
            print("错误: 有效注册信息文件不存在。请先运行 config/setup_registration.py")
            return False
        
        # 读取有效注册信息
        with open(valid_reg_file, 'r', encoding='utf-8') as vf:
            valid_content = vf.read().strip()
        
        # 写入注册文件
        registration_file = os.path.join(config_dir, 'registration.dat')
        with open(registration_file, 'w', encoding='utf-8') as f:
            f.write(valid_content)
        
        print(f"注册文件已生成: {registration_file}")
        
        # 解密显示注册信息
        decoded = ''.join([chr(ord(c) - 1) for c in valid_content])
        parts = decoded.split('|')
        if len(parts) >= 2:
            print(f"注册码: {parts[0]}")
            print(f"单位名称: {parts[1]}")
            
        print("系统已成功注册！")
        return True
    except Exception as e:
        print(f"生成注册文件失败: {str(e)}")
        return False

if __name__ == "__main__":
    if generate_registration_file():
        sys.exit(0)
    else:
        sys.exit(1)
