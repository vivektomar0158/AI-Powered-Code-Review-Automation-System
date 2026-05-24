import pytest
from app.agents.style_agent import StyleAgent
from app.agents.base_agent import CodeContext
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_style_agent_analysis():
    agent = StyleAgent()
    context = CodeContext(
        pr_number=1,
        repository="owner/repo",
        diff_content="def myFunc():\n  pass",
        files_changed=1
    )
    
    mock_response = {
        "issues": [
            {
                "file_path": "main.py",
                "line_number": 1,
                "severity": "suggestion",
                "message": "Use snake_case for function names.",
                "suggestion": "def my_func():",
                "confidence_score": 0.9
            }
        ]
    }
    
    with patch('app.services.llm_client.LLMClient.analyze_code', new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = mock_response
        issues = await agent.analyze(context)
        
        assert len(issues) == 1
        assert issues[0].severity == "suggestion"
        assert issues[0].message == "Use snake_case for function names."
