"""
Cyber Security Evaluator - Green Agent Implementation.

This is the main Green Agent that evaluates Purple Agents on their ability
to detect cybersecurity vulnerabilities across multiple attack types.
Uses the advanced multi-agent framework with production-safe features.
"""

import asyncio
import argparse
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

import httpx
from agentbeats.green_executor import GreenAgent
from agentbeats.models import EvalRequest as AgentBeatsEvalRequest
from a2a.server.tasks import TaskUpdater
from pydantic import BaseModel, Field

# Import framework components
import sys
sys.path.append(str(Path(__file__).parent.parent))

from framework.ecosystem import UnifiedEcosystem
from framework.base import PurpleAgent, SecurityScenario
from framework.models import Attack, TestResult, DetectionOutcome
from framework.scenarios import PromptInjectionScenario
# TODO: Add more attack-type scenarios as we create them:
# from framework.scenarios import SQLInjectionScenario, CommandInjectionScenario, XSSScenario
from green_agents.agent_card import cybersecurity_agent_card


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class EvalConfig(BaseModel):
    """Configuration for evaluation."""
    scenario: str = Field(default="prompt_injection", description="Attack type to evaluate")
    max_rounds: int = Field(default=10, ge=1, le=100, description="Maximum evaluation rounds")
    budget_usd: float = Field(default=50.0, ge=0, description="Maximum budget in USD")
    use_sandbox: bool = Field(default=True, description="Use container isolation (CRITICAL for production)")
    use_cost_optimization: bool = Field(default=True, description="Enable cost optimization")
    use_coverage_tracking: bool = Field(default=True, description="Enable MITRE ATT&CK tracking")
    num_boundary_probers: int = Field(default=2, ge=1, le=5)
    num_exploiters: int = Field(default=3, ge=1, le=5)
    num_mutators: int = Field(default=2, ge=1, le=5)
    num_validators: int = Field(default=1, ge=1, le=3)
    random_seed: Optional[int] = None


class EvalRequest(BaseModel):
    """Evaluation request from client."""
    purple_agent_id: str
    purple_agent_endpoint: str
    config: Dict[str, Any] = Field(default_factory=dict)


class EvalResponse(BaseModel):
    """Evaluation response to client."""
    status: str
    purple_agent_id: str
    scenario: str
    metrics: Dict[str, float]
    evasions_found: int
    total_tests: int
    coverage: Optional[Dict[str, Any]] = None
    cost_usd: float = 0.0
    duration_seconds: float
    timestamp: str


# ============================================================================
# Purple Agent HTTP Proxy
# ============================================================================

class PurpleAgentA2AProxy(PurpleAgent):
    """
    A2A-compliant proxy for Purple Agents.

    Uses AgentBeats SDK to communicate with Purple Agents following A2A protocol.
    Converts framework's internal Attack objects to A2A messages and back.
    """

    def __init__(self, endpoint: str, timeout: float = 30.0):
        """
        Initialize purple agent proxy.

        Args:
            endpoint: HTTP endpoint of purple agent (e.g., "http://127.0.0.1:8001")
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint.rstrip('/')
        self.timeout = timeout
        logger.info(f"Purple Agent A2A Proxy initialized: {endpoint}")

    async def detect(self, attack: Attack) -> TestResult:
        """
        Call purple agent using A2A protocol.

        Args:
            attack: Attack object from framework

        Returns:
            TestResult with detection outcome
        """
        try:
            # Import A2A SDK helper
            from agentbeats.client import send_message

            # Create A2A-formatted detection request
            detection_request = {
                "attack_id": attack.attack_id,
                "payload": str(attack.payload),
                "technique": attack.technique,
                "scenario": attack.scenario,
                "metadata": attack.metadata
            }

            request_json = json.dumps(detection_request)

            # Use A2A SDK to send message (handles agent card, client creation, etc.)
            logger.debug(f"Sending A2A message to {self.endpoint}")
            response = await send_message(
                message=request_json,
                base_url=self.endpoint,
                streaming=False
            )

            # Parse A2A response
            response_text = response.get('response', '')
            logger.debug(f"Received A2A response: {response_text[:200]}")

            # Try to parse response as JSON
            try:
                result_data = json.loads(response_text)
                detected = result_data.get('detected', False)
                confidence = result_data.get('confidence', 0.5)
                detection_reason = result_data.get('reasons', [])
            except json.JSONDecodeError:
                # Fallback: simple text parsing
                detected = 'detected' in response_text.lower() and 'true' in response_text.lower()
                confidence = 0.5
                detection_reason = ["Unable to parse response"]
                logger.warning(f"Could not parse A2A response as JSON: {response_text[:100]}")

            # Calculate outcome using ground truth (GREEN AGENT'S JOB!)
            from framework.models import calculate_outcome
            outcome = calculate_outcome(attack, detected)

            return TestResult(
                attack=attack,
                detected=detected,
                confidence=confidence,
                outcome=outcome,
                timestamp=datetime.now(),
                metadata={
                    "purple_agent_response": response,
                    "a2a_context_id": response.get('context_id'),
                    "detection_reason": detection_reason
                }
            )

        except Exception as e:
            logger.error(f"A2A call failed: {e}")
            # Return error as non-detection
            from framework.models import calculate_outcome
            outcome = calculate_outcome(attack, detected=False)
            return TestResult(
                attack=attack,
                detected=False,
                confidence=0.0,
                outcome=outcome,
                timestamp=datetime.now(),
                metadata={"error": str(e)}
            )

    async def close(self):
        """Close any resources (A2A SDK handles client lifecycle)."""
        pass


# ============================================================================
# Main Green Agent
# ============================================================================

class CyberSecurityEvaluator(GreenAgent):
    """
    Green Agent for evaluating cybersecurity detection capabilities.

    This agent uses an advanced multi-agent framework with:
    - Coalition-based attack generation
    - Adaptive testing with Thompson Sampling
    - Novelty search for attack evolution
    - Production-safe sandbox isolation
    - MITRE ATT&CK coverage tracking
    - Cost-optimized LLM usage

    Supports multiple attack types:
    - SQL Injection
    - Cross-Site Scripting (XSS)
    - Command Injection
    - Path Traversal
    - Authentication Bypass
    - And more...
    """

    def __init__(self, enable_llm: bool = False):
        """
        Initialize the Cyber Security Evaluator.

        Args:
            enable_llm: Whether to enable LLM integration (requires API key)
        """
        super().__init__()

        # LLM Integration (Optional - for enhanced analysis)
        self.llm_enabled = False
        self.llm_clients = []

        if enable_llm:
            try:
                from llm import LLMClient

                # Try to initialize LLM client (requires API key)
                try:
                    self.llm_clients = [LLMClient()]
                    self.llm_enabled = True
                    logger.info("LLM integration enabled")
                except ValueError:
                    logger.info("LLM integration disabled (no API key)")
                except Exception as e:
                    logger.warning(f"LLM initialization failed: {e}")

            except ImportError:
                logger.warning("LLM package not available")

        logger.info("Cyber Security Evaluator initialized")

    async def run_eval(self, req: EvalRequest, updater: TaskUpdater) -> EvalResponse:
        """
        Run evaluation on a Purple Agent.

        This is the main entry point called by the A2A framework.

        Args:
            req: Evaluation request with purple agent info and config
            updater: Task updater for progress reporting

        Returns:
            EvalResponse with evaluation results
        """
        start_time = asyncio.get_event_loop().time()

        try:
            # Parse configuration
            config = EvalConfig(**req.config)
            logger.info(f"Starting evaluation for scenario: {config.scenario}")
            logger.info(f"Purple Agent: {req.purple_agent_id} at {req.purple_agent_endpoint}")
            logger.info(f"Sandbox: {'ENABLED ✅' if config.use_sandbox else 'DISABLED ⚠️'}")

            if not config.use_sandbox:
                logger.warning("⚠️  PRODUCTION RISK: Sandbox is disabled!")
                logger.warning("⚠️  Purple agent code will execute without isolation!")

            # Update task status
            await updater.update(status="running", message="Initializing evaluation framework...")

            # Load scenario
            scenario = self._load_scenario(config.scenario)

            # Create Purple Agent A2A Proxy (uses AgentBeats SDK)
            purple_agent = PurpleAgentA2AProxy(
                endpoint=req.purple_agent_endpoint,
                timeout=30.0
            )

            # Initialize evaluation engine (UnifiedEcosystem)
            await updater.update(status="running", message="Initializing multi-agent framework...")

            engine = UnifiedEcosystem(
                scenario=scenario,
                use_llm=self.llm_enabled,
                llm_clients=self.llm_clients if self.llm_enabled else None,
                config={
                    'use_sandbox': config.use_sandbox,
                    'sandbox_config': {
                        'image': 'python:3.10-slim',
                        'cpu_limit': 0.5,
                        'memory_limit': '512m',
                        'timeout_seconds': 30,
                        'enable_network': False
                    },
                    'use_cost_optimization': config.use_cost_optimization,
                    'use_coverage_tracking': config.use_coverage_tracking,
                    'num_boundary_probers': config.num_boundary_probers,
                    'num_exploiters': config.num_exploiters,
                    'num_mutators': config.num_mutators,
                    'num_validators': config.num_validators,
                }
            )

            # Run evaluation
            await updater.update(status="running", message="Running multi-agent evaluation...")

            result = await engine.evaluate(
                purple_agent=purple_agent,
                max_rounds=config.max_rounds,
                budget_usd=config.budget_usd
            )

            # Close purple agent connection
            await purple_agent.close()

            # Calculate duration
            duration = asyncio.get_event_loop().time() - start_time

            # Get coverage report (if enabled)
            coverage_report = None
            if config.use_coverage_tracking and engine.coverage_tracker:
                coverage_report = engine.coverage_tracker.get_coverage_report()

            # Prepare response
            response = EvalResponse(
                status="completed",
                purple_agent_id=req.purple_agent_id,
                scenario=config.scenario,
                metrics={
                    "f1_score": result.metrics.f1_score,
                    "precision": result.metrics.precision,
                    "recall": result.metrics.recall,
                    "accuracy": result.metrics.accuracy,
                    "false_positive_rate": result.metrics.false_positive_rate,
                    "false_negative_rate": result.metrics.false_negative_rate,
                },
                evasions_found=len(result.evasions),
                total_tests=result.total_tests,
                coverage=coverage_report,
                cost_usd=result.cost_usd,
                duration_seconds=duration,
                timestamp=datetime.now().isoformat()
            )

            # Update task as completed
            await updater.update(
                status="completed",
                message=f"Evaluation completed. F1: {result.metrics.f1_score:.3f}"
            )

            logger.info(f"Evaluation completed in {duration:.1f}s")
            logger.info(f"F1: {result.metrics.f1_score:.3f}, "
                       f"Precision: {result.metrics.precision:.3f}, "
                       f"Recall: {result.metrics.recall:.3f}")
            logger.info(f"Evasions found: {len(result.evasions)}")

            return response

        except Exception as e:
            logger.error(f"Evaluation failed: {e}", exc_info=True)
            await updater.update(status="failed", message=f"Error: {str(e)}")

            # Return error response
            duration = asyncio.get_event_loop().time() - start_time
            return EvalResponse(
                status="failed",
                purple_agent_id=req.purple_agent_id,
                scenario=req.config.get('scenario', 'unknown'),
                metrics={},
                evasions_found=0,
                total_tests=0,
                coverage=None,
                cost_usd=0.0,
                duration_seconds=duration,
                timestamp=datetime.now().isoformat()
            )

    def _load_scenario(self, scenario_name: str) -> SecurityScenario:
        """
        Load scenario by name.

        Args:
            scenario_name: Name of the scenario (e.g., "prompt_injection")

        Returns:
            SecurityScenario instance
        """
        scenario_map = {
            'prompt_injection': PromptInjectionScenario,
            # TODO: Add more attack-type scenarios as we create them:
            # 'sql_injection': SQLInjectionScenario,
            # 'command_injection': CommandInjectionScenario,
            # 'xss': XSSScenario,
            # 'path_traversal': PathTraversalScenario,
        }

        scenario_class = scenario_map.get(scenario_name.lower())
        if not scenario_class:
            raise ValueError(
                f"Unknown scenario: {scenario_name}. "
                f"Available: {list(scenario_map.keys())}"
            )

        return scenario_class()


# ============================================================================
# CLI Entry Point
# ============================================================================

async def main():
    """Main entry point for running as HTTP server."""
    import uvicorn
    from agentbeats.green_executor import GreenExecutor
    from a2a.server.apps import A2AStarletteApplication
    from a2a.server.request_handlers import DefaultRequestHandler
    from a2a.server.tasks import InMemoryTaskStore

    parser = argparse.ArgumentParser(
        description="Cyber Security Evaluator - Green Agent for security detection evaluation"
    )
    parser.add_argument(
        '--host',
        type=str,
        default='127.0.0.1',
        help='Host to bind to (default: 127.0.0.1)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=9010,
        help='Port to bind to (default: 9010)'
    )
    parser.add_argument(
        '--enable-llm',
        action='store_true',
        help='Enable LLM integration (requires API key)'
    )

    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("Cyber Security Evaluator - Green Agent")
    logger.info("=" * 70)
    logger.info(f"Host: {args.host}")
    logger.info(f"Port: {args.port}")
    logger.info(f"LLM: {'Enabled' if args.enable_llm else 'Disabled'}")
    logger.info("=" * 70)

    # Create agent
    agent = CyberSecurityEvaluator(enable_llm=args.enable_llm)

    # Create executor
    executor = GreenExecutor(agent)

    # Get agent card
    card_url = f"http://{args.host}:{args.port}/"
    agent_card = cybersecurity_agent_card(
        agent_name="Cyber Security Evaluator",
        card_url=card_url
    )

    # Create request handler
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )

    # Create A2A server
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    logger.info(f"\n✅ Agent card: {card_url}.well-known/agent-card.json")
    logger.info(f"✅ JSON-RPC endpoint: {card_url} (POST)")
    logger.info("\nWaiting for evaluation requests...\n")

    # Start server with correct A2A routes
    app = server.build(
        agent_card_url='/.well-known/agent-card.json',
        rpc_url='/'
    )

    uvicorn_config = uvicorn.Config(app, host=args.host, port=args.port)
    uvicorn_server = uvicorn.Server(uvicorn_config)
    await uvicorn_server.serve()


if __name__ == "__main__":
    asyncio.run(main())
