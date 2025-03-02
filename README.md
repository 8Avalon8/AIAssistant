# AI助手项目

这是一个基于Python的AI助手项目，集成了多种功能，包括：

- AI对话功能
- Jenkins工具集成
- SVN代码审查
- 飞书通知功能
- 构建通知系统

## 安装

1. 克隆仓库
```bash
git clone https://github.com/yourusername/AIAssistant.git
cd AIAssistant
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件，填入必要的配置信息
```

## 使用方法

运行主应用：
```bash
python app.py
```

## 功能模块

- `AIAssistant.py`: AI助手核心功能
- `app.py`: Web应用入口
- `jenkinstools.py`: Jenkins工具集成
- `svncommiterreview.py`: SVN代码审查功能
- `build_notify.py`: 构建通知系统
- `feishu_notifier.py`: 飞书通知功能

## 环境变量配置

请参考`.env.example`文件了解需要配置的环境变量。 