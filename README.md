# 打印机共享修复工具

Windows 10/11 打印机共享问题一键修复工具（GUI 图形界面版）

![Python](https://img.shields.io/badge/Python-3.9-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%207%20%7C%2010%20%7C%2011-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 功能简介

本工具基于原版 BAT 脚本升级而来，采用 Python + tkinter 构建图形界面，提供 **14 项修复功能**，可一键解决 Windows 10/11 打印机共享的各种常见问题。

### 修复项目

| # | 修复项 | 说明 |
|---|--------|------|
| 1 | 启用 Guest 账户 | 解决匿名访问问题 |
| 2 | 配置防火墙规则 | 允许文件和打印机共享、网络发现 |
| 3 | 开放 LPR/LPD 端口 | TCP 515 / 721-731 |
| 4 | 注册表安全设置 | SMB签名、NTLM、AllowInsecureGuestAuth 等 |
| 5 | 打印机注册表配置 | RPC协议、Point and Print、驱动搜索、0x0000011b 修复 |
| 6 | 关闭 Defender 防火墙 | 三个配置文件全部关闭 |
| 7 | 设置网络为专用 | 所有网络接口改为专用网络 |
| 8 | 启用 SMB1 协议 | DISM 启用 |
| 9 | 安装 LPD 打印服务 | LPD/LPR 打印服务组件 |
| 10 | 配置系统服务 | Browser/SSDP/UPnP/FDResPub 等 |
| 11 | 修复网络访问权限 | secedit 安全策略 |
| 12 | 禁用隐藏共享 | C$/D$/Admin$ 等 |
| 13 | 刷新组策略 | gpupdate /force |
| 14 | 重启打印后台服务 | Print Spooler |

---

## 系统要求

- **操作系统**: Windows 7 SP1 / Windows 10 / Windows 11
- **权限**: 需要管理员权限（运行后自动请求 UAC 提权）
- **网络**: 部分功能需要联网（如 DISM 启用功能）

---

## 使用方法

### 方式一：直接运行 EXE（推荐）

1. 从 [Releases](https://github.com/你的用户名/PrinterShareFixer/releases) 下载最新版 `打印机共享修复工具.exe`
2. 双击运行（会自动请求管理员权限）
3. 选择需要修复的项目，点击"一键修复全部"或"修复选中项目"

### 方式二：从源码运行

```bash
# 1. 克隆仓库
git clone https://github.com/你的用户名/PrinterShareFixer.git
cd PrinterShareFixer

# 2. 运行（需要 Python 3.8+）
python PrinterShareFixer.py
```

### 方式三：自行打包 EXE

```bash
# 1. 安装依赖
pip install pyinstaller

# 2. 打包
pyinstaller PrinterShareFixer.spec --clean --noconfirm

# 3. 生成的 EXE 在 dist/ 目录下
```

---

## 界面预览

- 左侧复选框列表，可自由选择修复项
- 一键修复全部 / 修复选中项目 / 仅重启后台服务
- 实时进度条和状态提示
- 暗色日志区域，清晰显示执行过程

---

## 目录结构

```
PrinterShareFixer/
├── PrinterShareFixer.py      # GUI 主程序源代码
├── PrinterShareFixer.spec    # PyInstaller 打包配置
├── build.bat                 # 一键重新打包脚本
├── redist/                   # 运行时 DLL（Win7 兼容）
│   ├── ucrtbase.dll
│   ├── vcruntime140.dll
│   ├── vcruntime140_1.dll
│   └── api-ms-win-*.dll
├── dist/                     # 打包产物
│   └── 打印机共享修复工具.exe
├── win10.11打印机共享修复工具.bat  # 原版 BAT 脚本
├── README.md                 # 项目说明
├── LICENSE                   # 开源协议
└── CHANGELOG.md              # 更新日志
```

---

## 常见问题

### Q: 运行后提示需要管理员权限？
A: 工具会自动请求 UAC 提权，请点击"是"允许。

### Q: 某些修复项失败？
A: 部分功能需要系统组件支持（如 DISM），请确保系统完整。可查看日志区域了解具体错误。

### Q: Win7 系统无法运行？
A: 请确保使用最新版的 EXE，已内置 VC++ 运行时库。如果仍有问题，请安装 [VC++ 2015-2022 Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)。

### Q: 修复后还是无法共享？
A: 建议重启电脑后再次尝试，并确保主机和客户端在同一局域网内。

---

## 免责声明

本工具通过修改系统注册表和防火墙设置来解决打印机共享问题。虽然已尽量保证安全性，但作者不对因使用本工具导致的任何问题承担责任。建议在使用前备份重要数据。

---

## 作者

- **WqlSoft**（原版 BAT 脚本作者）
- GUI 版本由 AI 辅助开发

---

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件
