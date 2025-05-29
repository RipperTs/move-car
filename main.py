from flask import Flask, render_template, request, jsonify
import json
import os
import requests
import time

# 创建Flask应用实例
app = Flask(__name__, template_folder='.')

# 频率限制缓存 - 存储每个车辆ID的最后通知时间
notification_cache = {}
NOTIFICATION_COOLDOWN = 2 * 60  # 2分钟冷却时间（秒）

def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"car_list": []}
    except json.JSONDecodeError:
        return {"car_list": []}

def find_car_by_id(car_id):
    """根据ID查找车辆信息"""
    config = load_config()
    car_list = config.get('car_list', [])
    
    for car in car_list:
        if car.get('id') == car_id:
            return car
    return None

def check_notification_rate_limit(car_id):
    """检查通知频率限制"""
    current_time = time.time()
    last_notification_time = notification_cache.get(car_id, 0)
    
    if current_time - last_notification_time < NOTIFICATION_COOLDOWN:
        # 仍在冷却期
        remaining_time = NOTIFICATION_COOLDOWN - (current_time - last_notification_time)
        return False, remaining_time
    
    return True, 0

def update_notification_cache(car_id):
    """更新通知缓存"""
    notification_cache[car_id] = time.time()

def send_pushdeer_notification(token, message):
    """发送PushDeer通知"""
    try:
        url = "https://api2.pushdeer.com/message/push"
        params = {
            'pushkey': token,
            'text': message
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        return result
    except requests.exceptions.RequestException as e:
        print(f"PushDeer通知发送失败: {e}")
        return None
    except Exception as e:
        print(f"发送通知时发生错误: {e}")
        return None

@app.route('/')
def index():
    """主页路由，渲染挪车码页面"""
    return render_template('index.html')

@app.route('/car-detail')
def car_detail():
    """车辆详情接口，根据ID查询车辆信息"""
    # 获取ID参数
    car_id = request.args.get('id')
    
    if not car_id:
        return jsonify({
            'success': False,
            'message': '缺少必要参数：id',
            'data': None
        }), 400
    
    try:
        car_id = int(car_id)
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'ID参数格式错误，必须为数字',
            'data': None
        }), 400
    
    # 查找车辆信息
    car_info = find_car_by_id(car_id)
    
    if car_info:
        # 创建返回数据，移除敏感的push_deer_token字段
        safe_car_info = {
            'id': car_info.get('id'),
            'phone': car_info.get('phone')
        }
        
        return jsonify({
            'success': True,
            'message': '查询成功',
            'data': safe_car_info
        })
    else:
        return jsonify({
            'success': False,
            'message': f'未找到ID为 {car_id} 的车辆信息',
            'data': None
        }), 404

@app.route('/notify-car')
def notify_car():
    """挪车通知接口，通过PushDeer发送通知"""
    # 获取ID参数
    car_id = request.args.get('id')
    
    if not car_id:
        return jsonify({
            'success': False,
            'message': '缺少必要参数：id',
            'data': None
        }), 400
    
    try:
        car_id = int(car_id)
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'ID参数格式错误，必须为数字',
            'data': None
        }), 400
    
    # 检查频率限制
    can_notify, remaining_time = check_notification_rate_limit(car_id)
    if not can_notify:
        remaining_minutes = int(remaining_time // 60)
        remaining_seconds = int(remaining_time % 60)
        return jsonify({
            'success': False,
            'message': f'通知过于频繁，请等待 {remaining_minutes}分{remaining_seconds}秒后再试',
            'data': {
                'remaining_time': remaining_time,
                'cooldown_period': NOTIFICATION_COOLDOWN
            }
        }), 429  # Too Many Requests
    
    # 查找车辆信息
    car_info = find_car_by_id(car_id)
    
    if not car_info:
        return jsonify({
            'success': False,
            'message': f'未找到ID为 {car_id} 的车辆信息',
            'data': None
        }), 404
    
    # 获取PushDeer token
    push_deer_token = car_info.get('push_deer_token', '').strip()
    
    # 更新通知缓存（无论是否发送通知都要更新，防止频繁请求）
    update_notification_cache(car_id)
    
    if not push_deer_token:
        # 没有配置token，不发送通知但返回成功
        return jsonify({
            'success': True,
            'message': '挪车通知已处理（该车辆未配置推送服务）',
            'data': {
                'car_id': car_id,
                'notification_sent': False,
                'reason': 'no_token_configured',
                'next_available_time': time.time() + NOTIFICATION_COOLDOWN
            }
        })
    
    # 发送通知
    message = "您被挪车催了一下, 请尽快挪车."
    result = send_pushdeer_notification(push_deer_token, message)
    
    if result:
        return jsonify({
            'success': True,
            'message': '挪车通知发送成功',
            'data': {
                'car_id': car_id,
                'notification_sent': True,
                'notification_result': result,
                'next_available_time': time.time() + NOTIFICATION_COOLDOWN
            }
        })
    else:
        return jsonify({
            'success': False,
            'message': '挪车通知发送失败，请稍后重试',
            'data': None
        }), 500

@app.route('/health')
def health():
    """健康检查路由"""
    return {'status': 'ok', 'message': '挪车码服务运行正常'}

if __name__ == '__main__':
    print("🚗 挪车码服务启动中...")
    print("📱 访问地址: http://localhost:8000")
    print("🔗 健康检查: http://localhost:8000/health")
    print("⏹️  按 Ctrl+C 停止服务")
    
    # 启动Flask开发服务器
    app.run(
        host='0.0.0.0',  # 允许外部访问
        port=8000,       # 端口号
        debug=True       # 开启调试模式
    )
