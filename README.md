# 应用程序生成器

这是一个使用Streamlit开发的Web应用，能够根据用户输入的需求描述，使用人工智能（LLM）生成应用程序，并提供可执行文件和源代码下载。

## 功能特点

- 基于用户需求生成自定义应用
- 支持多种编程语言（Python、JavaScript、HTML/CSS/JS）
- 支持多种应用类型（桌面应用、命令行工具、Web应用）
- 自动打包为可执行文件
- 提供源代码下载
- 支持自定义OpenAI API密钥和端点

## 安装与使用

1. 安装依赖：

```bash
pip install -r requirements.txt
```

2. 运行应用：

```bash
streamlit run app.py
```

3. 在浏览器中打开显示的URL（通常是 http://localhost:8501）

## 使用方法

1. 在侧边栏配置您的OpenAI API密钥和端点
2. 填写应用名称和详细需求描述
3. 选择应用类型、编程语言和复杂度
4. 点击"生成应用"按钮
5. 等待生成和打包过程完成
6. 下载生成的可执行文件和源代码

## 系统要求

- Python 3.7+
- 用于打包的PyInstaller（会自动安装）
- 有效的OpenAI API密钥

## 注意事项

- 生成的可执行文件和源代码存储在临时目录中，应用重启后可能无法访问之前生成的文件
- 复杂应用的生成可能需要更长时间和更多的API tokens
- Python应用的打包需要PyInstaller，会自动安装 # StreamlitForge
