"""
应用配置文件 - 存储默认设置和常量
"""

# API相关配置
DEFAULT_API_ENDPOINT = "https://api.openai.com/v1"
DEFAULT_MODELS = ["gpt-4", "gpt-3.5-turbo"]
DEFAULT_MODEL = "gpt-3.5-turbo"

# UI配置
APP_TITLE = "Streamlit应用生成器"
APP_ICON = "🚀"
APP_DESCRIPTION = "输入您的需求，AI将为您生成一个美观的Streamlit网页应用，并提供可在任何平台运行的启动器。"

# 应用类型选项
UI_THEMES = {
    "简约现代": "简洁的设计，使用柔和的颜色，重视留白和易用性，适合数据展示和分析。",
    "丰富多彩": "使用鲜艳的颜色和动态元素，视觉效果丰富，适合创意和交互性强的应用。",
    "商务专业": "使用深色和蓝色调，布局严谨，适合商业分析和专业报告。"
}

COMPLEXITY_DESCRIPTIONS = {
    "简单": "功能简洁，页面不超过2个，适合单一任务",
    "中等": "具有3-5个功能模块，可能有多个页面，适合中等复杂度的应用",
    "复杂": "功能丰富，包含多个页面和高级功能，可能需要数据处理和复杂可视化"
}

# 文件上传配置
ALLOWED_IMAGE_TYPES = ['png', 'jpg', 'jpeg', 'gif', 'svg']
ALLOWED_DATA_TYPES = ['csv', 'xlsx', 'json', 'txt']

# 代码检查配置
COMMON_PYTHON_MODULES = [
    "streamlit", "pandas", "numpy", "matplotlib", "plotly", 
    "os", "sys", "time", "datetime", "json", "re", "math", 
    "random", "pathlib", "collections", "csv", "io"
]

# 资源目录结构
RESOURCE_CATEGORIES = {
    "图片": "images",
    "数据": "data",
    "其他": "misc"
}

# 依赖包配置
DEFAULT_DEPENDENCIES = [
    "# Streamlit应用依赖", 
    "streamlit>=1.25.0", 
    "pandas>=1.3.0", 
    "numpy>=1.20.0"
]

DEPENDENCY_KEYWORDS = {
    "图表": ["matplotlib>=3.5.0", "plotly>=5.8.0"],
    "可视化": ["matplotlib>=3.5.0", "plotly>=5.8.0"],
    "图形": ["matplotlib>=3.5.0", "plotly>=5.8.0"],
    "绘图": ["matplotlib>=3.5.0", "plotly>=5.8.0"],
    "数据": ["openpyxl>=3.0.0"],
    "表格": ["openpyxl>=3.0.0"],
    "分析": ["openpyxl>=3.0.0"],
    "统计": ["openpyxl>=3.0.0"],
    "机器学习": ["scikit-learn>=1.0.0"],
    "预测": ["scikit-learn>=1.0.0"],
    "模型": ["scikit-learn>=1.0.0"],
    "网络": ["requests>=2.28.0"],
    "爬虫": ["requests>=2.28.0"],
    "请求": ["requests>=2.28.0"],
    "地图": ["pydeck>=0.7.0", "pillow>=9.0.0"],
    "地理": ["pydeck>=0.7.0", "pillow>=9.0.0"],
    "位置": ["pydeck>=0.7.0", "pillow>=9.0.0"]
} 