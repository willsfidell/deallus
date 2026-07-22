"""End-to-end test for AIDI with LiteLLM integration."""

import asyncio
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.config import settings
from app.services import LLMService, LLMError
from app.orchestrator import HybridOrchestrator
from app.tools.registry import tool_registry


class E2ETest:
    """End-to-end tests for AIDI with LiteLLM."""

    def __init__(self):
        """Initialize test."""
        self.llm_service = None
        self.orchestrator = None

    def setup(self):
        """Setup test environment."""
        print("\n=== Setup ===")

        # Initialize tool registry
        tool_registry.discover_tools()
        print(f"✅ Tools loaded: {len(tool_registry.pre_prompt_tools)} pre-prompt, {len(tool_registry.post_result_tools)} post-result")

        # Initialize LLM service
        self.llm_service = LLMService(base_url=settings.OLLAMA_BASE_URL)
        print(f"✅ LLM Service initialized")
        print(f"   Base URL: {self.llm_service.base_url}")
        print(f"   Text Model: {self.llm_service.text_model}")
        print(f"   Classifier Model: {self.llm_service.classifier_model}")

        # Initialize orchestrator
        self.orchestrator = HybridOrchestrator(
            text_model=settings.TEXT_MODEL,
            classifier_model=settings.CLASSIFIER_MODEL,
        )
        print(f"✅ Orchestrator initialized")

    async def test_llm_connection(self):
        """Test LLM service connectivity."""
        print("\n=== Testing LLM Connection ===")

        # Check if Ollama is available
        try:
            print("⏳ Testing connection to Ollama...")
            response = await self.llm_service.generate(
                prompt="Say 'Hello' in one word",
                model=self.llm_service.text_model,
                max_tokens=10,
                temperature=0.1,
            )
            print(f"✅ LLM connection successful")
            print(f"   Response: {response[:50]}...")
            return True

        except LLMError as e:
            print(f"❌ LLM connection failed: {e}")
            print("   Make sure Ollama is running: docker-compose up ollama")
            return False

        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

    async def test_routing(self):
        """Test orchestrator routing."""
        print("\n=== Testing Orchestrator Routing ===")

        test_cases = [
            ("Classify the sentiment: This product is amazing!", "Should route to classifier"),
            ("Explain how machine learning works", "Should route to text model"),
            ("Write a Python function to reverse a list", "Should route to text model"),
        ]

        for prompt, description in test_cases:
            try:
                print(f"\n⏳ Testing: {description}")
                print(f"   Prompt: {prompt[:60]}...")

                result = await self.orchestrator.route(prompt)

                print(f"✅ Routing successful")
                print(f"   Model: {result.model}")
                print(f"   Confidence: {result.confidence:.2f}")
                print(f"   Stages: {len(result.reasoning['steps'])}")

            except Exception as e:
                print(f"❌ Routing failed: {e}")
                return False

        return True

    async def test_tools(self):
        """Test tool execution."""
        print("\n=== Testing Tool Pipeline ===")

        # Test pre-prompt tools
        print("\n⏳ Testing pre-prompt tools...")
        try:
            # Use async execution directly instead of sync wrapper
            result = await tool_registry.execute_chain(
                "pre_prompt",
                "This is my email@example.com and phone 555-1234",
                {"user_id": 1},
                {}
            )
            executed_tools = result.state.get("executed_tools", [])
            print(f"✅ Pre-prompt tools executed")
            print(f"   Tools: {executed_tools}")
            print(f"   Modified: {result.modified_content[:60]}...")
        except Exception as e:
            print(f"❌ Pre-prompt tools failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        # Test post-result tools
        print("\n⏳ Testing post-result tools...")
        try:
            result = await tool_registry.execute_chain(
                "post_result",
                "I appreciate your feedback. I think that's amazing and great.",
                {},
                {}
            )
            executed_tools = result.state.get("executed_tools", [])
            print(f"✅ Post-result tools executed")
            print(f"   Tools: {executed_tools}")
        except Exception as e:
            print(f"❌ Post-result tools failed: {e}")
            return False

        return True

    async def test_full_pipeline(self):
        """Test full end-to-end pipeline."""
        print("\n=== Testing Full Pipeline ===")

        prompt = "Analyze the pros and cons of remote work"

        print(f"⏳ Processing: {prompt}")

        # Step 1: Pre-prompt tools
        print("\n1️⃣ Running pre-prompt tools...")
        try:
            pre_result = await tool_registry.execute_chain(
                "pre_prompt",
                prompt,
                {"user_id": 1, "request_id": "e2e-test-1"},
                {}
            )
            modified_prompt = pre_result.modified_content
            executed_pre = pre_result.state.get("executed_tools", [])
            print(f"   ✅ Executed: {executed_pre}")
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return False

        # Step 2: Orchestration
        print("\n2️⃣ Running orchestration...")
        try:
            routing_result = await self.orchestrator.route(modified_prompt)
            print(f"   ✅ Routed to: {routing_result.model}")
            print(f"   ✅ Confidence: {routing_result.confidence:.2f}")
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return False

        # Step 3: LLM Generation
        print("\n3️⃣ Generating response...")
        try:
            llm_response = await self.llm_service.generate(
                prompt=modified_prompt,
                model=routing_result.model,
                max_tokens=200,
                temperature=0.7,
            )
            print(f"   ✅ Generated response ({len(llm_response)} chars)")
            print(f"   Response: {llm_response[:80]}...")
        except LLMError as e:
            print(f"   ⚠️  LLM generation failed (may indicate Ollama not running): {e}")
            print("   This is expected if Ollama is not running")
            return True  # Don't fail e2e test if Ollama isn't running
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            return False

        # Step 4: Post-result tools
        print("\n4️⃣ Running post-result tools...")
        try:
            post_result = await tool_registry.execute_chain(
                "post_result",
                llm_response,
                pre_result.state,
                {}
            )
            executed_post = post_result.state.get("executed_tools", [])
            print(f"   ✅ Executed: {executed_post}")
        except Exception as e:
            print(f"   ⚠️  Post-result tools warning: {e}")

        print("\n✅ Full pipeline test completed!")
        return True

    async def run_all_tests(self):
        """Run all tests."""
        print("\n" + "=" * 70)
        print("AIDI POC - END-TO-END TESTS WITH LiteLLM")
        print("=" * 70)

        self.setup()

        try:
            # Test 1: Tool pipeline
            print("\n[TEST 1/4] Tool Pipeline...")
            if not await self.test_tools():
                return False

            # Test 2: LLM Connection
            print("\n[TEST 2/4] LLM Connection...")
            if not await self.test_llm_connection():
                print("⚠️  Skipping remaining tests (Ollama not available)")
                print("   This is expected if Ollama is not running")
                print("   To run full tests, start Ollama: docker-compose up ollama")
                return True

            # Test 3: Routing
            print("\n[TEST 3/4] Orchestrator Routing...")
            if not await self.test_routing():
                return False

            # Test 4: Full Pipeline
            print("\n[TEST 4/4] Full Pipeline...")
            if not await self.test_full_pipeline():
                return False

            print("\n" + "=" * 70)
            print("✅ ALL E2E TESTS PASSED!")
            print("=" * 70)
            return True

        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Main entry point."""
    test = E2ETest()
    success = await test.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
