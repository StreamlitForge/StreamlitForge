"""
提示模板集合 - 用于LLM生成过程
"""

# 应用生成的主提示模板
APP_GENERATION_PROMPT = """
请为我创建一个名为"{app_name}"的Streamlit网页应用，使用Python编程语言。

应用描述:
{app_description}

技术要求:
1. 必须使用Streamlit库创建web应用界面
2. 代码必须完整、可运行，包含必要的注释
3. 遵循UI主题风格: {ui_theme} - {theme_desc}
4. 复杂度级别: {complexity} - {complex_desc}
5. 使用Streamlit的最佳实践，如st.cache_data装饰器提高性能
6. 应用需要模块化设计，将功能分解为不同的函数或模块
7. 如果需要处理数据，优先使用pandas和numpy库
8. 如果需要数据可视化，优先使用plotly或matplotlib库
9. 所有的依赖库必须在requirements.txt中列出

{resources_text}

文件上传功能:
- 应用中应包含文件/图片上传功能
- 使用st.file_uploader组件实现上传功能
- 对上传的文件类型做适当的限制和验证
- 上传后应提供预览和处理功能

请提供以下文件:
1. app.py - Streamlit应用主文件
2. 如果功能复杂，将辅助功能拆分为单独的Python模块
3. 任何其他必要的资源文件

对于每个文件，使用以下格式:

文件: <文件名>
```python
<文件内容>
```

请让应用美观易用，遵循Streamlit应用的最佳实践。
"""

# 资源文件描述的格式模板
RESOURCES_FORMAT = """提供的资源文件:
{resources_list}

请确保在应用中适当使用这些资源文件。"""

# README.md模板
README_TEMPLATE = """# {app_name}

## 描述
{app_description}

## 使用方法

### 方法 1: 使用启动器（推荐）
1. 解压下载的文件
2. 双击 `启动应用.bat` (Windows) 或 `启动应用.sh` (Mac/Linux)

### 方法 2: 手动运行
1. 确保安装了Python 3.7+
2. 安装依赖:
   ```
   pip install -r requirements.txt
   ```
3. 运行应用:
   ```
   streamlit run app.py
   ```

## 功能说明
此应用使用Streamlit构建，是一个交互式Web应用。
浏览器将自动打开应用界面，您可以在其中进行交互。
应用包含文件/图片上传功能，可用于处理和分析用户提供的数据。
{resources_section}
## 自定义
所有源代码都包含在此包中，您可以自由修改它们以满足您的需求。
"""

# 资源部分模板
RESOURCES_SECTION_TEMPLATE = """
## 包含的资源文件

{images_section}
{data_section}
{other_section}
"""

IMAGES_SECTION_TEMPLATE = """### 图片资源
{images_list}
"""

DATA_SECTION_TEMPLATE = """### 数据资源
{data_list}
"""

OTHER_SECTION_TEMPLATE = """### 其他资源
{other_list}
"""

RESOURCE_ITEM_TEMPLATE = "- {name} (路径: {path})\n" 