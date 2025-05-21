import os
import shutil
import sys

def copy_resources():
    """复制必要资源到dist目录"""
    try:
        # 源目录和目标目录
        base_dir = os.path.dirname(os.path.abspath(__file__))
        dist_dir = os.path.join(base_dir, 'dist')
        
        # 确保dist目录存在
        if not os.path.exists(dist_dir):
            os.makedirs(dist_dir)
        
        # 需要复制的目录
        dirs_to_copy = ['resources', 'config', 'src']
        
        # 复制每个目录
        for dir_name in dirs_to_copy:
            src = os.path.join(base_dir, dir_name)
            dst = os.path.join(dist_dir, dir_name)
            
            # 如果目标目录已存在，先删除
            if os.path.exists(dst):
                print(f"正在删除旧目录: {dst}")
                shutil.rmtree(dst, ignore_errors=True)
            
            # 复制目录
            if os.path.exists(src):
                print(f"正在复制: {src} -> {dst}")
                shutil.copytree(src, dst)
            else:
                print(f"警告: 源目录不存在: {src}")
        
        print("\n资源复制完成！")
        print(f"请确保以下文件和目录存在于 {dist_dir} 目录中：")
        print("- ArchiveManager.exe")
        print("- resources/")
        print("- config/")
        print("- src/")
        print("\n然后可以运行 ArchiveManager.exe 启动程序。")
        
        return True
        
    except Exception as e:
        print(f"复制资源时出错: {str(e)}")
        return False

if __name__ == "__main__":
    if copy_resources():
        sys.exit(0)
    else:
        sys.exit(1)
