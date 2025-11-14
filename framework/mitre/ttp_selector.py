"""
MITRE TTP Selector - Downloads and caches MITRE ATT&CK and ATLAS data.

This module provides functionality to:
1. Download latest MITRE ATT&CK and ATLAS STIX files
2. Cache them locally with configurable refresh interval
3. Select appropriate TTPs based on agent profile
4. Map techniques to attack vectors

Data Sources:
- MITRE ATT&CK: https://github.com/mitre-attack/attack-stix-data
- MITRE ATLAS: https://github.com/mitre-atlas/atlas-data
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum


logger = logging.getLogger(__name__)


class TTPSource(Enum):
    """TTP data sources."""
    ATTACK = "attack"  # MITRE ATT&CK
    ATLAS = "atlas"    # MITRE ATLAS (AI/ML specific)


class Platform(Enum):
    """Target platforms for techniques."""
    LINUX = "linux"
    WINDOWS = "windows"
    MACOS = "macos"
    CLOUD = "cloud"
    WEB = "web"
    MOBILE = "mobile"
    NETWORK = "network"
    AI_ML = "ai-ml"
    LLM = "llm"
    CONTAINERS = "containers"


@dataclass
class MITRETechnique:
    """Represents a MITRE technique."""
    technique_id: str  # e.g., "T1059" or "AML.T0051"
    name: str
    description: str
    tactics: List[str]  # e.g., ["execution", "persistence"]
    platforms: List[str]  # e.g., ["linux", "windows"]
    data_sources: List[str] = field(default_factory=list)
    mitigations: List[str] = field(default_factory=list)
    detection: str = ""
    examples: List[str] = field(default_factory=list)
    source: TTPSource = TTPSource.ATTACK
    sub_techniques: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_applicable_to_platform(self, platform: str) -> bool:
        """Check if technique applies to given platform."""
        return platform.lower() in [p.lower() for p in self.platforms]

    def is_applicable_to_tactic(self, tactic: str) -> bool:
        """Check if technique applies to given tactic."""
        return tactic.lower() in [t.lower() for t in self.tactics]


@dataclass
class CacheMetadata:
    """Metadata for cached MITRE data."""
    last_updated: datetime
    source_url: str
    version: str
    technique_count: int
    source_type: TTPSource


class MITRETTPSelector:
    """
    Downloads, caches, and selects MITRE ATT&CK and ATLAS techniques.
    
    Features:
    - Downloads latest STIX data from official sources
    - Caches locally with configurable refresh
    - Selects relevant TTPs based on agent profile
    - Supports both ATT&CK and ATLAS frameworks
    """

    # Official MITRE data sources
    ATTACK_STIX_URLS = {
        "enterprise": "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json",
        "mobile": "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/mobile-attack/mobile-attack.json",
        "ics": "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/ics-attack/ics-attack.json"
    }
    
    # ATLAS STIX data location (updated to correct path)
    ATLAS_STIX_URL = "https://raw.githubusercontent.com/mitre-atlas/atlas-navigator-data/main/dist/stix-atlas.json"

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        refresh_interval_hours: int = 168,  # Default: 1 week (7 days * 24 hours)
        auto_download: bool = True,
        use_bundled_fallback: bool = True
    ):
        """
        Initialize MITRE TTP Selector.

        Args:
            cache_dir: Directory to cache MITRE data (default: ~/.seceval/mitre)
            refresh_interval_hours: Hours before refreshing cached data (default: 168 = 1 week)
            auto_download: Automatically download data if cache is stale (default: True)
            use_bundled_fallback: Use bundled baseline data if download fails (default: True)
        """
        self.cache_dir = cache_dir or Path.home() / '.seceval' / 'mitre'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Bundled baseline STIX files (fallback if downloads fail)
        self.baseline_dir = Path(__file__).parent / "baseline_stix"
        
        self.refresh_interval = timedelta(hours=refresh_interval_hours)
        self.auto_download = auto_download
        self.use_bundled_fallback = use_bundled_fallback

        # In-memory cache
        self.techniques: Dict[str, MITRETechnique] = {}
        self.tactics: Set[str] = set()
        self.platforms: Set[str] = set()
        self.cache_metadata: Dict[str, CacheMetadata] = {}

        # Load cached data or download fresh
        self._load_or_download()

    def _load_or_download(self):
        """Load cached data or download if stale/missing."""
        needs_refresh = False

        # Check if cache exists and is fresh
        for source_type in ["attack_enterprise", "atlas"]:
            cache_file = self.cache_dir / f"{source_type}.json"
            metadata_file = self.cache_dir / f"{source_type}_metadata.json"

            if not cache_file.exists() or not metadata_file.exists():
                logger.info(f"Cache missing for {source_type}, will download")
                needs_refresh = True
                break

            # Check freshness
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    last_updated = datetime.fromisoformat(metadata['last_updated'])
                    
                    if datetime.now() - last_updated > self.refresh_interval:
                        logger.info(f"Cache stale for {source_type} (age: {datetime.now() - last_updated})")
                        needs_refresh = True
                        break
            except Exception as e:
                logger.warning(f"Error reading metadata for {source_type}: {e}")
                needs_refresh = True
                break

        if needs_refresh and self.auto_download:
            logger.info("Downloading fresh MITRE data...")
            success = self.download_and_cache()
            if not success and self.use_bundled_fallback:
                logger.warning("Download failed, loading bundled baseline data...")
                self._load_bundled_baseline()
        elif needs_refresh and not self.auto_download and self.use_bundled_fallback:
            logger.info("Auto-download disabled, loading bundled baseline data...")
            self._load_bundled_baseline()
        else:
            logger.info("Loading MITRE data from cache...")
            try:
                self._load_from_cache()
            except Exception as e:
                if self.use_bundled_fallback:
                    logger.warning(f"Failed to load from cache: {e}, loading bundled baseline...")
                    self._load_bundled_baseline()
                else:
                    raise

    def download_and_cache(self) -> bool:
        """
        Download latest MITRE ATT&CK and ATLAS data and cache locally.

        Returns:
            True if successful, False otherwise
        """
        success = True

        # Download ATT&CK Enterprise
        try:
            logger.info("Downloading MITRE ATT&CK Enterprise...")
            response = requests.get(self.ATTACK_STIX_URLS["enterprise"], timeout=30)
            response.raise_for_status()
            
            attack_data = response.json()
            cache_file = self.cache_dir / "attack_enterprise.json"
            
            with open(cache_file, 'w') as f:
                json.dump(attack_data, f, indent=2)
            
            # Save metadata
            metadata = {
                'last_updated': datetime.now().isoformat(),
                'source_url': self.ATTACK_STIX_URLS["enterprise"],
                'version': attack_data.get('spec_version', 'unknown'),
                'technique_count': len([obj for obj in attack_data.get('objects', []) 
                                       if obj.get('type') == 'attack-pattern']),
                'source_type': 'attack'
            }
            
            with open(self.cache_dir / "attack_enterprise_metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"✅ Downloaded {metadata['technique_count']} ATT&CK techniques")
            
        except Exception as e:
            logger.error(f"Failed to download ATT&CK data: {e}")
            success = False

        # Download ATLAS
        try:
            logger.info("Downloading MITRE ATLAS...")
            response = requests.get(self.ATLAS_STIX_URL, timeout=30)
            response.raise_for_status()
            
            atlas_data = response.json()
            cache_file = self.cache_dir / "atlas.json"
            
            with open(cache_file, 'w') as f:
                json.dump(atlas_data, f, indent=2)
            
            # Save metadata
            metadata = {
                'last_updated': datetime.now().isoformat(),
                'source_url': self.ATLAS_STIX_URL,
                'version': atlas_data.get('spec_version', 'unknown'),
                'technique_count': len([obj for obj in atlas_data.get('objects', []) 
                                       if obj.get('type') == 'attack-pattern']),
                'source_type': 'atlas'
            }
            
            with open(self.cache_dir / "atlas_metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"✅ Downloaded {metadata['technique_count']} ATLAS techniques")
            
        except Exception as e:
            logger.error(f"Failed to download ATLAS data: {e}")
            success = False

        if success:
            # Reload from fresh cache
            self._load_from_cache()
        
        return success

    def _load_from_cache(self):
        """Load MITRE data from local cache."""
        self.techniques.clear()
        self.tactics.clear()
        self.platforms.clear()

        # Load ATT&CK Enterprise
        try:
            cache_file = self.cache_dir / "attack_enterprise.json"
            with open(cache_file, 'r') as f:
                attack_data = json.load(f)
            
            self._parse_stix_data(attack_data, TTPSource.ATTACK)
            logger.info(f"Loaded {len([t for t in self.techniques.values() if t.source == TTPSource.ATTACK])} ATT&CK techniques")
        except Exception as e:
            logger.error(f"Failed to load ATT&CK cache: {e}")

        # Load ATLAS
        try:
            cache_file = self.cache_dir / "atlas.json"
            with open(cache_file, 'r') as f:
                atlas_data = json.load(f)
            
            self._parse_stix_data(atlas_data, TTPSource.ATLAS)
            logger.info(f"Loaded {len([t for t in self.techniques.values() if t.source == TTPSource.ATLAS])} ATLAS techniques")
        except Exception as e:
            logger.error(f"Failed to load ATLAS cache: {e}")

        logger.info(f"Total techniques: {len(self.techniques)}")
        logger.info(f"Tactics: {len(self.tactics)}")
        logger.info(f"Platforms: {len(self.platforms)}")

    def _load_bundled_baseline(self):
        """Load bundled baseline MITRE data as fallback."""
        logger.info(f"Loading bundled baseline data from {self.baseline_dir}")
        
        self.techniques.clear()
        self.tactics.clear()
        self.platforms.clear()

        # Load bundled ATT&CK Enterprise
        try:
            baseline_file = self.baseline_dir / "attack_enterprise_baseline.json"
            if baseline_file.exists():
                with open(baseline_file, 'r') as f:
                    attack_data = json.load(f)
                
                self._parse_stix_data(attack_data, TTPSource.ATTACK)
                logger.info(f"✅ Loaded {len([t for t in self.techniques.values() if t.source == TTPSource.ATTACK])} ATT&CK techniques from baseline")
            else:
                logger.warning(f"Bundled ATT&CK baseline not found: {baseline_file}")
        except Exception as e:
            logger.error(f"Failed to load bundled ATT&CK baseline: {e}")

        # Load bundled ATLAS
        try:
            baseline_file = self.baseline_dir / "atlas_baseline.json"
            if baseline_file.exists():
                with open(baseline_file, 'r') as f:
                    atlas_data = json.load(f)
                
                self._parse_stix_data(atlas_data, TTPSource.ATLAS)
                logger.info(f"✅ Loaded {len([t for t in self.techniques.values() if t.source == TTPSource.ATLAS])} ATLAS techniques from baseline")
            else:
                logger.warning(f"Bundled ATLAS baseline not found: {baseline_file}")
        except Exception as e:
            logger.error(f"Failed to load bundled ATLAS baseline: {e}")

        # Load baseline metadata
        try:
            metadata_file = self.baseline_dir / "baseline_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                logger.info(f"📦 Using bundled baseline from {metadata.get('bundled_date', 'unknown date')}")
        except Exception as e:
            logger.warning(f"Could not load baseline metadata: {e}")

        logger.info(f"Total techniques: {len(self.techniques)}")
        logger.info(f"Tactics: {len(self.tactics)}")
        logger.info(f"Platforms: {len(self.platforms)}")

    def _parse_stix_data(self, stix_data: Dict, source: TTPSource):
        """Parse STIX JSON data into MITRETechnique objects."""
        objects = stix_data.get('objects', [])

        for obj in objects:
            if obj.get('type') != 'attack-pattern':
                continue

            # Extract technique ID
            external_refs = obj.get('external_references', [])
            technique_id = None
            for ref in external_refs:
                if ref.get('source_name') in ['mitre-attack', 'mitre-atlas']:
                    technique_id = ref.get('external_id')
                    break

            if not technique_id:
                continue

            # Extract kill chain phases (tactics)
            kill_chain_phases = obj.get('kill_chain_phases', [])
            tactics = [phase.get('phase_name', '') for phase in kill_chain_phases]
            self.tactics.update(tactics)

            # Extract platforms
            platforms = obj.get('x_mitre_platforms', [])
            self.platforms.update(platforms)

            # Extract data sources
            data_sources = []
            for ds in obj.get('x_mitre_data_sources', []):
                if isinstance(ds, str):
                    data_sources.append(ds)
                elif isinstance(ds, dict):
                    data_sources.append(ds.get('name', ''))

            # Create technique
            technique = MITRETechnique(
                technique_id=technique_id,
                name=obj.get('name', ''),
                description=obj.get('description', ''),
                tactics=tactics,
                platforms=platforms,
                data_sources=data_sources,
                detection=obj.get('x_mitre_detection', ''),
                source=source,
                metadata={
                    'created': obj.get('created', ''),
                    'modified': obj.get('modified', ''),
                    'version': obj.get('x_mitre_version', ''),
                    'deprecated': obj.get('x_mitre_deprecated', False),
                    'revoked': obj.get('revoked', False)
                }
            )

            self.techniques[technique_id] = technique

    def select_techniques_for_profile(
        self,
        agent_profile: Dict[str, Any],
        max_techniques: int = 50,
        prioritize_tactics: Optional[List[str]] = None
    ) -> List[MITRETechnique]:
        """
        Select relevant MITRE techniques based on agent profile.

        Args:
            agent_profile: Agent profile from profiler (platforms, capabilities, etc.)
            max_techniques: Maximum number of techniques to return
            prioritize_tactics: Tactics to prioritize (e.g., ['execution', 'persistence'])

        Returns:
            List of relevant MITRETechnique objects
        """
        relevant_techniques = []

        # Extract profile information
        agent_platforms = agent_profile.get('platforms', [])
        agent_type = agent_profile.get('type', '').lower()
        agent_capabilities = agent_profile.get('capabilities', [])
        agent_domains = agent_profile.get('domains', [])

        # Determine if agent is AI/ML focused
        is_ai_agent = any(keyword in agent_type or keyword in ' '.join(agent_capabilities).lower()
                         for keyword in ['ai', 'ml', 'llm', 'gpt', 'neural', 'model', 'language'])

        logger.info(f"Selecting techniques for agent: {agent_profile.get('name', 'unknown')}")
        logger.info(f"Platforms: {agent_platforms}")
        logger.info(f"Type: {agent_type}")
        logger.info(f"AI/ML Agent: {is_ai_agent}")

        # Score each technique
        technique_scores = []
        
        for tech_id, technique in self.techniques.items():
            # Skip deprecated/revoked
            if technique.metadata.get('deprecated') or technique.metadata.get('revoked'):
                continue

            score = 0

            # Source preference scoring
            if technique.source == TTPSource.ATLAS:
                # ATLAS techniques are relevant for all agents (prompt injection, model attacks, etc.)
                # But give bonus for AI/ML agents
                score += 10 if is_ai_agent else 5
            else:  # ATT&CK
                # ATT&CK techniques are broadly applicable
                score += 5

            # Platform match (high weight)
            if agent_platforms:
                platform_matches = sum(1 for p in agent_platforms 
                                     if technique.is_applicable_to_platform(p))
                score += platform_matches * 10

            # Tactic priority
            if prioritize_tactics:
                tactic_matches = sum(1 for t in prioritize_tactics 
                                   if technique.is_applicable_to_tactic(t))
                score += tactic_matches * 5

            # Domain relevance
            if agent_domains:
                for domain in agent_domains:
                    if domain.lower() in technique.description.lower():
                        score += 3

            # AI/ML specific technique bonus
            if is_ai_agent and technique.source == TTPSource.ATLAS:
                score += 8
            
            # Scenario-based relevance (ATLAS techniques for prompt injection scenarios)
            tech_name_lower = technique.name.lower()
            tech_desc_lower = technique.description.lower()
            
            # Prompt injection related techniques (highly relevant for any agent with text input)
            if any(keyword in tech_name_lower or keyword in tech_desc_lower 
                   for keyword in ['prompt', 'jailbreak', 'llm']):
                score += 12  # High relevance for prompt injection testing
            
            # Input manipulation techniques
            if any(keyword in tech_name_lower or keyword in tech_desc_lower
                   for keyword in ['input', 'injection', 'adversarial', 'evade']):
                score += 6
            
            # Data exfiltration techniques  
            if any(keyword in tech_name_lower or keyword in tech_desc_lower
                   for keyword in ['exfiltration', 'leak', 'extract']):
                score += 4

            # Only include techniques with some relevance
            if score > 0:
                technique_scores.append((technique, score))

        # Sort by score and return top N
        technique_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Store scores in technique metadata and return techniques
        relevant_techniques = []
        for tech, score in technique_scores[:max_techniques]:
            tech.metadata['selection_score'] = score
            relevant_techniques.append(tech)

        logger.info(f"Selected {len(relevant_techniques)} techniques (from {len(technique_scores)} candidates)")

        return relevant_techniques

    def get_technique_by_id(self, technique_id: str) -> Optional[MITRETechnique]:
        """Get technique by ID."""
        return self.techniques.get(technique_id)

    def get_techniques_by_tactic(self, tactic: str) -> List[MITRETechnique]:
        """Get all techniques for a given tactic."""
        return [tech for tech in self.techniques.values() 
                if tech.is_applicable_to_tactic(tactic)]

    def get_techniques_by_platform(self, platform: str) -> List[MITRETechnique]:
        """Get all techniques for a given platform."""
        return [tech for tech in self.techniques.values() 
                if tech.is_applicable_to_platform(platform)]

    def get_all_tactics(self) -> Set[str]:
        """Get all available tactics."""
        return self.tactics.copy()

    def get_all_platforms(self) -> Set[str]:
        """Get all available platforms."""
        return self.platforms.copy()

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cached data."""
        info = {
            'cache_dir': str(self.cache_dir),
            'total_techniques': len(self.techniques),
            'attack_techniques': len([t for t in self.techniques.values() if t.source == TTPSource.ATTACK]),
            'atlas_techniques': len([t for t in self.techniques.values() if t.source == TTPSource.ATLAS]),
            'tactics': sorted(self.tactics),
            'platforms': sorted(self.platforms),
            'sources': {}
        }

        # Add metadata for each source
        for source_name in ['attack_enterprise', 'atlas']:
            metadata_file = self.cache_dir / f"{source_name}_metadata.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        info['sources'][source_name] = metadata
                except Exception as e:
                    logger.error(f"Error reading {source_name} metadata: {e}")

        return info

    def force_refresh(self) -> bool:
        """Force refresh of cached data."""
        logger.info("Forcing refresh of MITRE data...")
        return self.download_and_cache()


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize selector
    selector = MITRETTPSelector(
        cache_dir=Path("./cache/mitre"),
        refresh_interval_hours=24,
        auto_download=True
    )
    
    # Example agent profile
    test_profile = {
        'name': 'ChatBot Agent',
        'type': 'llm',
        'platforms': ['web', 'ai-ml'],
        'capabilities': ['text generation', 'conversation'],
        'domains': ['natural language processing']
    }
    
    # Select techniques
    techniques = selector.select_techniques_for_profile(
        agent_profile=test_profile,
        max_techniques=10,
        prioritize_tactics=['execution', 'exfiltration']
    )
    
    print(f"\n✅ Selected {len(techniques)} techniques:")
    for tech in techniques[:5]:
        print(f"  - {tech.technique_id}: {tech.name}")
        print(f"    Tactics: {', '.join(tech.tactics)}")
        print(f"    Platforms: {', '.join(tech.platforms)}")
        print()
    
    # Get cache info
    cache_info = selector.get_cache_info()
    print(f"\n📊 Cache Info:")
    print(f"  Total Techniques: {cache_info['total_techniques']}")
    print(f"  ATT&CK: {cache_info['attack_techniques']}")
    print(f"  ATLAS: {cache_info['atlas_techniques']}")
