# MITRE Baseline STIX Data

This directory contains **bundled baseline MITRE STIX data** that serves as a reliable fallback when fresh downloads are unavailable or disabled.

## Purpose

This baseline data ensures the SecurityEvaluator framework can operate **offline** and provides **reproducible results** independent of network connectivity or MITRE server availability.

## Contents

```
baseline_stix/
├── README.md                        # This file
├── attack_enterprise_baseline.json  # MITRE ATT&CK Enterprise
├── atlas_baseline.json              # MITRE ATLAS (AI/ML)
└── baseline_metadata.json           # Version and source info
```

## Data Sources

### MITRE ATT&CK Enterprise
- **File**: `attack_enterprise_baseline.json`
- **Version**: v15.1
- **Techniques**: 835
- **Source**: https://github.com/mitre/cti/blob/master/enterprise-attack/enterprise-attack.json
- **License**: Apache 2.0
- **Bundled Date**: 2025-11-13

### MITRE ATLAS
- **File**: `atlas_baseline.json`
- **Version**: v4.6.0
- **Techniques**: 140 (AI/ML specific)
- **Source**: https://github.com/mitre-atlas/atlas-data/blob/main/dist/ATLAS.json
- **License**: Apache 2.0
- **Bundled Date**: 2025-11-13

## When This Data Is Used

The framework automatically uses this baseline data when:

1. **Fresh downloads fail** (network timeout, MITRE servers down)
2. **Auto-download is disabled** (`auto_download = false` in config)
3. **Cache is invalid** (corrupted or incomplete files)
4. **Offline operation** (no network connectivity)
5. **First run** (before any cache exists)

## Fallback Behavior

```
┌─────────────────────────────────────────────┐
│  Try to load from cache (~/.seceval/mitre)  │
└──────────────────┬──────────────────────────┘
                   │
                   ├─ Cache exists & fresh?
                   │  └─ ✅ Use cached data
                   │
                   ├─ Cache expired & auto_download=true?
                   │  ├─ Download fresh data
                   │  ├─ Download successful? ✅ Use fresh data
                   │  └─ Download failed? ⬇️ Fall back to baseline
                   │
                   └─ No cache or auto_download=false?
                      └─ ⬇️ Use baseline data
```

## Version Information

Check the bundled version:
```bash
cat framework/mitre/baseline_stix/baseline_metadata.json
```

Example output:
```json
{
  "bundled_date": "2025-11-13T10:00:00",
  "attack_version": "15.1",
  "atlas_version": "4.6.0",
  "attack_techniques": 835,
  "atlas_techniques": 140,
  "description": "Baseline MITRE STIX data bundled with SecurityEvaluator"
}
```

## Updating Baseline (Maintainers Only)

To update the bundled baseline data:

```bash
cd framework/mitre/baseline_stix/

# Download latest ATT&CK Enterprise
curl -o attack_enterprise_baseline.json \
  https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json

# Download latest ATLAS
curl -o atlas_baseline.json \
  https://raw.githubusercontent.com/mitre-atlas/atlas-data/main/dist/ATLAS.json

# Update metadata
cat > baseline_metadata.json << 'EOF'
{
  "bundled_date": "2025-11-13T10:00:00",
  "attack_version": "15.1",
  "atlas_version": "4.6.0",
  "attack_source": "https://github.com/mitre/cti/blob/master/enterprise-attack/enterprise-attack.json",
  "atlas_source": "https://github.com/mitre-atlas/atlas-data/blob/main/dist/ATLAS.json",
  "description": "Baseline MITRE STIX data bundled with SecurityEvaluator",
  "license": "Apache 2.0"
}
EOF

# Commit to version control
git add .
git commit -m "Update MITRE baseline data to ATT&CK v15.1, ATLAS v4.6.0"
```

## Advantages of Bundled Baseline

### ✅ Reliability
- Always available (no network dependency)
- Guaranteed to work offline
- No download failures

### ✅ Reproducibility
- Same techniques across environments
- Version-controlled with package
- Consistent test results

### ✅ Speed
- Instant loading (no download time)
- No network latency
- Faster test execution

### ✅ Stability
- Known technique set
- No unexpected changes
- Predictable behavior

## Trade-offs

### ❌ Freshness
- Not the latest techniques
- Missing newest tactics
- Delayed updates

**Solution**: Enable auto-download for fresh data
```toml
[mitre]
auto_download = true
cache_refresh_hours = 168  # Weekly updates
```

### ❌ File Size
- Adds ~15MB to package
- Larger repository size

**Solution**: Acceptable trade-off for reliability

## Best Practices

### For Development
```toml
[mitre]
auto_download = false  # Use baseline for consistency
```

### For CI/CD
```toml
[mitre]
auto_download = false  # Use baseline for reproducibility
```

### For Production
```toml
[mitre]
auto_download = true   # Get latest techniques
cache_refresh_hours = 168  # Weekly refresh
use_bundled_fallback = true  # Fall back to baseline if needed
```

## File Format

Both files use the [STIX 2.0](https://oasis-open.github.io/cti-documentation/) format:

```json
{
  "type": "bundle",
  "id": "bundle--...",
  "spec_version": "2.0",
  "objects": [
    {
      "type": "attack-pattern",
      "id": "attack-pattern--...",
      "name": "Technique Name",
      "description": "...",
      "kill_chain_phases": [...],
      "x_mitre_platforms": [...],
      ...
    }
  ]
}
```

## Credits

- **MITRE Corporation** for ATT&CK and ATLAS frameworks
- Licensed under [Apache 2.0](https://github.com/mitre/cti/blob/master/LICENSE.txt)
- Learn more: 
  - https://attack.mitre.org/
  - https://atlas.mitre.org/
