# ServerControl

远程服务器管理工具 -- 基于 Python + Tkinter + Paramiko 构建的 SSH 客户端。  

## 功能特性

- SSH 连接管理：支持密码和密钥文件两种认证方式
- 会话管理器：保存历史登录会话，支持快速重连
- 密码安全存储：使用 Windows 凭据管理器（keyring）或 Fernet 加密文件存储密码
- 命令面板：预设常用服务器管理命令，一键执行
- 流式输出控制台：实时显示命令执行结果，支持错误高亮
- 连接测试：在保存连接前可测试连接是否正常

## 项目结构

```
ServerControl/
|-- assets/style/           # 样式资源
|-- config/
|   |-- commands.json       # 预设命令配置
|-- src/
|   |-- core/
|   |   |-- ssh_manager.py  # SSH 连接管理器
|   |   |-- sftp_browser.py # SFTP 文件浏览
|   |   |-- command_registry.py # 命令注册表
|   |-- security/
|   |   |-- credential_store.py # 凭据存储（keyring + 加密文件）
|   |   |-- crypto_utils.py    # 加密工具
|   |-- ui/
|   |   |-- main_window.py  # 主窗口
|   |   |-- session_manager.py # 会话管理器
|   |   |-- command_panel.py # 命令面板
|   |   |-- output_console.py # 输出控制台
|   |   |-- connection_dialog.py # 连接配置对话框
|   |   |-- setup_wizard.py # 首次配置向导
|   |   |-- styles.py       # UI 样式定义
|   |-- utils/
|   |   |-- config_paths.py # 配置文件路径
|   |   |-- logger.py       # 日志配置
|   |   |-- error_messages.py # 错误信息
|   |-- workers/
|   |   |-- __init__.py     # 任务运行器（线程池）
|   |-- app.py              # 应用启动器
|   |-- main.py             # 入口点
|-- requirements.txt        # Python 依赖
|-- build.bat               # 打包脚本
|-- LICENSE                 # MIT 许可证
```

## 技术栈

- Python 3.8+
- Tkinter（GUI 框架，Python 内置）
- Paramiko（SSH 协议实现）
- Keyring（系统凭据存储）
- Cryptography（Fernet 对称加密）

## 安装与运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行程序

```bash
python src/main.py
```


## 打包为可执行文件

### 安装 PyInstaller

```bash
pip install pyinstaller
```

### 执行打包

或直接运行 `build.bat`：

```bash
pyinstaller --onefile --windowed --name "ServerControl" --icon "assets/app_icon.ico" --add-data "assets;assets" --add-data "config;config" --hidden-import "keyring.backends.windows" --hidden-import "paramiko.transport" --noconfirm src/main.py
```

打包完成后，exe 文件位于 `dist/ServerControl.exe`。

## 命令配置

预设命令存储在 `config/commands.json` 中，支持以下字段：

| 字段 | 说明 |
|------|------|
| id | 命令唯一标识 |
| name | 命令显示名称 |
| description | 命令描述 |
| command | 要执行的 Shell 命令 |
| category | 命令分类 |
| confirm | 执行前是否需要确认 |
| confirm_message | 确认对话框显示的消息 |

## 安全说明

- 密码和连接信息加密存储在本机，不会发送到任何外部服务器
- 优先使用 Windows 凭据管理器存储密码（最安全）
- 凭据管理器不可用时，回退到加密文件存储（位于 `%APPDATA%\ServerControl\`）
- 程序不会在任何地方记录或传输明文密码

## 许可证

MIT License - 详见 [LICENSE](LICENSE)
