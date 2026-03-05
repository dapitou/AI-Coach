import os
import re
import sys
import traceback

# 强制设置控制台输出编码为 UTF-8，防止 Windows 下打印特殊字符报错
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

# 获取脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENTRY_FILE = os.path.join(BASE_DIR, 'index.html')
OUTPUT_FILE = os.path.join(BASE_DIR, 'PPT_Packed.html')

def inline_resources():
    print("="*50)
    print(f"工作目录: {BASE_DIR}")
    print(f"入口文件: {ENTRY_FILE}")
    print(f"输出文件: {OUTPUT_FILE}")
    print("="*50)
    
    if not os.path.exists(ENTRY_FILE):
        print(f"❌ 错误: 找不到入口文件 {ENTRY_FILE}")
        return

    try:
        print("1. 读取 HTML 文件...")
        with open(ENTRY_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"   文件大小: {len(content)} 字符")

        # 1. 内联 CSS
        print("2. 处理 CSS 链接...")
        def replace_css(match):
            href = match.group(1)
            if href.startswith('http') or href.startswith('//'):
                return match.group(0)
            
            # 去除 URL 参数 (如 ?v=2.2) 以便找到本地文件
            clean_href = href.split('?')[0]
            full_path = os.path.join(BASE_DIR, clean_href)
            if os.path.exists(full_path):
                print(f"   [CSS] 合并: {href}")
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        return f'<style>\n/* Source: {href} */\n{f.read()}\n</style>'
                except Exception as e:
                    print(f"   [CSS] 读取失败 {href}: {e}")
                    return match.group(0)
            else:
                print(f"   [CSS] ⚠️ 未找到: {full_path}")
            return match.group(0)

        content = re.sub(r'<link rel="stylesheet" href="(.*?)">', replace_css, content)

        # 2. 内联 JS
        print("3. 处理 JS 脚本...")
        script_pattern = re.compile(r'<script([^>]*)src="([^"]+)"([^>]*)>\s*</script>')

        def replace_js(match):
            pre_attrs = match.group(1)
            src = match.group(2)
            post_attrs = match.group(3)

            if src.startswith('http') or src.startswith('//'):
                return match.group(0)

            # 去除 URL 参数 (如 ?v=2.2) 以便找到本地文件
            clean_src = src.split('?')[0]
            full_path = os.path.join(BASE_DIR, clean_src)
            if os.path.exists(full_path):
                print(f"   [JS]  合并: {src}")
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        new_tag = f'<script{pre_attrs}{post_attrs}>'
                        new_tag = re.sub(r'\s+', ' ', new_tag).replace(' >', '>')
                        return f'{new_tag}\n/* Source: {src} */\n{f.read()}\n</script>'
                except Exception as e:
                    print(f"   [JS]  读取失败 {src}: {e}")
                    return match.group(0)
            else:
                print(f"   [JS]  ⚠️ 未找到: {full_path}")
            return match.group(0)

        content = script_pattern.sub(replace_js, content)

        print("4. 写入输出文件...")
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("\n" + "="*50)
        print(f"✅ 打包成功！")
        print(f"文件已保存至: {OUTPUT_FILE}")
        print("="*50)

    except Exception as e:
        print("\n❌ 发生未预期的错误:")
        traceback.print_exc()

if __name__ == '__main__':
    inline_resources()
    input("\n按回车键退出...") # 防止窗口直接关闭
