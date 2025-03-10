import os
import requests
import json
from pathlib import Path
import tempfile
import shutil
import re

# 导入配置、提示模板和模板加载器
import config
from prompts import (
    APP_GENERATION_PROMPT, 
    RESOURCES_FORMAT, 
    README_TEMPLATE,
    RESOURCES_SECTION_TEMPLATE,
    IMAGES_SECTION_TEMPLATE,
    DATA_SECTION_TEMPLATE,
    OTHER_SECTION_TEMPLATE,
    RESOURCE_ITEM_TEMPLATE
)
from template_loader import TemplateLoader

class LLMHandler:
    def __init__(self, api_key, api_endpoint, model=config.DEFAULT_MODEL):
        """
        初始化LLM处理程序
        
        参数:
            api_key (str): OpenAI API密钥
            api_endpoint (str): API端点URL
            model (str): 使用的模型名称
        """
        self.api_key = api_key
        self.api_endpoint = api_endpoint
        self.model = model
        
        # 确保API端点格式正确
        if not self.api_endpoint.endswith('/'):
            self.api_endpoint += '/'
        if not self.api_endpoint.endswith('v1/'):
            self.api_endpoint += 'v1/' if 'v1' not in self.api_endpoint else ''
    
    def get_available_models(self):
        """
        获取API端点提供的可用模型列表
        
        返回:
            list: 可用模型ID列表，如果请求失败则返回默认模型列表
        """
        if not self.api_key:
            # 如果没有API密钥，返回默认模型列表
            return config.DEFAULT_MODELS
            
        try:
            # 构建获取模型的API URL
            models_url = f"{self.api_endpoint}models"
            
            # 发送请求
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(models_url, headers=headers)
            
            if response.status_code == 200:
                models_data = response.json()
                # 提取模型ID列表，仅保留GPT模型
                model_ids = [model["id"] for model in models_data["data"] 
                            if "gpt" in model["id"].lower()]
                
                # 如果成功获取到模型列表但为空，返回默认模型
                if not model_ids:
                    return config.DEFAULT_MODELS
                
                # 对模型进行排序，将gpt-4和gpt-3.5放在前面
                def model_sort_key(model_id):
                    if "gpt-4" in model_id:
                        return 0
                    elif "gpt-3.5" in model_id:
                        return 1
                    else:
                        return 2
                
                return sorted(model_ids, key=model_sort_key)
            else:
                # 请求失败，返回默认模型列表
                return config.DEFAULT_MODELS
                
        except Exception as e:
            # 出现异常，返回默认模型列表
            print(f"获取模型列表时出错: {str(e)}")
            return config.DEFAULT_MODELS
        
    def generate_code(self, app_name, app_description, app_type, language, complexity, ui_theme="简约现代", resources=None):
        """
        根据用户需求生成应用代码
        
        参数:
            app_name (str): 应用名称
            app_description (str): 应用描述
            app_type (str): 应用类型
            language (str): 编程语言
            complexity (str): 复杂度
            ui_theme (str): UI主题风格
            resources (list): 上传的资源列表
            
        返回:
            dict: 包含生成结果的字典
        """
        try:
            # 创建临时目录存放生成的代码
            temp_dir = Path(tempfile.mkdtemp())
            app_dir = temp_dir / app_name
            app_dir.mkdir(exist_ok=True)
            
            # 创建资源目录
            resources_dir = app_dir / "resources"
            resources_dir.mkdir(exist_ok=True)
            
            # 如果有资源文件，复制到应用目录
            resource_descriptions = []
            if resources:
                for resource in resources:
                    try:
                        source_path = Path(resource["path"])
                        if not source_path.exists():
                            continue
                            
                        # 确定目标路径和类型
                        if resource["type"] == "图片":
                            target_dir = resources_dir / config.RESOURCE_CATEGORIES["图片"]
                            category = config.RESOURCE_CATEGORIES["图片"]
                        elif resource["type"] == "数据":
                            target_dir = resources_dir / config.RESOURCE_CATEGORIES["数据"]
                            category = config.RESOURCE_CATEGORIES["数据"]
                        else:
                            target_dir = resources_dir / config.RESOURCE_CATEGORIES["其他"]
                            category = config.RESOURCE_CATEGORIES["其他"]
                            
                        target_dir.mkdir(exist_ok=True)
                        target_path = target_dir / resource["name"]
                        
                        # 复制文件
                        shutil.copy2(source_path, target_path)
                        
                        # 生成资源描述
                        rel_path = target_path.relative_to(app_dir)
                        resource_descriptions.append({
                            "name": resource["name"],
                            "id": resource["id"],
                            "type": resource["type"],
                            "path": str(rel_path),
                            "category": category
                        })
                    except Exception as e:
                        print(f"复制资源 {resource['name']} 时出错: {str(e)}")
            
            # 构建提示
            prompt = self._build_prompt(app_name, app_description, complexity, ui_theme, resource_descriptions)
            
            # 调用OpenAI API
            response = self._call_openai_api(prompt)
            
            # 解析并保存代码
            files_data = self._parse_code_from_response(response, language)
            
            # 检查代码质量和错误
            check_result = self._check_code_quality(files_data)
            if not check_result["success"]:
                return {
                    "success": False,
                    "error": f"代码质量检查失败: {check_result['error']}"
                }
                
            # 保存文件
            saved_files = self._save_generated_files(files_data, app_dir)
            
            # 创建requirements.txt
            self._create_requirements_file(app_dir, app_description)
            
            # 创建README
            self._create_readme(app_dir, app_name, app_description, resource_descriptions)
            
            # 创建启动脚本
            self._create_launcher(app_dir, app_name)
            
            # 打包文件
            source_zip_path = self._create_zip_archive(app_dir, app_name)
            
            return {
                "success": True,
                "app_dir": str(app_dir),
                "source_zip": str(source_zip_path),
                "files": saved_files
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_prompt(self, app_name, app_description, complexity, ui_theme, resource_descriptions=None):
        """构建LLM提示，专注于生成Streamlit应用"""
        # 获取UI主题和复杂度描述
        theme_desc = config.UI_THEMES.get(ui_theme, config.UI_THEMES["简约现代"])
        complex_desc = config.COMPLEXITY_DESCRIPTIONS.get(complexity, config.COMPLEXITY_DESCRIPTIONS["简单"])
        
        # 构建资源文件描述
        resources_text = ""
        if resource_descriptions and len(resource_descriptions) > 0:
            resources_list = ""
            for i, resource in enumerate(resource_descriptions):
                resources_list += f"{i+1}. {resource['name']} (类型: {resource['type']}, 路径: {resource['path']})\n"
            
            resources_text = RESOURCES_FORMAT.format(resources_list=resources_list)
        
        # 使用提示模板填充参数
        return APP_GENERATION_PROMPT.format(
            app_name=app_name,
            app_description=app_description,
            ui_theme=ui_theme,
            theme_desc=theme_desc,
            complexity=complexity,
            complex_desc=complex_desc,
            resources_text=resources_text
        )
    
    def _call_openai_api(self, prompt):
        """调用OpenAI API"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 4000
        }
        
        # 构建完整的API URL
        if 'chat/completions' not in self.api_endpoint:
            api_url = f"{self.api_endpoint}chat/completions"
        else:
            api_url = self.api_endpoint
            
        response = requests.post(api_url, headers=headers, json=data)
        
        if response.status_code != 200:
            raise Exception(f"API调用失败: {response.text}")
        
        return response.json()
    
    def _check_code_quality(self, files_data):
        """检查生成的代码质量和潜在错误"""
        try:
            # 检查是否有必要的文件
            has_main_app = False
            streamlit_import_found = False
            file_uploader_found = False
            
            for file_data in files_data:
                file_name = file_data["name"]
                content = file_data["content"]
                
                # 检查是否有主应用文件
                if file_name == "app.py" or file_name.endswith("/app.py"):
                    has_main_app = True
                    
                    # 检查是否导入了streamlit
                    if "import streamlit" in content or "from streamlit" in content:
                        streamlit_import_found = True
                    
                    # 检查是否包含文件上传功能
                    if "st.file_uploader" in content:
                        file_uploader_found = True
                    
                    # 检查语法错误
                    try:
                        compile(content, file_name, 'exec')
                    except SyntaxError as e:
                        return {
                            "success": False,
                            "error": f"文件 {file_name} 中有语法错误: {str(e)}"
                        }
                    
                    # 检查常见的错误模式
                    if "st.write(" in content and not streamlit_import_found:
                        return {
                            "success": False,
                            "error": f"文件 {file_name} 使用了st.write但没有导入streamlit"
                        }
                        
                    # 检查是否有不存在的导入
                    import_pattern = r"import\s+(\w+)|from\s+(\w+)"
                    imports = re.findall(import_pattern, content)
                    for imp in imports:
                        module_name = imp[0] if imp[0] else imp[1]
                        if module_name not in config.COMMON_PYTHON_MODULES:
                            # 这只是一个简单检查，可能会有误报
                            pass
            
            if not has_main_app:
                return {
                    "success": False,
                    "error": "缺少主应用文件app.py"
                }
                
            if not streamlit_import_found:
                return {
                    "success": False,
                    "error": "代码中没有导入streamlit库"
                }
                
            if not file_uploader_found:
                return {
                    "success": False,
                    "error": "代码中没有包含文件上传功能(st.file_uploader)"
                }
                
            return {
                "success": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"代码质量检查出错: {str(e)}"
            }
    
    def _parse_code_from_response(self, response, language):
        """从API响应中解析代码"""
        content = response['choices'][0]['message']['content']
        files_data = []
        
        # 查找所有文件块
        import re
        file_blocks = re.findall(r'文件: (.+?)\n```(?:.*?)\n(.*?)```', content, re.DOTALL)
        
        for file_name, file_content in file_blocks:
            files_data.append({
                "name": file_name.strip(),
                "content": file_content.strip()
            })
            
        # 如果没有找到文件块，尝试其他格式
        if not files_data:
            # 尝试英文格式
            file_blocks = re.findall(r'File: (.+?)\n```(?:.*?)\n(.*?)```', content, re.DOTALL)
            for file_name, file_content in file_blocks:
                files_data.append({
                    "name": file_name.strip(),
                    "content": file_content.strip()
                })
                
        # 仍然没有找到，尝试查找单个代码块
        if not files_data:
            code_blocks = re.findall(r'```(?:.*?)\n(.*?)```', content, re.DOTALL)
            if code_blocks:
                # 假设这是主应用文件
                files_data.append({
                    "name": "app.py",
                    "content": code_blocks[0].strip()
                })
                
        # 如果还是没有找到任何代码，尝试提取没有格式的代码
        if not files_data and "import streamlit" in content:
            # 尝试直接提取代码部分
            files_data.append({
                "name": "app.py",
                "content": content
            })
                
        return files_data
    
    def _save_generated_files(self, files_data, app_dir):
        """保存生成的文件到应用目录"""
        saved_files = []
        
        for file_data in files_data:
            file_name = file_data["name"]
            file_content = file_data["content"]
            
            # 确保路径存在（处理嵌套目录）
            file_path = app_dir / file_name
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_content)
                
            saved_files.append(str(file_path))
            
        return saved_files
    
    def _create_requirements_file(self, app_dir, app_description):
        """为Streamlit应用创建requirements.txt"""
        # 基本依赖
        requirements = config.DEFAULT_DEPENDENCIES.copy()
        
        # 根据应用描述推断可能的依赖
        for keyword, packages in config.DEPENDENCY_KEYWORDS.items():
            if keyword in app_description.lower():
                requirements.extend(packages)
        
        # 添加图片处理依赖（统一添加）
        if "pillow" not in " ".join(requirements).lower():
            requirements.append("pillow>=9.0.0")
            
        # 写入requirements.txt
        with open(app_dir / "requirements.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(requirements))
            
    def _create_readme(self, app_dir, app_name, app_description, resource_descriptions=None):
        """创建README文件"""
        # 准备资源部分
        resources_section = ""
        if resource_descriptions and len(resource_descriptions) > 0:
            # 按类型分组
            images = [r for r in resource_descriptions if r["type"] == "图片"]
            data_files = [r for r in resource_descriptions if r["type"] == "数据"]
            other_files = [r for r in resource_descriptions if r["type"] not in ["图片", "数据"]]
            
            # 创建各部分内容
            images_list = ""
            for img in images:
                images_list += RESOURCE_ITEM_TEMPLATE.format(name=img['name'], path=img['path'])
                
            data_list = ""
            for data in data_files:
                data_list += RESOURCE_ITEM_TEMPLATE.format(name=data['name'], path=data['path'])
                
            other_list = ""
            for file in other_files:
                other_list += RESOURCE_ITEM_TEMPLATE.format(name=file['name'], path=file['path'])
            
            # 创建各节
            images_section = IMAGES_SECTION_TEMPLATE.format(images_list=images_list) if images else ""
            data_section = DATA_SECTION_TEMPLATE.format(data_list=data_list) if data_files else ""
            other_section = OTHER_SECTION_TEMPLATE.format(other_list=other_list) if other_files else ""
            
            # 组合资源部分
            if images or data_files or other_files:
                resources_section = RESOURCES_SECTION_TEMPLATE.format(
                    images_section=images_section,
                    data_section=data_section,
                    other_section=other_section
                )
        
        # 使用README模板
        readme_content = README_TEMPLATE.format(
            app_name=app_name,
            app_description=app_description,
            resources_section=resources_section
        )
        
        with open(app_dir / "README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)
    
    def _create_launcher(self, app_dir, app_name):
        """创建跨平台启动脚本"""
        # 使用模板加载器获取模板
        try:
            # Windows启动器
            bat_template = TemplateLoader.get_launcher_template("windows")
            bat_content = TemplateLoader.render(bat_template, app_name=app_name)
            
            # Unix启动器
            sh_template = TemplateLoader.get_launcher_template("unix")
            sh_content = TemplateLoader.render(sh_template, app_name=app_name)
            
            # HTML启动指南
            html_template = TemplateLoader.get_launcher_guide_template()
            html_content = TemplateLoader.render(html_template, app_name=app_name)
            
            # 创建启动文件
            with open(app_dir / "启动应用.bat", "w", encoding="utf-8") as f:
                f.write(bat_content)
                
            with open(app_dir / "启动应用.sh", "w", encoding="utf-8") as f:
                f.write(sh_content)
                
            with open(app_dir / "启动说明.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            
            # 确保shell脚本可执行
            sh_path = app_dir / "启动应用.sh"
            sh_path.chmod(sh_path.stat().st_mode | 0o111)  # 添加执行权限
            
        except Exception as e:
            # 如果加载模板失败，回退到硬编码模板（确保功能不会中断）
            print(f"警告: 加载启动器模板失败，使用备用模板: {str(e)}")
            # 这里可以添加备用的硬编码模板
    
    def _create_zip_archive(self, app_dir, app_name):
        """创建源代码的ZIP压缩包"""
        zip_path = app_dir.parent / f"{app_name}_source.zip"
        shutil.make_archive(
            str(zip_path).replace(".zip", ""),
            'zip',
            app_dir
        )
        return zip_path 