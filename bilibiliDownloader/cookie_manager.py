"""
Cookie 统一管理器，确保不同下载器使用相同的登录凭证
"""
from config import load_user_config

def get_bilibili_cookies():
    """获取B站cookies"""
    user_config = load_user_config()
    
    # 必要的登录凭证
    cookies = {
        'SESSDATA': user_config.get('sessdata', ''),
        'bili_jct': user_config.get('bili_jct', ''),
        'buvid3': user_config.get('buvid3', '')
    }
    
    # 防盗链相关的cookie
    anti_theft_cookies = {
        'buvid_fp': '45f95911b287556b17a766d625fbd571',
        'b_nut': '1715147201',
        'CURRENT_FNVAL': '4048',
        'CURRENT_QUALITY': '120',
        'innersign': '0'
    }
    
    # 合并cookies
    cookies.update(anti_theft_cookies)
    
    # 去除空值
    return {k: v for k, v in cookies.items() if v}
