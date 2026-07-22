"""End-to-end integration tests for AIDI (without database dependency)."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.config import settings
from app.orchestrator import HybridOrchestrator
from app.tools.registry import tool_registry


class TestIntegration:
    """Integration tests for AIDI POC."""

    def test_tool_system_integration(self):
        """Test tool registry and tool chain execution."""
        print("\n=== Testing Tool System ===")

        # Discover tools
        tool_registry.discover_tools()

        # Verify tools loaded
        assert len(tool_registry.pre_prompt_tools) == 3, f"Expected 3 pre-prompt tools, got {len(tool_registry.pre_prompt_tools)}"
        assert len(tool_registry.post_result_tools) == 2, f"Expected 2 post-result tools, got {len(tool_registry.post_result_tools)}"
        print(f"✅ Tools loaded: {len(tool_registry.pre_prompt_tools)} pre-prompt, {len(tool_registry.post_result_tools)} post-result")

        # Test pre-prompt tools
        result = tool_registry.run_pre_prompt_tools(
            content="Tell me about armadillos",
            state={},
        )
        assert result.content is not None
        assert len(result.executed_tools) > 0
        print(f"✅ Pre-prompt tools executed: {result.executed_tools}")
        print(f"   Modified content preview: {result.content[:50]}...")

        # Test post-result tools
        result = tool_registry.run_post_result_tools(
            content="This is a test response that contains very generic and repetitive content.",
            state={},
        )
        assert result.content is not None
        assert len(result.executed_tools) > 0
        print(f"✅ Post-result tools executed: {result.executed_tools}")
        print(f"   Response preview: {result.content[:50]}...")

    async def test_orchestrator_integration(self):
        """Test orchestrator routing."""
        print("\n=== Testing Orchestrator ===")

        orchestrator = HybridOrchestrator(
            text_model=settings.TEXT_MODEL,
            classifier_model=settings.CLASSIFIER_MODEL,
        )

        test_cases = [
            "Classify this sentiment: great product",
            "Explain how neural networks work",
            "Write Python code to sort a list",
            "What is the capital of France?",
            "Analyze the pros and cons of remote work",
        ]

        for prompt in test_cases:
            result = await orchestrator.route(prompt)
            assert result.model is not None
            assert result.confidence > 0
            print(f"✅ '{prompt[:40]}...' → {result.model} (confidence: {result.confidence:.2f})")

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
        print("\n1️⃣  Running pre-prompt tools...")
        pre_result = tool_registry.run_pre_prompt_tools(
            content=prompt,
            state={"user_id": 1, "request_id": "test-123"},
        )
        print(f"   Tools executed: {pre_result.executed_tools}")
        modified_prompt = pre_result.content

        # Step 2: Orchestration
        print("2️⃣  Running orchestration...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            orchestration_result = loop.run_until_complete(
                orchestrator.route(modified_prompt)
            )
            print(f"   Routed to: {orchestration_result.model}")
            print(f"   Confidence: {orchestration_result.confidence:.2f}")
            print(f"   Reasoning stages: {len(orchestration_result.reasoning['steps'])}")
        finally:
            loop.close()

        # Step 3: Simulate LLM response
        print("3️⃣  Simulating LLM response...")
        llm_response = f"[Mock {orchestration_result.model} response] Positive sentiment detected in the review."

        # Step 4: Post-result tools
        print("4️⃣  Running post-result tools...")
        post_result = tool_registry.run_post_result_tools(
            content=llm_response,
            state=pre_result.state,
        )
        print(f"   Tools executed: {post_result.executed_tools}")

        print("\n✅ Full pipeline test completed successfully!")

    def run_all_tests(self):
        """Run all integration tests."""
        print("\n" + "=" * 70)
        print("AIDI POC - INTEGRATION TESTS (Phase 2 Complete)")
        print("=" * 70)

        try:
            print("\n--- Test 1: Tool System Integration ---")
            self.test_tool_system_integration()

            print("\n--- Test 2: Orchestrator Integration ---")
            self.test_orchestrator_sync()

            print("\n--- Test 3: Full Pipeline ---")
            self.test_full_pipeline()

            print("\n" + "=" * 70)
            print("✅ ALL INTEGRATION TESTS PASSED!")
            print("=" * 70)
            return True

        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point."""
    test = TestIntegration()
    success = test.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
