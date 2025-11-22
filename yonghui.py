import os
import time
import requests
import json
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from dotenv import load_dotenv
from notify import send  # 导入通知功能

# 完整抓包永辉线上超市小程序链接https://api.yonghuivip.com/web/member/task/doTask?xxxx
# 环境变量中yonghui为抓包的链接，如有多个以@分隔

class QingLongURLProcessor:
    def __init__(self):
        load_dotenv()  # 加载.env文件
        self.env_var_name = 'yonghui'
        
        # 请求参数
        self.payload = {
            "taskId": 1206,
            "shopId": "9468",
            "taskCode": "TASK1761895132409vOziLpV"
        }
        
        self.headers = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 15; RMX5080 Build/AP3A.240617.008; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/142.0.7444.21 Mobile Safari/537.36 XWEB/1420005 MMWEBSDK/20250904 MMWEBID/5673 MicroMessenger/8.0.65.2960(0x2800413C) WeChat/arm64 Weixin NetType/5G Language/zh_CN ABI/arm64 miniProgram/wxc9cf7c95499ee604",
            'Accept': "application/json",
            'Accept-Encoding': "gzip, deflate, br, zstd",
            'Content-Type': "application/json",
            'sec-ch-ua-platform': "\"Android\"",
            'x-yh-context': "origin=h5&morse=1",
            'sec-ch-ua': "\"Chromium\";v=\"142\", \"Android WebView\";v=\"142\", \"Not_A Brand\";v=\"99\"",
            'sec-ch-ua-mobile': "?1",
            'x-yh-biz-params': "ncjkdy=,!')&nzggzmdy=(&xdotdy='&gib=-$!0-!,'*_)!''*(__&gvo=+$0'$--*,'+)_*)_'+",
            'origin': "https://m.yonghuivip.com",
            'x-requested-with': "com.tencent.mm",
            'sec-fetch-site': "same-site",
            'sec-fetch-mode': "cors",
            'sec-fetch-dest': "empty",
            'referer': "https://m.yonghuivip.com/",
            'accept-language': "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            'priority': "u=1, i"
        }
        
        # 统计变量
        self.success_count = 0
        self.already_count = 0
        self.fail_count = 0
        self.details = []  # 存储每个URL的详细结果
    
    def get_environment_urls(self):
        """从环境变量获取URL列表"""
        env_value = os.environ.get(self.env_var_name)
        if not env_value:
            print(f"❌ 未找到环境变量 '{self.env_var_name}'")
            return []
        
        # 使用@分割URL
        urls = [url.strip() for url in env_value.split('@') if url.strip()]
        return urls
    
    def update_timestamp_in_url(self, url):
        """更新单个URL的时间戳"""
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        current_timestamp = str(int(time.time() * 1000))
        query_params['timestamp'] = [current_timestamp]
        new_query = urlencode(query_params, doseq=True)
        new_url = urlunparse((
            parsed_url.scheme, parsed_url.netloc, parsed_url.path,
            parsed_url.params, new_query, parsed_url.fragment
        ))
        return new_url
    
    def parse_response(self, response_text):
        """解析响应并返回相应的状态信息"""
        try:
            response_data = json.loads(response_text)
            code = response_data.get('code')
            data = response_data.get('data')
            message = response_data.get('message')
            
            if code == 0:
                # 签到成功
                self.success_count += 1
                return f"🎉 签到成功，获得 {data} 积分"
            elif code == 700005 and message == "任务已完成，请勿重复点击":
                # 今日已签到
                self.already_count += 1
                return "📅 今日已签到"
            else:
                # 其他情况
                self.fail_count += 1
                return f"❌ 签到失败，请检查URL。响应: {response_text}"
        except json.JSONDecodeError:
            # 响应不是有效的JSON
            self.fail_count += 1
            return f"❌ 响应不是有效的JSON格式: {response_text}"
    
    def send_post_request(self, url):
        """发送POST请求并返回响应"""
        try:
            # 发送POST请求
            response = requests.post(
                url, 
                data=json.dumps(self.payload), 
                headers=self.headers,
                timeout=30  # 设置超时时间
            )
            
            print(f"✅ 请求成功，状态码: {response.status_code}")
            
            # 解析响应并打印相应的状态信息
            status_message = self.parse_response(response.text)
            print(f"📄 {status_message}")
            
            return {
                'status_code': response.status_code,
                'response_text': response.text,
                'status_message': status_message,
                'success': True
            }
            
        except requests.exceptions.RequestException as e:
            error_message = f"❌ 请求失败: {e}"
            self.fail_count += 1
            print(error_message)
            return {
                'status_code': None,
                'response_text': str(e),
                'status_message': error_message,
                'success': False
            }
    
    def process_all_urls(self):
        """处理所有URL"""
        urls = self.get_environment_urls()
        if not urls:
            return []
        
        print(f"📋 从环境变量找到 {len(urls)} 个URL")
        
        updated_urls = []
        for i, url in enumerate(urls, 1):
            print(f"\n--- 处理第 {i}/{len(urls)} 个URL ---")
            
            try:
                # 更新时间戳
                updated_url = self.update_timestamp_in_url(url)
                updated_urls.append(updated_url)
                
                # 发送POST请求
                result = self.send_post_request(updated_url)
                
                # 添加请求结果到URL信息中
                url_info = {
                    'original_url': url,
                    'updated_url': updated_url,
                    'request_result': result
                }
                updated_urls[-1] = url_info  # 替换为包含请求结果的字典
                
                # 添加到详细结果中
                self.details.append({
                    'url_index': i,
                    'status': result['status_message'],
                    'success': result['success']
                })
                
                # 在请求之间添加延迟，避免过于频繁
                if i < len(urls):
                    print("⏳ 等待2秒后处理下一个URL...")
                    time.sleep(2)
                    
            except Exception as e:
                error_message = f"❌ 处理URL时出错: {e}"
                self.fail_count += 1
                print(error_message)
                # 即使出错也保留原URL信息
                url_info = {
                    'original_url': url,
                    'updated_url': url,  # 出错时使用原URL
                    'request_result': {
                        'status_code': None,
                        'response_text': str(e),
                        'status_message': error_message,
                        'success': False
                    }
                }
                updated_urls.append(url_info)
                self.details.append({
                    'url_index': i,
                    'status': error_message,
                    'success': False
                })
        
        return updated_urls
    
    def generate_notification_content(self):
        """生成通知内容"""
        total_urls = self.success_count + self.already_count + self.fail_count
        
        content = f"永辉签到任务完成报告\n\n"
        content += f"📊 总体统计:\n"
        content += f"• 总处理账号: {total_urls} 个\n"
        content += f"• 签到成功: {self.success_count} 个\n"
        content += f"• 今日已签到: {self.already_count} 个\n"
        content += f"• 签到失败: {self.fail_count} 个\n\n"
        
        if self.details:
            content += f"📋 详细结果:\n"
            for detail in self.details:
                status_icon = "✅" if "成功" in detail['status'] else "⚠️" if "已签到" in detail['status'] else "❌"
                content += f"• 账号{detail['url_index']}: {status_icon} {detail['status']}\n"
        
        # 添加时间戳
        content += f"\n⏰ 执行时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        return content
    
    def send_notification(self, title, content):
        """发送通知"""
        try:
            send(title, content)
            print("📢 通知发送成功")
        except Exception as e:
            print(f"❌ 通知发送失败: {e}")
    
    def run(self):
        """主运行函数"""
        print("🚀 开始处理环境变量中的多个URL")
        start_time = time.time()
        
        results = self.process_all_urls()
        
        if results:
            print("\n" + "="*60)
            print("🎉 所有URL处理完成!")
            
            # 计算执行时间
            execution_time = time.time() - start_time
            
            # 生成通知内容
            notification_title = f"永辉签到报告 - 成功:{self.success_count} 重复:{self.already_count} 失败:{self.fail_count}"
            notification_content = self.generate_notification_content()
            
            # 发送通知
            self.send_notification(notification_title, notification_content)
            
            # 控制台输出统计信息
            print(f"✅ 成功处理 {len(results)} 个URL")
            print(f"📊 请求统计: 成功 {self.success_count} 个, 重复 {self.already_count} 个, 失败 {self.fail_count} 个")
            print(f"⏱️ 执行时间: {execution_time:.2f} 秒")
            
            # 返回处理结果
            return {
                'results': results,
                'success_count': self.success_count,
                'already_count': self.already_count,
                'fail_count': self.fail_count,
                'execution_time': execution_time
            }
        else:
            error_message = "❌ 没有找到可处理的URL"
            print(error_message)
            # 发送错误通知
            self.send_notification("永辉签到失败", error_message)
            return None


# 使用示例
if __name__ == "__main__":
    processor = QingLongURLProcessor()
    result = processor.run()
    
    if result:
        print(f"\n🎯 最终统计:")
        print(f"总处理URL数: {len(result['results'])}")
        print(f"签到成功: {result['success_count']} 个")
        print(f"今日已签到: {result['already_count']} 个")
        print(f"签到失败: {result['fail_count']} 个")
        print(f"执行时间: {result['execution_time']:.2f} 秒")
    else:
        print("❌ 处理失败，没有结果返回")
