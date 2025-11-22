import os
import time
import requests
import json
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from dotenv import load_dotenv

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
                return f"🎉 签到成功，获得 {data} 积分"
            elif code == 700005 and message == "任务已完成，请勿重复点击":
                # 今日已签到
                return "📅 今日已签到"
            else:
                # 其他情况
                return f"❌ 签到失败，请检查URL。响应: {response_text}"
        except json.JSONDecodeError:
            # 响应不是有效的JSON
            return f"❌ 响应不是有效的JSON格式: {response_text}"
    
    def send_post_request(self, url):
        """发送POST请求并返回响应"""
        try:
            # print(f"📤 发送POST请求到: {url[:100]}...")
            
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
            # print(f"原始URL: {url[:100]}...")  # 只显示前100个字符
            
            try:
                # 更新时间戳
                updated_url = self.update_timestamp_in_url(url)
                updated_urls.append(updated_url)
                # print(f"✅ 时间戳更新成功")
                # print(f"更新后URL: {updated_url[:100]}...")
                
                # 发送POST请求
                result = self.send_post_request(updated_url)
                
                # 添加请求结果到URL信息中
                url_info = {
                    'original_url': url,
                    'updated_url': updated_url,
                    'request_result': result
                }
                updated_urls[-1] = url_info  # 替换为包含请求结果的字典
                
                # 在请求之间添加延迟，避免过于频繁
                if i < len(urls):
                    print("⏳ 等待2秒后处理下一个URL...")
                    time.sleep(2)
                    
            except Exception as e:
                error_message = f"❌ 处理URL时出错: {e}"
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
        
        return updated_urls
    
    def run(self):
        """主运行函数"""
        print("🚀 开始处理环境变量中的多个URL")
        results = self.process_all_urls()
        
        if results:
            print("\n" + "="*60)
            print("🎉 所有URL处理完成!")
            print(f"✅ 成功处理 {len(results)} 个URL")
            
            # 统计成功和失败的请求
            successful_requests = sum(1 for r in results if r['request_result']['success'])
            failed_requests = len(results) - successful_requests
            
            print(f"📊 请求统计: 成功 {successful_requests} 个, 失败 {failed_requests} 个")
            
            # 打印每个URL的详细结果
            print("\n📋 详细结果:")
            for i, result in enumerate(results, 1):
                print(f"\n--- 第 {i} 个URL结果 ---")
                print(f"请求状态: {'成功' if result['request_result']['success'] else '失败'}")
                if result['request_result']['status_code']:
                    print(f"状态码: {result['request_result']['status_code']}")
                print(f"状态信息: {result['request_result']['status_message']}")
            
            # 返回处理结果
            return {
                'results': results,
                'successful_count': successful_requests,
                'failed_count': failed_requests
            }
        else:
            print("❌ 没有找到可处理的URL")
            return None


# 使用示例
if __name__ == "__main__":
    processor = QingLongURLProcessor()
    result = processor.run()
    
    if result:
        print(f"\n🎯 最终统计:")
        print(f"总处理URL数: {len(result['results'])}")
        print(f"成功请求数: {result['successful_count']}")
        print(f"失败请求数: {result['failed_count']}")
        
        # 额外统计签到成功和已签到的数量
        success_count = 0
        already_count = 0
        fail_count = 0
        
        for r in result['results']:
            status_msg = r['request_result'].get('status_message', '')
            if '签到成功' in status_msg:
                success_count += 1
            elif '今日已签到' in status_msg:
                already_count += 1
            else:
                fail_count += 1
        
        print(f"\n📈 签到结果统计:")
        print(f"签到成功: {success_count} 个")
        print(f"今日已签到: {already_count} 个")
        print(f"签到失败: {fail_count} 个")
    else:
        print("❌ 处理失败，没有结果返回")
