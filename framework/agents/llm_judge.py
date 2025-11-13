"""
LLM Judge Agent - Calibrated consensus building.

Implements Dawid-Skene model for calibrated judge consensus (Enhancement 3).
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import numpy as np

from ..base import UnifiedAgent, AgentCapabilities, Capability, AgentRole, Task, KnowledgeBase
from ..models import Attack, TestResult


class LLMJudgeAgent(UnifiedAgent):
    """
    Agent that provides calibrated consensus judgments using LLMs.

    Uses Dawid-Skene model to calibrate judge reliability.
    """

    def __init__(
        self,
        agent_id: str,
        knowledge_base: KnowledgeBase,
        llm_clients: List[Any],  # Multiple LLMs for consensus
        model_router: Optional[Any] = None
    ):
        """
        Initialize LLM judge agent.

        Args:
            agent_id: Unique agent identifier
            knowledge_base: Shared knowledge base
            llm_clients: List of LLM clients for multi-judge consensus
            model_router: Optional model router for cost optimization
        """
        capabilities = AgentCapabilities(
            capabilities={Capability.DEBATE, Capability.EVALUATE},
            role=AgentRole.LLM_JUDGE,
            requires_llm=True,
            cost_per_invocation=0.15 * len(llm_clients),
            avg_latency_ms=2000.0
        )
        super().__init__(agent_id, capabilities, knowledge_base)
        self.llm_clients = llm_clients
        self.model_router = model_router

        # Dawid-Skene model state
        self.judge_confusion_matrices: Dict[str, np.ndarray] = {}
        self.class_priors: Optional[np.ndarray] = None

        # Initialize confusion matrices (2 classes: detected, not_detected)
        for i, client in enumerate(llm_clients):
            judge_id = f"judge_{i}"
            # Identity matrix as initial estimate (assume perfect judges)
            self.judge_confusion_matrices[judge_id] = np.array([
                [0.9, 0.1],  # True class 0: P(judge says 0 | true 0), P(judge says 1 | true 0)
                [0.1, 0.9]   # True class 1: P(judge says 0 | true 1), P(judge says 1 | true 1)
            ])

        self.class_priors = np.array([0.5, 0.5])  # Equal priors

        # Judgment history
        self.judgments: List[Dict[str, Any]] = []

    def execute_task(self, task: Task) -> Any:
        """
        Execute judgment task.

        Args:
            task: Task with parameters:
                - attacks: List of attacks to judge
                - test_results: List of test results

        Returns:
            Dictionary with consensus judgments
        """
        attacks = task.parameters.get('attacks', [])
        test_results = task.parameters.get('test_results', [])

        if not attacks or not test_results:
            self.logger.error("Missing attacks or test_results")
            return {'error': 'Missing data'}

        # Get judgments from all judges
        all_judgments = self._collect_judgments(attacks, test_results)

        # Apply Dawid-Skene calibration
        calibrated_judgments = self._calibrate_judgments(all_judgments)

        # Share knowledge
        self.share_knowledge(
            entry_type='judgment',
            data={
                'num_items': len(attacks),
                'num_judges': len(self.llm_clients),
                'calibrated_results': calibrated_judgments
            },
            tags={'judgment', 'consensus'}
        )

        return {'judgments': calibrated_judgments}

    def _collect_judgments(
        self,
        attacks: List[Attack],
        test_results: List[TestResult]
    ) -> Dict[str, Dict[str, int]]:
        """
        Collect judgments from all LLM judges.

        Args:
            attacks: Attacks to judge
            test_results: Test results

        Returns:
            Dictionary mapping attack_id to judge votes
        """
        all_judgments = {}

        for attack, result in zip(attacks, test_results):
            votes = {}

            for i, llm_client in enumerate(self.llm_clients):
                judge_id = f"judge_{i}"

                # Get judgment from this judge
                vote = self._get_single_judgment(llm_client, attack, result)
                votes[judge_id] = vote

            all_judgments[attack.attack_id] = votes

        return all_judgments

    def _get_single_judgment(
        self,
        llm_client: Any,
        attack: Attack,
        result: TestResult
    ) -> int:
        """
        Get judgment from single LLM judge.

        Args:
            llm_client: LLM client
            attack: Attack
            result: Test result

        Returns:
            Judgment: 0 (not detected) or 1 (detected)
        """
        # Get client identifier for logging
        client_name = getattr(llm_client, 'model_name', 'unknown')
        provider = getattr(llm_client, 'provider', None)
        if provider:
            client_id = f"{provider.value}/{client_name}" if hasattr(provider, 'value') else f"{provider}/{client_name}"
        else:
            client_id = client_name

        self.logger.info(f"🤖 Calling LLM Judge: {client_id}")

        prompt = f"""Judge whether this security test result is correct.

Attack: {attack.payload}
Detection Result: {"Detected" if result.detected else "Not Detected"}
Confidence: {result.confidence:.3f}

Is this detection result correct? Answer YES or NO.
"""

        try:
            # Route to appropriate model if router available
            if self.model_router:
                task = Task(
                    task_id=f"judge_{attack.attack_id}_{datetime.now().timestamp()}",
                    task_type='judge',
                    description=f"Judge detection result",
                    parameters={'attack_id': attack.attack_id}
                )
                model_client = self.model_router.route(task, prompt)
                self.logger.info(f"Routed to model: {model_client.name}")
            else:
                model_client = llm_client

            response = model_client.generate(prompt=prompt, max_tokens=10, temperature=0.3)

            self.logger.info(f"✅ {client_id}: Response received - {response[:50]}")

            # Parse response
            if 'YES' in response.upper():
                judgment = 1  # Detected
            else:
                judgment = 0  # Not detected

            # Update router with quality feedback
            if self.model_router:
                # Assess quality: definitive answers (YES/NO) are high quality
                has_definitive = ('YES' in response.upper() or 'NO' in response.upper())
                quality_feedback = 1.0 if has_definitive else 0.3
                self.model_router.update('judge', quality_feedback)

            return judgment

        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            self.logger.error(f"❌ {client_id} FAILED: {error_type} - {error_msg}")
            self.logger.error(f"   Falling back to original detection result")
            return int(result.detected)  # Fall back to original result

    def _calibrate_judgments(
        self,
        all_judgments: Dict[str, Dict[str, int]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calibrate judgments using Dawid-Skene model.

        Args:
            all_judgments: Raw judgments from all judges

        Returns:
            Calibrated consensus judgments
        """
        # Convert to matrix format
        items = list(all_judgments.keys())
        judges = list(self.judge_confusion_matrices.keys())
        n_items = len(items)
        n_judges = len(judges)

        # Rating matrix: [n_items, n_judges]
        ratings = np.zeros((n_items, n_judges), dtype=int)

        for i, item_id in enumerate(items):
            for j, judge_id in enumerate(judges):
                if judge_id in all_judgments[item_id]:
                    ratings[i, j] = all_judgments[item_id][judge_id]
                else:
                    ratings[i, j] = -1  # Missing

        # Run EM algorithm
        posteriors = self._dawid_skene_em(ratings, max_iterations=20)

        # Extract consensus
        calibrated = {}
        for i, item_id in enumerate(items):
            consensus_class = int(np.argmax(posteriors[i]))
            consensus_prob = float(posteriors[i, consensus_class])

            calibrated[item_id] = {
                'consensus_detected': bool(consensus_class),
                'confidence': consensus_prob,
                'raw_votes': all_judgments[item_id]
            }

        return calibrated

    def _dawid_skene_em(
        self,
        ratings: np.ndarray,
        max_iterations: int = 20
    ) -> np.ndarray:
        """
        Dawid-Skene EM algorithm.

        Args:
            ratings: Rating matrix [n_items, n_judges]
            max_iterations: Maximum EM iterations

        Returns:
            Posterior probabilities [n_items, n_classes]
        """
        n_items, n_judges = ratings.shape
        n_classes = 2  # Binary: detected / not detected

        # Initialize posteriors with majority vote
        posteriors = np.zeros((n_items, n_classes))
        for i in range(n_items):
            votes = ratings[i, ratings[i] >= 0]
            if len(votes) > 0:
                majority = int(votes.mean() > 0.5)
                posteriors[i, majority] = 1.0
            else:
                posteriors[i] = self.class_priors

        # EM iterations
        for iteration in range(max_iterations):
            # E-step: Update item posteriors
            for i in range(n_items):
                posterior = self.class_priors.copy()

                for j in range(n_judges):
                    if ratings[i, j] >= 0:
                        judge_id = list(self.judge_confusion_matrices.keys())[j]
                        observed = int(ratings[i, j])
                        # P(observed | true_class) for each class
                        likelihood = self.judge_confusion_matrices[judge_id][:, observed]
                        posterior *= likelihood

                # Normalize
                if posterior.sum() > 0:
                    posterior /= posterior.sum()
                else:
                    posterior = self.class_priors

                posteriors[i] = posterior

            # M-step: Update judge confusion matrices
            for j, judge_id in enumerate(self.judge_confusion_matrices.keys()):
                confusion = np.zeros((n_classes, n_classes))

                for i in range(n_items):
                    if ratings[i, j] >= 0:
                        observed = int(ratings[i, j])
                        for true_class in range(n_classes):
                            confusion[true_class, observed] += posteriors[i, true_class]

                # Normalize rows
                for true_class in range(n_classes):
                    row_sum = confusion[true_class].sum()
                    if row_sum > 0:
                        confusion[true_class] /= row_sum
                    else:
                        confusion[true_class] = np.array([0.5, 0.5])

                self.judge_confusion_matrices[judge_id] = confusion

            # Update class priors
            self.class_priors = posteriors.mean(axis=0)

        return posteriors

    def can_execute(self, task: Task) -> bool:
        """Check if agent can execute task."""
        return task.task_type in ['judge', 'consensus', 'debate']
