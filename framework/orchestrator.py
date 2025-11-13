"""
Meta-Orchestrator - Coordinates agent coalitions and test allocation.

Implements Thompson Sampling for Bayesian test allocation (Enhancement 1)
and manages coalition lifecycle.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime
import logging
import random
from scipy.stats import beta
import numpy as np

from .base import (
    UnifiedAgent, Coalition, CoalitionType, CoalitionGoal, Phase,
    Capability, Task, KnowledgeBase, PurpleAgent, SecurityScenario
)
from .models import Attack, TestResult, EvaluationResult, Metrics, CoverageReport


class ThompsonSamplingAllocator:
    """
    Thompson Sampling for adaptive test allocation.

    Uses Bayesian optimization to allocate tests to techniques/regions
    that are most likely to discover vulnerabilities.
    """

    def __init__(
        self,
        techniques: List[str],
        boundary_bins: int = 10
    ):
        """
        Initialize Thompson Sampling allocator.

        Args:
            techniques: List of attack techniques
            boundary_bins: Number of boundary regions to track
        """
        self.techniques = techniques
        self.boundary_bins = boundary_bins

        # Beta distribution parameters for each (technique, bin) context
        # alpha = successes (evasions found)
        # beta = failures (attacks detected)
        self.posteriors: Dict[Tuple[str, int], Dict[str, float]] = {}

        for tech in techniques:
            for bin_id in range(boundary_bins):
                context = (tech, bin_id)
                self.posteriors[context] = {'alpha': 1.0, 'beta': 1.0}  # Uniform prior

    def select_next_test(self) -> Tuple[str, int]:
        """
        Select next test context using Thompson Sampling.

        Returns:
            Tuple of (technique, boundary_bin)
        """
        max_sample = -1.0
        best_context = None

        # Sample from each context's posterior
        for context, params in self.posteriors.items():
            # Sample success probability from Beta distribution
            theta_sample = beta.rvs(params['alpha'], params['beta'])

            if theta_sample > max_sample:
                max_sample = theta_sample
                best_context = context

        return best_context if best_context else (self.techniques[0], 0)

    def update(self, technique: str, boundary_bin: int, success: bool):
        """
        Update posterior after observing result.

        Args:
            technique: Technique tested
            boundary_bin: Boundary bin tested
            success: True if evasion found, False if detected
        """
        context = (technique, boundary_bin)

        if context in self.posteriors:
            if success:
                self.posteriors[context]['alpha'] += 1.0
            else:
                self.posteriors[context]['beta'] += 1.0

    def get_exploration_stats(self) -> Dict[str, Any]:
        """
        Get exploration statistics.

        Returns:
            Dictionary with stats
        """
        stats = {
            'contexts': len(self.posteriors),
            'total_samples': sum(p['alpha'] + p['beta'] - 2 for p in self.posteriors.values()),
            'by_technique': {}
        }

        for tech in self.techniques:
            tech_contexts = [(t, b) for (t, b) in self.posteriors.keys() if t == tech]
            total_alpha = sum(self.posteriors[c]['alpha'] for c in tech_contexts)
            total_beta = sum(self.posteriors[c]['beta'] for c in tech_contexts)

            stats['by_technique'][tech] = {
                'successes': total_alpha - len(tech_contexts),  # Subtract prior
                'failures': total_beta - len(tech_contexts),
                'success_rate': (total_alpha - len(tech_contexts)) / (total_alpha + total_beta - 2 * len(tech_contexts))
                    if (total_alpha + total_beta - 2 * len(tech_contexts)) > 0 else 0.0
            }

        return stats


class MetaOrchestrator:
    """
    Meta-Orchestrator that coordinates all agents and coalitions.

    Manages:
    - Coalition formation and dissolution
    - Thompson Sampling test allocation
    - Phase transitions
    - Resource management
    - Optional sandbox isolation
    """

    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        scenario: SecurityScenario,
        agents: List[UnifiedAgent],
        use_sandbox: bool = False,
        sandbox_config: Optional[Dict[str, Any]] = None,
        use_cost_optimization: bool = False
    ):
        """
        Initialize meta-orchestrator.

        Args:
            knowledge_base: Shared knowledge base
            scenario: Security scenario
            agents: List of available agents
            use_sandbox: Whether to use sandbox isolation
            sandbox_config: Optional sandbox configuration
            use_cost_optimization: Whether to use budget enforcement
        """
        self.knowledge_base = knowledge_base
        self.scenario = scenario
        self.agents = agents
        self.use_sandbox = use_sandbox
        self.sandbox_config = sandbox_config or {}
        self.use_cost_optimization = use_cost_optimization
        self.logger = logging.getLogger("MetaOrchestrator")

        # Initialize sandbox if enabled
        self.sandbox = None
        if use_sandbox:
            try:
                from .sandbox import FormalSandbox
                self.sandbox = FormalSandbox(
                    image=self.sandbox_config.get('image', 'python:3.10-slim'),
                    cpu_limit=self.sandbox_config.get('cpu_limit', 0.5),
                    memory_limit=self.sandbox_config.get('memory_limit', '512m'),
                    timeout_seconds=self.sandbox_config.get('timeout_seconds', 30),
                    enable_network=self.sandbox_config.get('enable_network', False)
                )
                self.logger.info("Sandbox initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize sandbox: {e}")
                self.logger.warning("Continuing without sandbox (NOT PRODUCTION SAFE)")
                self.use_sandbox = False

        # Initialize budget enforcer if enabled
        self.budget_enforcer = None
        if use_cost_optimization:
            try:
                from .cost_optimizer import BudgetEnforcer
                self.budget_enforcer = BudgetEnforcer()
                self.logger.info("Budget enforcer initialized for cost optimization")
            except Exception as e:
                self.logger.error(f"Failed to initialize budget enforcer: {e}")
                self.use_cost_optimization = False

        # State
        self.current_phase = Phase.EXPLORATION
        self.coalitions: List[Coalition] = []
        self.coalition_counter = 0

        # Thompson Sampling allocator
        techniques = scenario.get_techniques()
        self.allocator = ThompsonSamplingAllocator(techniques)

        # Metrics
        self.phase_history: List[Dict[str, Any]] = []
        self.coalition_history: List[Dict[str, Any]] = []

    def _wrap_purple_agent(self, purple_agent: PurpleAgent) -> PurpleAgent:
        """
        Wrap purple agent in sandbox if enabled.

        Args:
            purple_agent: Original purple agent

        Returns:
            Sandboxed or original purple agent
        """
        if self.use_sandbox and self.sandbox:
            try:
                from .sandbox import SandboxedPurpleAgent
                wrapped = SandboxedPurpleAgent(purple_agent, self.sandbox)
                self.logger.info(f"Wrapped {purple_agent.get_name()} in sandbox")
                return wrapped
            except Exception as e:
                self.logger.error(f"Failed to wrap purple agent in sandbox: {e}")
                self.logger.warning("Using unwrapped purple agent (NOT PRODUCTION SAFE)")
                return purple_agent
        return purple_agent

    def orchestrate_evaluation(
        self,
        purple_agent: PurpleAgent,
        max_rounds: int = 10,
        budget_usd: Optional[float] = None
    ) -> EvaluationResult:
        """
        Orchestrate complete evaluation.

        Args:
            purple_agent: Purple agent to evaluate
            max_rounds: Maximum number of rounds
            budget_usd: Optional cost budget

        Returns:
            Evaluation result
        """
        self.logger.info(f"Starting evaluation of {purple_agent.get_name()}")

        # Wrap purple agent in sandbox if enabled
        purple_agent = self._wrap_purple_agent(purple_agent)

        # Initialize budget enforcer if enabled and budget provided
        if self.budget_enforcer and budget_usd:
            self.budget_enforcer.set_budget(budget_usd)
            self.logger.info(f"Budget enforcer configured with ${budget_usd:.2f}")

        # Initialize evaluation result
        eval_result = EvaluationResult(
            evaluation_id=f"eval_{purple_agent.get_name()}_{datetime.now().timestamp()}",
            purple_agent=purple_agent.get_name(),
            scenario=self.scenario.get_name(),
            start_time=datetime.now()
        )

        # Track costs
        total_cost = 0.0

        # Execute evaluation rounds
        for round_num in range(max_rounds):
            self.logger.info(f"=== Round {round_num + 1}/{max_rounds} ===")

            # Check budget (basic or enforcer)
            if self.budget_enforcer and budget_usd:
                # Use budget enforcer for phase-based checking
                if not self.budget_enforcer.can_afford(self.current_phase, 0.05):  # Estimate round cost
                    self.logger.info(f"Phase budget exhausted for {self.current_phase.name}")
                    # Try to advance phase
                    if self.current_phase == Phase.EXPLORATION:
                        self.current_phase = Phase.EXPLOITATION
                        self.logger.info("Advanced to EXPLOITATION phase")
                    elif self.current_phase == Phase.EXPLOITATION:
                        self.current_phase = Phase.VALIDATION
                        self.logger.info("Advanced to VALIDATION phase")
                    else:
                        self.logger.info("All phase budgets exhausted")
                        break
            elif budget_usd and total_cost >= budget_usd:
                # Simple budget check (fallback)
                self.logger.info(f"Budget exhausted: ${total_cost:.2f} >= ${budget_usd:.2f}")
                break

            # Execute round
            round_cost = self._execute_round(purple_agent, eval_result)
            total_cost += round_cost

            # Record cost in budget enforcer
            if self.budget_enforcer:
                self.budget_enforcer.record_cost(self.current_phase, round_cost)

            # Update phase if needed
            self._update_phase(eval_result)

            # Check termination criteria
            if self._should_terminate(eval_result):
                self.logger.info("Termination criteria met")
                break

        # Finalize evaluation
        eval_result.total_cost_usd = total_cost
        eval_result.finalize()

        self.logger.info(f"Evaluation complete: F1={eval_result.metrics.f1_score:.3f}, "
                        f"Cost=${total_cost:.2f}")

        return eval_result

    def _execute_round(
        self,
        purple_agent: PurpleAgent,
        eval_result: EvaluationResult
    ) -> float:
        """
        Execute one evaluation round.

        Args:
            purple_agent: Purple agent
            eval_result: Evaluation result (updated in place)

        Returns:
            Cost of this round
        """
        round_cost = 0.0

        # Phase-specific execution
        if self.current_phase == Phase.EXPLORATION:
            round_cost = self._execute_exploration(purple_agent, eval_result)

        elif self.current_phase == Phase.EXPLOITATION:
            round_cost = self._execute_exploitation(purple_agent, eval_result)

        elif self.current_phase == Phase.VALIDATION:
            round_cost = self._execute_validation(purple_agent, eval_result)

        elif self.current_phase == Phase.CONSENSUS:
            round_cost = self._execute_consensus(purple_agent, eval_result)

        return round_cost

    def _execute_exploration(
        self,
        purple_agent: PurpleAgent,
        eval_result: EvaluationResult
    ) -> float:
        """Execute exploration phase (boundary probing)."""
        self.logger.info("Phase: EXPLORATION (Boundary Probing)")

        # Form exploration coalition
        coalition = self._form_coalition(
            coalition_type=CoalitionType.EXPLORATION,
            required_capabilities={Capability.PROBE}
        )

        cost = 0.0

        # Probe each technique
        for technique in self.scenario.get_techniques():
            task = Task(
                task_id=f"probe_{technique}_{datetime.now().timestamp()}",
                task_type="probe_boundaries",
                description=f"Probe boundaries for {technique}",
                parameters={
                    'purple_agent': purple_agent,
                    'technique': technique,
                    'num_probes': 20
                }
            )

            agent = coalition.assign_task(task)
            if agent:
                result = agent.execute_task(task)
                cost += agent.capabilities.cost_per_invocation

                # ✅ FIX: Record probe results in evaluation metrics
                # Extract probe_history from BoundaryProber agent
                if hasattr(agent, 'probe_history'):
                    for attack, test_result in agent.probe_history:
                        # Only record if not already recorded
                        if attack not in eval_result.attacks:
                            eval_result.attacks.append(attack)
                            eval_result.test_results.append(test_result)
                            eval_result.total_attacks_tested += 1

                    self.logger.info(f"Recorded {len(agent.probe_history)} probe results for {technique}")

        coalition.execute()
        coalition.dissolve()

        return cost

    def _execute_exploitation(
        self,
        purple_agent: PurpleAgent,
        eval_result: EvaluationResult
    ) -> float:
        """Execute exploitation phase (attack generation & testing)."""
        self.logger.info("Phase: EXPLOITATION (Attack Generation)")

        cost = 0.0

        # Use Thompson Sampling to select next test
        technique, boundary_bin = self.allocator.select_next_test()

        # Form attacker coalition
        coalition = self._form_coalition(
            coalition_type=CoalitionType.ATTACKER,
            required_capabilities={Capability.GENERATE, Capability.MUTATE, Capability.VALIDATE}
        )

        # Generate attacks
        gen_task = Task(
            task_id=f"generate_{technique}_{datetime.now().timestamp()}",
            task_type="generate_attacks",
            description=f"Generate attacks for {technique}",
            parameters={
                'technique': technique,
                'num_attacks': 50,
                'boundary_info': self._get_boundary_info(technique, boundary_bin)
            }
        )

        gen_agent = coalition.assign_task(gen_task)
        if gen_agent:
            gen_result = gen_agent.execute_task(gen_task)
            attacks = gen_result.get('attacks', [])
            cost += gen_agent.capabilities.cost_per_invocation

            # Validate attacks
            val_task = Task(
                task_id=f"validate_{technique}_{datetime.now().timestamp()}",
                task_type="validate",
                description="Validate attacks",
                parameters={'attacks': attacks}
            )

            val_agent = coalition.assign_task(val_task)
            if val_agent:
                val_result = val_agent.execute_task(val_task)
                valid_attacks = val_result.get('valid', [])
                cost += val_agent.capabilities.cost_per_invocation

                # Test attacks
                for attack in valid_attacks:
                    result = self.scenario.execute_attack(attack, purple_agent)
                    eval_result.attacks.append(attack)
                    eval_result.test_results.append(result)
                    eval_result.total_attacks_tested += 1

                    # Update Thompson Sampling
                    success = result.is_evasion()
                    self.allocator.update(technique, boundary_bin, success)

        coalition.dissolve()
        return cost

    def _execute_validation(
        self,
        purple_agent: PurpleAgent,
        eval_result: EvaluationResult
    ) -> float:
        """Execute validation phase (Red vs Blue)."""
        self.logger.info("Phase: VALIDATION (Red vs Blue)")

        # Form validator coalition
        coalition = self._form_coalition(
            coalition_type=CoalitionType.VALIDATOR,
            required_capabilities={Capability.VALIDATE, Capability.EVALUATE}
        )

        cost = 0.0

        # Re-validate evasions
        evasions = eval_result.get_evasions()
        if evasions:
            task = Task(
                task_id=f"revalidate_{datetime.now().timestamp()}",
                task_type="validate",
                description="Re-validate evasions",
                parameters={'attacks': [e.attack_id for e in evasions]}
            )

            agent = coalition.assign_task(task)
            if agent:
                agent.execute_task(task)
                cost += agent.capabilities.cost_per_invocation

        coalition.dissolve()
        return cost

    def _execute_consensus(
        self,
        purple_agent: PurpleAgent,
        eval_result: EvaluationResult
    ) -> float:
        """Execute consensus phase (LLM Judge + multi-perspective assessment)."""
        self.logger.info("Phase: CONSENSUS (LLM Judge Assessment)")

        # Form debate coalition
        coalition = self._form_coalition(
            coalition_type=CoalitionType.DEBATE,
            required_capabilities={Capability.EVALUATE, Capability.DEBATE}
        )

        cost = 0.0

        # Check if we have attacks and results to judge
        if not eval_result.attacks or not eval_result.test_results:
            self.logger.warning("No attacks/results to judge, skipping consensus")
            coalition.dissolve()
            return cost

        # Create judgment task for LLM Judge agents
        judgment_task = Task(
            task_id=f"judge_{datetime.now().timestamp()}",
            task_type="judge",
            description="LLM Judge consensus assessment",
            parameters={
                'attacks': eval_result.attacks,
                'test_results': eval_result.test_results
            }
        )

        # Execute LLM Judge consensus
        for agent in coalition.members:
            if Capability.DEBATE in agent.capabilities.capabilities:
                try:
                    result = agent.execute_task(judgment_task)
                    cost += agent.capabilities.cost_per_invocation

                    # Log judgment results if available
                    if result and 'judgments' in result:
                        num_judgments = len(result['judgments'])
                        self.logger.info(f"LLM Judge completed {num_judgments} judgments")
                except Exception as e:
                    self.logger.error(f"LLM Judge execution failed: {e}")

        coalition.dissolve()
        return cost

    def _form_coalition(
        self,
        coalition_type: CoalitionType,
        required_capabilities: Set[Capability]
    ) -> Coalition:
        """
        Form a coalition with required capabilities.

        Args:
            coalition_type: Type of coalition
            required_capabilities: Required capabilities

        Returns:
            Formed coalition
        """
        self.coalition_counter += 1
        coalition_id = f"coalition_{self.coalition_counter}"

        goal = CoalitionGoal(
            goal_id=f"goal_{self.coalition_counter}",
            goal_type=coalition_type.name,
            description=f"{coalition_type.name} coalition",
            required_capabilities=required_capabilities,
            success_criteria={}
        )

        coalition = Coalition(
            coalition_id=coalition_id,
            coalition_type=coalition_type,
            goal=goal,
            knowledge_base=self.knowledge_base
        )

        # Add agents with required capabilities
        for agent in self.agents:
            if any(cap in agent.capabilities.capabilities for cap in required_capabilities):
                coalition.add_member(agent)

        self.coalitions.append(coalition)
        self.coalition_history.append({
            'coalition_id': coalition_id,
            'type': coalition_type.name,
            'members': [a.agent_id for a in coalition.members],
            'created_at': datetime.now()
        })

        return coalition

    def _get_boundary_info(self, technique: str, boundary_bin: int) -> Optional[Dict[str, Any]]:
        """Get boundary information for a technique."""
        entries = self.knowledge_base.query(entry_type='boundary', tags={technique})

        if entries:
            # Get boundaries for this bin (simplified - should be more sophisticated)
            boundaries_data = entries[0].data.get('boundaries', [])

            # Handle both dict and list formats
            if isinstance(boundaries_data, dict):
                # If it's a dict, return the whole dict
                return boundaries_data
            elif isinstance(boundaries_data, list) and boundaries_data:
                # If it's a list, return an element by index
                return boundaries_data[boundary_bin % len(boundaries_data)]

        return None

    def _update_phase(self, eval_result: EvaluationResult):
        """Update evaluation phase based on progress."""
        if self.current_phase == Phase.EXPLORATION:
            # Move to exploitation after initial probing
            if eval_result.total_attacks_tested > 50:
                self.current_phase = Phase.EXPLOITATION
                self.logger.info("Transitioning to EXPLOITATION phase")

        elif self.current_phase == Phase.EXPLOITATION:
            # Move to validation after sufficient testing
            if eval_result.total_attacks_tested > 200:
                self.current_phase = Phase.VALIDATION
                self.logger.info("Transitioning to VALIDATION phase")

        elif self.current_phase == Phase.VALIDATION:
            # Move to consensus
            self.current_phase = Phase.CONSENSUS
            self.logger.info("Transitioning to CONSENSUS phase")

        elif self.current_phase == Phase.CONSENSUS:
            # Complete
            self.current_phase = Phase.COMPLETE

    def _should_terminate(self, eval_result: EvaluationResult) -> bool:
        """Check if evaluation should terminate."""
        # Terminate if reached consensus phase
        if self.current_phase == Phase.COMPLETE:
            return True

        # Terminate if metrics are stable
        if eval_result.total_attacks_tested > 100:
            # Calculate current metrics
            eval_result.metrics = Metrics()
            for result in eval_result.test_results:
                if result.outcome:
                    if result.outcome.name == 'TRUE_POSITIVE':
                        eval_result.metrics.true_positives += 1
                    elif result.outcome.name == 'FALSE_NEGATIVE':
                        eval_result.metrics.false_negatives += 1

            eval_result.metrics.calculate_derived_metrics()

            # Terminate if F1 > 0.9 or no evasions found recently
            if eval_result.metrics.f1_score > 0.9:
                return True

        return False
