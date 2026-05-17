"""
OAuth Configuration for multi-platform authentication.

Environment Variables Required:
- JWT_SECRET_KEY: Secret key for JWT token signing
- SUPABASE_URL: Supabase project URL
- SUPABASE_KEY: Supabase service role or anon key

OAuth Provider Credentials:
- GitHub: GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET
- Microsoft: MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET, MICROSOFT_TENANT_ID
- Feishu: FEISHU_CLIENT_ID, FEISHU_CLIENT_SECRET
- WeChat: WECHAT_CLIENT_ID, WECHAT_CLIENT_SECRET
- Alipay: ALIPAY_CLIENT_ID, ALIPAY_CLIENT_SECRET
- Douyin: DOUYIN_CLIENT_ID, DOUYIN_CLIENT_SECRET
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # JWT Settings
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 * 24 * 60  # 30 days
    
    # Supabase Database Settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # OAuth Providers - GitHub
    GITHUB_CLIENT_ID: str = "demo-github"
    GITHUB_CLIENT_SECRET: str = "demo-secret"
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/api/auth/callback/github"
    
    # OAuth Providers - Microsoft
    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""
    MICROSOFT_TENANT_ID: str = "common"
    MICROSOFT_REDIRECT_URI: str = "http://localhost:8000/api/auth/callback/microsoft"
    
    # OAuth Providers - Feishu
    FEISHU_CLIENT_ID: str = ""
    FEISHU_CLIENT_SECRET: str = ""
    FEISHU_REDIRECT_URI: str = "http://localhost:8000/api/auth/callback/feishu"
    
    # OAuth Providers - WeChat
    WECHAT_CLIENT_ID: str = ""
    WECHAT_CLIENT_SECRET: str = ""
    WECHAT_REDIRECT_URI: str = "http://localhost:8000/api/auth/callback/wechat"
    
    # OAuth Providers - Alipay
    ALIPAY_CLIENT_ID: str = ""
    ALIPAY_CLIENT_SECRET: str = ""
    ALIPAY_REDIRECT_URI: str = "http://localhost:8000/api/auth/callback/alipay"
    
    # OAuth Providers - Douyin
    DOUYIN_CLIENT_ID: str = ""
    DOUYIN_CLIENT_SECRET: str = ""
    DOUYIN_REDIRECT_URI: str = "http://localhost:8000/api/auth/callback/douyin"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# OAuth Provider configurations
OAUTH_PROVIDERS = {
    "github": {
        "name": "GitHub",
        "icon": "github",
        "authorize_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "user_info_url": "https://api.github.com/user",
        "scope": "user:email"
    },
    "microsoft": {
        "name": "Microsoft",
        "icon": "microsoft",
        "authorize_url": "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
        "user_info_url": "https://graph.microsoft.com/v1.0/me",
        "scope": "User.Read"
    },
    "feishu": {
        "name": "飞书",
        "icon": "feishu",
        "authorize_url": "https://open.feishu.cn/open-apis/authen/v1/authorize",
        "token_url": "https://open.feishu.cn/open-apis/authen/v1/access_token",
        "user_info_url": "https://open.feishu.cn/open-apis/authen/v1/user_info",
        "scope": "user.email"
    },
    "wechat": {
        "name": "微信",
        "icon": "wechat",
        "authorize_url": "https://open.weixin.qq.com/connect/qrconnect",
        "token_url": "https://api.weixin.qq.com/sns/oauth2/access_token",
        "user_info_url": "https://api.weixin.qq.com/sns/userinfo",
        "scope": "snsapi_login"
    },
    "alipay": {
        "name": "支付宝",
        "icon": "alipay",
        "authorize_url": "https://openauth.alipay.com/oauth2/publicAppAuthorize",
        "token_url": "https://openapi.alipay.com/gateway.do",
        "user_info_url": "https://openapi.alipay.com/userinfo/share",
        "scope": "auth_user"
    },
    "douyin": {
        "name": "抖音",
        "icon": "douyin",
        "authorize_url": "https://open.douyin.com/oauth/authorize",
        "token_url": "https://open.douyin.com/oauth/access_token",
        "user_info_url": "https://open.douyin.com/oauth/userinfo",
        "scope": "user_info.basic"
    }
}

