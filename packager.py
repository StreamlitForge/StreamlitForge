import os
import subprocess
import tempfile
import logging
import shutil
import sys
import platform
from pathlib import Path

from template_loader import TemplateLoader

class AppPackager:
    def __init__(self):
        """初始化应用打包器"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def package_app(self, app_dir, app_name, app_type, language):
        """
        将Streamlit应用打包为跨平台启动器
        
        参数:
            app_dir (str/Path): 应用源代码目录
            app_name (str): 应用名称
            app_type (str): 应用类型 ('Streamlit Web应用')
            language (str): 编程语言 ('Python')
            
        返回:
            dict: 包含打包结果信息的字典
        """
        app_dir = Path(app_dir)
        
        try:
            if not app_dir.exists():
                raise FileNotFoundError(f"应用目录不存在: {app_dir}")
                
            # 检查是否是Streamlit应用
            if not self._is_streamlit_app(app_dir):
                self.logger.warning("这可能不是一个有效的Streamlit应用")
                
            # 创建启动包
            return self._create_launcher_package(app_dir, app_name)
                
        except Exception as e:
            self.logger.error(f"打包应用时出错: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _is_streamlit_app(self, app_dir):
        """检查是否是有效的Streamlit应用"""
        app_py = app_dir / "app.py"
        if not app_py.exists():
            return False
            
        with open(app_py, "r", encoding="utf-8") as f:
            content = f.read()
            return "import streamlit" in content or "from streamlit" in content
    
    def _create_launcher_package(self, app_dir, app_name):
        """创建适用于所有平台的启动包"""
        try:
            # 创建输出目录
            output_dir = app_dir.parent / f"{app_name}_launcher"
            if output_dir.exists():
                shutil.rmtree(output_dir)
            output_dir.mkdir()
            
            # 复制所有源码文件
            self.logger.info("正在创建启动包...")
            for item in app_dir.glob("**/*"):
                if item.is_file():
                    rel_path = item.relative_to(app_dir)
                    dest_path = output_dir / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest_path)
            
            # 检查启动器文件是否存在
            launch_html = output_dir / "启动说明.html"
            if not launch_html.exists():
                self.logger.warning("未找到启动说明HTML文件，可能是因为使用了旧版生成器")
                # 创建启动页
                try:
                    # 获取HTML模板并渲染
                    html_template = TemplateLoader.get_launcher_guide_template()
                    html_content = TemplateLoader.render(html_template, app_name=app_name)
                    
                    # 写入HTML文件
                    with open(output_dir / "启动说明.html", "w", encoding="utf-8") as f:
                        f.write(html_content)
                except Exception as e:
                    self.logger.warning(f"创建启动说明页失败: {str(e)}")
            
            # 确保启动脚本具有正确的权限
            bat_file = output_dir / "启动应用.bat"
            sh_file = output_dir / "启动应用.sh"
            
            if sh_file.exists():
                # 添加执行权限
                try:
                    sh_file.chmod(sh_file.stat().st_mode | 0o755)
                except Exception as e:
                    self.logger.warning(f"无法设置shell脚本权限: {str(e)}")
            
            # 创建一个README.txt文件，说明如何启动应用
            readme_content = f"""# {app_name} - 启动说明

## 快速启动指南

1. 解压下载的文件到任意位置
2. 打开"启动说明.html"文件了解详细的启动选项
3. Windows用户: 双击运行"启动应用.bat"
4. Mac/Linux用户: 打开终端，进入解压目录，输入:
   chmod +x 启动应用.sh
   ./启动应用.sh

## 注意事项

- 首次运行时，启动器会自动检查Python环境并安装必要的依赖
- 如果没有安装Python，启动器将尝试自动下载并安装
- 所有代码和资源都包含在此包中，可以离线运行
"""
            readme_path = output_dir / "README.txt"
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(readme_content)
            
            # 创建ZIP包
            launcher_zip = app_dir.parent / f"{app_name}_启动包.zip"
            shutil.make_archive(
                str(launcher_zip).replace(".zip", ""),
                'zip',
                output_dir
            )
            
            self.logger.info(f"启动包已创建: {launcher_zip}")
            
            return {
                "success": True,
                "exe_path": str(launcher_zip),
                "launcher_dir": str(output_dir)
            }
            
        except Exception as e:
            self.logger.error(f"创建启动包时出错: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_html_launcher(self, app_name):
        """创建HTML启动器页面"""
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{app_name} - Streamlit应用启动器</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background-color: #f5f7fa;
            color: #333;
        }}
        .container {{
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            width: 90%;
            max-width: 800px;
            text-align: center;
        }}
        header {{
            background-color: #ff4b4b;
            color: white;
            padding: 30px 20px;
        }}
        h1 {{
            margin: 0;
            font-size: 2em;
        }}
        .content {{
            padding: 30px 40px;
        }}
        p {{
            font-size: 1.1em;
            line-height: 1.6;
            color: #555;
        }}
        .launcher {{
            margin: 40px 0;
            display: flex;
            flex-direction: column;
            gap: 15px;
            align-items: center;
        }}
        .button {{
            display: inline-block;
            padding: 15px 30px;
            background-color: #ff4b4b;
            color: white;
            text-decoration: none;
            border-radius: 25px;
            font-weight: 600;
            font-size: 1.1em;
            transition: all 0.3s ease;
            min-width: 200px;
            text-align: center;
        }}
        .button:hover {{
            background-color: #e54141;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(229, 65, 65, 0.3);
        }}
        .alt-button {{
            background-color: #f0f0f0;
            color: #333;
        }}
        .alt-button:hover {{
            background-color: #e0e0e0;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }}
        .footer {{
            margin-top: 40px;
            padding: 20px;
            border-top: 1px solid #eee;
            font-size: 0.9em;
            color: #888;
        }}
        .instructions {{
            text-align: left;
            margin: 30px 0;
            padding: 20px;
            background-color: #f9f9f9;
            border-radius: 8px;
        }}
        .instructions h3 {{
            margin-top: 0;
        }}
        .instructions ol {{
            padding-left: 22px;
        }}
        code {{
            background-color: #f0f0f0;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: Consolas, monospace;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{app_name}</h1>
            <p style="color: white; margin-top: 10px;">Streamlit应用启动器</p>
        </header>
        <div class="content">
            <p>这是一个Streamlit Web应用，您可以通过以下方式启动它：</p>
            
            <div class="launcher">
                <a href="启动应用.bat" class="button" download>下载Windows启动器</a>
                <a href="启动应用.sh" class="button" download>下载Mac/Linux启动器</a>
                <a href="app.py" class="button alt-button" download>下载源代码</a>
            </div>
            
            <div class="instructions">
                <h3>启动说明</h3>
                <ol>
                    <li><strong>Windows用户</strong>: 下载并解压所有文件，然后双击运行 <code>启动应用.bat</code></li>
                    <li><strong>Mac/Linux用户</strong>: 下载并解压所有文件，给 <code>启动应用.sh</code> 添加执行权限，然后运行它</li>
                </ol>
                <h3>手动运行</h3>
                <ol>
                    <li>确保安装了Python 3.7+</li>
                    <li>安装依赖: <code>pip install -r requirements.txt</code></li>
                    <li>运行应用: <code>streamlit run app.py</code></li>
                </ol>
            </div>
        </div>
        <div class="footer">
            由Streamlit应用生成器创建 | 遵循Streamlit的最佳实践
        </div>
    </div>
</body>
</html>
""" 