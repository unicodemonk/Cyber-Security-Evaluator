"""
Agent Profiler - Automatically profiles purple agents from their agent cards.

This module reads and analyzes agent cards to extract relevant information
for security testing and MITRE technique selection.

Features:
- Agent card fetching (HTTP/local file)
- Metadata extraction (platforms, capabilities, domains)
- Agent classification (web, AI/ML, IoT, etc.)
- Risk surface analysis
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse
import httpx


logger = logging.getLogger(__name__)


@dataclass
class AgentProfile:
    """Represents a profiled purple agent."""
    agent_id: str
    name: str
    description: str
    platforms: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)
    agent_type: str = "unknown"  # web, llm, iot, automation, etc.
    risk_level: str = "medium"  # low, medium, high, critical
    attack_surface: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'description': self.description,
            'platforms': self.platforms,
            'capabilities': self.capabilities,
            'domains': self.domains,
            'technologies': self.technologies,
            'agent_type': self.agent_type,
            'risk_level': self.risk_level,
            'attack_surface': self.attack_surface,
            'metadata': self.metadata
        }


class AgentProfiler:
    """
    Profiles purple agents by analyzing their agent cards.
    
    Supports:
    - Agent card fetching from URLs or local files
    - Metadata extraction and normalization
    - Platform and technology detection
    - Risk surface analysis
    - Agent type classification
    """

    # Platform keywords for detection
    PLATFORM_KEYWORDS = {
        'windows': ['windows', 'win32', 'powershell', 'cmd.exe', '.net'],
        'linux': ['linux', 'ubuntu', 'debian', 'centos', 'bash', 'sh'],
        'macos': ['macos', 'darwin', 'apple', 'osx'],
        'web': ['http', 'https', 'browser', 'javascript', 'html', 'web'],
        'cloud': ['aws', 'azure', 'gcp', 'cloud', 's3', 'lambda'],
        'containers': ['docker', 'kubernetes', 'k8s', 'container'],
        'mobile': ['android', 'ios', 'mobile', 'app'],
        'iot': ['iot', 'embedded', 'sensor', 'device'],
        'ai-ml': ['ai', 'ml', 'llm', 'gpt', 'model', 'neural', 'machine learning'],
    }

    # Technology stack keywords
    TECH_KEYWORDS = {
        'python': ['python', 'django', 'flask', 'fastapi', 'uvicorn'],
        'javascript': ['javascript', 'node.js', 'npm', 'react', 'vue', 'angular'],
        'java': ['java', 'spring', 'maven', 'gradle', 'jvm'],
        'go': ['golang', 'go'],
        'rust': ['rust', 'cargo'],
        'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'database'],
        'api': ['rest', 'graphql', 'api', 'endpoint', 'webhook'],
        'llm': ['openai', 'anthropic', 'llm', 'chatgpt', 'claude', 'gemini'],
    }

    # Domain/application area keywords
    DOMAIN_KEYWORDS = {
        'automation': ['automation', 'control', 'orchestration', 'workflow'],
        'iot': ['iot', 'smart home', 'smart device', 'sensor'],
        'finance': ['finance', 'banking', 'payment', 'transaction'],
        'healthcare': ['health', 'medical', 'patient', 'clinical'],
        'ecommerce': ['ecommerce', 'shopping', 'cart', 'checkout', 'order'],
        'social': ['social', 'messaging', 'chat', 'communication'],
        'analytics': ['analytics', 'data', 'metrics', 'reporting'],
        'security': ['security', 'authentication', 'authorization', 'encryption'],
    }

    # Agent type classification rules
    AGENT_TYPE_RULES = {
        'llm': lambda p: any(k in p.technologies for k in ['llm', 'openai', 'anthropic']) or 'ai-ml' in p.platforms,
        'web': lambda p: 'web' in p.platforms or any(k in p.technologies for k in ['javascript', 'api']),
        'iot': lambda p: 'iot' in p.platforms or 'iot' in p.domains,
        'automation': lambda p: 'automation' in p.domains,
        'cloud': lambda p: 'cloud' in p.platforms,
    }

    def __init__(self, cache_dir: Optional[Path] = None, timeout: int = 10):
        """
        Initialize agent profiler.

        Args:
            cache_dir: Directory to cache agent cards (optional)
            timeout: HTTP request timeout in seconds
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / '.seceval' / 'agent_cards'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        
        logger.info(f"AgentProfiler initialized (cache: {self.cache_dir})")

    def profile_agent(
        self,
        agent_card_url: Optional[str] = None,
        agent_card_path: Optional[Path] = None,
        agent_card_dict: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> AgentProfile:
        """
        Profile an agent from its agent card.

        Args:
            agent_card_url: URL to fetch agent card from
            agent_card_path: Local path to agent card file
            agent_card_dict: Agent card as dictionary (already loaded)
            use_cache: Whether to use cached agent cards

        Returns:
            AgentProfile object with extracted information

        Raises:
            ValueError: If no agent card source provided
            Exception: If agent card cannot be fetched/parsed
        """
        # Fetch agent card
        if agent_card_dict:
            card_data = agent_card_dict
        elif agent_card_path:
            card_data = self._load_from_file(agent_card_path)
        elif agent_card_url:
            card_data = self._fetch_from_url(agent_card_url, use_cache)
        else:
            raise ValueError("Must provide agent_card_url, agent_card_path, or agent_card_dict")

        # Extract profile
        profile = self._extract_profile(card_data)

        logger.info(f"Profiled agent: {profile.name} (type: {profile.agent_type}, platforms: {profile.platforms})")

        return profile

    def _fetch_from_url(self, url: str, use_cache: bool) -> Dict[str, Any]:
        """Fetch agent card from URL."""
        # Check cache first
        cache_key = self._url_to_cache_key(url)
        cache_file = self.cache_dir / cache_key
        
        if use_cache and cache_file.exists():
            logger.debug(f"Loading cached agent card: {cache_file}")
            with open(cache_file, 'r') as f:
                return json.load(f)

        # Fetch from URL
        logger.info(f"Fetching agent card from: {url}")
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url)
                response.raise_for_status()
                
                # Try to parse as JSON
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    # If not JSON, try to extract JSON from text
                    data = self._extract_json_from_text(response.text)

            # Cache the result
            if use_cache:
                with open(cache_file, 'w') as f:
                    json.dump(data, f, indent=2)

            return data

        except Exception as e:
            logger.error(f"Failed to fetch agent card from {url}: {e}")
            raise

    def _load_from_file(self, path: Path) -> Dict[str, Any]:
        """Load agent card from local file."""
        logger.info(f"Loading agent card from: {path}")
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load agent card from {path}: {e}")
            raise

    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text (handles markdown code blocks, etc.)."""
        # Try to find JSON in code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        # Try to find raw JSON
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        
        raise ValueError("Could not extract JSON from text")

    def _url_to_cache_key(self, url: str) -> str:
        """Convert URL to cache filename."""
        parsed = urlparse(url)
        # Use domain + path as cache key
        cache_key = f"{parsed.netloc}{parsed.path}".replace('/', '_').replace(':', '_')
        return f"{cache_key}.json"

    def _extract_profile(self, card_data: Dict[str, Any]) -> AgentProfile:
        """Extract profile information from agent card data."""
        # Extract basic info
        agent_id = card_data.get('id', card_data.get('agent_id', 'unknown'))
        name = card_data.get('name', card_data.get('title', 'Unknown Agent'))
        description = card_data.get('description', card_data.get('summary', ''))

        # Combine all text for keyword extraction
        all_text = self._combine_text_fields(card_data).lower()

        # Detect platforms
        platforms = self._detect_platforms(all_text, card_data)

        # Detect technologies
        technologies = self._detect_technologies(all_text, card_data)

        # Detect domains
        domains = self._detect_domains(all_text, card_data)

        # Extract capabilities
        capabilities = self._extract_capabilities(card_data)

        # Create initial profile
        profile = AgentProfile(
            agent_id=agent_id,
            name=name,
            description=description,
            platforms=platforms,
            capabilities=capabilities,
            domains=domains,
            technologies=technologies,
            metadata=card_data
        )

        # Classify agent type
        profile.agent_type = self._classify_agent_type(profile)

        # Analyze attack surface
        profile.attack_surface = self._analyze_attack_surface(profile, card_data)

        # Determine risk level
        profile.risk_level = self._determine_risk_level(profile)

        return profile

    def _combine_text_fields(self, data: Dict[str, Any]) -> str:
        """Combine all text fields from agent card for analysis."""
        text_parts = []
        
        # Common fields
        for field in ['name', 'title', 'description', 'summary', 'purpose', 'overview']:
            if field in data:
                text_parts.append(str(data[field]))
        
        # Nested fields
        if 'capabilities' in data:
            if isinstance(data['capabilities'], list):
                text_parts.extend(str(c) for c in data['capabilities'])
            else:
                text_parts.append(str(data['capabilities']))
        
        if 'tags' in data:
            text_parts.extend(str(t) for t in data.get('tags', []))
        
        if 'technologies' in data:
            text_parts.extend(str(t) for t in data.get('technologies', []))

        return ' '.join(text_parts)

    def _detect_platforms(self, text: str, card_data: Dict[str, Any]) -> List[str]:
        """Detect platforms from text and card data."""
        detected = set()

        # Check explicit platform field
        if 'platforms' in card_data:
            platforms = card_data['platforms']
            if isinstance(platforms, list):
                detected.update(p.lower() for p in platforms)
            else:
                detected.add(str(platforms).lower())

        # Keyword detection
        for platform, keywords in self.PLATFORM_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                detected.add(platform)

        return sorted(list(detected))

    def _detect_technologies(self, text: str, card_data: Dict[str, Any]) -> List[str]:
        """Detect technologies from text and card data."""
        detected = set()

        # Check explicit tech fields
        for field in ['technologies', 'tech_stack', 'stack', 'tools']:
            if field in card_data:
                techs = card_data[field]
                if isinstance(techs, list):
                    detected.update(t.lower() for t in techs)
                else:
                    detected.add(str(techs).lower())

        # Keyword detection
        for tech, keywords in self.TECH_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                detected.add(tech)

        return sorted(list(detected))

    def _detect_domains(self, text: str, card_data: Dict[str, Any]) -> List[str]:
        """Detect application domains from text and card data."""
        detected = set()

        # Check explicit domain fields
        for field in ['domain', 'domains', 'category', 'categories', 'industry']:
            if field in card_data:
                doms = card_data[field]
                if isinstance(doms, list):
                    detected.update(d.lower() for d in doms)
                else:
                    detected.add(str(doms).lower())

        # Keyword detection
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                detected.add(domain)

        return sorted(list(detected))

    def _extract_capabilities(self, card_data: Dict[str, Any]) -> List[str]:
        """Extract agent capabilities."""
        capabilities = []

        # Check explicit capabilities field
        if 'capabilities' in card_data:
            caps = card_data['capabilities']
            if isinstance(caps, list):
                capabilities.extend(str(c) for c in caps)
            else:
                capabilities.append(str(caps))

        # Check actions/functions field
        for field in ['actions', 'functions', 'operations', 'methods']:
            if field in card_data:
                actions = card_data[field]
                if isinstance(actions, list):
                    capabilities.extend(str(a) for a in actions)
                elif isinstance(actions, dict):
                    capabilities.extend(actions.keys())

        return capabilities

    def _classify_agent_type(self, profile: AgentProfile) -> str:
        """Classify agent type based on profile characteristics."""
        # Apply classification rules in priority order
        for agent_type, rule in self.AGENT_TYPE_RULES.items():
            if rule(profile):
                return agent_type
        
        # Fallback: use first platform/domain
        if profile.platforms:
            return profile.platforms[0]
        elif profile.domains:
            return profile.domains[0]
        
        return 'generic'

    def _analyze_attack_surface(self, profile: AgentProfile, card_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze attack surface of the agent."""
        surface = {
            'input_vectors': [],
            'output_vectors': [],
            'external_interfaces': [],
            'data_stores': [],
            'authentication': False,
            'authorization': False
        }

        # Analyze capabilities for attack vectors
        for cap in profile.capabilities:
            cap_lower = cap.lower()
            
            # Input vectors
            if any(k in cap_lower for k in ['input', 'receive', 'accept', 'parse', 'read']):
                surface['input_vectors'].append(cap)
            
            # Output vectors
            if any(k in cap_lower for k in ['output', 'send', 'write', 'transmit', 'export']):
                surface['output_vectors'].append(cap)
            
            # External interfaces
            if any(k in cap_lower for k in ['api', 'http', 'webhook', 'external', 'remote']):
                surface['external_interfaces'].append(cap)
            
            # Data stores
            if any(k in cap_lower for k in ['database', 'store', 'persist', 'cache', 'save']):
                surface['data_stores'].append(cap)
            
            # Security features
            if any(k in cap_lower for k in ['auth', 'login', 'credential']):
                surface['authentication'] = True
            if any(k in cap_lower for k in ['authorization', 'permission', 'access control']):
                surface['authorization'] = True

        # Check for endpoints
        if 'endpoints' in card_data:
            surface['external_interfaces'].extend(card_data['endpoints'])

        return surface

    def _determine_risk_level(self, profile: AgentProfile) -> str:
        """Determine risk level based on profile characteristics."""
        risk_score = 0

        # High-risk platforms
        if any(p in profile.platforms for p in ['web', 'cloud', 'ai-ml']):
            risk_score += 2

        # High-risk domains
        if any(d in profile.domains for d in ['finance', 'healthcare', 'security']):
            risk_score += 2

        # Attack surface factors
        if len(profile.attack_surface.get('input_vectors', [])) > 3:
            risk_score += 1
        if len(profile.attack_surface.get('external_interfaces', [])) > 2:
            risk_score += 2
        if not profile.attack_surface.get('authentication'):
            risk_score += 1
        if not profile.attack_surface.get('authorization'):
            risk_score += 1

        # Classify risk
        if risk_score >= 7:
            return 'critical'
        elif risk_score >= 5:
            return 'high'
        elif risk_score >= 3:
            return 'medium'
        else:
            return 'low'


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create sample agent card
    sample_card = {
        "id": "home-automation-001",
        "name": "Smart Home Controller",
        "description": "An AI-powered home automation agent that controls smart devices",
        "platforms": ["iot", "cloud"],
        "technologies": ["python", "mqtt", "llm"],
        "domains": ["automation", "iot"],
        "capabilities": [
            "control_lights",
            "adjust_thermostat",
            "lock_doors",
            "receive_voice_commands",
            "send_notifications"
        ],
        "endpoints": [
            "https://api.smarthome.example/control",
            "mqtt://broker.example/home/commands"
        ]
    }
    
    # Initialize profiler
    profiler = AgentProfiler()
    
    # Profile the agent
    profile = profiler.profile_agent(agent_card_dict=sample_card)
    
    print("\n✅ Agent Profile:")
    print(f"  Name: {profile.name}")
    print(f"  Type: {profile.agent_type}")
    print(f"  Risk Level: {profile.risk_level}")
    print(f"  Platforms: {', '.join(profile.platforms)}")
    print(f"  Technologies: {', '.join(profile.technologies)}")
    print(f"  Domains: {', '.join(profile.domains)}")
    print(f"\n  Attack Surface:")
    print(f"    Input Vectors: {len(profile.attack_surface['input_vectors'])}")
    print(f"    External Interfaces: {len(profile.attack_surface['external_interfaces'])}")
    print(f"    Authentication: {profile.attack_surface['authentication']}")
    print(f"    Authorization: {profile.attack_surface['authorization']}")
