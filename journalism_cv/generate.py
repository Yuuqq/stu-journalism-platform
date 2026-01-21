import json
import os
import sys

# Try to import jinja2
try:
    from jinja2 import Template
except ImportError:
    print("错误: 未检测到 jinja2 库。")
    print("请运行以下命令安装: pip install jinja2")
    sys.exit(1)

def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def render_cv(config_path, template_path_ignored, output_path):
    # Load data
    if not os.path.exists(config_path):
        print(f"错误: 找不到配置文件 {config_path}")
        return
    
    data = load_config(config_path)
    
    # Determine Layout
    layout = data.get('meta', {}).get('layout', 'modern')
    base_dir = os.path.dirname(config_path)
    
    # Map layout names to filenames
    # Default is template.html (which is modern), but we now have specific files
    template_map = {
        'modern': 'template.html',
        'classic': 'template_classic.html',
        'agency': 'template_agency.html',
        'visual': 'template_visual.html'
    }
    
    template_filename = template_map.get(layout, 'template.html')
    template_path = os.path.join(base_dir, template_filename)

    # Fallback check
    if not os.path.exists(template_path):
        print(f"⚠️ 警告: 找不到布局模板 {template_filename}，尝试使用默认模板。")
        template_path = os.path.join(base_dir, 'template.html')

    if not os.path.exists(template_path):
         print(f"错误: 找不到模板文件 {template_path}")
         return

    print(f"🎨 使用布局: {layout} ({os.path.basename(template_path)})")

    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Render
    template = Template(template_content)
    rendered_html = template.render(**data)
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(rendered_html)
    
    print(f"✅ 简历生成成功: {os.path.basename(output_path)}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Template path arg is now ignored in favor of internal logic, keeping sig for compat if needed or just pass None
    dummy_template = os.path.join(base_dir, 'template.html') 

    # If args provided: python generate.py config.json output.html
    if len(sys.argv) == 3:
        config_file = sys.argv[1]
        output_file = sys.argv[2]
        render_cv(config_file, dummy_template, output_file)
    else:
        # Default behavior: Generate all demos
        demos = [
            ('config_advertising.json', 'cv_advertising.html'),
            ('config_new_media.json', 'cv_new_media.html'),
            ('config_journalism.json', 'cv_journalism.html'),
            ('config_broadcasting.json', 'cv_broadcasting.html'),
            ('config.json', 'my_cv.html')
        ]
        
        print("🚀 开始批量生成简历...")
        for conf, out in demos:
            conf_path = os.path.join(base_dir, conf)
            out_path = os.path.join(base_dir, out)
            if os.path.exists(conf_path):
                render_cv(conf_path, dummy_template, out_path)
            else:
                print(f"⚠️ 跳过: {conf} (文件不存在)")
        
        print("\n👉 请在浏览器中打开生成的 .html 文件，然后使用打印功能 (Ctrl+P) 保存为 PDF。")
        print("💡 提示: 在打印设置中，勾选 '背景图形' (Background graphics) 以确保颜色正确显示。")
