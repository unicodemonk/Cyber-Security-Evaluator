"""
Cyber Security Evaluator - Green Agent Implementation.

This is the main Green Agent that evaluates Purple Agents on their ability
to detect cybersecurity vulnerabilities across multiple attack types.
Uses the advanced multi-agent framework with production-safe features.
"""

import asyncio
import argparse
import logging
import json
from pathlib import Path
from typing import Any, Dict, Optional, List, Union
from datetime import datetime

import httpx
from fastapi.responses import JSONResponse
from agentbeats.green_executor import GreenAgent
from agentbeats.models import EvalRequest as AgentBeatsEvalRequest
from a2a.server.tasks import TaskUpdater
from a2a.utils import new_agent_text_message
from pydantic import BaseModel, Field

# Import framework components
import sys
sys.path.append(str(Path(__file__).parent.parent))

from framework.ecosystem import UnifiedEcosystem
from framework.base import PurpleAgent, SecurityScenario
from framework.models import Attack, TestResult, DetectionOutcome
from framework.scenarios import PromptInjectionScenario, ComprehensiveSecurityScenario
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
    
    # Dual Evaluation Options
    use_dual_evaluation: bool = Field(default=True, description="Enable dual evaluation (Green + Purple perspectives)")
    generate_reports: bool = Field(default=True, description="Generate comprehensive markdown and JSON reports")
    report_dir: str = Field(default="reports", description="Directory for generated reports")
    report_format: Union[str, List[str]] = Field(default=["markdown", "json"], description="Report formats to generate")
    
    num_boundary_probers: int = Field(default=2, ge=1, le=5)
    num_exploiters: int = Field(default=3, ge=1, le=5)
    num_mutators: int = Field(default=2, ge=1, le=5)
    num_validators: int = Field(default=1, ge=1, le=3)
    random_seed: Optional[int] = None
    
    # MITRE Configuration (from TOML [config.mitre] section)
    mitre: Optional[Dict[str, Any]] = Field(default=None, description="MITRE ATT&CK/ATLAS configuration")


class EvalResponse(BaseModel):
    """Evaluation response to client."""
    status: str
    purple_agent_id: str
    scenario: str
    metrics: Dict[str, Any]  # Changed from Dict[str, float] to support nested dicts
    evasions_found: int
    total_tests: int
    coverage: Optional[Dict[str, Any]] = None
    cost_usd: float = 0.0
    duration_seconds: float
    timestamp: str
    report_files: Optional[Dict[str, Any]] = None  # Add report file paths


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

    def get_name(self) -> str:
        """Get the name of this purple agent."""
        return f"PurpleAgent@{self.endpoint}"

    def reset(self):
        """Reset purple agent state (if supported)."""
        # Most purple agents don't support reset, so this is a no-op
        pass

    def detect(self, attack: Attack) -> TestResult:
        """
        Call purple agent using A2A protocol (synchronous wrapper).

        Args:
            attack: Attack object from framework

        Returns:
            TestResult with detection outcome
        """
        # Run the async detect method in a thread pool to avoid event loop conflicts
        import asyncio
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, self._detect_async(attack))
            return future.result(timeout=self.timeout + 5)

    async def _detect_async(self, attack: Attack) -> TestResult:
        """
        Call purple agent using A2A protocol.

        Args:
            attack: Attack object from framework

        Returns:
            TestResult with detection outcome
        """
        try:
            # Create A2A-formatted detection request
            # Purple agent expects {"command": "...", "parameters": {...}}
            detection_request = {
                "command": str(attack.payload),  # The actual attack payload
                "parameters": {
                    # Include attack metadata in parameters for tracking
                    "attack_id": attack.attack_id,
                    "technique": attack.technique,
                    "scenario": attack.scenario,
                    **attack.metadata  # Spread any additional metadata
                }
            }

            # Wrap in A2A message format
            a2a_message = {
                "kind": "message",
                "role": "user",
                "parts": [{
                    "kind": "text",
                    "text": json.dumps(detection_request)
                }]
            }

            # Send directly using httpx
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.debug(f"Sending A2A message to {self.endpoint}")
                response = await client.post(
                    self.endpoint,
                    json=a2a_message,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Purple agent HTTP {response.status_code}: {response.text[:200]}")
                    raise Exception(f"HTTP Error {response.status_code}: {response.text}")
                
                response_data = response.json()
                
                # Extract text from A2A response
                response_text = ""
                if 'parts' in response_data:
                    for part in response_data.get('parts', []):
                        if isinstance(part, dict) and 'text' in part:
                            response_text = part['text']
                            break
                
                logger.debug(f"Received A2A response: {response_text[:200]}")

            # Try to parse response as JSON
            try:
                result_data = json.loads(response_text)
                
                # Purple agent returns CommandResponse format:
                # {"success": bool, "action_taken": str, "details": {}, "state_changes": {}}
                # We need to interpret this for security testing:
                # - If success=True, the attack was NOT detected (purple agent executed it)
                # - If success=False or error, the attack WAS detected/blocked
                
                success = result_data.get('success', False)
                action_taken = result_data.get('action_taken', '')
                
                # For security evaluation:
                # detected = False means attack succeeded (bad - purple agent is vulnerable)
                # detected = True means attack was blocked (good - purple agent is secure)
                detected = not success  # Inverted logic for security testing
                
                # Higher confidence if we got a clear response
                confidence = 0.9 if 'action_taken' in result_data else 0.5
                
                detection_reason = f"Action: {action_taken}" if action_taken else "No action taken"
                
            except json.JSONDecodeError:
                # If we can't parse the response, assume attack failed (detected)
                detected = True
                confidence = 0.5
                detection_reason = "Unable to parse response - assuming blocked"
                logger.warning(f"Could not parse A2A response as JSON: {response_text[:100]}")

            # Calculate outcome using ground truth (GREEN AGENT'S JOB!)
            from framework.models import calculate_outcome
            outcome = calculate_outcome(attack, detected)

            return TestResult(
                result_id=f"result_{attack.attack_id}",
                attack_id=attack.attack_id,
                purple_agent=self.get_name(),
                detected=detected,
                confidence=confidence,
                detection_reason=detection_reason,
                outcome=outcome,
                timestamp=datetime.now(),
                metadata={
                    "purple_agent_response": response_text,
                    "response_data": result_data if 'result_data' in locals() else None,
                    "action_taken": action_taken if 'action_taken' in locals() else None
                }
            )

        except Exception as e:
            logger.error(f"A2A call failed: {e}")
            # Return error as non-detection
            from framework.models import calculate_outcome
            outcome = calculate_outcome(attack, detected=False)
            return TestResult(
                result_id=f"result_{attack.attack_id}_error",
                attack_id=attack.attack_id,
                purple_agent=self.get_name(),
                detected=False,
                confidence=0.0,
                detection_reason="A2A call failed",
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

    def validate_request(self, req: AgentBeatsEvalRequest) -> tuple[bool, str]:
        """
        Validate the evaluation request.

        Args:
            req: AgentBeats evaluation request

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check that we have a purple_agent participant
            if "purple_agent" not in req.participants:
                return False, "Missing required participant: purple_agent"
            
            return True, ""
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    async def run_eval(self, req: AgentBeatsEvalRequest, updater: TaskUpdater) -> EvalResponse:
        """
        Run evaluation on a Purple Agent.

        This is the main entry point called by the A2A framework.

        Args:
            req: AgentBeats evaluation request with participants and config
            updater: Task updater for progress reporting

        Returns:
            EvalResponse with evaluation results
        """
        start_time = asyncio.get_event_loop().time()

        try:
            # Extract purple agent endpoint from participants
            purple_agent_endpoint = str(req.participants.get("purple_agent", ""))
            purple_agent_id = req.config.get("purple_agent_id", "unknown")
            
            # Parse configuration
            config = EvalConfig(**req.config)
            logger.info(f"Starting evaluation for scenario: {config.scenario}")
            logger.info(f"Purple Agent: {purple_agent_id} at {purple_agent_endpoint}")
            logger.info(f"Sandbox: {'ENABLED ✅' if config.use_sandbox else 'DISABLED ⚠️'}")

            if not config.use_sandbox:
                logger.warning("⚠️  PRODUCTION RISK: Sandbox is disabled!")
                logger.warning("⚠️  Purple agent code will execute without isolation!")

            # Update task status
            await updater.update_status("working", new_agent_text_message("Initializing evaluation framework..."))

            # Load scenario
            scenario = self._load_scenario(config.scenario)

            # Create Purple Agent A2A Proxy (uses AgentBeats SDK)
            purple_agent = PurpleAgentA2AProxy(
                endpoint=purple_agent_endpoint,
                timeout=30.0
            )

            # Initialize evaluation engine (UnifiedEcosystem)
            await updater.update_status("working", new_agent_text_message("Initializing multi-agent framework..."))

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
                    'mitre': config.mitre,  # Pass MITRE configuration to ecosystem
                }
            )

            # Run evaluation
            await updater.update_status("working", new_agent_text_message("Running multi-agent evaluation..."))

            result = engine.evaluate(
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

            # Get evasions
            evasions = result.get_evasions()

            # ============================================================================
            # DUAL EVALUATION INTEGRATION (Green Agent + Purple Agent Perspectives)
            # ============================================================================
            
            dual_result = None
            report_files = {}
            
            # Check if dual evaluation is enabled in config
            use_dual_evaluation = getattr(config, 'use_dual_evaluation', True)
            
            logger.info(f"Dual evaluation enabled: {use_dual_evaluation}")
            logger.debug(f"Evaluation result: {len(result.attacks)} attacks, {len(result.test_results)} test results")
            
            if use_dual_evaluation:
                await updater.update_status("working", new_agent_text_message("Running dual evaluation (Green + Purple perspectives)..."))
                
                try:
                    from framework.scoring import DualScoringEngine
                    from framework.reporting import GreenAgentReporter, PurpleAgentReporter
                    from pathlib import Path
                    
                    logger.info(f"Converting evaluation result: {len(result.attacks)} attacks, {len(result.test_results)} test results")
                    
                    # Convert EvaluationResult to dual evaluation format
                    test_results, attacks = self._convert_to_dual_format(result)
                    logger.debug(f"Conversion complete: {len(attacks)} attacks, {len(test_results)} test results")
                    
                    # Run dual evaluation
                    dual_engine = DualScoringEngine()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    dual_result = dual_engine.evaluate(
                        evaluation_id=f"eval_{purple_agent_id}_{timestamp}",
                        results=test_results,
                        attacks=attacks,
                        purple_agent_name=purple_agent_id,
                        scenario=config.scenario
                    )
                    
                    # Generate reports if enabled
                    generate_reports = getattr(config, 'generate_reports', True)
                    
                    if generate_reports:
                        await updater.update_status("working", new_agent_text_message("Generating comprehensive reports..."))
                        
                        green_reporter = GreenAgentReporter()
                        purple_reporter = PurpleAgentReporter()
                        
                        report_dir = Path(getattr(config, 'report_dir', 'reports'))
                        report_dir.mkdir(exist_ok=True)
                        
                        report_format = getattr(config, 'report_format', ['markdown', 'json'])
                        if isinstance(report_format, str):
                            report_format = [report_format]
                        
                        # Generate markdown reports
                        if 'markdown' in report_format:
                            green_path = report_dir / f"GREEN_AGENT_{purple_agent_id}_{timestamp}.md"
                            purple_path = report_dir / f"PURPLE_AGENT_{purple_agent_id}_{timestamp}.md"
                            
                            green_path.write_text(green_reporter.generate_markdown_report(dual_result))
                            purple_path.write_text(purple_reporter.generate_markdown_report(dual_result))
                            
                            report_files['green_markdown'] = str(green_path)
                            report_files['purple_markdown'] = str(purple_path)
                            
                            logger.info(f"Reports saved: {green_path.name}, {purple_path.name}")
                        
                        # Export JSON
                        if 'json' in report_format:
                            json_exports = dual_engine.export_dual_reports(dual_result, str(report_dir))
                            report_files['json_exports'] = json_exports
                            logger.info(f"JSON exports saved to {report_dir}")
                    
                    logger.info(f"Dual Evaluation Complete:")
                    logger.info(f"  Green Agent Score: {dual_result.green_agent_metrics.competition_score:.1f}/100 ({dual_result.green_agent_metrics.grade})")
                    logger.info(f"  Purple Agent Security: {dual_result.purple_agent_assessment.security_score:.1f}/100 ({dual_result.purple_agent_assessment.risk_level})")
                    logger.info(f"  Vulnerabilities Found: {dual_result.purple_agent_assessment.total_vulnerabilities}")
                    
                except Exception as e:
                    import traceback
                    
                    logger.error(f"Dual evaluation failed (continuing with standard metrics): {e}")
                    logger.error(f"Full traceback:\n{traceback.format_exc()}")
                    dual_result = None

            # Prepare response
            metrics = {
                "f1_score": result.metrics.f1_score,
                "precision": result.metrics.precision,
                "recall": result.metrics.recall,
                "accuracy": result.metrics.accuracy,
                "false_positive_rate": result.metrics.false_positive_rate,
                "false_negative_rate": result.metrics.false_negative_rate,
            }
            
            # Add dual evaluation metrics if available
            if dual_result:
                metrics["green_agent"] = {
                    "competition_score": dual_result.green_agent_metrics.competition_score,
                    "grade": dual_result.green_agent_metrics.grade,
                    "f1_score": dual_result.green_agent_metrics.f1_score,
                    "precision": dual_result.green_agent_metrics.precision,
                    "recall": dual_result.green_agent_metrics.recall
                }
                metrics["purple_agent"] = {
                    "security_score": dual_result.purple_agent_assessment.security_score,
                    "risk_level": dual_result.purple_agent_assessment.risk_level,
                    "vulnerabilities": dual_result.purple_agent_assessment.total_vulnerabilities,
                    "critical_count": dual_result.purple_agent_assessment.critical_count,
                    "high_count": dual_result.purple_agent_assessment.high_count,
                    "medium_count": dual_result.purple_agent_assessment.medium_count,
                    "low_count": dual_result.purple_agent_assessment.low_count
                }
            
            response = EvalResponse(
                status="completed",
                purple_agent_id=purple_agent_id,
                scenario=config.scenario,
                metrics=metrics,
                evasions_found=len(evasions),
                total_tests=result.total_attacks_tested,
                coverage=coverage_report,
                cost_usd=result.total_cost_usd,
                duration_seconds=duration,
                timestamp=datetime.now().isoformat()
            )
            
            # Add report files to response if generated
            if report_files:
                response.report_files = report_files

            # Update task as completed
            completion_msg = f"Evaluation completed. F1: {result.metrics.f1_score:.3f}"
            if dual_result:
                completion_msg += f"\n\n🎯 Green Agent: {dual_result.green_agent_metrics.competition_score:.1f}/100 ({dual_result.green_agent_metrics.grade})"
                completion_msg += f"\n🛡️  Purple Agent: {dual_result.purple_agent_assessment.security_score:.1f}/100 ({dual_result.purple_agent_assessment.risk_level})"
                completion_msg += f"\n⚠️  Vulnerabilities: {dual_result.purple_agent_assessment.total_vulnerabilities}"
                if report_files:
                    completion_msg += f"\n📄 Reports saved to: {report_files.get('green_markdown', 'reports/')}"
            
            result_message = new_agent_text_message(
                f"{completion_msg}\n\n{response.model_dump_json(indent=2)}"
            )
            await updater.complete(result_message)

            logger.info(f"Evaluation completed in {duration:.1f}s")
            logger.info(f"F1: {result.metrics.f1_score:.3f}, "
                       f"Precision: {result.metrics.precision:.3f}, "
                       f"Recall: {result.metrics.recall:.3f}")
            logger.info(f"Evasions found: {len(result.evasions)}")

            return response

        except Exception as e:
            logger.error(f"Evaluation failed: {e}", exc_info=True)
            error_message = new_agent_text_message(f"Error: {str(e)}")
            await updater.failed(error_message)

            # Return error response
            duration = asyncio.get_event_loop().time() - start_time
            return EvalResponse(
                status="failed",
                purple_agent_id=purple_agent_id if 'purple_agent_id' in locals() else "unknown",
                scenario=req.config.get('scenario', 'unknown'),
                metrics={},
                evasions_found=0,
                total_tests=0,
                coverage=None,
                cost_usd=0.0,
                duration_seconds=duration,
                timestamp=datetime.now().isoformat()
            )

    def _convert_to_dual_format(self, result) -> tuple:
        """
        Convert EvaluationResult to dual evaluation format.
        
        Args:
            result: EvaluationResult from ecosystem.evaluate()
            
        Returns:
            Tuple of (test_results, attacks) for dual evaluation
        """
        from scenarios.security.models import (
            DetectionOutcome as SecurityDetectionOutcome, 
            TestResult as SecurityTestResult,
            PurpleAgentResponse
        )
        from framework.models import Attack, Severity, TestOutcome
        
        test_results = []
        attacks_list = []
        
        logger.info(f"Converting evaluation result with {len(result.attacks)} attacks and {len(result.test_results)} test results")
        
        # Convert attacks
        for attack_obj in result.attacks:
            # Determine severity
            severity = Severity.MEDIUM  # Default
            if hasattr(attack_obj, 'severity'):
                if isinstance(attack_obj.severity, Severity):
                    severity = attack_obj.severity
                elif isinstance(attack_obj.severity, str):
                    severity_map = {'critical': Severity.CRITICAL, 'high': Severity.HIGH, 'medium': Severity.MEDIUM, 'low': Severity.LOW}
                    severity = severity_map.get(attack_obj.severity.lower(), Severity.MEDIUM)
            
            attacks_list.append(attack_obj)  # Use attack objects directly
        
        # Convert test results
        for test_result_obj in result.test_results:
            # Map TestOutcome to DetectionOutcome
            outcome_map = {
                TestOutcome.TRUE_POSITIVE: SecurityDetectionOutcome.TRUE_POSITIVE,
                TestOutcome.FALSE_POSITIVE: SecurityDetectionOutcome.FALSE_POSITIVE,
                TestOutcome.TRUE_NEGATIVE: SecurityDetectionOutcome.TRUE_NEGATIVE,
                TestOutcome.FALSE_NEGATIVE: SecurityDetectionOutcome.FALSE_NEGATIVE,
            }
            
            # Get the outcome
            outcome = test_result_obj.outcome
            if outcome not in [SecurityDetectionOutcome.TRUE_POSITIVE, SecurityDetectionOutcome.FALSE_POSITIVE,
                             SecurityDetectionOutcome.TRUE_NEGATIVE, SecurityDetectionOutcome.FALSE_NEGATIVE]:
                # Need to map from TestOutcome to SecurityDetectionOutcome
                outcome = outcome_map.get(outcome, SecurityDetectionOutcome.TRUE_POSITIVE)
            
            # Get the attack_id to link test result to attack object
            attack_id = getattr(test_result_obj, 'attack_id', None) or getattr(test_result_obj, 'result_id', f"test_{len(test_results)}")
            
            # Find the corresponding attack to get ground truth (is_malicious)
            attack = next((a for a in attacks_list if a.attack_id == attack_id), None)
            ground_truth = attack.is_malicious if attack else False
            
            # Determine prediction from outcome (how purple agent performed)
            if outcome in [SecurityDetectionOutcome.TRUE_POSITIVE, SecurityDetectionOutcome.FALSE_POSITIVE]:
                predicted = True  # Purple agent detected/blocked it
            else:
                predicted = False  # Purple agent did not detect it
            
            # Extract purple agent response from original TestResult metadata
            original_metadata = getattr(test_result_obj, 'metadata', {}) or {}
            purple_agent_response_text = (
                original_metadata.get('purple_agent_response') or
                original_metadata.get('agent_response') or
                original_metadata.get('response') or
                None
            )
            
            # Create PurpleAgentResponse object if we have response data
            purple_agent_response_obj = None
            if purple_agent_response_text:
                try:
                    # Try to parse as JSON if it's a string
                    if isinstance(purple_agent_response_text, str):
                        import json
                        try:
                            response_data = json.loads(purple_agent_response_text)
                            purple_agent_response_obj = PurpleAgentResponse(
                                success=response_data.get('success', False),
                                action_taken=response_data.get('action_taken', ''),
                                details=response_data.get('details', {}),
                                state_changes=response_data.get('state_changes', {}),
                                metadata=response_data.get('metadata', {})
                            )
                        except (json.JSONDecodeError, TypeError):
                            # If not JSON, create a simple response object
                            purple_agent_response_obj = PurpleAgentResponse(
                                success=False,
                                action_taken=purple_agent_response_text[:200],  # Truncate long responses
                                details={'raw_response': purple_agent_response_text},
                                state_changes={},
                                metadata={}
                            )
                    elif isinstance(purple_agent_response_text, dict):
                        # Already a dict, create PurpleAgentResponse directly
                        purple_agent_response_obj = PurpleAgentResponse(
                            success=purple_agent_response_text.get('success', False),
                            action_taken=purple_agent_response_text.get('action_taken', ''),
                            details=purple_agent_response_text.get('details', {}),
                            state_changes=purple_agent_response_text.get('state_changes', {}),
                            metadata=purple_agent_response_text.get('metadata', {})
                        )
                except Exception as e:
                    logger.warning(f"Could not create PurpleAgentResponse object: {e}")
                    purple_agent_response_obj = None
            
            test_result = SecurityTestResult(
                test_case_id=attack_id,  # Use attack_id so DualScoringEngine can match
                ground_truth=ground_truth,  # From attack.is_malicious
                predicted=predicted,  # From outcome (purple agent's performance)
                outcome=outcome,
                category=attack_id.split('_')[0] if attack else 'unknown',
                language='python',
                confidence=getattr(test_result_obj, 'confidence', 0.5),
                execution_time_ms=getattr(test_result_obj, 'latency_ms', 0),
                purple_agent_response=purple_agent_response_obj
            )
            test_results.append(test_result)
        
        logger.info(f"Converted {len(test_results)} test results and {len(attacks_list)} attacks for dual evaluation")
        
        if not test_results or not attacks_list:
            raise ValueError(f"Insufficient data for dual evaluation: {len(test_results)} results, {len(attacks_list)} attacks")
        
        return test_results, attacks_list

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
            'comprehensive_security': ComprehensiveSecurityScenario,
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
    parser.add_argument(
        '--card-url',
        type=str,
        default=None,
        help='Public URL for agent card (for AgentBeats platform)'
    )
    parser.add_argument(
        '--name-prefix',
        type=str,
        default='',
        help='Prefix for agent name (e.g., "001" for "001_Cyber Security Evaluator")'
    )

    args = parser.parse_args()

    # Build agent name with optional prefix
    base_name = "Cyber Security Evaluator"
    agent_name = f"{args.name_prefix}_{base_name}" if args.name_prefix else base_name
    
    logger.info("=" * 70)
    logger.info(f"{agent_name} - Green Agent")
    logger.info("=" * 70)
    logger.info(f"Host: {args.host}")
    logger.info(f"Port: {args.port}")
    logger.info(f"LLM: {'Enabled' if args.enable_llm else 'Disabled'}")
    if args.name_prefix:
        logger.info(f"Name Prefix: {args.name_prefix}")
    logger.info("=" * 70)

    # Create agent
    agent = CyberSecurityEvaluator(enable_llm=args.enable_llm)

    # Create executor
    executor = GreenExecutor(agent)

    # Create agent card
    # Use provided card-url if available, otherwise construct from host:port
    card_url = args.card_url if args.card_url else f"http://{args.host}:{args.port}/"
    agent_card = cybersecurity_agent_card(
        agent_name=agent_name,
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

    # Add GET handler for root path (Launcher URL support)
    @app.route("/", methods=["GET"])
    async def launcher_health(request):
        return JSONResponse({
            "status": "online",
            "launcher": "ready",
            "agent": {
                "name": agent_card.name,
                "url": agent_card.url,
                "card_url": f"{agent_card.url}/.well-known/agent-card.json"
            }
        })

    # Add /status endpoint for AgentBeats launcher validation
    @app.route("/status", methods=["GET"])
    async def launcher_status(request):
        return JSONResponse({
            "status": "server up, with agent running",
            "version": "1",
            "agent": agent_card.name,
            "description": "Green Agent launcher is ready"
        })

    # Add /reset endpoint for AgentBeats battle reset
    @app.route("/reset", methods=["POST"])
    async def reset_agent_endpoint(request):
        """Reset agent state between battles."""
        try:
            # Reset the Green Agent if it has a reset method
            if hasattr(agent, 'reset'):
                agent.reset()

            logger.info("Agent reset successful")
            return JSONResponse({
                "status": "success",
                "message": "Agent has been reset",
                "agent": agent_card.name
            })
        except Exception as e:
            logger.error(f"Reset failed: {e}")
            return JSONResponse({
                "status": "error",
                "message": f"Reset failed: {str(e)}",
                "agent": agent_card.name
            }, status_code=500)

    uvicorn_config = uvicorn.Config(app, host=args.host, port=args.port)
    uvicorn_server = uvicorn.Server(uvicorn_config)
    await uvicorn_server.serve()


if __name__ == "__main__":
    asyncio.run(main())
