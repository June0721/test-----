"""
配置文件，存储常量和配置项
"""
import os
import json

# 默认下载目录
DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "bilibili_videos")
# 确保下载目录存在
if not os.path.exists(DEFAULT_DOWNLOAD_DIR):
    os.makedirs(DEFAULT_DOWNLOAD_DIR)

# 用户配置文件
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_config.json")

# 加载用户配置，增加错误处理
def load_user_config():
    """
    从文件加载用户配置
    
    Returns:
        dict: 配置字典
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            print(f"Debug - 成功加载配置文件")
            
            # 检查SESSDATA是否存在
            if "sessdata" in config:
                print(f"Debug - 发现SESSDATA，长度={len(config['sessdata'])}")
            else:
                print(f"Warning - 配置文件中不存在SESSDATA")
                
            return config
        except json.JSONDecodeError:
            print(f"Error - 配置文件格式错误: {CONFIG_FILE}")
            return {}
        except Exception as e:
            import traceback
            print(f"Error - 加载配置失败: {str(e)}")
            print(traceback.format_exc())
            return {}
    else:
        print(f"Info - 配置文件不存在，将使用默认配置: {CONFIG_FILE}")
        return {}

# 保存用户配置
def save_user_config(config):
    """
    保存用户配置到文件，并更新全局变量
    
    Args:
        config: 配置字典
    """
    print(f"Debug - 保存用户配置: {list(config.keys())}")
    
    # 确保SESSDATA存在时不为空字符串
    if "sessdata" in config and not config["sessdata"]:
        print("Warning - SESSDATA为空字符串，将从配置中移除")
        del config["sessdata"]
        
    try:
        # 确保配置目录存在
        config_dir = os.path.dirname(CONFIG_FILE)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            
        # 保存到文件
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        # 测试保存是否成功
        if os.path.exists(CONFIG_FILE):
            print(f"Debug - 配置文件已保存: {CONFIG_FILE}")
        else:
            print(f"Error - 配置文件保存失败: {CONFIG_FILE}")
            
        # 更新全局变量USER_CONFIG和DEFAULT_CONFIG中的登录信息
        global USER_CONFIG, DEFAULT_CONFIG
        USER_CONFIG = config.copy()
        
        # 更新DEFAULT_CONFIG中的登录信息
        for key in ["sessdata", "bili_jct", "buvid3"]:
            if key in config:
                DEFAULT_CONFIG[key] = config[key]
                if key == "sessdata":
                    print(f"Debug - 更新DEFAULT_CONFIG[{key}]成功，长度={len(config[key])}")
            else:
                print(f"Debug - 配置中不存在{key}")
                DEFAULT_CONFIG[key] = ""
    
    except Exception as e:
        import traceback
        print(f"Error - 保存配置失败: {str(e)}")
        print(traceback.format_exc())

# 更新单个配置项
def update_config(key, value):
    """
    更新单个配置项，保证配置同步
    
    Args:
        key: 配置键
        value: 配置值
    """
    global DEFAULT_CONFIG, USER_CONFIG
    
    # 更新内存中的配置
    DEFAULT_CONFIG[key] = value
    USER_CONFIG[key] = value
    
    # 保存到文件
    save_user_config(USER_CONFIG)
    
    print(f"Debug - 配置项'{key}'已更新")

# 用户配置
USER_CONFIG = load_user_config()

# 默认下载设置
DEFAULT_CONFIG = {
    "download_dir": DEFAULT_DOWNLOAD_DIR,
    "thread_count": 8,          # 默认下载线程数
    "default_quality": "superhigh",  # 默认画质选择为4K
    "chunk_size": 1024 * 1024,  # 每个分块1MB
    "debug": True,              # 调试模式
    # B站登录信息，从用户配置中加载
    "sessdata": USER_CONFIG.get("sessdata", ""),      # 登录cookie: SESSDATA
    "bili_jct": USER_CONFIG.get("bili_jct", ""),      # 登录cookie: bili_jct
    "buvid3": USER_CONFIG.get("buvid3", ""),           # 登录cookie: buvid3
    "auto_degrade": True,        # 自动降级到最高可用画质
    "show_degrade_notice": True  # 是否显示降级提示
}

# 画质配置
QUALITY_OPTIONS = {
    "ultra": {
        "code": 127,
        "desc": "超清 8K",
        "requires_vip": True
    },
    "superhigh": {
        "code": 120,
        "desc": "超清 4K",
        "requires_vip": True
    },
    "high": {
        "code": 116,
        "desc": "高清 1080P60",
        "requires_vip": True
    },
    "medium": {
        "code": 80,
        "desc": "高清 1080P",
        "requires_vip": False
    },
    "low": {
        "code": 64,
        "desc": "高清 720P",
        "requires_vip": False
    }
}

# 画质ID到描述的映射
QUALITY_MAP = {
    127: "超清 8K",
    126: "杜比视界",
    125: "HDR 真彩色",
    120: "超清 4K",
    116: "高清 1080P60",
    112: "高清 1080P+",
    80: "高清 1080P",
    74: "高清 720P60",
    64: "高清 720P",
    32: "清晰 480P",
    16: "流畅 360P"
}

# API相关
BILIBILI_API = {
    "video_info": "https://api.bilibili.com/x/web-interface/view",  # 使用基础API
    "video_stream": "https://api.bilibili.com/x/player/playurl",    # 使用基础API
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "accept": "application/json, text/plain, */*",
    "accept_language": "zh-CN,zh;q=0.9,en;q=0.8",
    "accept_encoding": "gzip, deflate, br"
}

# 历史记录文件
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "download_history.json")

# 错误重试次数
MAX_RETRIES = 3
RETRY_DELAY = 1  # 重试延迟（秒）
