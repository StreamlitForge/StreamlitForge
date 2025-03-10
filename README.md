# StreamlitForge - Streamlit应用生成平台

这是一个使用Streamlit开发的AI驱动平台，能够根据用户输入的需求描述，使用大型语言模型（LLM）生成完整的Streamlit应用程序，并提供多种部署和分发选项。

## 功能特点

- 基于用户需求生成自定义Streamlit应用
- 美观的用户界面，支持多种UI主题和复杂度级别
- 支持多种编程语言（Python、JavaScript、HTML/CSS/JS）
- 支持多种应用类型（Streamlit Web应用、桌面应用、命令行工具）
- 自动打包为跨平台智能启动包
- 提供源代码下载
- **一键部署到GitHub** - 将生成的应用自动部署到StreamlitForge组织
- **自动配置GitHub Pages** - 为每个应用创建美观的展示页面
- 支持自定义资源上传（图片、数据文件等）
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
3. 选择应用复杂度和界面风格
4. 可选：上传自定义资源（图片、数据文件等）
5. 点击"生成应用"按钮
6. 等待生成和打包过程完成
7. 选择下载源代码、智能启动包或部署到GitHub

### GitHub部署

要使用GitHub部署功能：

1. 在侧边栏的"GitHub部署配置"部分输入您的GitHub访问令牌
2. 生成应用后，点击"部署到StreamlitForge组织"按钮
3. 应用将自动部署到GitHub，并配置GitHub Pages
4. 部署完成后，您可以通过提供的链接访问仓库和网站

## 系统要求

- Python 3.7+
- 有效的OpenAI API密钥
- 用于GitHub部署功能的GitHub访问令牌（可选）

## 注意事项

- 生成的可执行文件和源代码存储在临时目录中，应用重启后可能无法访问之前生成的文件
- 复杂应用的生成可能需要更长时间和更多的API tokens
- GitHub部署功能需要有效的访问令牌，且令牌需要有StreamlitForge组织的访问权限
- GitHub Pages部署可能需要几分钟才能生效

## 贡献

欢迎对StreamlitForge做出贡献！您可以通过以下方式参与：

- 提交功能请求和Bug报告
- 改进文档
- 提交Pull Request

## 相关链接

- [StreamlitForge组织](https://github.com/StreamlitForge)
- [生成的应用示例](https://github.com/StreamlitForge)
