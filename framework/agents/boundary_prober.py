"""
Boundary Prober Agent - Explores decision boundaries.

Implements boundary learning through systematic probing to identify
weak decision boundaries where attacks are likely to evade detection.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
import random
from datetime import datetime
from pathlib import Path

from ..base import UnifiedAgent, AgentCapabilities, Capability, AgentRole, Task, KnowledgeBase, PurpleAgent
from ..models import Attack, TestResult, TestOutcome

# MITRE integration components
try:
    from ..profiler import AgentProfiler, AgentProfile
    from ..mitre.ttp_selector import MITRETTPSelector, MITRETechnique, TTPSource
    MITRE_AVAILABLE = True
except ImportError as e:
    MITRE_AVAILABLE = False
    import logging
    logging.getLogger(__name__).warning(f"MITRE components not available: {e}")


class BoundaryProberAgent(UnifiedAgent):
    """
    Agent that explores decision boundaries of purple agents.

    Uses binary search and systematic probing to find weak boundaries
    where attacks may evade detection.
    """

    def __init__(
        self,
        agent_id: str,
        knowledge_base: KnowledgeBase,
        scenario: 'SecurityScenario',
        mitre_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize boundary prober.

        Args:
            agent_id: Unique agent identifier
            knowledge_base: Shared knowledge base
            scenario: Security scenario being evaluated
            mitre_config: MITRE configuration (refresh_interval_hours, use_bundled_fallback, etc.)
        """
        capabilities = AgentCapabilities(
            capabilities={Capability.PROBE},
            role=AgentRole.BOUNDARY_PROBER,
            requires_llm=False,
            cost_per_invocation=0.0,
            avg_latency_ms=100.0
        )
        super().__init__(agent_id, capabilities, knowledge_base)
        self.scenario = scenario
        self.mitre_config = mitre_config or {}

        # Probing state
        self.boundaries_found: List[Dict[str, Any]] = []
        self.probe_history: List[Tuple[Attack, TestResult]] = []
        
        # MITRE integration (optional, graceful fallback)
        self.agent_profile: Optional[AgentProfile] = None
        self.selected_ttps: List[MITRETechnique] = []
        self._profiled = False  # Track if profiling has been done
        
        if MITRE_AVAILABLE and self.mitre_config.get('enabled', True):
            try:
                self.profiler = AgentProfiler(
                    cache_dir=Path.home() / '.seceval' / 'agent_cards'
                )
                self.ttp_selector = MITRETTPSelector(
                    cache_dir=Path.home() / '.seceval' / 'mitre',
                    refresh_interval_hours=self.mitre_config.get('refresh_interval_hours', 168),
                    auto_download=self.mitre_config.get('auto_download', True),
                    use_bundled_fallback=self.mitre_config.get('use_bundled_fallback', True)
                )
                self.logger.info("MITRE components initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize MITRE components: {e}")
                self.profiler = None
                self.ttp_selector = None
        else:
            self.profiler = None
            self.ttp_selector = None

    def execute_task(self, task: Task) -> Any:
        """
        Execute boundary probing task.

        Args:
            task: Task with parameters:
                - purple_agent: Target agent
                - technique: Technique to probe
                - num_probes: Number of probes (default: 20)

        Returns:
            Dictionary with boundary information
        """
        purple_agent = task.parameters.get('purple_agent')
        technique = task.parameters.get('technique')
        num_probes = task.parameters.get('num_probes', 20)

        if not purple_agent or not technique:
            self.logger.error("Missing required parameters: purple_agent, technique")
            return {'error': 'Missing parameters'}

        # MITRE Enhancement: Profile agent and select TTPs (once per agent)
        if not self._profiled and self.profiler and self.ttp_selector:
            self._profile_and_select_ttps(purple_agent)

        # Execute probing
        boundaries = self._probe_boundaries(purple_agent, technique, num_probes)

        # Share knowledge
        self.share_knowledge(
            entry_type='boundary',
            data={
                'technique': technique,
                'boundaries': boundaries,
                'num_probes': num_probes,
                'agent_name': purple_agent.get_name()
            },
            tags={'boundary', technique}
        )

        return boundaries

    def _profile_and_select_ttps(self, purple_agent: PurpleAgent) -> None:
        """
        Profile purple agent and select relevant MITRE TTPs.
        
        This is called once per agent and shares findings to knowledge base.
        
        Args:
            purple_agent: Purple agent to profile
        """
        try:
            self.logger.info(f"Profiling purple agent: {purple_agent.get_name()}")
            
            # Try to get agent card URL (if purple agent supports it)
            agent_card_url = None
            if hasattr(purple_agent, 'get_agent_card_url'):
                try:
                    agent_card_url = purple_agent.get_agent_card_url()
                except Exception as e:
                    self.logger.debug(f"Could not get agent card URL: {e}")
            
            # Profile the agent
            if agent_card_url:
                self.agent_profile = self.profiler.profile_agent(agent_card_url=agent_card_url)
            else:
                # Create minimal profile from agent name
                self.agent_profile = self._create_minimal_profile(purple_agent)
            
            self.logger.info(f"Agent profiled: type={self.agent_profile.agent_type}, "
                           f"platforms={self.agent_profile.platforms}")
            
            # Select relevant MITRE TTPs based on profile
            profile_dict = {
                'platforms': self.agent_profile.platforms,
                'type': self.agent_profile.agent_type,
                'domains': self.agent_profile.domains,
                'capabilities': self.agent_profile.capabilities,
                'name': self.agent_profile.name,
                # Enable ATLAS prioritization for AI/ML/automation agents
                'is_ai_agent': self.agent_profile.agent_type in ['ai', 'ml', 'automation', 'iot'],
                'is_ml_model': self.agent_profile.agent_type in ['ml', 'ai']
            }
            
            self.selected_ttps = self.ttp_selector.select_techniques_for_profile(
                agent_profile=profile_dict,
                max_techniques=25  # Increased from 20 to allow more ATLAS techniques
            )
            
            self.logger.info(f"Selected {len(self.selected_ttps)} MITRE TTPs for agent")
            
            # Share profile to knowledge base
            self.share_knowledge(
                entry_type='agent_profile',
                data={
                    'agent_id': purple_agent.get_name(),
                    'profile': self.agent_profile.to_dict()
                },
                tags={'agent_profile', purple_agent.get_name()}
            )
            
            # Share selected TTPs to knowledge base
            self.share_knowledge(
                entry_type='selected_ttps',
                data={
                    'agent_id': purple_agent.get_name(),
                    'techniques': [
                        {
                            'technique_id': ttp.technique_id,
                            'name': ttp.name,
                            'description': ttp.description,
                            'tactics': ttp.tactics,
                            'platforms': ttp.platforms,
                            'source': ttp.source.value
                        }
                        for ttp in self.selected_ttps
                    ],
                    'count': len(self.selected_ttps)
                },
                tags={'selected_ttps', purple_agent.get_name()}
            )
            
            self._profiled = True
            
        except Exception as e:
            self.logger.warning(f"MITRE profiling failed, continuing without it: {e}")
            self._profiled = True  # Don't retry
    
    def _create_minimal_profile(self, purple_agent: PurpleAgent) -> AgentProfile:
        """
        Create minimal profile when agent card is not available.
        
        Args:
            purple_agent: Purple agent
            
        Returns:
            Minimal AgentProfile
        """
        from ..profiler import AgentProfile
        
        agent_name = purple_agent.get_name()
        
        # Infer platform from name (basic heuristics)
        platforms = ['web']  # Default
        if 'iot' in agent_name.lower() or 'automation' in agent_name.lower():
            platforms = ['iot', 'web']
        if 'llm' in agent_name.lower() or 'ai' in agent_name.lower():
            platforms.append('ai-ml')
        
        return AgentProfile(
            agent_id=agent_name,
            name=agent_name,
            description=f"Agent {agent_name} (no agent card available)",
            platforms=platforms,
            capabilities=[],
            domains=['automation'] if 'automation' in agent_name.lower() else [],
            technologies=[],
            agent_type='generic',
            risk_level='medium',
            attack_surface={},
            metadata={}
        )

    def _probe_boundaries(
        self,
        purple_agent: PurpleAgent,
        technique: str,
        num_probes: int
    ) -> Dict[str, Any]:
        """
        Probe decision boundaries for a technique.

        Args:
            purple_agent: Target agent
            technique: Attack technique
            num_probes: Number of probes

        Returns:
            Dictionary with boundary information
        """
        self.logger.info(f"Probing boundaries for technique: {technique}")

        # Get baseline samples
        baseline_samples = self._get_baseline_samples(technique)

        # Test baseline samples
        results = []
        for sample in baseline_samples[:num_probes]:
            attack = self.scenario.create_attack(
                technique=technique,
                payload=sample['payload'],
                metadata={
                    'probe_type': 'baseline',
                    'expected_detection': sample.get('expected_detection', True)
                }
            )
            attack.created_by = self.agent_id

            result = self.scenario.execute_attack(attack, purple_agent)
            results.append({'attack': attack, 'result': result})
            self.probe_history.append((attack, result))

        # Analyze boundaries
        boundaries = self._analyze_boundaries(results)
        self.boundaries_found.extend(boundaries)

        return {
            'technique': technique,
            'boundaries': boundaries,
            'total_probes': len(results),
            'detection_rate': sum(1 for r in results if r['result'].detected) / len(results) if results else 0.0
        }

    def _get_baseline_samples(self, technique: str) -> List[Dict[str, Any]]:
        """
        Get baseline samples for probing.

        Args:
            technique: Attack technique

        Returns:
            List of baseline samples
        """
        # Check if scenario provides baseline dataset
        baseline_dataset = self.scenario.get_baseline_dataset()
        if baseline_dataset:
            # Filter by technique
            technique_samples = [
                {'payload': attack.payload, 'expected_detection': attack.expected_detection}
                for attack in baseline_dataset
                if attack.technique == technique
            ]
            if technique_samples:
                return technique_samples

        # Generate synthetic samples if no baseline
        return self._generate_synthetic_samples(technique)

    def _generate_synthetic_samples(self, technique: str) -> List[Dict[str, Any]]:
        """
        Generate synthetic probing samples.

        Override in scenario-specific implementations for better samples.

        Args:
            technique: Attack technique

        Returns:
            List of synthetic samples
        """
        # Default: Generic samples (should be overridden per scenario)
        return [
            {'payload': f'safe_input_{i}', 'expected_detection': False}
            for i in range(5)
        ] + [
            {'payload': f'{technique}_attack_{i}', 'expected_detection': True}
            for i in range(15)
        ]

    def _analyze_boundaries(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze probing results to identify boundaries.

        Args:
            results: List of probe results

        Returns:
            List of boundary information
        """
        boundaries = []

        # Find misclassifications (potential boundaries)
        for item in results:
            attack = item['attack']
            result = item['result']

            # Check if outcome differs from expected
            if attack.expected_detection and not result.detected:
                # False Negative - weak boundary!
                boundaries.append({
                    'type': 'weak_boundary',
                    'attack_id': attack.attack_id,
                    'payload': attack.payload,
                    'technique': attack.technique,
                    'reason': 'false_negative',
                    'confidence': 1.0 - result.confidence
                })

            elif not attack.expected_detection and result.detected:
                # False Positive
                boundaries.append({
                    'type': 'over_detection',
                    'attack_id': attack.attack_id,
                    'payload': attack.payload,
                    'technique': attack.technique,
                    'reason': 'false_positive',
                    'confidence': result.confidence
                })

        # Sort by confidence (prioritize high-confidence boundaries)
        boundaries.sort(key=lambda x: x.get('confidence', 0.0), reverse=True)

        return boundaries

    def get_weak_boundaries(self, technique: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get weak boundaries discovered.

        Args:
            technique: Filter by technique (optional)

        Returns:
            List of weak boundaries
        """
        if technique:
            return [
                b for b in self.boundaries_found
                if b['technique'] == technique and b['type'] == 'weak_boundary'
            ]
        return [b for b in self.boundaries_found if b['type'] == 'weak_boundary']

    def can_execute(self, task: Task) -> bool:
        """Check if agent can execute task."""
        return task.task_type in ['probe_boundaries', 'explore']
