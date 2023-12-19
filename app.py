from apiflask import APIFlask, HTTPTokenAuth
import pymysql
import time
from config import CONFIG

app = APIFlask(__name__)
auth = HTTPTokenAuth()

trigger = 0
trigger_button = 'None'
trigger_times = 0

class CoinDB(object):
    def __init__(self) -> None:
        pass
    
    def connect():
        global db_coin
        db_coin = pymysql.connect(
                            host=CONFIG.HOST,
                            port=CONFIG.PORT,
                            user=CONFIG.USER,
                            password=CONFIG.PASSWORD,
                            database=CONFIG.DATABASE
                            )
        
    def disconnect():
        global db_coin
        db_coin.close()
        
    def use_coin(user):
        ''':param user: 需要扣除币数的用户'''
        coin_cursor = db_coin.cursor()
        coin_sql = f"SELECT * FROM coins WHERE `user` = '{user}'"
        try:
            coin_cursor.execute(coin_sql)
            result = coin_cursor.fetchall()
            if not result:
                return False
            username = result[0][0]
            coin = result[0][1] - 1
            update_sql = f"UPDATE `coins` SET `coin`='{coin}' WHERE `user`='{username}'"
            try:
                coin_cursor.execute(update_sql)
                db_coin.commit()
            except Exception as e:
                print(f'更新错误:{e}')
                db_coin.rollback()
                return False
            return True, coin
        except Exception as e:
            print(e)
            return False

# 存储token和对应的用户示例
users = {'114514':'judjdigj','1919810':'AkariMai'}

# 用于验证令牌的字段
@auth.verify_token
def verify_token(token):
    if token in users:
        return users[token]
    return False

@auth.error_handler
def error_auth(status):
    if status == 401:
        return {'status': 'error', 'message' :'login require'}, 401
    elif status == 404:
        return {'status': 'error', 'message': 'Not found'}, 404
    else:
        return {'status': 'error', 'message' :'internal error'}, status
    
@app.get('/trigger')
@auth.login_required
def trigger_handler():
    '''
    按钮处理函数，通过监听单片机请求实现长轮询\n
    若触发test_pin()时中断轮询并实现向单片机发送信息
    '''
    global trigger, trigger_button, trigger_times
    
    if trigger == 1:
        trigger = 0 # 复位
        trigger_time = trigger_times
        trigger_times = 0 # 复位
        return {'status':'success','pin':f'{trigger_button}','times': trigger_time},200
    return{'status':'empty'},203
        

@app.get('/coin_pin')
@auth.login_required
def coin_pin():
    # 这里判断如果触发成功后的扣除次数逻辑，使用MySQL比对用户名后扣除数据库中次数
    cdb=CoinDB
    cdb.connect()
    user = auth.current_user
    coin = cdb.use_coin(user)
    if coin:
        print("成功扣除")
        # TODO:在这里执行将引脚设置为低电平的操作
        global trigger,trigger_button,trigger_times
        trigger = 1
        trigger_times += 1
        trigger_button = 'service'
        print("trigger SERVICE")
    else:
        print("扣币失败...")
        cdb.disconnect()
        return {'status': 'failed', 'message': f"Cannot taken {user}'s COIN.", 'coin': f'{coin[1]+1}'}
    cdb.disconnect()
    return {'status': 'success', 'message': f'{user} trigger COIN Pin', 'coin': f'{coin[1]}'}

@app.get('/test_pin')
@auth.login_required
def test_pin():
    # 在这里执行将引脚设置为低电平的操作
    user = auth.current_user
    global trigger,trigger_button
    trigger = 1
    trigger_button = 'test'
    print("trigger TEST")
    return {'status': 'success', 'message': f'{user} trigger TEST Pin'}

if __name__ == '__main__':
    app.run(host='192.168.0.103',port='5000',debug=True)
