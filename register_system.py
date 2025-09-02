import os
import sys

def generate_registration_file():
    """生成注册文件"""
    try:
        # 创建配置目录
        config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
        
        # 注册信息
        reg_code = "2xdqzr5zyghj"
        user_name = "新都区自然资源规划局"
        
        # 加密注册信息（简单位移加密）
        content = f"{reg_code}|{user_name}"
        encoded_content = ''.join([chr(ord(c) + 1) for c in content])
        
        # 写入注册文件
        registration_file = os.path.join(config_dir, 'registration.dat')
        with open(registration_file, 'w', encoding='utf-8') as f:
            f.write(encoded_content)
        
        print(f"注册文件已生成: {registration_file}")
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
