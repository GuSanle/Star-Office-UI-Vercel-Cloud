#!/usr/bin/env python3
import sys
import os
import requests

def main():
    if len(sys.argv) < 2:
        print("Usage: python push_status.py <state> [detail]")
        sys.exit(1)
        
    state = sys.argv[1]
    detail = sys.argv[2] if len(sys.argv) > 2 else ""
    
    url = os.getenv("AGENT_CLOUD_URL")
    secret = os.getenv("AGENT_CLOUD_SECRET")
    name = os.getenv("AGENT_CLOUD_NAME", "Agent")
    
    if not url or not secret:
        print("error:Missing AGENT_CLOUD_URL or AGENT_CLOUD_SECRET")
        sys.exit(1)
        
    # Remove trailing slash if present
    if url.endswith("/"):
        url = url[:-1]
        
    try:
        res = requests.post(f"{url}/agent-push", json={
            "secret": secret,
            "state": state,
            "detail": detail,
            "name": name
        }, timeout=10).json()
        
        if res.get("ok"):
            print(f"ok:{res.get('remainingSeconds')}")
        elif res.get("code") == "SESSION_EXPIRED":
            print("expired")
            sys.exit(2)
        elif res.get("code") in ["PENDING", "REJECTED"]:
            print(res.get("code").lower())
            sys.exit(0) # 静默退出，不重复申请，等待审批
        else:
            if "未注册" in str(res.get("msg")):
                 print("need_join")
                 sys.exit(2) # 视为需要重新加入
            print(f"error:{res.get('msg')}")
            sys.exit(1)
    except Exception as e:
        print(f"error:{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
