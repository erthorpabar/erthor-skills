'''
帖子发布系统自动化测试脚本
支持 SQLAlchemy + redis.asyncio 版本
使用方法: python test.py
'''

import requests
import json
import time
from typing import Optional
import sys

# 配置
BASE_URL = "http://localhost:8000"
TEST_USER_1 = {"email": "testuser1@example.com", "username": "testuser1", "password": "password123"}
TEST_USER_2 = {"email": "testuser2@example.com", "username": "testuser2", "password": "password456"}

class Colors:
    """终端颜色输出"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_success(message: str):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message: str):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message: str):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_title(message: str):
    print(f"{Colors.BOLD}{Colors.CYAN}{message}{Colors.END}")

class PostSystemTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.user_id: Optional[int] = None
        self.news_ids = []
        self.user2_token: Optional[str] = None  # 用于测试跨用户操作
        
    def test_health_check(self):
        """测试健康检查"""
        print_info("测试健康检查...")
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "ok"
            print_success(f"健康检查通过 - {data.get('service', '未知服务')}")
            return True
        except requests.exceptions.ConnectionError:
            print_error("健康检查失败: 无法连接到服务器，请确保服务器正在运行")
            return False
        except Exception as e:
            print_error(f"健康检查失败: {e}")
            return False
    
    def test_register(self, email: str, username: str, password: str, should_success: bool = True):
        """测试用户注册"""
        print_info(f"测试用户注册: {email} ({username})...")
        try:
            response = requests.post(
                f"{self.base_url}/register",
                json={"email": email, "username": username, "password": password},
                timeout=5
            )
            
            if should_success:
                assert response.status_code == 200
                data = response.json()
                assert "user_id" in data
                assert "username" in data
                print_success(f"注册成功: {data['username']} (ID: {data['user_id']})")
                return True
            else:
                assert response.status_code != 200
                print_success(f"预期失败的注册确实失败了 - {response.json().get('detail', '')}")
                return True
        except AssertionError:
            if should_success:
                print_error(f"注册应该成功但失败了: {response.text}")
            else:
                print_error(f"注册应该失败但成功了: {response.text}")
            return False
        except Exception as e:
            print_error(f"注册测试失败: {e}")
            return False
    
    def test_login(self, email: str, password: str, should_success: bool = True, save_as_user2: bool = False):
        """测试用户登录"""
        print_info(f"测试用户登录: {email}...")
        try:
            response = requests.post(
                f"{self.base_url}/login",
                json={"email": email, "password": password},
                timeout=5
            )
            
            if should_success:
                assert response.status_code == 200
                data = response.json()
                token = data["token"]
                if save_as_user2:
                    self.user2_token = token
                    print_success(f"用户2登录成功，获得token: {token[:20]}...")
                else:
                    self.token = token
                    self.user_id = data.get("user_id")
                    print_success(f"登录成功，获得token: {token[:20]}...")
                    print(f"  用户ID: {data.get('user_id')}, 用户名: {data.get('username')}")
                return True
            else:
                assert response.status_code != 200
                print_success(f"预期失败的登录确实失败了 - {response.json().get('detail', '')}")
                return True
        except AssertionError:
            if should_success:
                print_error(f"登录应该成功但失败了: {response.text}")
            else:
                print_error(f"登录应该失败但成功了: {response.text}")
            return False
        except Exception as e:
            print_error(f"登录测试失败: {e}")
            return False
    
    def test_get_current_user(self):
        """测试获取当前用户信息"""
        print_info("测试获取当前用户信息...")
        try:
            response = requests.get(
                f"{self.base_url}/me",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=5
            )
            assert response.status_code == 200
            data = response.json()
            assert "user_id" in data
            assert "username" in data
            assert "email" in data
            self.user_id = data["user_id"]
            print_success(f"获取用户信息成功: {data['username']} (ID: {data['user_id']}, Email: {data['email']})")
            return True
        except Exception as e:
            print_error(f"获取用户信息失败: {e}")
            return False
    
    def test_create_news(self, title: str, article: str):
        """测试发布帖子"""
        print_info(f"测试发布帖子: {title}...")
        # 检查token是否存在
        if not self.token:
            print_error("Token不存在，无法发布帖子")
            return False
        try:
            response = requests.post(
                f"{self.base_url}/news",
                json={"title": title, "article": article},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=5
            )
            
            # 先检查状态码，如果不是200，打印详细信息
            if response.status_code != 200:
                print_error(f"HTTP状态码: {response.status_code}")
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', response.text)
                    print_error(f"错误详情: {error_detail}")
                except:
                    print_error(f"响应内容: {response.text}")
                return False
            
            data = response.json()
            news_id = data["news_id"]
            self.news_ids.append(news_id)
            print_success(f"发布成功，帖子ID: {news_id}, 标题: {data['title']}")
            return True
        except AssertionError:
            print_error(f"断言失败: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print_error(f"错误详情: {error_data.get('detail', response.text)}")
            except:
                print_error(f"响应内容: {response.text}")
            return False
        except Exception as e:
            print_error(f"发布帖子失败: {e}")
            if hasattr(e, 'response'):
                print_error(f"响应: {e.response.text}")
            return False
    
    def test_get_news_list(self, page: int = 1, page_size: int = 10):
        """测试获取帖子列表"""
        print_info(f"测试获取帖子列表 (第{page}页，每页{page_size}条)...")
        try:
            params = {"page": page, "page_size": page_size}
            response = requests.get(
                f"{self.base_url}/news",
                params=params,
                timeout=5
            )
            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert "total" in data
            assert "page" in data
            assert "page_size" in data
            news_list = data["data"]
            print_success(f"获取帖子列表成功，共 {data['total']} 条，当前页 {len(news_list)} 条")
            for news in news_list[:3]:  # 只显示前3条
                print(f"  - [{news['id']}] {news['title']} by {news.get('username', 'N/A')}")
            if len(news_list) > 3:
                print(f"  ... 还有 {len(news_list) - 3} 条帖子")
            return True
        except Exception as e:
            print_error(f"获取帖子列表失败: {e}")
            return False
    
    def test_get_news_detail(self, news_id: int):
        """测试获取帖子详情"""
        print_info(f"测试获取帖子详情: ID={news_id}...")
        try:
            response = requests.get(f"{self.base_url}/news/{news_id}", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            news_data = data["data"]
            print_success(f"获取帖子详情成功: {news_data['title']}")
            print(f"  作者: {news_data.get('username', 'N/A')} (ID: {news_data['user_id']})")
            print(f"  内容预览: {news_data['article'][:50]}...")
            return True
        except Exception as e:
            print_error(f"获取帖子详情失败: {e}")
            return False
    
    def test_delete_news(self, news_id: int, should_success: bool = True, use_user2: bool = False):
        """测试删除帖子"""
        print_info(f"测试删除帖子: ID={news_id}...")
        try:
            token = self.user2_token if use_user2 else self.token
            response = requests.delete(
                f"{self.base_url}/news/{news_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5
            )
            
            if should_success:
                assert response.status_code == 200
                data = response.json()
                print_success(f"删除帖子成功 (ID: {data.get('news_id', news_id)})")
                return True
            else:
                assert response.status_code != 200
                print_success(f"预期失败的删除确实失败了 - {response.json().get('detail', '')}")
                return True
        except AssertionError:
            if should_success:
                print_error(f"删除应该成功但失败了: {response.text}")
            else:
                print_error(f"删除应该失败但成功了: {response.text}")
            return False
        except Exception as e:
            print_error(f"删除帖子测试失败: {e}")
            return False
    
    def test_logout(self):
        """测试登出"""
        print_info("测试用户登出...")
        try:
            response = requests.post(
                f"{self.base_url}/logout",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=5
            )
            assert response.status_code == 200
            data = response.json()
            print_success(f"登出成功 (用户ID: {data.get('user_id', 'N/A')})")
            return True
        except Exception as e:
            print_error(f"登出失败: {e}")
            return False
    
    def test_access_after_logout(self):
        """测试登出后访问需要认证的接口"""
        print_info("测试登出后访问需要认证的接口（应该失败）...")
        try:
            response = requests.get(
                f"{self.base_url}/me",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=5
            )
            assert response.status_code == 401
            print_success("登出后正确拒绝了访问")
            return True
        except Exception as e:
            print_error(f"测试失败: {e}")
            return False
    
    def test_unauthorized_access(self):
        """测试未登录访问需要认证的接口"""
        print_info("测试未登录访问需要认证的接口（应该失败）...")
        try:
            response = requests.post(
                f"{self.base_url}/news",
                json={"title": "测试", "article": "测试"},
                timeout=5
            )
            assert response.status_code == 401
            print_success("未登录正确拒绝了访问")
            return True
        except Exception as e:
            print_error(f"测试失败: {e}")
            return False

def run_all_tests():
    """运行所有测试"""
    print_title("=" * 60)
    print_title("🧪 帖子发布系统自动化测试")
    print_title("📦 使用 SQLAlchemy + redis.asyncio")
    print_title("=" * 60)
    print()
    
    tester = PostSystemTester(BASE_URL)
    results = []
    
    # ====== 第一部分：基础功能测试 ======
    print_title("\n【第一部分：基础功能测试】")
    
    # 1. 健康检查
    results.append(("健康检查", tester.test_health_check()))
    if not results[-1][1]:
        print_error("\n⚠️ 服务器未运行，无法继续测试")
        return False
    time.sleep(0.3)
    
    # 2. 未登录访问
    results.append(("未登录访问保护", tester.test_unauthorized_access()))
    time.sleep(0.3)
    
    # ====== 第二部分：用户注册与登录 ======
    print_title("\n【第二部分：用户注册与登录】")
    
    # 3. 用户注册
    results.append(("用户1注册", tester.test_register(
        TEST_USER_1["email"],
        TEST_USER_1["username"], 
        TEST_USER_1["password"]
    )))
    time.sleep(0.3)
    
    results.append(("用户2注册", tester.test_register(
        TEST_USER_2["email"],
        TEST_USER_2["username"], 
        TEST_USER_2["password"]
    )))
    time.sleep(0.3)
    
    # 4. 重复注册（应该失败）
    results.append(("重复注册测试", tester.test_register(
        TEST_USER_1["email"],
        TEST_USER_1["username"], 
        "otherpassword",
        should_success=False
    )))
    time.sleep(0.3)
    
    # 5. 用户登录
    results.append(("用户1登录", tester.test_login(
        TEST_USER_1["email"],
        TEST_USER_1["password"]
    )))
    time.sleep(0.3)
    
    # 6. 错误密码登录（应该失败）
    results.append(("错误密码登录", tester.test_login(
        TEST_USER_1["email"],
        "wrongpassword",
        should_success=False
    )))
    time.sleep(0.3)
    
    # 7. 重新登录获取token（确保有有效token）
    tester.test_login(TEST_USER_1["email"], TEST_USER_1["password"])
    time.sleep(0.3)
    
    # 8. 获取当前用户信息
    results.append(("获取用户信息", tester.test_get_current_user()))
    time.sleep(0.3)
    
    # ====== 第三部分：帖子CRUD操作 ======
    print_title("\n【第三部分：帖子CRUD操作】")
    
    # 9. 发布帖子
    results.append(("发布帖子1", tester.test_create_news(
        "我的第一篇帖子",
        "这是一篇测试帖子的内容。今天天气很好，适合写代码！使用SQLAlchemy让数据库操作更加优雅。"
    )))
    time.sleep(0.3)
    
    results.append(("发布帖子2", tester.test_create_news(
        "FastAPI学习笔记",
        "FastAPI是一个现代、快速的Web框架，用于构建API。它基于Python 3.6+的类型提示，性能非常出色。"
    )))
    time.sleep(0.3)
    
    results.append(("发布帖子3", tester.test_create_news(
        "Redis缓存实践",
        "使用redis.asyncio来缓存JWT token，实现快速的登录状态验证。Redis的高性能特性让系统响应更快。"
    )))
    time.sleep(0.3)
    
    results.append(("发布帖子4", tester.test_create_news(
        "SQLAlchemy 2.0 新特性",
        "SQLAlchemy 2.0带来了许多改进，包括更好的类型提示支持和异步操作支持。"
    )))
    time.sleep(0.3)
    
    # 10. 获取帖子列表
    results.append(("获取帖子列表", tester.test_get_news_list()))
    time.sleep(0.3)
    
    # 11. 分页测试
    results.append(("获取帖子列表-分页", tester.test_get_news_list(page=1, page_size=2)))
    time.sleep(0.3)
    
    # 12. 获取帖子详情
    if tester.news_ids:
        results.append(("获取帖子详情", tester.test_get_news_detail(tester.news_ids[0])))
        time.sleep(0.3)
    
    # ====== 第四部分：权限测试 ======
    print_title("\n【第四部分：权限测试】")
    
    # 13. 用户2登录
    tester.test_login(TEST_USER_2["email"], TEST_USER_2["password"], save_as_user2=True)
    time.sleep(0.3)
    
    # 14. 尝试删除他人帖子（应该失败）
    if tester.news_ids:
        results.append(("删除他人帖子测试", tester.test_delete_news(
            tester.news_ids[0], 
            should_success=False,
            use_user2=True
        )))
        time.sleep(0.3)
    
    # 15. 删除自己的帖子（切回用户1）
    if tester.news_ids and len(tester.news_ids) > 1:
        results.append(("删除自己的帖子", tester.test_delete_news(tester.news_ids[-1])))
        time.sleep(0.3)
    
    # 16. 验证删除后列表变化（软删除，帖子不显示但记录还在）
    results.append(("验证删除后列表", tester.test_get_news_list()))
    time.sleep(0.3)
    
    # ====== 第五部分：登出与会话管理 ======
    print_title("\n【第五部分：登出与会话管理】")
    
    # 17. 用户登出
    results.append(("用户登出", tester.test_logout()))
    time.sleep(0.3)
    
    # 18. 登出后访问
    results.append(("登出后访问测试", tester.test_access_after_logout()))
    time.sleep(0.3)
    
    # ====== 测试结果总结 ======
    print()
    print_title("=" * 60)
    print_title("📊 测试结果总结")
    print_title("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        if result:
            status = f"{Colors.GREEN}✅ 通过{Colors.END}"
        else:
            status = f"{Colors.RED}❌ 失败{Colors.END}"
        print(f"{status} - {name}")
    
    print()
    print_title("-" * 60)
    
    if passed == total:
        print_success(f"🎉 所有测试通过！({passed}/{total})")
        print_success("✨ 系统运行正常，SQLAlchemy + redis.asyncio 集成成功！")
    else:
        failed_count = total - passed
        print_warning(f"⚠️ {failed_count} 个测试失败 ({passed}/{total} 通过)")
        print_info("💡 请检查失败的测试项，确保数据库和Redis连接正常")
    
    print_title("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print()
        print_warning("⚠️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print_error(f"❌ 测试执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)