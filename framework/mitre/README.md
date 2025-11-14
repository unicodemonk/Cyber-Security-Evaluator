# MITRE Integration Directory Structure

This directory contains the MITRE ATT&CK and ATLAS integration components for the SecurityEvaluator framework.

## Directory Structure

```
framework/mitre/
├── README.md                      # This file
├── __init__.py                    # Module exports
├── ttp_selector.py                # MITRE TTP selection engine
├── payload_generator.py           # Attack payload generator
├── baseline_stix/                 # ✅ Bundled baseline STIX data (FALLBACK)
│   ├── README.md                  # Data source information
│   ├── attack_enterprise_baseline.json  # ATT&CK Enterprise v15.1 (835 techniques)
│   ├── atlas_baseline.json        # ATLAS v4.6.0 (140 techniques)
│   └── baseline_metadata.json     # Baseline version info
└── cache/                         # ⚙️ Downloaded MITRE data (CONFIGURABLE)
    ├── attack_enterprise.json     # Latest ATT&CK from MITRE
    ├── attack_enterprise_metadata.json
    ├── atlas.json                 # Latest ATLAS from MITRE
    └── atlas_metadata.json
```

## Data Sources

### 1. `baseline_stix/` - Bundled Baseline Data (Fallback)

**Purpose**: Reliable fallback data bundled with the package

- **Location**: `framework/mitre/baseline_stix/`
- **Updated**: Manually when package is released
- **Contains**:
  - MITRE ATT&CK Enterprise v15.1 (835 techniques)
  - MITRE ATLAS v4.6.0 (140 ML/AI techniques)
- **Usage**: Automatically loaded if:
  - Fresh downloads fail (network issues)
  - `auto_download=False` in configuration
  - Cache is invalid/corrupted

**Benefits**:
- ✅ Always available (no network required)
- ✅ Version-controlled with the package
- ✅ Guaranteed to work offline
- ✅ Known baseline for reproducibility

### 2. `cache/` - Downloaded MITRE Data (Configurable Cache)

**Purpose**: Fresh MITRE data downloaded from official sources

- **Location**: `~/.seceval/mitre/` (default, configurable)
- **Updated**: Automatically based on refresh interval
- **Refresh Interval**: Configurable (default: 1 week)
- **Sources**:
  - ATT&CK: https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json
  - ATLAS: https://raw.githubusercontent.com/mitre-atlas/atlas-data/main/dist/ATLAS.json
- **Usage**: Primary data source when available and fresh

**Benefits**:
- ✅ Latest techniques and updates from MITRE
- ✅ New tactics and procedures
- ✅ Updated descriptions and metadata
- ✅ Configurable refresh schedule

## Configuration

### In Scenario TOML File

```toml
[mitre]
# Enable automatic downloads from MITRE (default: true)
auto_download = true

# Cache refresh interval in hours (default: 168 = 1 week)
cache_refresh_hours = 168

# Use bundled baseline if downloads fail (default: true)
use_bundled_fallback = true

# Maximum techniques to select per agent (default: 20)
max_techniques_per_agent = 20
```

### Programmatic Configuration

```python
from framework.mitre import MITRETTPSelector

# Custom configuration
selector = MITRETTPSelector(
    cache_dir=Path('/custom/cache/dir'),
    refresh_interval_hours=24,        # Refresh daily
    auto_download=True,                # Auto-download fresh data
    use_bundled_fallback=True          # Fall back to baseline if needed
)
```

## Cache Management

### Refresh Strategies

1. **Aggressive** (24 hours): Always get latest techniques
   ```toml
   cache_refresh_hours = 24
   ```

2. **Balanced** (1 week, default): Good balance of freshness and stability
   ```toml
   cache_refresh_hours = 168
   ```

3. **Stable** (1 month): Maximum stability for long-term testing
   ```toml
   cache_refresh_hours = 720
   ```

4. **Offline** (never): Use bundled baseline only
   ```toml
   auto_download = false
   ```

### Manual Cache Management

```bash
# View cache location
python -c "from pathlib import Path; print(Path.home() / '.seceval' / 'mitre')"

# Clear cache (force fresh download)
rm -rf ~/.seceval/mitre/

# View cache metadata
cat ~/.seceval/mitre/attack_enterprise_metadata.json
cat ~/.seceval/mitre/atlas_metadata.json
```

## Data Versioning

### Baseline Version

Check bundled baseline version:
```bash
cat framework/mitre/baseline_stix/baseline_metadata.json
```

### Cache Version

Check downloaded cache version:
```bash
cat ~/.seceval/mitre/attack_enterprise_metadata.json
cat ~/.seceval/mitre/atlas_metadata.json
```

### Version Information

The metadata files contain:
- `last_updated`: Download/bundle timestamp
- `source_url`: Original MITRE source URL
- `version`: STIX spec version
- `technique_count`: Number of techniques
- `source_type`: 'attack' or 'atlas'

## Troubleshooting

### Issue: "No techniques loaded"

**Solution**: Check if baseline exists
```bash
ls -la framework/mitre/baseline_stix/
```

### Issue: "Download failed"

**Solution**: Framework will automatically fall back to baseline
- Check logs for fallback message
- Verify `use_bundled_fallback = true` in config
- Manually inspect baseline files

### Issue: "Outdated techniques"

**Solution**: Force cache refresh
```bash
# Delete cache
rm -rf ~/.seceval/mitre/

# Or set aggressive refresh
cache_refresh_hours = 24
```

### Issue: "Network timeout"

**Solution**: Use offline mode
```toml
[mitre]
auto_download = false  # Use baseline only
```

## Best Practices

1. **Development**: Use baseline for consistency
   ```toml
   auto_download = false
   ```

2. **CI/CD**: Use baseline for reproducibility
   ```toml
   auto_download = false
   ```

3. **Production**: Use weekly refresh for freshness
   ```toml
   auto_download = true
   cache_refresh_hours = 168
   ```

4. **Research**: Use monthly refresh for stability
   ```toml
   auto_download = true
   cache_refresh_hours = 720
   ```

## Data Sources & Credits

- **MITRE ATT&CK**: https://attack.mitre.org/
- **MITRE ATLAS**: https://atlas.mitre.org/
- **STIX Format**: https://oasis-open.github.io/cti-documentation/

All MITRE data is used under the [Apache 2.0 License](https://github.com/mitre/cti/blob/master/LICENSE.txt).

## Updating Baseline Data

To update the bundled baseline (maintainers only):

```bash
# Download latest MITRE data
cd framework/mitre/baseline_stix/

# Update ATT&CK
curl -o attack_enterprise_baseline.json \
  https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json

# Update ATLAS
curl -o atlas_baseline.json \
  https://raw.githubusercontent.com/mitre-atlas/atlas-data/main/dist/ATLAS.json

# Update metadata
python -c "
import json
from datetime import datetime

metadata = {
    'bundled_date': datetime.now().isoformat(),
    'attack_version': '15.1',
    'atlas_version': '4.6.0',
    'description': 'Baseline MITRE STIX data bundled with SecurityEvaluator'
}

with open('baseline_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)
"
```
