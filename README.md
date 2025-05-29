# 挪车通知 H5 页面

一个简洁美观的移动端挪车通知页面，专为扫码挪车场景设计。现已集成Flask后端服务。

## 功能特点

- 📱 **移动端优化**: 专为手机端设计的响应式布局
- 🎨 **现代化UI**: 采用渐变背景和毛玻璃效果，界面简洁大方
- 📞 **智能电话拨打**: 根据车辆ID动态获取车主电话并拨打
- ⏰ **催促提醒**: 发送挪车提醒通知
- 🎯 **交互反馈**: 按钮点击动效和提示消息
- 🌟 **动画效果**: 页面加载和按钮交互动画
- 🚀 **Flask后端**: 集成Flask web服务器
- 📊 **JSON配置**: 使用JSON文件存储车辆信息
- 🔗 **URL参数支持**: 支持通过URL参数传递车辆信息
- 🔔 **PushDeer通知**: 集成PushDeer推送服务

## 快速开始

### 方式一：Python直接运行

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 启动服务

```bash
python main.py
```

### 方式二：Docker运行

#### 本地构建镜像

```bash
# 构建Docker镜像
docker build -t nuoche-app .

# 运行容器
docker run -d \
  --name nuoche-code-app \
  -p 8000:8000 \
  -v $(pwd)/config.json:/app/config.json:ro \
  nuoche-app
```

#### 使用Docker Compose（推荐）

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

**Docker Compose特点：**
- 自动使用预构建镜像 `registry.cn-hangzhou.aliyuncs.com/ripper/move-car:latest`
- 配置文件热更新（修改 `config.json` 后重启容器即可生效）
- 包含健康检查和自动重启
- 日志挂载到 `./logs` 目录

### 3. 访问应用

- 主页: http://localhost:8000
- 带车辆ID的页面: http://localhost:8000/?car_id=10001&type=qrcode
- 健康检查: http://localhost:8000/health
- 车辆详情: http://localhost:8000/car-detail?id=10001
- 挪车通知: http://localhost:8000/notify-car?id=10001

服务启动后，你可以在浏览器中访问上述地址查看挪车页面。

## 页面设计

### 视觉特色
- 蓝紫色渐变背景
- 半透明毛玻璃容器
- 圆角设计和阴影效果
- 汽车图标和emoji装饰

### 功能按钮
1. **电话通知车主** (蓝色按钮)
   - 自动获取车主电话号码
   - 点击后直接拨打车主电话
   - 支持tel:协议唤起拨号程序
   - 2分钟冷却时间防止频繁拨打

2. **催一下车主** (绿色按钮)
   - 发送挪车提醒消息
   - 可集成短信或推送通知
   - 2分钟冷却时间防止频繁催促

### URL参数说明

页面支持以下URL参数：
- `car_id`: 车辆ID（必需），用于获取车主信息
- `type`: 访问类型（可选），如 `qrcode` 表示二维码扫描访问

**访问示例**：
```
http://localhost:8000/?car_id=10001&type=qrcode
```

## Flask应用结构

```
挪车码/
├── main.py              # Flask应用主文件
├── index.html           # HTML模板
├── config.json          # 车辆信息配置文件
├── requirements.txt     # Python依赖
└── README.md           # 项目说明
```

### 路由说明

- `GET /`: 渲染挪车页面
- `GET /health`: 健康检查接口，返回服务状态
- `GET /car-detail`: 车辆详情接口，根据ID查询车辆信息
- `GET /notify-car`: 挪车通知接口，通过PushDeer发送通知

### API接口详情

#### 车辆详情接口

**接口地址**: `/car-detail`  
**请求方法**: GET  
**请求参数**:
- `id` (必需): 车辆ID，数字类型

**响应格式**:
```json
{
    "success": true,
    "message": "查询成功",
    "data": {
        "id": 10001,
        "phone": ""
    }
}
```

**安全说明**: 为保护隐私，该接口不会返回 `push_deer_token` 等敏感信息。

#### 挪车通知接口

**接口地址**: `/notify-car`  
**请求方法**: GET  
**请求参数**:
- `id` (必需): 车辆ID，数字类型

**响应格式**:

成功发送通知：
```json
{
    "success": true,
    "message": "挪车通知发送成功",
    "data": {
        "car_id": 10001,
        "notification_sent": true,
        "notification_result": {
            "code": 0,
            "content": {
                "result": ["success"]
            }
        },
        "next_available_time": 1748495150.141845
    }
}
```

未配置推送服务：
```json
{
    "success": true,
    "message": "挪车通知已处理（该车辆未配置推送服务）",
    "data": {
        "car_id": 10002,
        "notification_sent": false,
        "reason": "no_token_configured",
        "next_available_time": 1748495154.495306
    }
}
```

频率限制错误：
```json
{
    "success": false,
    "message": "通知过于频繁，请等待 1分54秒后再试",
    "data": {
        "remaining_time": 114.7,
        "cooldown_period": 120
    }
}
```

**频率限制**: 
- 每个车辆ID 2分钟内只能发送一次通知
- 限制在服务端内存中维护，重启服务后重置
- 无论是否实际发送通知，都会触发频率限制

**推送配置**:
- 如果车辆未配置 `push_deer_token` 或token为空，不会发送实际通知
- 但仍会返回成功状态，并触发频率限制
- 这样可以防止恶意频繁请求

**使用示例**:
```bash
# 查询存在的车辆
curl "http://localhost:8000/car-detail?id=10001"

# 发送挪车通知
curl "http://localhost:8000/notify-car?id=10001"

# 查询不存在的车辆
curl "http://localhost:8000/car-detail?id=99999"
```

### 配置文件说明

`config.json` 文件用于存储车辆信息，格式如下：

```json
{
    "car_list": [
        {
            "id": 10001,
            "phone": "",
            "push_deer_token": ""
        }
    ]
}
```

字段说明：
- `id`: 车辆唯一标识符
- `phone`: 车主电话号码
- `push_deer_token`: PushDeer推送服务的token

## 自定义配置

### 集成真实功能

在 JavaScript 代码中：

```javascript
// 电话通知 - 替换为实际车主电话
window.location.href = 'tel:车主电话号码';

// 催促提醒 - 集成你的短信或推送服务
// 例如调用后端API发送通知
fetch('/api/send-reminder', {
    method: 'POST',
    body: JSON.stringify({ carId: '车辆ID' })
});
```

### Flask配置

可以在 `main.py` 中修改以下配置：
- 端口号 (默认8000)
- 主机地址 (默认0.0.0.0)
- 调试模式 (默认开启)

### 样式自定义

可以通过修改CSS变量来调整页面样式：
- 修改渐变色彩
- 调整按钮颜色
- 更改圆角大小
- 调整间距和字体

## 技术特点

- Flask后端服务
- 纯HTML/CSS/JavaScript前端
- 无第三方依赖
- 支持现代浏览器
- 响应式设计
- 优雅的动画效果
- 频率限制防止滥用

## 浏览器兼容性

- iOS Safari 10+
- Android Chrome 60+
- 微信内置浏览器
- 支付宝内置浏览器

## 部署说明

### 开发环境
```bash
python main.py
```

### 生产环境
推荐使用Gunicorn等WSGI服务器：
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

### Docker部署（推荐）

#### 使用Docker Compose（推荐）
```bash
# 启动服务（后台运行）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看实时日志
docker-compose logs -f nuoche-app

# 重启服务（配置文件修改后）
docker-compose restart

# 停止并删除容器
docker-compose down
```

#### 本地构建部署
```bash
# 1. 构建镜像
docker build -t nuoche-app:latest .

# 2. 创建并运行容器
docker run -d \
  --name nuoche-code-app \
  -p 8000:8000 \
  -v $(pwd)/config.json:/app/config.json:ro \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  nuoche-app:latest

# 3. 查看容器状态
docker ps

# 4. 查看日志
docker logs -f nuoche-code-app
```

#### Docker部署注意事项
1. **配置文件管理**: `config.json` 通过数据卷挂载，可以在宿主机直接修改
2. **日志管理**: 日志文件挂载到 `./logs` 目录，便于查看和备份
3. **健康检查**: 容器内置健康检查，会自动检测服务状态
4. **自动重启**: 配置了 `unless-stopped` 重启策略，服务异常时自动重启
5. **网络配置**: 容器内服务运行在8000端口，映射到宿主机8000端口

#### 生产环境Docker配置建议
1. **反向代理**: 建议使用Nginx作为反向代理，配置HTTPS
2. **镜像管理**: 使用私有镜像仓库管理镜像版本
3. **数据持久化**: 重要配置和日志文件进行数据卷挂载
4. **监控告警**: 配置容器监控和告警机制
5. **资源限制**: 根据需要设置容器资源限制

### 其他建议
1. 配置HTTPS（推荐用于电话拨打功能）
2. 集成后端服务处理挪车通知逻辑
3. 可配置二维码指向此页面URL
4. 添加日志记录和监控 

### 工作流程

1. **页面加载**: 从URL参数中获取 `car_id`
2. **点击电话按钮**: 
   - 调用 `/car-detail` 接口获取车辆信息
   - 提取 `phone` 字段
   - 使用 `tel:` 协议拨打电话
3. **点击催促按钮**:
   - 调用 `/notify-car` 接口发送PushDeer通知
   - 显示发送结果提示
4. **错误处理**: 
   - 缺少车辆ID时显示警告
   - 接口调用失败时显示错误提示
   - 冷却期内点击时显示等待提示

### PushDeer配置

系统使用PushDeer服务发送挪车通知，需要在 `config.json` 中配置每个车辆的 `push_deer_token`：

```json
{
    "car_list": [
        {
            "id": 10001,
            "phone": "",
            "push_deer_token": ""
        }
    ]
}
```

通知消息内容：`您被挪车催了一下, 请尽快挪车.` 