# Config/GUI.py
import tkinter as tk
from tkinter import scrolledtext, messagebox
import os
from Config.Base64 import process_base64_content
from Config.Logger import log_info, log_error

class NodeManagerGUI:
    """节点管理器GUI类"""
    
    def __init__(self, root):
        """
        初始化GUI
        
        Args:
            root: Tkinter根窗口
        """
        self.root = root
        self.text_area = None
        self.node_count_label = None
        self.setup_gui()
        
    def setup_gui(self):
        """设置GUI界面"""
        self.root.title("节点管理器")
        self.root.geometry("900x600")
        self.root.configure(bg="#f5f5f5")
        
        # 设置窗口居中
        window_width = 900
        window_height = 600
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 创建主框架
        main_frame = tk.Frame(self.root, bg="#ffffff", bd=1, relief=tk.SOLID)
        main_frame.place(relx=0.5, rely=0.5, anchor="center", width=860, height=560)
        
        # 标题区域 - 40像素
        title_frame = tk.Frame(main_frame, bg="#ffffff", height=40)
        title_frame.pack(fill=tk.X, padx=20)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="节点配置输入",
            font=("Microsoft YaHei", 14, "bold"),
            fg="#333333",
            bg="#ffffff"
        )
        title_label.pack(side=tk.LEFT, pady=10)
        
        # 说明标签区域 - 30像素
        instruction_frame = tk.Frame(main_frame, bg="#ffffff", height=30)
        instruction_frame.pack(fill=tk.X, padx=20)
        instruction_frame.pack_propagate(False)
        
        instruction_label = tk.Label(
            instruction_frame,
            text="请在下方输入节点内容（每行一个节点或Base64编码的订阅内容）：",
            font=("Microsoft YaHei", 10),
            fg="#666666",
            bg="#ffffff",
            justify="left"
        )
        instruction_label.pack(side=tk.LEFT)
        
        # 文本输入区域 - 350像素（占用主要空间）
        text_frame = tk.Frame(main_frame, bg="#ffffff")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(5, 10))
        
        # 添加滚动文本区域
        self.text_area = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#fafafa",
            fg="#333333",
            padx=12,
            pady=12,
            relief=tk.SOLID,
            borderwidth=1
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)
        
        # 按钮区域 - 50像素
        button_frame = tk.Frame(main_frame, bg="#ffffff", height=50)
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 5))
        button_frame.pack_propagate(False)
        
        # 清空按钮（靠左）
        clear_btn = tk.Button(
            button_frame,
            text="清空",
            command=self.clear_text,
            bg="#e0e0e0",
            fg="#333333",
            font=("Microsoft YaHei", 10),
            padx=20,
            pady=6,
            relief=tk.FLAT,
            activebackground="#cccccc"
        )
        clear_btn.place(relx=0.0, rely=0.5, anchor="w")
        
        # 创建右侧按钮容器
        right_button_frame = tk.Frame(button_frame, bg="#ffffff")
        right_button_frame.place(relx=1.0, rely=0.5, anchor="e")
        
        # 取消按钮（靠右侧第一个）
        cancel_btn = tk.Button(
            right_button_frame,
            text="取消",
            command=self.root.destroy,
            bg="#f44336",
            fg="white",
            font=("Microsoft YaHei", 10),
            padx=20,
            pady=6,
            relief=tk.FLAT,
            activebackground="#d32f2f"
        )
        cancel_btn.pack(side=tk.RIGHT)
        
        # 保存按钮（靠右侧第二个，在取消按钮左边）
        save_btn = tk.Button(
            right_button_frame,
            text="保存并继续",
            command=self.save_and_close,
            bg="#4CAF50",
            fg="white",
            font=("Microsoft YaHei", 10, "bold"),
            padx=25,
            pady=6,
            relief=tk.FLAT,
            activebackground="#45a049"
        )
        save_btn.pack(side=tk.RIGHT, padx=(0, 12))
        
        # 节点数量显示区域 - 30像素（位于最下方）
        count_frame = tk.Frame(main_frame, bg="#f8f9fa", height=30)
        count_frame.pack(fill=tk.X, side=tk.BOTTOM)
        count_frame.pack_propagate(False)
        
        # 添加一条分割线
        separator = tk.Frame(main_frame, bg="#e0e0e0", height=1)
        separator.pack(fill=tk.X, side=tk.BOTTOM, padx=20)
        
        # 节点数量标签（居中显示）
        self.node_count_label = tk.Label(
            count_frame,
            text="检测到 0 个节点",
            font=("Microsoft YaHei", 9),
            fg="#999999",
            bg="#f8f9fa"
        )
        self.node_count_label.pack(expand=True)
        
        # 添加悬停效果
        for btn, hover_color in [
            (clear_btn, "#cccccc"),
            (save_btn, "#45a049"),
            (cancel_btn, "#d32f2f")
        ]:
            original_color = btn.cget("bg")
            btn.bind("<Enter>", lambda e, b=btn, h=hover_color: self.on_hover_enter(e, b, h))
            btn.bind("<Leave>", lambda e, b=btn, oc=original_color: self.on_hover_leave(e, b, oc))
        
        # 键盘快捷键
        self.root.bind('<Control-s>', lambda e: self.save_and_close())
        self.root.bind('<Control-q>', lambda e: self.root.destroy())
        self.root.bind('<Escape>', lambda e: self.root.destroy())
        
        # 让文本区域获得焦点
        self.text_area.focus_set()
        
        # 绑定文本区域内容变化事件，更新节点数量
        self.text_area.bind('<KeyRelease>', self.update_node_count)
        self.text_area.bind('<ButtonRelease>', self.update_node_count)
        
        # 初始更新节点数量
        self.update_node_count()
        
        # 设置窗口最小大小
        self.root.minsize(900, 600)
        self.root.maxsize(900, 600)
        
        log_info("GUI窗口已创建")
    
    def on_hover_enter(self, event, button, color):
        """鼠标悬停进入事件"""
        button.config(bg=color, cursor="hand2")
    
    def on_hover_leave(self, event, button, original_color):
        """鼠标悬停离开事件"""
        button.config(bg=original_color, cursor="")
    
    def clear_text(self):
        """清空文本区域"""
        if messagebox.askyesno("确认", "确定要清空所有内容吗？"):
            self.text_area.delete("1.0", tk.END)
    
    def update_node_count(self, event=None):
        """更新节点数量显示"""
        content = self.text_area.get("1.0", tk.END).strip()
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        count = len(lines)
        self.node_count_label.config(text=f"检测到 {count} 个节点")
        
        # 根据节点数量调整颜色
        if count == 0:
            self.node_count_label.config(fg="#999999", font=("Microsoft YaHei", 9))
        elif count > 0 and count <= 50:
            self.node_count_label.config(fg="#4CAF50", font=("Microsoft YaHei", 9, "bold"))
        elif count > 50:
            self.node_count_label.config(fg="#FF9800", font=("Microsoft YaHei", 9, "bold"))
    
    def save_and_close(self):
        """保存并关闭窗口"""
        content = self.text_area.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("警告", "请输入节点内容！")
            return
            
        try:
            # 确保input目录存在
            os.makedirs("input", exist_ok=True)
            
            # 使用base64处理函数来处理内容
            nodes = process_base64_content(content)
            
            # 保存处理后的节点列表
            with open("input/Input.txt", "w", encoding="utf-8") as f:
                for node in nodes:
                    f.write(node + "\n")
            
            log_info(f"已成功保存 {len(nodes)} 个节点到 Input/Input.txt")
            self.root.destroy()
        except Exception as e:
            log_error(f"保存文件时出错：{str(e)}")
            messagebox.showerror("错误", f"保存文件时出错：{str(e)}")
    
    def run(self):
        """运行GUI主循环"""
        self.root.mainloop()

def create_gui():
    """
    创建并运行GUI窗口
    
    Returns:
        None: 直接运行GUI，完成后返回
    """
    root = tk.Tk()
    app = NodeManagerGUI(root)
    app.run()