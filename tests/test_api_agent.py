"""
Tests for agent API endpoint.
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.agents.schemas import ChosenPointInfo, IrrigationAgentResult
from app.api.main import app
from app.domain.models import CoefficientSource, ComputationInputs, IrrigationPlan, ProfileInput

client = TestClient(app)

@pytest.fixture
def mock_agent_result():
    return IrrigationAgentResult(
        answer_text="Based on your location, I recommend 25 liters per day.",
        plan=IrrigationPlan(
            date=date(2025, 12, 27),
            mode="farm",
            liters_per_day=25.0,
            liters_per_dunam=5000.0,
            pulses_per_day=1,
            inputs_used=ComputationInputs(kc=0.5, efficiency=0.9, area_m2=5.0, evap_mm=5.0),
            coefficient_value_used=0.5,
            coefficient_source=CoefficientSource(source_type="fao56", source_title="FAO-56"),
            warnings=[]
        ),
        chosen_point=ChosenPointInfo(
            name="Test Station",
            lat=32.0,
            lon=34.8,
            distance_km=0.5,
            date=date(2025, 12, 27),
            evap_mm=5.0
        ),
        inputs_used=ProfileInput(
            mode="farm",
            lat=32.0,
            lon=34.8,
            crop_name="tomato",
            area_dunam=0.005 # 5 m2
        ),
        warnings=[]
    )

def test_agent_run_success(mock_agent_result):
    with patch("app.api.routes.agent.build_agent") as mock_build:
        mock_agent = MagicMock()
        mock_agent.structured_output.return_value = mock_agent_result
        mock_build.return_value = mock_agent

        # Register the router in app/api/main.py (Phase D)
        # Assuming it's there for now.

        payload = {"message": "I have a small tomato farm at 32, 34.8. What is the plan?"}
        response = client.post("/agent/run", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert data["result"]["answer_text"].startswith("Based on your location")

def test_agent_run_rate_limit():
    # We can test rate limiting by calling it many times or mocking check_rate_limit
    with patch("app.api.routes.agent.check_rate_limit", return_value=False):
        payload = {"message": "Hi"}
        response = client.post("/agent/run", json=payload)
        assert response.status_code == 429
        assert response.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"

def test_agent_run_message_too_long():
    payload = {"message": "a" * 5001}
    response = client.post("/agent/run", json=payload)
    assert response.status_code == 422 # Pydantic validation error

@pytest.mark.llm
def test_agent_run_llm_integration():
    # This test is gated and only runs if RUN_LLM_TESTS=1
    import os
    if os.environ.get("RUN_LLM_TESTS") != "1" or not os.environ.get("GOOGLE_API_KEY"):
        pytest.skip("Skipping LLM integration test")

    payload = {
        "message": (
            "lat=32.0 lon=34.8 mode=farm crop_name=tomato area_dunam=5. "
            "Compute today plan."
        )
    }
    response = client.post("/agent/run", json=payload)
    assert response.status_code == 200
    assert "result" in response.json()

