from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal, create_all
from app.models import Candidate
from app.services.events import log_event


DEMO_CANDIDATES = [
    ("陈安", "AI 产品经理", "待用人部门二筛", "清河大学", "信息管理", "本科"),
    ("李北", "测试工程师", "二筛通过", "华东理工大学", "软件工程", "本科"),
    ("王辰", "AI 管培生", "待约面试", "南方财经大学", "工商管理", "硕士"),
    ("赵笛", "后端开发工程师", "已约面试", "西湖大学", "计算机科学", "硕士"),
    ("周禾", "AI 产品经理", "面试完成", "北城大学", "人工智能", "硕士"),
    ("吴景", "测试工程师", "待面试反馈", "东岭学院", "自动化", "本科"),
    ("郑澜", "后端开发工程师", "面试通过", "海州大学", "软件工程", "本科"),
    ("孙沐", "AI 管培生", "Offer 待审批", "江南大学", "数据科学", "硕士"),
    ("何宁", "AI 产品经理", "Offer 已发放", "岭南大学", "统计学", "硕士"),
    ("唐青", "测试工程师", "二筛不通过", "示例科技大学", "电子信息", "本科"),
    ("许然", "后端开发工程师", "已入职", "中州大学", "网络工程", "本科"),
    ("罗舒", "AI 管培生", "已放弃", "明德大学", "心理学", "本科"),
]


def seed_demo_data(db: Session) -> int:
    existing = db.scalar(select(Candidate).limit(1))
    if existing:
        return 0
    now = datetime.now(timezone.utc)
    for index, (name, position, stage, school, major, degree) in enumerate(DEMO_CANDIDATES, start=1):
        candidate = Candidate(
            name=name,
            phone=f"1390000{index:04d}",
            email=f"candidate{index}@example.com",
            school=school,
            major=major,
            degree=degree,
            graduation_date="2026-06",
            applied_position=position,
            department="AI 平台部" if "AI" in position else "工程效能部",
            hr_owner="HR Demo",
            current_stage=stage,
            current_status="active",
            ai_summary=f"{name} 是虚构演示候选人，简历摘要由 Demo AI 生成，仅用于流程演示。",
            skills=["Python", "数据分析"] if "AI" in position else ["SQL", "自动化测试", "FastAPI"],
            matching_points=["岗位关键词匹配", "项目经历可追溯到简历文本"],
            risk_points=["需要人工确认业务深度"],
            interview_questions=["请说明一个最能代表你能力的项目。"],
            confidence=0.82,
            created_at=now - timedelta(days=index % 7),
            updated_at=now - timedelta(hours=index * 4),
        )
        db.add(candidate)
        db.flush()
        log_event(db, "demo_candidate_seeded", candidate_id=candidate.id, new_stage=stage, note="Fictional demo data")
    db.commit()
    return len(DEMO_CANDIDATES)


def main() -> None:
    create_all()
    with SessionLocal() as db:
        count = seed_demo_data(db)
    print(f"Seeded {count} demo candidates")


if __name__ == "__main__":
    main()
