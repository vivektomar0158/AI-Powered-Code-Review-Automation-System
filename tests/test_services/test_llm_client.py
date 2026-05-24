import pytest
from app.services.llm_client import LLMClient
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_llm_client_fallback():
    client = LLMClient()
    
    with patch.object(client, '_call_gemini', new_callable=AsyncMock) as mock_gemini:
        with patch.object(client, '_call_openrouter', new_callable=AsyncMock) as mock_openrouter:
            
            # Scenario 1: Gemini succeeds
            mock_gemini.return_value = {"success": True}
            result = await client.analyze_code("prompt", "system")
            assert result == {"success": True}
            mock_openrouter.assert_not_called()
            
            # Scenario 2: Gemini fails, OpenRouter succeeds
            mock_gemini.side_effect = Exception("API Error")
            mock_openrouter.return_value = {"success": True, "fallback": True}
            result = await client.analyze_code("prompt", "system")
            assert result == {"success": True, "fallback": True}
            mock_openrouter.assert_called_once()
