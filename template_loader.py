"""
模板加载器 - 用于加载和填充模板
"""

import os
from pathlib import Path
from string import Template

# 模板目录
TEMPLATE_DIR = Path(__file__).parent / "templates"

class TemplateLoader:
    """模板加载和渲染工具"""
    
    @staticmethod
    def load_template(template_path):
        """
        从文件加载模板内容
        
        参数:
            template_path (str): 模板文件路径，相对于模板目录
            
        返回:
            str: 模板内容
        """
        full_path = TEMPLATE_DIR / template_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"模板文件不存在: {full_path}")
            
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def render(template_str, **kwargs):
        """
        使用参数渲染模板字符串
        
        参数:
            template_str (str): 模板字符串
            **kwargs: 用于替换的键值对
            
        返回:
            str: 渲染后的内容
        """
        template = Template(template_str)
        return template.safe_substitute(**kwargs)
    
    @staticmethod
    def load_and_render(template_path, **kwargs):
        """
        加载并渲染模板
        
        参数:
            template_path (str): 模板文件路径，相对于模板目录
            **kwargs: 用于替换的键值对
            
        返回:
            str: 渲染后的内容
        """
        template_str = TemplateLoader.load_template(template_path)
        return TemplateLoader.render(template_str, **kwargs)
        
    @staticmethod
    def get_launcher_template(platform):
        """
        获取特定平台的启动器模板
        
        参数:
            platform (str): 平台类型 ('windows' 或 'unix')
            
        返回:
            str: 模板内容
        """
        if platform.lower() == 'windows':
            return TemplateLoader.load_template('launchers/windows_launcher.bat')
        elif platform.lower() in ('unix', 'linux', 'mac', 'macos'):
            return TemplateLoader.load_template('launchers/unix_launcher.sh')
        else:
            raise ValueError(f"不支持的平台类型: {platform}")
            
    @staticmethod
    def get_launcher_guide_template():
        """
        获取启动指南HTML模板
        
        返回:
            str: 模板内容
        """
        return TemplateLoader.load_template('launchers/launcher_guide.html') 