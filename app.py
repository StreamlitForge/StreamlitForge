import streamlit as st
import os
import json
import tempfile
import shutil
import time
import uuid
from pathlib import Path
import requests  # 添加用于 GitHub API 请求
import base64    # 添加用于 GitHub API 认证

# 导入配置
import config

# 导入自定义模块
from llm_handler import LLMHandler
from packager import AppPackager

# 初始化会话状态
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_app' not in st.session_state:
    st.session_state.current_app = None
if 'available_models' not in st.session_state:
    st.session_state.available_models = config.DEFAULT_MODELS
if 'endpoint_changed' not in st.session_state:
    st.session_state.endpoint_changed = False
if 'progress' not in st.session_state:
    st.session_state.progress = {"stage": "", "details": "", "percent": 0}
if 'uploaded_resources' not in st.session_state:
    st.session_state.uploaded_resources = []
if 'github_token' not in st.session_state:
    st.session_state.github_token = ""
if 'github_deployment' not in st.session_state:
    st.session_state.github_deployment = {"status": "", "url": "", "repo_name": ""}

# 创建资源目录
resource_dir = Path("resources")
resource_dir.mkdir(exist_ok=True)

# 创建获取模型列表的回调函数
def update_available_models():
    # 标记端点已更改
    st.session_state.endpoint_changed = True

# 更新进度的函数
def update_progress(stage, details, percent):
    st.session_state.progress = {
        "stage": stage,
        "details": details,
        "percent": percent
    }

# 处理上传的资源
def handle_uploaded_resource(uploaded_file, resource_type):
    if uploaded_file is not None:
        # 生成唯一ID
        file_id = str(uuid.uuid4())[:8]
        # 确保文件名是安全的
        safe_filename = ''.join(c for c in uploaded_file.name if c.isalnum() or c in '._-')
        # 构建资源路径
        resource_path = resource_dir / f"{file_id}_{safe_filename}"
        
        # 保存文件
        with open(resource_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        # 添加到上传的资源列表
        resource_info = {
            "id": file_id,
            "name": safe_filename,
            "path": str(resource_path),
            "type": resource_type,
            "size": uploaded_file.size,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state.uploaded_resources.append(resource_info)
        return resource_info
    return None

# 设置页面配置
st.set_page_config(page_title=config.APP_TITLE, page_icon=config.APP_ICON, layout="wide")
st.title(f"{config.APP_ICON} {config.APP_TITLE}")
st.markdown(config.APP_DESCRIPTION)

# 侧边栏配置
with st.sidebar:
    st.header("API 配置")
    
    # API Endpoint配置（放在最顶部）
    api_endpoint = st.text_input("API Endpoint", 
                                value=config.DEFAULT_API_ENDPOINT, 
                                help="API端点URL",
                                on_change=update_available_models,
                                key="api_endpoint")
    
    # API Key配置
    api_key = st.text_input("OpenAI API Key", 
                          type="password", 
                          help="输入您的OpenAI API密钥",
                          on_change=update_available_models,
                          key="api_key")
    
    # 如果API端点或密钥已更改，尝试获取模型列表
    if st.session_state.endpoint_changed and api_key and api_endpoint:
        with st.spinner("正在获取可用模型..."):
            try:
                llm_handler = LLMHandler(api_key, api_endpoint)
                models = llm_handler.get_available_models()
                st.session_state.available_models = models
                st.success(f"成功获取到 {len(models)} 个可用模型")
            except Exception as e:
                st.error(f"获取模型列表失败: {str(e)}")
        st.session_state.endpoint_changed = False
    
    # 模型选择
    model = st.selectbox("选择模型", 
                        options=st.session_state.available_models, 
                        index=min(1, len(st.session_state.available_models)-1) if len(st.session_state.available_models) > 1 else 0)
    
    st.divider()
    
    # 添加 GitHub 配置部分
    st.header("GitHub 部署配置")
    github_token = st.text_input(
        "GitHub 访问令牌", 
        type="password",
        help="用于部署到 StreamlitForge 组织的 GitHub 访问令牌，需要有组织仓库创建权限",
        value=st.session_state.github_token,
        key="github_token_input"
    )
    
    # 保存令牌到会话状态
    if github_token != st.session_state.github_token:
        st.session_state.github_token = github_token
    
    st.divider()
    st.header("关于")
    st.info("这是一个生成Streamlit网页应用的工具。输入您的需求描述，AI将生成一个美观的Streamlit应用，并提供可在任何平台运行的启动包。")

# 主界面
tab1, tab2, tab3 = st.tabs(["创建应用", "资源管理", "历史记录"])

with tab1:
    st.header("应用需求")
    app_name = st.text_input("应用名称", help="给您的应用起一个简短的名称")
    app_description = st.text_area("详细需求描述", 
                               height=200, 
                               help="请详细描述应用的功能、界面和行为",
                               placeholder="例如：创建一个数据可视化应用，能够上传CSV文件并生成多种类型的图表，包括折线图、柱状图和饼图。应用界面要美观，有侧边栏和多页面布局。")
    
    col1, col2 = st.columns(2)
    with col1:
        complexity = st.select_slider("复杂度", options=list(config.COMPLEXITY_DESCRIPTIONS.keys()), value="简单")
    with col2:
        ui_theme = st.selectbox("界面风格", list(config.UI_THEMES.keys()), index=0)
    
    # 使用上传的资源
    if st.session_state.uploaded_resources:
        st.subheader("包含上传的资源")
        resources_to_include = []
        
        # 按类型分组显示可用资源
        images = [r for r in st.session_state.uploaded_resources if r["type"] == "图片"]
        data_files = [r for r in st.session_state.uploaded_resources if r["type"] == "数据"]
        other_files = [r for r in st.session_state.uploaded_resources if r["type"] not in ["图片", "数据"]]
        
        col1, col2 = st.columns(2)
        
        with col1:
            if images:
                st.write("**可用图片:**")
                for img in images:
                    include = st.checkbox(
                        f"{img['name']} ({img['id']})", 
                        value=False,
                        key=f"img_{img['id']}"
                    )
                    if include:
                        resources_to_include.append(img['id'])
                        
            if other_files:
                st.write("**其他文件:**")
                for file in other_files:
                    include = st.checkbox(
                        f"{file['name']} ({file['id']})", 
                        value=False,
                        key=f"other_{file['id']}"
                    )
                    if include:
                        resources_to_include.append(file['id'])
                
        with col2:
            if data_files:
                st.write("**数据文件:**")
                for data in data_files:
                    include = st.checkbox(
                        f"{data['name']} ({data['id']})", 
                        value=False,
                        key=f"data_{data['id']}"
                    )
                    if include:
                        resources_to_include.append(data['id'])
    else:
        resources_to_include = []
        st.info("如需包含自定义资源，请前往「资源管理」选项卡上传文件或图片")
        
    generate_button = st.button("生成应用", type="primary", use_container_width=True)
    
    # 显示详细进度
    if st.session_state.progress["stage"]:
        progress_bar = st.progress(st.session_state.progress["percent"])
        st.subheader(f"当前阶段: {st.session_state.progress['stage']}")
        st.info(st.session_state.progress["details"])
    
    # 生成应用逻辑
    if generate_button:
        if not api_key:
            st.error("请提供OpenAI API Key以继续")
        elif not app_name or not app_description:
            st.error("请填写应用名称和需求描述")
        else:
            # 默认应用类型为Streamlit Web应用
            app_type = "Streamlit Web应用"
            language = "Python"
            
            # 收集选中的资源
            selected_resources = []
            for resource_id in resources_to_include:
                for resource in st.session_state.uploaded_resources:
                    if resource["id"] == resource_id:
                        selected_resources.append(resource)
                        break
            
            # 重置进度
            update_progress("准备", "正在初始化生成过程...", 0)
            
            # 创建处理进度显示
            with st.status("正在生成应用...", expanded=True) as status:
                # 初始化LLM处理程序
                llm_handler = LLMHandler(api_key, api_endpoint, model)
                
                # 阶段1：分析需求
                update_progress("分析需求", "AI正在分析您的应用需求...", 10)
                st.write("1. 正在分析您的需求...")
                time.sleep(1)  # 模拟过程
                
                # 阶段2：生成代码
                update_progress("生成代码", "AI正在为您的Streamlit应用生成代码...", 30)
                st.write("2. 正在生成Streamlit应用代码...")
                code_result = llm_handler.generate_code(
                    app_name=app_name,
                    app_description=app_description,
                    app_type=app_type,
                    language=language,
                    complexity=complexity,
                    ui_theme=ui_theme,
                    resources=selected_resources
                )
                
                if not code_result["success"]:
                    st.error(f"生成代码失败: {code_result.get('error', '未知错误')}")
                    status.update(label="应用生成失败", state="error")
                    update_progress("失败", f"生成失败: {code_result.get('error', '未知错误')}", 100)
                else:
                    app_dir = code_result["app_dir"]
                    source_zip = code_result["source_zip"]
                    
                    # 阶段3：检查代码质量
                    update_progress("代码检查", "正在检查生成的代码质量和潜在错误...", 60)
                    st.write("3. 正在检查代码质量...")
                    
                    # 阶段4：创建启动器
                    update_progress("创建启动器", "正在创建跨平台启动器...", 80)
                    st.write("4. 正在打包应用...")
                    packager = AppPackager()
                    package_result = packager.package_app(
                        app_dir=app_dir,
                        app_name=app_name,
                        app_type=app_type,
                        language=language
                    )
                    
                    if not package_result["success"]:
                        st.warning(f"打包应用失败: {package_result.get('error', '未知错误')}")
                        st.write("将只提供源代码下载。")
                        exe_path = None
                        update_progress("部分完成", "应用源代码已生成，但打包失败", 90)
                    else:
                        exe_path = package_result["exe_path"]
                        st.write("5. 打包完成！")
                        update_progress("完成", "您的Streamlit应用已成功生成并打包！", 100)
                    
                    # 更新会话状态
                    app_info = {
                        "name": app_name,
                        "description": app_description[:100] + "..." if len(app_description) > 100 else app_description,
                        "type": app_type,
                        "language": language,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "source_zip": source_zip,
                        "exe_path": exe_path,
                        "resources": selected_resources
                    }
                    st.session_state.current_app = app_info
                    st.session_state.history.append(app_info)
                    
                    status.update(label="Streamlit应用生成完成！", state="complete")
            
            # 显示结果和下载选项
            if st.session_state.current_app:
                st.success(f"应用「{app_name}」已成功生成！")
                
                source_zip = st.session_state.current_app["source_zip"]
                exe_path = st.session_state.current_app["exe_path"]
                
                st.subheader("下载选项")
                col1, col2 = st.columns(2)
                
                # 源代码下载
                with col1:
                    if os.path.exists(source_zip):
                        with open(source_zip, "rb") as f:
                            st.download_button(
                                "下载源代码",
                                data=f.read(),
                                file_name=f"{app_name}_source.zip",
                                mime="application/zip",
                                help="下载包含所有源代码的ZIP压缩包，您可以自行修改和运行",
                                use_container_width=True
                            )
                    else:
                        st.error("源代码包丢失")
                
                # 启动包下载
                with col2:
                    if exe_path and os.path.exists(exe_path):
                        with open(exe_path, "rb") as f:
                            st.download_button(
                                "下载智能启动包",
                                data=f.read(),
                                file_name=os.path.basename(exe_path),
                                mime="application/octet-stream",
                                help="下载智能启动包，自动配置环境并运行应用（支持自动安装Python及创建虚拟环境）",
                                use_container_width=True
                            )
                    else:
                        st.warning("启动包不可用")

                # 添加 GitHub 部署选项
                st.subheader("GitHub 部署")
                
                if st.session_state.github_token:
                    if st.session_state.github_deployment.get("status") == "success":
                        # 已经成功部署
                        st.success(f"应用已成功部署到 GitHub: {st.session_state.github_deployment.get('url', '')}")
                        st.markdown(f"[查看仓库]({st.session_state.github_deployment.get('url', '')})")
                    else:
                        # 显示部署按钮
                        if st.button("部署到 StreamlitForge 组织", type="primary", use_container_width=True):
                            with st.status("正在部署到 GitHub...", expanded=True) as status:
                                # 从源代码部署到 GitHub
                                app_dir = os.path.join(os.path.dirname(source_zip), "app")
                                if not os.path.exists(app_dir):
                                    # 如果app目录不存在，尝试解压源代码包
                                    temp_dir = tempfile.mkdtemp()
                                    shutil.unpack_archive(source_zip, temp_dir, 'zip')
                                    app_dir = temp_dir
                                
                                # 调用 GitHub 部署函数
                                deploy_result = deploy_to_github(
                                    app_dir=app_dir,
                                    app_name=app_name,
                                    github_token=st.session_state.github_token
                                )
                                
                                if deploy_result["success"]:
                                    st.session_state.github_deployment = {
                                        "status": "success",
                                        "url": deploy_result["repo_url"],
                                        "repo_name": deploy_result["repo_name"]
                                    }
                                    status.update(label=f"成功部署到 GitHub！", state="complete")
                                    st.success(f"应用已成功部署到 GitHub 组织 StreamlitForge")
                                    st.markdown(f"[查看仓库]({deploy_result['repo_url']})")
                                else:
                                    st.session_state.github_deployment = {
                                        "status": "failed",
                                        "error": deploy_result.get("error", "未知错误")
                                    }
                                    status.update(label="GitHub 部署失败", state="error")
                                    st.error(f"部署失败: {deploy_result.get('error', '未知错误')}")
                else:
                    st.warning("请在侧边栏中配置 GitHub 访问令牌以启用部署功能")
                    st.info("如何获取 GitHub 访问令牌: \n1. 登录 GitHub \n2. 进入 Settings > Developer Settings > Personal access tokens \n3. 创建一个带有 `repo` 和 `workflow` 权限的令牌")

                # 使用说明
                with st.expander("使用说明", expanded=True):
                    st.markdown("""
                    ### 如何运行您的Streamlit应用
                    
                    #### 方法1：使用智能启动包（推荐）
                    1. 下载"智能启动包"并解压到任意位置
                    2. 打开解压后的文件夹，查看"启动说明.html"获取详细帮助
                    3. Windows用户：双击运行"启动应用.bat"
                    4. Mac/Linux用户：打开终端，给"启动应用.sh"添加执行权限，然后运行
                       ```
                       chmod +x 启动应用.sh
                       ./启动应用.sh
                       ```
                    5. 启动器会自动检查您的系统环境：
                       - 如果没有安装Python，会尝试自动下载并安装
                       - 自动创建虚拟环境并安装所需依赖
                       - 启动应用并在浏览器中打开
                    
                    #### 方法2：从源代码手动运行
                    1. 下载"源代码"并解压
                    2. 确保您已安装Python 3.7+
                    3. 打开命令行，进入解压后的目录
                    4. 创建并激活虚拟环境（推荐）：
                       ```
                       # Windows
                       python -m venv venv
                       venv\\Scripts\\activate
                       
                       # Mac/Linux
                       python3 -m venv venv
                       source venv/bin/activate
                       ```
                    5. 安装依赖：`pip install -r requirements.txt`
                    6. 运行应用：`streamlit run app.py`
                    """)

# 资源管理选项卡
with tab2:
    st.header("资源管理")
    st.markdown("上传文件和图片，可用于生成的应用中")
    
    # 资源上传部分
    upload_type = st.radio("上传类型", ["图片", "数据", "其他文件"], horizontal=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if upload_type == "图片":
            uploaded_file = st.file_uploader("上传图片", type=config.ALLOWED_IMAGE_TYPES, 
                                            help="支持PNG、JPG、GIF和SVG格式", key="image_uploader")
            if st.button("添加图片", key="add_image"):
                if uploaded_file:
                    resource = handle_uploaded_resource(uploaded_file, "图片")
                    if resource:
                        st.success(f"图片 {resource['name']} 上传成功！")
                else:
                    st.error("请先选择要上传的图片")
                    
        elif upload_type == "数据":
            uploaded_file = st.file_uploader("上传数据文件", type=config.ALLOWED_DATA_TYPES, 
                                           help="支持CSV、Excel、JSON和文本文件", key="data_uploader")
            if st.button("添加数据", key="add_data"):
                if uploaded_file:
                    resource = handle_uploaded_resource(uploaded_file, "数据")
                    if resource:
                        st.success(f"数据文件 {resource['name']} 上传成功！")
                else:
                    st.error("请先选择要上传的数据文件")
                    
        else:  # 其他文件
            uploaded_file = st.file_uploader("上传其他文件", type=None, key="other_uploader")
            if st.button("添加文件", key="add_other"):
                if uploaded_file:
                    resource = handle_uploaded_resource(uploaded_file, "其他")
                    if resource:
                        st.success(f"文件 {resource['name']} 上传成功！")
                else:
                    st.error("请先选择要上传的文件")
    
    with col2:
        if upload_type == "图片" and uploaded_file:
            st.image(uploaded_file, caption="预览图片", use_column_width=True)
        elif upload_type == "数据" and uploaded_file:
            if uploaded_file.name.endswith('.csv'):
                try:
                    import pandas as pd
                    df = pd.read_csv(uploaded_file)
                    st.dataframe(df.head(5))
                except Exception as e:
                    st.warning(f"无法预览CSV: {str(e)}")
            elif uploaded_file.name.endswith('.xlsx'):
                try:
                    import pandas as pd
                    df = pd.read_excel(uploaded_file)
                    st.dataframe(df.head(5))
                except Exception as e:
                    st.warning(f"无法预览Excel: {str(e)}")
            elif uploaded_file.name.endswith('.json'):
                try:
                    data = json.loads(uploaded_file.getvalue())
                    st.json(data)
                except Exception as e:
                    st.warning(f"无法预览JSON: {str(e)}")
            else:
                try:
                    content = uploaded_file.getvalue().decode('utf-8')
                    st.text_area("文件内容预览", value=content[:500] + ("..." if len(content) > 500 else ""), 
                               height=200, disabled=True)
                except:
                    st.warning("无法预览文件内容")
    
    # 已上传资源列表
    st.subheader("已上传的资源")
    
    if not st.session_state.uploaded_resources:
        st.info("您还没有上传任何资源")
    else:
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.write("**名称**")
        with col2:
            st.write("**类型**")
        with col3:
            st.write("**操作**")
            
        for i, resource in enumerate(st.session_state.uploaded_resources):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"{resource['name']} ({resource['id']})")
            with col2:
                st.write(resource['type'])
            with col3:
                if st.button("删除", key=f"del_{resource['id']}"):
                    # 删除文件
                    try:
                        os.remove(resource['path'])
                    except:
                        pass
                    # 从列表中移除
                    st.session_state.uploaded_resources.pop(i)
                    st.experimental_rerun()

# 历史记录页面
with tab3:
    st.header("生成历史")
    
    if not st.session_state.history:
        st.info("您还没有生成过应用")
    else:
        for i, app in enumerate(reversed(st.session_state.history)):
            with st.expander(f"{app['name']} - {app['timestamp']}"):
                st.write(f"**描述**: {app['description']}")
                st.write(f"**类型**: {app['type']}")
                
                # 显示包含的资源
                if 'resources' in app and app['resources']:
                    st.write("**包含的资源:**")
                    for resource in app['resources']:
                        st.write(f"- {resource['name']} ({resource['type']})")
                
                # 显示 GitHub 部署状态（如果有）
                if 'github_deployment' in app and app['github_deployment'].get('status') == 'success':
                    st.write(f"**GitHub 仓库**: [{app['github_deployment'].get('repo_name')}]({app['github_deployment'].get('url')})")
                
                col1, col2 = st.columns(2)
                with col1:
                    if app["source_zip"] and os.path.exists(app["source_zip"]):
                        with open(app["source_zip"], "rb") as f:
                            st.download_button(
                                f"下载源代码",
                                data=f.read(),
                                file_name=f"{app['name']}_source.zip",
                                mime="application/zip",
                                key=f"src_{i}",
                                use_container_width=True
                            )
                    else:
                        st.error("源代码不可用")
                        
                with col2:
                    if app["exe_path"] and os.path.exists(app["exe_path"]):
                        with open(app["exe_path"], "rb") as f:
                            st.download_button(
                                f"下载智能启动包",
                                data=f.read(),
                                file_name=os.path.basename(app["exe_path"]),
                                mime="application/octet-stream",
                                key=f"exe_{i}",
                                use_container_width=True
                            )
                    else:
                        st.warning("启动包不可用")

# 部署到 GitHub 的函数
def deploy_to_github(app_dir, app_name, github_token):
    # 更新进度
    update_progress("GitHub 部署", "正在部署到 StreamlitForge 组织...", 85)
    
    try:
        # 规范化仓库名（移除空格，使用短横线分隔）
        repo_name = app_name.lower().replace(" ", "-")
        # 移除其他非法字符
        repo_name = ''.join(c for c in repo_name if c.isalnum() or c == '-')
        
        # GitHub API 端点
        api_url = "https://api.github.com"
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # 1. 创建仓库
        create_repo_url = f"{api_url}/orgs/StreamlitForge/repos"
        repo_data = {
            "name": repo_name,
            "description": f"Streamlit 应用: {app_name}",
            "private": False,
            "auto_init": True
        }
        
        response = requests.post(create_repo_url, headers=headers, json=repo_data)
        
        if response.status_code != 201:
            return {"success": False, "error": f"创建仓库失败: {response.json().get('message', '未知错误')}"}
        
        # 仓库创建成功，获取仓库信息
        repo_info = response.json()
        repo_url = repo_info["html_url"]
        
        # 等待几秒钟，确保仓库初始化完成
        time.sleep(2)
        
        # 2. 上传应用文件
        files_to_upload = []
        for root, dirs, files in os.walk(app_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, app_dir)
                
                # 读取文件内容
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                files_to_upload.append({
                    "path": rel_path,
                    "content": content
                })
        
        # 3. 逐个上传文件
        for file_item in files_to_upload:
            # 更新进度详情
            update_progress("GitHub 部署", f"正在上传文件: {file_item['path']}", 90)
            
            upload_url = f"{api_url}/repos/StreamlitForge/{repo_name}/contents/{file_item['path']}"
            
            # 编码文件内容
            content_b64 = base64.b64encode(file_item['content']).decode('utf-8')
            
            upload_data = {
                "message": f"上传 {file_item['path']}",
                "content": content_b64
            }
            
            response = requests.put(upload_url, headers=headers, json=upload_data)
            
            if response.status_code not in [200, 201]:
                return {"success": False, "error": f"上传文件 {file_item['path']} 失败: {response.json().get('message', '未知错误')}"}
        
        # 4. 创建 requirements.txt（如果不存在）
        if not any(f['path'] == 'requirements.txt' for f in files_to_upload):
            req_content = "streamlit>=1.22.0\npandas\nmatplotlib\n"
            req_content_b64 = base64.b64encode(req_content.encode('utf-8')).decode('utf-8')
            
            req_upload_data = {
                "message": "添加 requirements.txt",
                "content": req_content_b64
            }
            
            req_upload_url = f"{api_url}/repos/StreamlitForge/{repo_name}/contents/requirements.txt"
            response = requests.put(req_upload_url, headers=headers, json=req_upload_data)
        
        # 部署完成
        update_progress("完成", "应用已成功部署到 GitHub！", 100)
        
        return {
            "success": True, 
            "repo_url": repo_url,
            "repo_name": repo_name,
            "org": "StreamlitForge"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
