ROLE_PROFILES = [
    {
        "position": "后端开发工程师",
        "department": "AI 平台部",
        "major": "计算机科学与技术",
        "skills": "Python、FastAPI、PostgreSQL、Docker、Redis",
        "experience": "参与招聘系统后端开发，负责候选人接口、权限校验和异步任务。",
        "project": "设计基于 FastAPI 和 PostgreSQL 的任务平台，接口平均响应时间降低 35%。",
    },
    {
        "position": "前端开发工程师",
        "department": "用户体验部",
        "major": "软件工程",
        "skills": "React、TypeScript、Next.js、Tailwind CSS、前端测试",
        "experience": "开发候选人管理页面、表格组件和响应式招聘数据看板。",
        "project": "重构前端数据缓存和组件加载逻辑，首屏时间降低 28%。",
    },
    {
        "position": "数据分析师",
        "department": "数据智能部",
        "major": "统计学",
        "skills": "Python、SQL、Tableau、数据分析、A/B 测试",
        "experience": "维护经营分析看板，完成渠道转化和招聘漏斗分析。",
        "project": "定位面试反馈环节瓶颈，将平均处理时间缩短 22%。",
    },
    {
        "position": "AI 产品经理",
        "department": "智能产品部",
        "major": "信息管理",
        "skills": "产品设计、LLM、SQL、用户研究、效果评估",
        "experience": "负责 AI 知识库需求分析、原型设计、评测集和效果复盘。",
        "project": "搭建问答产品指标体系，将无答案率从 18% 降低到 9%。",
    },
    {
        "position": "测试开发工程师",
        "department": "工程效能部",
        "major": "网络工程",
        "skills": "Python、Pytest、接口测试、自动化、CI/CD",
        "experience": "负责招聘平台接口自动化、回归测试和质量门禁。",
        "project": "建设核心流程自动化测试，将回归时间由 2 小时缩短至 20 分钟。",
    },
    {
        "position": "算法工程师",
        "department": "算法研发部",
        "major": "人工智能",
        "skills": "Python、PyTorch、机器学习、向量检索、LLM",
        "experience": "参与简历语义检索和候选人岗位匹配模型的训练与评估。",
        "project": "优化向量召回与重排流程，使 Top-10 召回率提升 16%。",
    },
    {
        "position": "招聘运营专员",
        "department": "人力资源部",
        "major": "人力资源管理",
        "skills": "招聘运营、数据录入、企业微信、腾讯文档、流程管理",
        "experience": "维护招聘台账、候选人沟通、面试安排和跨部门催办。",
        "project": "设计招聘数据模板和提醒规则，将人工漏记率降低 40%。",
    },
]


NAMES = [
    "李沐阳", "周清禾", "陈星野", "林知夏", "赵嘉言", "沈言川", "许昭宁", "顾南乔", "陆景明", "苏念安",
    "江予辰", "唐若溪", "宋时雨", "韩清越", "叶书宁", "程屿", "夏知遥", "温以宁", "秦朗", "乔安然",
    "傅云舟", "白芷晴", "谢临川", "罗星澜", "钟亦可", "孟书航", "何嘉树", "梁月白", "杜清和", "潘语桐",
    "魏景行", "余南栀", "姜予墨", "邵明轩", "袁可欣", "彭思远", "曹若岚", "蒋嘉禾", "范知行", "田雨眠",
    "金泽宇", "石晚晴", "廖星河", "邱以安", "任书瑶", "武承泽", "戴清妍", "贺云舒", "雷子昂", "郝嘉宁",
]

SCHOOLS = ["华东示例大学", "南方示例大学", "北方示例财经大学", "东部示例理工大学", "西部示例大学", "中部示例科技大学", "滨海示例大学"]


def build_demo_candidates() -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    legacy_roles = [0, 3, 2, 1, 4]
    legacy_slugs = [
        "li-muyang-backend",
        "zhou-qinghe-ai-pm",
        "chen-xingye-data",
        "lin-zhixia-frontend",
        "zhao-jiayan-qa",
    ]
    legacy_emails = [
        "demo.li@example.com",
        "demo.zhou@example.com",
        "demo.chen@example.com",
        "demo.lin@example.com",
        "demo.zhao@example.com",
    ]
    for index, name in enumerate(NAMES):
        target_index = legacy_roles[index] if index < len(legacy_roles) else index % len(ROLE_PROFILES)
        target = ROLE_PROFILES[target_index]
        # 约 60% 完全匹配、20% 相邻技能、20% 明显不匹配，用于展示二筛区分度。
        profile_match = "matched" if index % 5 < 3 else ("adjacent" if index % 5 == 3 else "mismatched")
        skill_offset = 0 if profile_match == "matched" else (1 if profile_match == "adjacent" else 3)
        evidence = ROLE_PROFILES[(target_index + skill_offset) % len(ROLE_PROFILES)]
        phone = f"199000000{index + 1:02d}" if index < 5 else f"199100000{index + 1:02d}"
        candidates.append(
            {
                "slug": legacy_slugs[index] if index < 5 else f"candidate-{index + 1:03d}",
                "name": name,
                "phone": phone,
                "email": legacy_emails[index] if index < 5 else f"demo.candidate{index + 1:03d}@example.com",
                "position": target["position"],
                "department": target["department"],
                "profile_match": profile_match,
                "school": SCHOOLS[index % len(SCHOOLS)],
                "degree": "硕士" if index % 6 == 0 else "本科",
                "major": evidence["major"],
                "graduation": f"{2024 + index % 3}-06",
                "skills": evidence["skills"],
                "experience": f"在虚构演示团队中{evidence['experience']}",
                "project": evidence["project"],
            }
        )
    return candidates


CANDIDATES = build_demo_candidates()


def _criterion(identifier: str, description: str, weight: int) -> dict:
    return {"id": identifier, "description": description, "weight": weight}


DEMO_JDS = [
    ("BE-2026-001", "后端开发工程师", "AI 平台部", [_criterion("python", "掌握 Python", 25), _criterion("api", "具有 FastAPI 或 Web API 开发经验", 25), _criterion("database", "熟悉 PostgreSQL 或 MySQL", 20)], [_criterion("docker", "有 Docker 使用经验", 10)]),
    ("FE-2026-001", "前端开发工程师", "用户体验部", [_criterion("react", "掌握 React", 25), _criterion("typescript", "掌握 TypeScript", 25), _criterion("web", "具有前端项目经验", 20)], [_criterion("nextjs", "有 Next.js 使用经验", 10)]),
    ("DATA-2026-001", "数据分析师", "数据智能部", [_criterion("sql", "掌握 SQL", 25), _criterion("analysis", "具有数据分析项目经验", 25), _criterion("python", "能够使用 Python 分析数据", 20)], [_criterion("bi", "熟悉 Tableau 或 BI 看板", 10)]),
    ("AIPM-2026-001", "AI 产品经理", "智能产品部", [_criterion("product", "具有产品设计经验", 25), _criterion("llm", "理解 LLM 产品能力", 25), _criterion("research", "具有用户研究或效果评估经验", 20)], [_criterion("sql", "能够使用 SQL", 10)]),
    ("QA-2026-001", "测试开发工程师", "工程效能部", [_criterion("automation", "具有自动化测试经验", 25), _criterion("python", "掌握 Python", 25), _criterion("api_test", "具有接口测试经验", 20)], [_criterion("cicd", "熟悉 CI/CD", 10)]),
    ("ML-2026-001", "算法工程师", "算法研发部", [_criterion("python", "掌握 Python", 20), _criterion("ml", "掌握机器学习基础", 25), _criterion("pytorch", "具有 PyTorch 项目经验", 20)], [_criterion("llm", "具有 LLM 或向量检索经验", 15)]),
    ("TAOPS-2026-001", "招聘运营专员", "人力资源部", [_criterion("recruiting", "具有招聘运营经验", 25), _criterion("wecom", "熟悉企业微信协作", 20), _criterion("docs", "熟悉在线文档和数据台账", 20)], [_criterion("process", "具有流程优化经验", 15)]),
]

JOB_CONTEXT = {
    "BE-2026-001": {
        "summary": "负责招聘智能化平台核心服务，围绕候选人数据、Agent 工作流和第三方协作系统建设稳定、可审计的后端能力。",
        "responsibilities": ["设计候选人、JD 与二筛流程的领域模型和 API", "建设异步任务、事件审计及企业协作系统集成", "通过监控、测试和性能分析保障服务稳定性"],
        "location": "上海 / 杭州",
        "employment_type": "全职 · 社会招聘",
        "minimum_years": 2,
        "domains": ["Web 后端", "分布式系统", "AI 应用工程"],
    },
    "FE-2026-001": {
        "summary": "负责招聘工作台、数据看板和 AI 二筛交互，面向高频业务操作打造清晰、高效且可访问的 Web 体验。",
        "responsibilities": ["使用 React 与 TypeScript 交付复杂业务页面", "建设可复用表格、表单和数据可视化组件", "与产品及后端共同定义接口和体验指标"],
        "location": "深圳 / 上海",
        "employment_type": "全职 · 社会招聘",
        "minimum_years": 2,
        "domains": ["企业级 Web", "数据可视化", "前端工程化"],
    },
    "DATA-2026-001": {
        "summary": "搭建招聘漏斗指标体系，识别渠道、筛选和面试环节的效率瓶颈，为 HR 与用人部门提供可执行洞察。",
        "responsibilities": ["定义招聘核心指标及统一口径", "使用 SQL 与 Python 完成专题分析和实验评估", "建设自助看板并推动分析结论落地"],
        "location": "北京 / 上海",
        "employment_type": "全职 · 校园/社会招聘",
        "minimum_years": 1,
        "domains": ["经营分析", "增长分析", "人效分析"],
    },
    "AIPM-2026-001": {
        "summary": "负责招聘 AI Agent 从需求洞察、方案设计、评测到上线迭代的完整链路，兼顾业务价值、模型效果和安全边界。",
        "responsibilities": ["调研 HR 与用人部门工作流并定义产品路线", "设计 Prompt、评测集和人机协同机制", "结合数据与用户反馈持续优化模型效果"],
        "location": "北京 / 深圳",
        "employment_type": "全职 · 社会招聘",
        "minimum_years": 2,
        "domains": ["AI 产品", "企业服务", "LLM 应用"],
    },
    "QA-2026-001": {
        "summary": "负责招聘平台质量保障和测试效能建设，覆盖 API、Web、AI 输出约束及关键业务链路。",
        "responsibilities": ["制定关键招聘流程的测试策略", "建设接口与端到端自动化测试", "建立发布门禁、缺陷分析和质量度量"],
        "location": "杭州 / 深圳",
        "employment_type": "全职 · 社会招聘",
        "minimum_years": 2,
        "domains": ["测试开发", "质量平台", "CI/CD"],
    },
    "ML-2026-001": {
        "summary": "研发简历理解、语义检索和岗位匹配算法，持续提升召回、排序与证据可解释性。",
        "responsibilities": ["构建简历与 JD 的训练及评测数据", "研发向量召回、重排和 LLM 应用方案", "完成模型部署、监控及线上效果迭代"],
        "location": "北京 / 上海",
        "employment_type": "全职 · 校园/社会招聘",
        "minimum_years": 1,
        "domains": ["机器学习", "NLP", "检索与推荐"],
    },
    "TAOPS-2026-001": {
        "summary": "负责招聘项目运营和数据流程治理，连接 HR、面试官与用人部门，提升候选人体验和跨团队交付效率。",
        "responsibilities": ["运营招聘台账、人才池及面试排期", "跟踪漏斗数据并推动异常闭环", "沉淀协作规范、模板和自动化流程"],
        "location": "上海 / 深圳",
        "employment_type": "全职 · 校园/社会招聘",
        "minimum_years": 1,
        "domains": ["招聘运营", "项目协同", "流程优化"],
    },
}


def job_payload(job: tuple) -> dict:
    code, title, department, must_have, nice_to_have = job
    context = JOB_CONTEXT[code]
    return {
        "job_code": code,
        "version": 1,
        "status": "active",
        "created_by": "Department Demo",
        "jd": {
            "title": title,
            "department": department,
            "summary": context["summary"],
            "responsibilities": context["responsibilities"],
            "location": context["location"],
            "employment_type": context["employment_type"],
            "must_have": must_have,
            "nice_to_have": nice_to_have,
            "education": {"minimum_degree": "本科", "preferred_majors": []},
            "experience": {"minimum_years": context["minimum_years"], "relevant_domains": context["domains"]},
            "disqualifiers": [],
            "screening_policy": {"pass_score": 65, "hold_score": 45},
        },
    }
