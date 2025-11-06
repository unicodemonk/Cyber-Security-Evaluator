"""
SQL Injection Detection Benchmark - Green Agent Implementation.

This is the main Green Agent that evaluates Purple Agents on their ability
to detect SQL injection vulnerabilities in code. Supports both fixed and
adaptive evaluation modes with comprehensive metrics tracking.
"""

import asyncio
import time
import random
import argparse
import logging
from pathlib import Path
from typing import Any

import httpx
from agentbeats.green_executor import GreenAgent
from agentbeats.models import EvalRequest as AgentBeatsEvalRequest
from a2a.server.tasks import TaskUpdater

# Handle both relative and absolute imports
try:
    from .models import (
        EvalRequest,
        EvalResponse,
        CodeSample,
        PurpleAgentResponse,
        TestResult,
        DetectionOutcome,
        EvaluationConfig,
        EvaluationMode,
        AdaptiveConfig,
        AdaptiveEvaluationResult,
        RoundResults,
        TestPhase
    )
    from .dataset_manager import DatasetManager
    from .scoring_engine import ScoringEngine
    from .adaptive_planner import AdaptiveTestPlanner
    from .agent_card import sql_injection_agent_card
except ImportError:
    from models import (
        EvalRequest,
        EvalResponse,
        CodeSample,
        PurpleAgentResponse,
        TestResult,
        DetectionOutcome,
        EvaluationConfig,
        EvaluationMode,
        AdaptiveConfig,
        AdaptiveEvaluationResult,
        RoundResults,
        TestPhase
    )
    from dataset_manager import DatasetManager
    from scoring_engine import ScoringEngine
    from adaptive_planner import AdaptiveTestPlanner
    from agent_card import sql_injection_agent_card


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SQLInjectionJudge(GreenAgent):
    """
    Green Agent for evaluating SQL injection detection capabilities.

    Implements both fixed and adaptive evaluation modes:
    - Fixed mode: Traditional test harness with predetermined test set
    - Adaptive mode: Autonomous decision-making with strategic test allocation
    """

    def __init__(self, dataset_root: str | Path, enable_llm: bool = True):
        """
        Initialize the SQL Injection Judge.

        Args:
            dataset_root: Root directory containing dataset JSON files
            enable_llm: Whether to enable LLM integration (requires API key)
        """
        super().__init__()
        self.dataset_manager = DatasetManager(dataset_root)
        self.scoring_engine = ScoringEngine()
        self.adaptive_planner: AdaptiveTestPlanner | None = None

        # LLM Integration (Optional - for enhanced analysis)
        self.llm_enabled = False
        self.llm_client = None
        self.prompt_manager = None

        if enable_llm:
            try:
                from llm import LLMClient, load_prompt_manager

                # Try to initialize LLM client (requires API key)
                try:
                    self.llm_client = LLMClient()
                    self.prompt_manager = load_prompt_manager()
                    self.llm_enabled = True
                    logger.info("LLM integration enabled (OpenAI)")
                except ValueError as e:
                    # No API key available
                    logger.info("LLM integration disabled (no API key)")
                except Exception as e:
                    logger.warning(f"LLM initialization failed: {e}")

            except ImportError:
                logger.warning("LLM package not available")

        # Load datasets
        logger.info("Loading datasets...")
        metadata = self.dataset_manager.load_datasets()
        logger.info(f"Loaded {metadata.total_samples} samples across {len(metadata.languages)} languages")
        logger.info(f"Categories: {metadata.categories}")
        logger.info(f"Vulnerable: {metadata.total_vulnerable}, Secure: {metadata.total_secure}")

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
        try:
            # Parse configuration
            config = self._parse_config(req.config)
            logger.info(f"Starting evaluation in {config.mode.value} mode")
            logger.info(f"Purple Agent: {req.purple_agent_id} at {req.purple_agent_endpoint}")

            # Set random seed for reproducibility
            if config.random_seed is not None:
                random.seed(config.random_seed)

            # Update task status
            await updater.update(status="running", message="Initializing evaluation...")

            # Run evaluation based on mode
            start_time = time.time()

            if config.mode == EvaluationMode.ADAPTIVE:
                response = await self._run_adaptive_evaluation(
                    req.purple_agent_id,
                    req.purple_agent_endpoint,
                    config,
                    updater
                )
            else:  # FIXED mode
                response = await self._run_fixed_evaluation(
                    req.purple_agent_id,
                    req.purple_agent_endpoint,
                    config,
                    updater
                )

            execution_time = time.time() - start_time
            response.execution_time_seconds = execution_time

            # Final update
            await updater.update(
                status="completed",
                message=f"Evaluation completed: F1={response.metrics.f1_score:.3f}"
            )

            logger.info(f"Evaluation completed in {execution_time:.2f}s")
            logger.info(f"Results: F1={response.metrics.f1_score:.3f}, "
                       f"Precision={response.metrics.precision:.3f}, "
                       f"Recall={response.metrics.recall:.3f}")

            return response

        except Exception as e:
            logger.error(f"Evaluation failed: {e}", exc_info=True)
            await updater.update(status="failed", message=f"Evaluation failed: {str(e)}")
            return EvalResponse(
                success=False,
                error_message=str(e),
                tests_executed=0,
                execution_time_seconds=0.0
            )

    async def _run_fixed_evaluation(
        self,
        purple_agent_id: str,
        purple_agent_endpoint: str,
        config: EvaluationConfig,
        updater: TaskUpdater
    ) -> EvalResponse:
        """
        Run fixed evaluation mode: predetermined test set.

        Args:
            purple_agent_id: ID of purple agent
            purple_agent_endpoint: Endpoint URL
            config: Evaluation configuration
            updater: Task updater

        Returns:
            EvalResponse with results
        """
        # Sample test cases
        test_samples = self.dataset_manager.sample_diverse(
            n=config.test_budget,
            seed=config.random_seed,
            categories=config.categories_to_test,
            languages=config.languages_to_test
        )

        logger.info(f"Selected {len(test_samples)} test cases")

        # Execute tests
        await updater.update(
            status="running",
            message=f"Executing {len(test_samples)} tests in fixed mode..."
        )

        test_results = await self._execute_tests(
            test_samples,
            purple_agent_endpoint,
            config.per_test_timeout_seconds,
            updater
        )

        # Calculate metrics
        overall_metrics = self.scoring_engine.calculate_metrics(test_results)
        category_metrics = self.scoring_engine.calculate_category_metrics(test_results)

        return EvalResponse(
            success=True,
            metrics=overall_metrics,
            category_metrics=category_metrics,
            tests_executed=len(test_results),
            execution_time_seconds=0.0,  # Will be set by caller
            metadata={
                "mode": "fixed",
                "purple_agent_id": purple_agent_id
            }
        )

    async def _run_adaptive_evaluation(
        self,
        purple_agent_id: str,
        purple_agent_endpoint: str,
        config: EvaluationConfig,
        updater: TaskUpdater
    ) -> EvalResponse:
        """
        Run adaptive evaluation mode: autonomous test allocation.

        Args:
            purple_agent_id: ID of purple agent
            purple_agent_endpoint: Endpoint URL
            config: Evaluation configuration
            updater: Task updater

        Returns:
            EvalResponse with adaptive results
        """
        adaptive_cfg = config.adaptive_config
        if adaptive_cfg is None:
            adaptive_cfg = AdaptiveConfig()

        # Initialize adaptive planner
        self.adaptive_planner = AdaptiveTestPlanner(
            weak_threshold=adaptive_cfg.weak_threshold,
            focus_percentage=adaptive_cfg.focus_percentage,
            stability_threshold=adaptive_cfg.stability_threshold,
            min_category_samples=adaptive_cfg.min_category_samples
        )

        all_categories = self.dataset_manager.get_all_categories()
        all_results: list[TestResult] = []
        tested_ids: set[str] = set()
        round_history: list[RoundResults] = []
        previous_metrics = None
        current_phase = TestPhase.EXPLORATION

        # Adaptive testing rounds
        for round_num in range(1, adaptive_cfg.max_rounds + 1):
            # Check budget
            remaining_budget = config.test_budget - len(all_results)
            if remaining_budget <= 0:
                logger.info("Test budget exhausted")
                break

            # Determine batch size
            if round_num == 1:
                batch_size = min(adaptive_cfg.initial_exploration_size, remaining_budget)
            else:
                batch_size = min(remaining_budget // (adaptive_cfg.max_rounds - round_num + 1), remaining_budget)

            logger.info(f"Round {round_num}/{adaptive_cfg.max_rounds}: {current_phase.value} phase, "
                       f"batch_size={batch_size}")

            await updater.update(
                status="running",
                message=f"Round {round_num}: {current_phase.value} phase ({batch_size} tests)..."
            )

            # Analyze performance (if not first round)
            if all_results:
                performance = self.adaptive_planner.analyze_performance(all_results, previous_metrics)

                # Check for early termination
                should_terminate, termination_reason = self.adaptive_planner.should_terminate_early(
                    round_number=round_num,
                    max_rounds=adaptive_cfg.max_rounds,
                    total_tests_executed=len(all_results),
                    test_budget=config.test_budget,
                    performance=performance,
                    previous_performance=None  # Could pass from previous round
                )

                if should_terminate:
                    logger.info(f"Early termination: {termination_reason}")
                    break

                # Decide next phase
                current_phase = self.adaptive_planner.decide_next_phase(
                    current_phase=current_phase,
                    round_number=round_num,
                    performance=performance,
                    total_tests_executed=len(all_results),
                    test_budget=config.test_budget
                )

                # Plan next batch
                test_plan = self.adaptive_planner.decide_next_batch(
                    phase=current_phase,
                    batch_size=batch_size,
                    performance=performance,
                    all_categories=all_categories,
                    tested_ids=tested_ids
                )
            else:
                # First round: exploration
                performance = None
                test_plan = self.adaptive_planner.decide_next_batch(
                    phase=TestPhase.EXPLORATION,
                    batch_size=batch_size,
                    performance=None,
                    all_categories=all_categories,
                    tested_ids=tested_ids
                )

            # Sample tests according to plan
            test_samples = self._sample_according_to_plan(
                test_plan,
                tested_ids,
                config
            )

            # Execute tests
            round_results = await self._execute_tests(
                test_samples,
                purple_agent_endpoint,
                config.per_test_timeout_seconds,
                updater
            )

            # Update tested IDs
            tested_ids.update(r.test_case_id for r in round_results)
            all_results.extend(round_results)

            # Calculate round metrics
            round_metrics = self.scoring_engine.calculate_metrics(round_results)
            round_category_metrics = self.scoring_engine.calculate_category_metrics(round_results)

            # Store round history
            round_history.append(RoundResults(
                round_number=round_num,
                phase=current_phase,
                test_results=round_results,
                metrics=round_metrics,
                category_metrics=round_category_metrics,
                decisions_made=self.adaptive_planner.get_decisions(),
                tests_executed=len(round_results),
                cumulative_tests=len(all_results)
            ))

            previous_metrics = round_metrics

            logger.info(f"Round {round_num} completed: F1={round_metrics.f1_score:.3f}, "
                       f"tests={len(round_results)}, cumulative={len(all_results)}")

        # Calculate final metrics
        final_metrics = self.scoring_engine.calculate_metrics(all_results)
        final_category_metrics = self.scoring_engine.calculate_category_metrics(all_results)

        # Build adaptive results
        adaptive_results = AdaptiveEvaluationResult(
            purple_agent_id=purple_agent_id,
            total_rounds=len(round_history),
            total_tests_executed=len(all_results),
            test_budget=config.test_budget,
            final_metrics=final_metrics,
            final_category_metrics=final_category_metrics,
            round_history=round_history,
            all_decisions=self.adaptive_planner.get_decisions(),
            termination_reason="Completed all rounds" if len(round_history) == adaptive_cfg.max_rounds else "Early termination",
            execution_time_seconds=0.0,  # Will be set by caller
            metadata={
                "mode": "adaptive",
                "phases_used": list(set(rh.phase for rh in round_history))
            }
        )

        return EvalResponse(
            success=True,
            metrics=final_metrics,
            category_metrics=final_category_metrics,
            tests_executed=len(all_results),
            execution_time_seconds=0.0,  # Will be set by caller
            adaptive_results=adaptive_results,
            metadata={
                "mode": "adaptive",
                "purple_agent_id": purple_agent_id,
                "total_rounds": len(round_history)
            }
        )

    def _sample_according_to_plan(
        self,
        test_plan: Any,
        tested_ids: set[str],
        config: EvaluationConfig
    ) -> list[CodeSample]:
        """
        Sample test cases according to the adaptive test plan.

        Args:
            test_plan: TestPlan with allocations
            tested_ids: IDs already tested
            config: Evaluation configuration

        Returns:
            List of code samples to test
        """
        samples = []

        for allocation in test_plan.allocations:
            category_samples = self.dataset_manager.get_samples_by_category(allocation.category)

            # Filter out already tested
            available = [s for s in category_samples if s.id not in tested_ids]

            # Apply language filter if specified
            if config.languages_to_test:
                available = [s for s in available if s.language in config.languages_to_test]

            # Sample requested count
            count = min(allocation.allocated_count, len(available))
            selected = random.sample(available, count) if available else []
            samples.extend(selected)

        return samples

    async def _execute_tests(
        self,
        test_samples: list[CodeSample],
        purple_agent_endpoint: str,
        timeout: float,
        updater: TaskUpdater
    ) -> list[TestResult]:
        """
        Execute tests by calling the Purple Agent.

        Args:
            test_samples: Code samples to test
            purple_agent_endpoint: Purple agent URL
            timeout: Timeout per test
            updater: Task updater

        Returns:
            List of test results
        """
        results = []

        async with httpx.AsyncClient(timeout=timeout) as client:
            for idx, sample in enumerate(test_samples):
                try:
                    # Call purple agent
                    purple_response = await self._call_purple_agent(
                        client,
                        purple_agent_endpoint,
                        sample
                    )

                    # Determine outcome
                    outcome = self._determine_outcome(sample.is_vulnerable, purple_response.is_vulnerable)

                    # Create test result
                    result = TestResult(
                        test_case_id=sample.id,
                        ground_truth=sample.is_vulnerable,
                        predicted=purple_response.is_vulnerable,
                        outcome=outcome,
                        category=sample.category,
                        language=sample.language,
                        confidence=purple_response.confidence,
                        execution_time_ms=purple_response.execution_time_ms,
                        purple_agent_response=purple_response
                    )
                    results.append(result)

                    # Update progress periodically
                    if (idx + 1) % 10 == 0:
                        await updater.update(
                            status="running",
                            message=f"Tested {idx + 1}/{len(test_samples)} samples..."
                        )

                except Exception as e:
                    logger.error(f"Test failed for sample {sample.id}: {e}")
                    # Record as failure (assume false negative for simplicity)
                    result = TestResult(
                        test_case_id=sample.id,
                        ground_truth=sample.is_vulnerable,
                        predicted=False,
                        outcome=DetectionOutcome.FALSE_NEGATIVE if sample.is_vulnerable else DetectionOutcome.TRUE_NEGATIVE,
                        category=sample.category,
                        language=sample.language,
                        confidence=0.0
                    )
                    results.append(result)

        return results

    async def _call_purple_agent(
        self,
        client: httpx.AsyncClient,
        endpoint: str,
        sample: CodeSample
    ) -> PurpleAgentResponse:
        """
        Call the Purple Agent to analyze a code sample.

        Args:
            client: HTTP client
            endpoint: Purple agent endpoint
            sample: Code sample to analyze

        Returns:
            PurpleAgentResponse with detection results
        """
        # Prepare request
        request_data = {
            "test_case_id": sample.id,
            "code": sample.code,
            "language": sample.language,
            "category": sample.category
        }

        # Make HTTP request
        start_time = time.time()
        response = await client.post(endpoint, json=request_data)
        response.raise_for_status()
        execution_time_ms = (time.time() - start_time) * 1000

        # Parse response
        data = response.json()

        return PurpleAgentResponse(
            test_case_id=data.get("test_case_id", sample.id),
            is_vulnerable=data.get("is_vulnerable", False),
            confidence=data.get("confidence", 0.5),
            vulnerability_type=data.get("vulnerability_type"),
            explanation=data.get("explanation"),
            detected_patterns=data.get("detected_patterns", []),
            line_numbers=data.get("line_numbers", []),
            severity=data.get("severity"),
            execution_time_ms=execution_time_ms
        )

    def _determine_outcome(self, ground_truth: bool, predicted: bool) -> DetectionOutcome:
        """
        Determine confusion matrix outcome.

        Args:
            ground_truth: Actual vulnerability status
            predicted: Purple agent's prediction

        Returns:
            DetectionOutcome
        """
        if ground_truth and predicted:
            return DetectionOutcome.TRUE_POSITIVE
        elif not ground_truth and not predicted:
            return DetectionOutcome.TRUE_NEGATIVE
        elif not ground_truth and predicted:
            return DetectionOutcome.FALSE_POSITIVE
        else:  # ground_truth and not predicted
            return DetectionOutcome.FALSE_NEGATIVE

    def _parse_config(self, config_dict: dict[str, Any]) -> EvaluationConfig:
        """
        Parse configuration from request.

        Args:
            config_dict: Configuration dictionary

        Returns:
            EvaluationConfig object
        """
        mode = EvaluationMode(config_dict.get("mode", "fixed"))

        adaptive_config = None
        if mode == EvaluationMode.ADAPTIVE:
            adaptive_config = AdaptiveConfig(
                initial_exploration_size=config_dict.get("adaptive_initial_exploration_size", 20),
                weak_threshold=config_dict.get("adaptive_weak_threshold", 0.6),
                focus_percentage=config_dict.get("adaptive_focus_percentage", 0.6),
                max_rounds=config_dict.get("adaptive_max_rounds", 5),
                stability_threshold=config_dict.get("adaptive_stability_threshold", 0.05),
                min_category_samples=config_dict.get("adaptive_min_category_samples", 5)
            )

        return EvaluationConfig(
            mode=mode,
            test_budget=config_dict.get("test_budget", 100),
            timeout_seconds=config_dict.get("timeout_seconds", 300),
            per_test_timeout_seconds=config_dict.get("per_test_timeout_seconds", 10.0),
            adaptive_config=adaptive_config,
            random_seed=config_dict.get("random_seed"),
            categories_to_test=config_dict.get("categories"),
            languages_to_test=config_dict.get("languages")
        )


async def main():
    """Main entry point for running the Green Agent."""
    import contextlib
    import uvicorn
    from agentbeats.green_executor import GreenExecutor
    from a2a.server.apps import A2AStarletteApplication
    from a2a.server.request_handlers import DefaultRequestHandler
    from a2a.server.tasks import InMemoryTaskStore

    parser = argparse.ArgumentParser(description="SQL Injection Detection Benchmark - Green Agent")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=9010, help="Port to bind to")
    parser.add_argument(
        "--dataset-root",
        default="datasets/sql_injection",
        help="Root directory containing datasets"
    )
    parser.add_argument("--card-url", type=str, help="External URL to provide in the agent card")
    parser.add_argument("--cloudflare-quick-tunnel", action="store_true",
                       help="Use a Cloudflare quick tunnel. Requires cloudflared. This will override --card-url")

    args = parser.parse_args()

    # Handle Cloudflare tunnel or use provided URL
    if args.cloudflare_quick_tunnel:
        from agentbeats.cloudflare import quick_tunnel
        agent_url_cm = quick_tunnel(f"http://{args.host}:{args.port}")
    else:
        agent_url_cm = contextlib.nullcontext(args.card_url or f"http://{args.host}:{args.port}/")

    async with agent_url_cm as agent_url:
        # Initialize judge
        dataset_root = Path(args.dataset_root)
        judge = SQLInjectionJudge(dataset_root)

        # Create executor
        executor = GreenExecutor(judge)

        # Create agent card
        agent_card = sql_injection_agent_card(
            agent_name="sql_injection_judge",
            card_url=agent_url
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

        # Start server
        logger.info(f"Starting SQL Injection Judge on {args.host}:{args.port}")
        logger.info(f"Dataset root: {dataset_root.absolute()}")

        uvicorn_config = uvicorn.Config(server.build(), host=args.host, port=args.port)
        uvicorn_server = uvicorn.Server(uvicorn_config)
        await uvicorn_server.serve()


if __name__ == "__main__":
    asyncio.run(main())
