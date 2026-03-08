#!/usr/bin/env python3
"""
ARL 灯塔批量导入 IP 工具
- 低速率导入（1 IP/秒）
- 实时汇报进度
- 配合 Nuclei 扫描
"""

import requests
import time
import json
import sys
import re

ARL_URL = "http://107.172.8.123:5003"
USERNAME = "admin"
PASSWORD = "yanling6,hate"

def login():
    """登录 ARL 获取 Cookie"""
    session = requests.Session()
    
    # 获取登录页面
    login_page = session.get(f"{ARL_URL}/", verify=False)
    
    # 提取 CSRF token
    csrf = re.search(r'name="_csrf" value="([^"]+)"', login_page.text)
    csrf_token = csrf.group(1) if csrf else ""
    
    # 登录
    login_data = f"username={USERNAME}&password={PASSWORD.replace(',', '%2C')}&_csrf={csrf_token}"
    resp = session.post(
        f"{ARL_URL}/user/login",
        data=login_data,
        verify=False,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if resp.status_code == 302:
        print(f"✅ ARL 登录成功")
        return session
    else:
        print(f"❌ 登录失败：{resp.status_code}")
        return None

def add_ip(session, ip):
    """添加 IP 到 ARL"""
    try:
        resp = session.post(
            f"{ARL_URL}/api/ip",
            json={"ip": ip, "group_id": 1},
            verify=False,
            timeout=10
        )
        return resp.status_code in [200, 201]
    except:
        return False

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    
    session = login()
    if session:
        print("测试添加 IP...")
        result = add_ip(session, "1.1.1.1")
        print(f"测试结果：{'成功' if result else '失败'}")
    else:
        sys.exit(1)
