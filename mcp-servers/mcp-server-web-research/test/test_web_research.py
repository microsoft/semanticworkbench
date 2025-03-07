import pytest
from mcp_server_web_research.web_research import perform_web_research


async def test_setup():
    assert True


@pytest.mark.skip
async def test_web_research():
    """
    Test the web research functionality.
    """
    question = "What are the latest trends in AI technology?"

    async def on_status_update(status: str):
        print(f"➡️ {status}", flush=True)

    try:
        result = await perform_web_research(question, on_status_update)
        print(f"✅ {result}")
        return result
    except Exception as e:
        print(f"❌ Error during research: {e}")
        raise
