import json
import os
import random

# Load curriculum
with open('CV/assets/course/curriculum_data_real.json', 'r', encoding='utf-8') as f:
    curriculum = json.load(f)

courses = curriculum['courses']

# Helper to find course by name keyword
def find_course(keyword):
    for code, data in courses.items():
        if keyword in data['name']:
            return data['name']
    return keyword

# Personas Definitions
personas = {
    "zhang": {
        "name": "Zhang X霸",
        "title": "数据新闻记者 | 融合媒体主编",
        "focus": ["Data", "Writing", "Research"],
        "base_gpa": 3.8
    },
    "li": {
        "name": "Li 导演",
        "title": "视频编导 | 新媒体运营",
        "focus": ["Video", "Visual", "Creative"],
        "base_gpa": 3.2
    },
    "wang": {
        "name": "Wang 逆袭",
        "title": "内容运营实习生",
        "focus": ["Marketing", "Operation"],
        "base_gpa": 2.5 # Starts low, improves
    }
}

# Skill Mappings (Course Keyword -> Skill Name)
skill_map = {
    "摄影": "Photography (DSLR/Mirrorless)",
    "摄像": "Videography",
    "编程": "Python Programming",
    "数据": "Data Analysis (Excel/SPSS)",
    "统计": "Statistics",
    "写作": "News Writing",
    "采访": "Interviewing",
    "剪辑": "Video Editing (Pr/FCP)",
    "设计": "Graphic Design (Ps/Ai)",
    "营销": "Digital Marketing",
    "舆情": "Public Opinion Monitoring"
}

def generate_profile(persona_key, stage):
    p = personas[persona_key]
    
    # Base Structure
    data = {
        "meta": {"layout": "modern", "theme_color": "teal", "font_family": "sans"},
        "profile": {
            "name": p['name'],
            "title": "新闻传播学院学生" if stage == 1 else p['title'],
            "email": f"{persona_key}@stu.edu.cn",
            "phone": "138-xxxx-xxxx",
            "location": "Guangdong, China"
        },
        "education": [{
            "school": "Shantou University",
            "degree": "B.A. Journalism & Communication",
            "time": "2023 - Present",
            "details": []
        }],
        "experience": [],
        "projects": [],
        "skills": {"professional": [], "software": [], "languages": ["Mandarin (Native)", "English (CET-4)"]}
    }
    
    # Stage Logic
    completed_courses = []
    gpa = p['base_gpa']
    
    if stage >= 1: # Year 1-2 (Foundation)
        completed_courses += ["新闻学概论", "摄影基础", "媒体技术基础", "新闻采访写作"]
        if persona_key == "li": completed_courses.append("数字媒体艺术")
        
        data['projects'].append({
            "name": "校园新闻摄影展",
            "role": "摄影师",
            "time": "Year 1",
            "desc": "完成《校园一角》组图拍摄，掌握光圈与快门运用。"
        })
        
    if stage >= 2: # Year 3 (Core & Specialization)
        completed_courses += ["非线性编辑", "传播统计学", "基础编程"]
        gpa += 0.2 if persona_key == "wang" else 0
        
        if "Data" in p['focus']:
            completed_courses.append("新媒体数据分析与应用")
            data['projects'].append({
                "name": "社交媒体舆情分析报告",
                "role": "数据分析师",
                "time": "Year 3",
                "desc": "使用 Python 抓取微博数据，分析热点事件传播路径。"
            })
            data['skills']['software'].append("Python (Pandas)")
            
        if "Video" in p['focus']:
            completed_courses.append("微短剧创作")
            completed_courses.append("纪录片制作")
            data['projects'].append({
                "name": "微纪录片《潮汕非遗》",
                "role": "导演/剪辑",
                "time": "Year 3",
                "desc": "统筹 5 人团队，完成 10 分钟纪录片，获学院奖银奖。"
            })
            data['skills']['software'] += ["Adobe Premiere", "After Effects"]

    if stage >= 3: # Year 4 (Internship & Advanced)
        completed_courses += ["数据新闻", "毕业实习", "媒介法规与伦理"]
        gpa += 0.3 if persona_key == "wang" else 0.1
        
        internship = {
            "company": "某知名互联网大厂" if "Data" in p['focus'] else "某省级电视台",
            "role": "运营实习生" if "Marketing" in p['focus'] else "实习记者/编导",
            "time": "Year 4",
            "details": ["参与核心项目执行", "撰写/制作发布内容 20+ 篇"]
        }
        data['experience'].append(internship)
        data['skills']['languages'].append("English (CET-6)")

    # Update Education Details
    data['education'][0]['details'].append(f"GPA: {min(gpa, 4.0):.2f}/4.0")
    data['education'][0]['details'].append(f"Core Courses: {', '.join(completed_courses[:4])}...")
    
    # Map Skills
    all_skills = set()
    for course in completed_courses:
        for key, skill in skill_map.items():
            if key in course:
                all_skills.add(skill)
    data['skills']['professional'] = list(all_skills)

    return data

# Generate Files
os.makedirs('CV/data/students', exist_ok=True)

for key in personas:
    for stage in [1, 2, 3]:
        data = generate_profile(key, stage)
        filename = f"CV/data/students/config_{key}_v{stage}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Generated {filename}")

print("Mock data generation complete.")
