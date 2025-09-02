import sys
import os
import tkinter as tk
from tkinter import messagebox

def main():
    try:
        # 创建主窗口
        root = tk.Tk()
        root.title("测试应用")
        
        # 显示当前工作目录
        info = f"程序启动成功！\n\n"
        info += f"工作目录: {os.getcwd()}\n"
        info += f"Python 版本: {sys.version[:50]}...\n"
        
        # 显示消息框
        messagebox.showinfo("测试", info)
        
        # 运行主循环
        root.mainloop()
        
    except Exception as e:
        # 如果出现错误，显示错误信息
        error_msg = f"程序出错:\n{str(e)}\n\n"
        error_msg += f"错误类型: {type(e).__name__}\n"
        error_msg += f"文件: {__file__}\n"
        error_msg += f"当前目录: {os.getcwd()}"
        
        # 尝试使用 tkinter 显示错误
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("错误", error_msg)
        except:
            # 如果 tkinter 也出错了，直接打印
            print(error_msg)
            input("按 Enter 键退出...")

if __name__ == "__main__":
    main()
