"""
Unified Ecosystem - Main entry point for the framework.

Provides high-level API for running security evaluations using the
unified agent-based architecture.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from .base import SecurityScenario, PurpleAgent, UnifiedAgent
from .models import EvaluationResult
from .knowledge_base import InMemoryKnowledgeBase
from .orchestrator import MetaOrchestrator
from .agents import (
    BoundaryProberAgent,
    ExploiterAgent,
    MutatorAgent,
    ValidatorAgent,
    PerspectiveAgent,
    LLMJudgeAgent,
    CounterfactualAgent
)


class UnifiedEcosystem:
    """
    Unified ecosystem for security evaluation.

    Main entry point that initializes all components and orchestrates
    agent-based evaluation.
    """

    def __init__(
        self,
        scenario: SecurityScenario,
        use_llm: bool = False,
        llm_clients: Optional[List[Any]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize unified ecosystem.

        Args:
            scenario: Security scenario to evaluate
            use_llm: Whether to use LLMs for generation/assessment
            llm_clients: List of LLM clients (required if use_llm=True)
            config: Optional configuration dictionary
        """
        self.scenario = scenario
        self.use_llm = use_llm
        self.llm_clients = llm_clients or []
        self.config = config or {}
        self.logger = logging.getLogger("UnifiedEcosystem")

        # Initialize knowledge base
        self.knowledge_base = InMemoryKnowledgeBase()

        # Initialize model router for cost optimization (if enabled)
        self.model_router = None
        if self.use_llm and self.llm_clients and self.config.get('use_cost_optimization', False):
            from .cost_optimizer import ModelRouter, EXAMPLE_MODELS
            self.model_router = ModelRouter(models=EXAMPLE_MODELS)
            self.logger.info("Model router initialized for cost optimization")

        # Initialize coverage tracker (if enabled)
        self.coverage_tracker = None
        if self.config.get('use_coverage_tracking', False):
            from .coverage_tracker import CoverageTracker
            self.coverage_tracker = CoverageTracker(
                scenario=scenario,
                taxonomy=self.config.get('taxonomy', 'MITRE_ATT&CK')
            )
            self.logger.info("Coverage tracker initialized for MITRE ATT&CK tracking")

        # Initialize agents
        self.agents = self._initialize_agents()

        # Initialize orchestrator with optional sandbox and cost optimization
        use_sandbox = self.config.get('use_sandbox', False)
        sandbox_config = self.config.get('sandbox_config', {})
        use_cost_optimization = self.config.get('use_cost_optimization', False)

        self.orchestrator = MetaOrchestrator(
            knowledge_base=self.knowledge_base,
            scenario=scenario,
            agents=self.agents,
            use_sandbox=use_sandbox,
            sandbox_config=sandbox_config,
            use_cost_optimization=use_cost_optimization
        )

        if use_sandbox:
            self.logger.info(f"Initialized ecosystem with {len(self.agents)} agents + SANDBOX (production-safe)")
        else:
            self.logger.warning(f"Initialized ecosystem with {len(self.agents)} agents WITHOUT sandbox (NOT production-safe)")
            self.logger.warning("⚠️  Set config['use_sandbox']=True for production deployments")

    def _initialize_agents(self) -> List[UnifiedAgent]:
        """
        Initialize all agents for the ecosystem.

        Returns:
            List of initialized agents
        """
        agents = []

        # 1. Boundary Prober Agents (1-3 agents)
        num_probers = self.config.get('num_boundary_probers', 2)
        for i in range(num_probers):
            agent = BoundaryProberAgent(
                agent_id=f"boundary_prober_{i}",
                knowledge_base=self.knowledge_base,
                scenario=self.scenario
            )
            agents.append(agent)

        # 2. Exploiter Agents (2-4 agents, some with LLM)
        num_exploiters = self.config.get('num_exploiters', 3)
        for i in range(num_exploiters):
            # Only first exploiter uses LLM (if enabled)
            use_agent_llm = self.use_llm and i == 0 and self.llm_clients
            llm_client = self.llm_clients[0] if use_agent_llm else None

            agent = ExploiterAgent(
                agent_id=f"exploiter_{i}",
                knowledge_base=self.knowledge_base,
                scenario=self.scenario,
                use_llm=use_agent_llm,
                llm_client=llm_client,
                model_router=self.model_router
            )
            agents.append(agent)

        # 3. Mutator Agents (2-3 agents with different strategies)
        num_mutators = self.config.get('num_mutators', 2)
        for i in range(num_mutators):
            agent = MutatorAgent(
                agent_id=f"mutator_{i}",
                knowledge_base=self.knowledge_base,
                scenario=self.scenario,
                population_size=self.config.get('population_size', 50),
                novelty_weight=0.3 + i * 0.2,  # Vary novelty weight
                llm_client=self.llm_clients[0] if self.use_llm and self.llm_clients else None,
                model_router=self.model_router,
                llm_mutation_ratio=self.config.get('llm_mutation_ratio', 0.3)
            )
            agents.append(agent)

        # 4. Validator Agents (1-2 agents)
        num_validators = self.config.get('num_validators', 1)
        validators = self.scenario.get_validators()

        for i in range(num_validators):
            agent = ValidatorAgent(
                agent_id=f"validator_{i}",
                knowledge_base=self.knowledge_base,
                validators=validators,
                llm_client=self.llm_clients[0] if self.use_llm and self.llm_clients else None,
                model_router=self.model_router,
                use_llm_semantic_check=self.config.get('use_llm_validation', True)
            )
            agents.append(agent)

        # 5. Perspective Agents (optional, requires LLM)
        if self.use_llm and self.llm_clients:
            perspectives = ['security_expert', 'developer', 'pentester']
            for i, perspective in enumerate(perspectives):
                if i < len(self.llm_clients):
                    agent = PerspectiveAgent(
                        agent_id=f"perspective_{perspective}",
                        knowledge_base=self.knowledge_base,
                        perspective_type=perspective,
                        llm_client=self.llm_clients[i % len(self.llm_clients)],
                        model_router=self.model_router
                    )
                    agents.append(agent)

        # 6. LLM Judge Agent (optional, requires multiple LLMs)
        if self.use_llm and len(self.llm_clients) >= 2:
            agent = LLMJudgeAgent(
                agent_id="llm_judge",
                knowledge_base=self.knowledge_base,
                llm_clients=self.llm_clients[:3],  # Use up to 3 LLMs for consensus
                model_router=self.model_router
            )
            agents.append(agent)

        # 7. Counterfactual Analyzer (1 agent)
        agent = CounterfactualAgent(
            agent_id="counterfactual_analyzer",
            knowledge_base=self.knowledge_base,
            scenario=self.scenario,
            beam_width=self.config.get('counterfactual_beam_width', 5),
            max_depth=self.config.get('counterfactual_max_depth', 3),
            llm_client=self.llm_clients[0] if self.use_llm and self.llm_clients else None,
            model_router=self.model_router,
            use_llm_suggestions=self.config.get('use_llm_remediation', True)
        )
        agents.append(agent)

        return agents

    def evaluate(
        self,
        purple_agent: PurpleAgent,
        max_rounds: int = 10,
        budget_usd: Optional[float] = None
    ) -> EvaluationResult:
        """
        Evaluate a purple agent using the unified ecosystem.

        Args:
            purple_agent: Purple agent to evaluate
            max_rounds: Maximum number of evaluation rounds
            budget_usd: Optional cost budget in USD

        Returns:
            Evaluation result
        """
        self.logger.info(f"Starting evaluation of {purple_agent.get_name()}")
        self.logger.info(f"Scenario: {self.scenario.get_name()}")
        self.logger.info(f"Max rounds: {max_rounds}, Budget: ${budget_usd if budget_usd else 'unlimited'}")

        # Predict cost if cost optimization enabled
        if self.config.get('use_cost_optimization', False) and self.use_llm:
            try:
                from .cost_optimizer import CostPredictor
                predictor = CostPredictor(agents=self.agents)

                predicted_cost = predictor.predict_cost(
                    num_rounds=max_rounds,
                    num_attacks=self.config.get('num_attacks_per_round', 50),
                    use_llm_agents=self.use_llm
                )

                self.logger.info(f"💰 Predicted cost: ${predicted_cost:.2f}")

                if budget_usd and predicted_cost > budget_usd:
                    self.logger.warning(f"⚠️  Predicted cost (${predicted_cost:.2f}) exceeds budget (${budget_usd:.2f})")
                    self.logger.warning(f"   Evaluation may terminate early due to budget constraints")
            except Exception as e:
                self.logger.warning(f"Cost prediction failed: {e}")

        # Reset knowledge base
        self.knowledge_base.clear()

        # Run orchestrated evaluation
        result = self.orchestrator.orchestrate_evaluation(
            purple_agent=purple_agent,
            max_rounds=max_rounds,
            budget_usd=budget_usd
        )

        # Add agent contributions
        result.agent_contributions = self._collect_agent_contributions()

        # Add coalition history
        result.coalition_history = self.orchestrator.coalition_history

        # Generate eBOM (Evaluation Bill of Materials)
        result.ebom = self._generate_ebom(result)

        # Update coverage tracking (if enabled)
        if self.coverage_tracker:
            self.coverage_tracker.update_coverage(result)
            coverage_report = self.coverage_tracker.generate_coverage_report()
            self.logger.info(f"📊 Coverage: {coverage_report['coverage_summary']['coverage_percentage']:.1f}% "
                           f"({coverage_report['coverage_summary']['covered']}/{coverage_report['coverage_summary']['total_techniques']} techniques)")

        self.logger.info("Evaluation complete")
        self.logger.info(f"Results: F1={result.metrics.f1_score:.3f}, "
                        f"Precision={result.metrics.precision:.3f}, "
                        f"Recall={result.metrics.recall:.3f}")
        self.logger.info(f"Total cost: ${result.total_cost_usd:.2f}, "
                        f"Time: {result.total_time_seconds:.1f}s")

        return result

    def _collect_agent_contributions(self) -> Dict[str, int]:
        """
        Collect agent contribution statistics.

        Returns:
            Dictionary mapping agent_id to contribution count
        """
        contributions = {}

        # Query knowledge base for agent contributions
        for agent in self.agents:
            entries = self.knowledge_base.query(source_agent=agent.agent_id)
            contributions[agent.agent_id] = len(entries)

        return contributions

    def _generate_ebom(self, result: EvaluationResult) -> Dict[str, Any]:
        """
        Generate Evaluation Bill of Materials (eBOM).

        Provides reproducibility information for the evaluation.

        Args:
            result: Evaluation result

        Returns:
            eBOM dictionary
        """
        ebom = {
            'version': '1.0',
            'generated_at': datetime.now().isoformat(),

            # Framework info
            'framework': {
                'name': 'Unified Adaptive Security Evaluation Framework',
                'version': '2.1',
                'scenario': self.scenario.get_name(),
                'scenario_version': getattr(self.scenario, 'version', 'unknown')
            },

            # Agent configuration
            'agents': [
                {
                    'agent_id': agent.agent_id,
                    'role': agent.get_role().name,
                    'requires_llm': agent.requires_llm(),
                    'contributions': result.agent_contributions.get(agent.agent_id, 0)
                }
                for agent in self.agents
            ],

            # LLM configuration
            'llm_config': {
                'enabled': self.use_llm,
                'num_clients': len(self.llm_clients),
                'models': [
                    getattr(client, 'model_name', 'unknown')
                    for client in self.llm_clients
                ] if self.use_llm else []
            },

            # Evaluation parameters
            'parameters': {
                'max_rounds': result.metrics.total_latency_ms,  # Placeholder
                'techniques': self.scenario.get_techniques(),
                'mutators': [m.get_mutation_type() for m in self.scenario.get_mutators()],
                'validators': [v.get_validator_type() for v in self.scenario.get_validators()]
            },

            # Resource usage
            'resources': {
                'total_cost_usd': result.total_cost_usd,
                'total_time_seconds': result.total_time_seconds,
                'llm_calls': result.llm_calls,
                'total_attacks_tested': result.total_attacks_tested
            },

            # Reproducibility
            'reproducibility': {
                'random_seed': self.config.get('random_seed', 'not_set'),
                'deterministic_mode': self.config.get('deterministic', False),
                'knowledge_base_entries': len(self.knowledge_base.entries)
            }
        }

        return ebom

    def get_stats(self) -> Dict[str, Any]:
        """
        Get ecosystem statistics.

        Returns:
            Dictionary with stats
        """
        return {
            'scenario': self.scenario.get_name(),
            'num_agents': len(self.agents),
            'agents_by_role': self._count_agents_by_role(),
            'use_llm': self.use_llm,
            'num_llm_clients': len(self.llm_clients),
            'knowledge_base': self.knowledge_base.get_stats()
        }

    def _count_agents_by_role(self) -> Dict[str, int]:
        """Count agents by role."""
        counts = {}
        for agent in self.agents:
            role = agent.get_role().name
            counts[role] = counts.get(role, 0) + 1
        return counts

    def get_coverage_report(self) -> Optional[Dict[str, Any]]:
        """
        Get current coverage report.

        Returns:
            Coverage report dict or None if coverage tracking disabled
        """
        if not self.coverage_tracker:
            self.logger.warning("Coverage tracking not enabled. Set config['use_coverage_tracking']=True")
            return None

        return self.coverage_tracker.generate_coverage_report()

    def suggest_next_scenario(self) -> Optional[Dict[str, Any]]:
        """
        Get suggestion for next scenario to implement.

        Returns:
            Suggestion dict or None if coverage tracking disabled
        """
        if not self.coverage_tracker:
            self.logger.warning("Coverage tracking not enabled. Set config['use_coverage_tracking']=True")
            return None

        from .coverage_tracker import CoverageExpansionAgent
        expansion_agent = CoverageExpansionAgent(self.coverage_tracker)
        return expansion_agent.suggest_next_scenario()

    def generate_scenario_template(self, technique: str) -> Optional[str]:
        """
        Generate Python code template for new scenario.

        Args:
            technique: MITRE technique ID (e.g., 'T1234')

        Returns:
            Python code template or None if coverage tracking disabled
        """
        if not self.coverage_tracker:
            self.logger.warning("Coverage tracking not enabled. Set config['use_coverage_tracking']=True")
            return None

        from .coverage_tracker import CoverageExpansionAgent
        expansion_agent = CoverageExpansionAgent(self.coverage_tracker)
        return expansion_agent.generate_scenario_template(technique)


def create_ecosystem(
    scenario: SecurityScenario,
    llm_mode: str = 'none',  # 'none', 'cheap', 'multi'
    llm_clients: Optional[List[Any]] = None,
    config: Optional[Dict[str, Any]] = None
) -> UnifiedEcosystem:
    """
    Factory function to create ecosystem with different LLM modes.

    Args:
        scenario: Security scenario
        llm_mode: LLM usage mode:
            - 'none': No LLM (algorithmic only)
            - 'cheap': Single cheap LLM for generation
            - 'multi': Multiple LLMs for full consensus
        llm_clients: LLM client instances
        config: Optional configuration

    Returns:
        Configured UnifiedEcosystem
    """
    use_llm = llm_mode != 'none'

    if use_llm and not llm_clients:
        raise ValueError("llm_clients required when llm_mode != 'none'")

    # Filter LLM clients based on mode
    if llm_mode == 'cheap':
        llm_clients = llm_clients[:1] if llm_clients else []
    elif llm_mode == 'multi':
        llm_clients = llm_clients if llm_clients else []

    return UnifiedEcosystem(
        scenario=scenario,
        use_llm=use_llm,
        llm_clients=llm_clients,
        config=config
    )
