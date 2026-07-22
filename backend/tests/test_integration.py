"""End-to-end integration tests for AIDI."""

import pytest
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.config import settings
from app.db import SessionLocal, init_db, drop_db
from app.auth import create_user, verify_user_credentials, create_api_key, verify_api_key
from app.orchestrator import HybridOrchestrator
from app.tools.registry import tool_registry

# For testing, use SQLite instead of PostgreSQL
import os
os.environ["DATABASE_URL"] = "sqlite:///test_aidi.db"

# Re-import database module after setting environment variable
import importlib
import app.db
importlib.reload(app.db)

# Update imports
from app.db import SessionLocal, init_db, drop_db


class TestIntegration:
    """Integration tests for AIDI POC."""

    @classmethod
    def setup_class(cls):
        """Setup test database."""
        # Initialize database
        init_db()

    @classmethod
    def teardown_class(cls):
        """Teardown test database."""
        drop_db()

    def test_database_and_auth_flow(self):
        """Test user creation, authentication, and API key generation."""
        db = SessionLocal()
        try:
            # Create user
            user = create_user(
                db=db,
                email="test@example.com",
                username="testuser",
                password="securepassword123",
            )
            assert user is not None
            assert user.email == "test@example.com"
            print("✅ User creation successful")

            # Verify credentials
            verified_user = verify_user_credentials(
                db=db,
                email="test@example.com",
                password="securepassword123",
            )
            assert verified_user is not None
            assert verified_user.id == user.id
            print("✅ User verification successful")

            # Create API key
            result = create_api_key(
                db=db,
                user_id=user.id,
                name="test-key",
            )
            assert result is not None
            full_key, api_key_obj = result
            print(f"✅ API key created: {full_key[:20]}...")

            # Verify API key
            verified_user_from_key = verify_api_key(db=db, api_key=full_key)
            assert verified_user_from_key is not None
            assert verified_user_from_key.id == user.id
            print("✅ API key verification successful")

        finally:
            db.close()

    def test_tool_system_integration(self):
        """Test tool registry and tool chain execution."""
        # Discover tools
        tool_registry.discover_tools()

        # Verify tools loaded
        assert len(tool_registry.pre_prompt_tools) == 3
        assert len(tool_registry.post_result_tools) == 2
        print(f"✅ Tools loaded: {len(tool_registry.pre_prompt_tools)} pre-prompt, {len(tool_registry.post_result_tools)} post-result")

        # Test pre-prompt tools
        result = tool_registry.run_pre_prompt_tools(
            content="Tell me about armadillos",
            state={},
        )
        assert result.content is not None
        assert len(result.executed_tools) > 0
        print(f"✅ Pre-prompt tools executed: {result.executed_tools}")

        # Test post-result tools
        result = tool_registry.run_post_result_tools(
            content="This is a test response.",
            state={},
        )
        assert result.content is not None
        assert len(result.executed_tools) > 0
        print(f"✅ Post-result tools executed: {result.executed_tools}")

    async def test_orchestrator_integration(self):
        """Test orchestrator routing."""
        orchestrator = HybridOrchestrator(
            text_model=settings.TEXT_MODEL,
            classifier_model=settings.CLASSIFIER_MODEL,
        )

        test_cases = [
            ("Classify this sentiment: great product", settings.CLASSIFIER_MODEL),
            ("Explain how neural networks work", settings.TEXT_MODEL),
            ("Write Python code to sort a list", settings.TEXT_MODEL),
        ]

        for prompt, expected_model_contains in test_cases:
            result = await orchestrator.route(prompt)
            assert result.model is not None
            assert result.confidence > 0
            print(f"✅ Orchestrator routed '{prompt[:30]}...' to {result.model}")

    def test_orchestrator_sync(self):
        """Test orchestrator in sync context."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.test_orchestrator_integration())
        finally:
            loop.close()

    def test_full_pipeline(self):
        """Test full pipeline: tools → orchestrator → tools."""
        print("\n=== Testing Full Pipeline ===")

        # Initialize
        tool_registry.discover_tools()
        orchestrator = HybridOrchestrator(
            text_model=settings.TEXT_MODEL,
            classifier_model=settings.CLASSIFIER_MODEL,
        )

        prompt = "Analyze the sentiment of this review: Amazing product!"

        # Step 1: Pre-prompt tools
        pre_result = tool_registry.run_pre_prompt_tools(
            content=prompt,
            state={"user_id": 1, "request_id": "test-123"},
        )
        print(f"  1. Pre-prompt tools: {pre_result.executed_tools}")
        modified_prompt = pre_result.content

        # Step 2: Orchestration
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            orchestration_result = loop.run_until_complete(
                orchestrator.route(modified_prompt)
            )
            print(f"  2. Orchestration: routed to {orchestration_result.model}")
        finally:
            loop.close()

        # Step 3: Simulate LLM response
        llm_response = f"[Mock {orchestration_result.model} response] Positive sentiment detected."

        # Step 4: Post-result tools
        post_result = tool_registry.run_post_result_tools(
            content=llm_response,
            state=pre_result.state,
        )
        print(f"  3. Post-result tools: {post_result.executed_tools}")

        print("\n✅ Full pipeline test passed!")


def run_tests():
    """Run all integration tests."""
    print("\n" + "=" * 70)
    print("AIDI POC - INTEGRATION TESTS")
    print("=" * 70)

    test = TestIntegration()
    test.setup_class()

    try:
        print("\n--- Test 1: Database & Authentication Flow ---")
        test.test_database_and_auth_flow()

        print("\n--- Test 2: Tool System Integration ---")
        test.test_tool_system_integration()

        print("\n--- Test 3: Orchestrator Integration ---")
        test.test_orchestrator_sync()

        print("\n--- Test 4: Full Pipeline ---")
        test.test_full_pipeline()

        print("\n" + "=" * 70)
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("=" * 70)

    finally:
        test.teardown_class()


if __name__ == "__main__":
    run_tests()
