from app.schemas import ParsedResume
from app.services.ai import mock_parse_resume


def test_mock_ai_output_validates_structured_resume() -> None:
    parsed = mock_parse_resume(
        """
        姓名: 林一
        电话: 13800001111
        邮箱: linyi@example.com
        学校: 示例大学
        专业: 计算机科学
        学历: 本科
        应聘岗位: 后端开发工程师
        技能: Python FastAPI SQL
        项目: 招聘数据看板
        """
    )

    validated = ParsedResume.model_validate(parsed.model_dump())

    assert validated.name == "林一"
    assert validated.applied_position == "后端开发工程师"
    assert "Python" in validated.skills
    assert 0 <= validated.confidence <= 1
