# CLI Commands

Manage plugins and inspect strutex from the command line.

!!! note "Requires cli extra"
`bash
    pip install strutex[cli]
    `

---

## Plugin Commands

### List Plugins

```bash
# List all plugins
strutex plugins list

# Filter by type
strutex plugins list --type provider

# JSON output for scripting
strutex plugins list --json

# Only show loaded plugins
strutex plugins list --loaded-only
```

**Output:**

```
PROVIDERS
----------------------------------------
  ✓ ● gemini               v1.0      priority: 50
       └─ capabilities: vision

VALIDATORS
----------------------------------------
  ✓ ○ invoice_validator    v1.0      priority: 60
```

**Legend:**

- `✓` = healthy, `✗` = unhealthy, `?` = unknown
- `●` = loaded, `○` = not loaded (lazy)

---

### Plugin Info

```bash
# Get detailed info about a plugin
strutex plugins info gemini --type provider

# JSON output
strutex plugins info gemini --type provider --json
```

**Output:**

```
Plugin: gemini
----------------------------------------
  version        : 1.0
  priority       : 50
  cost           : 1.0
  capabilities   : vision
  loaded         : True
  healthy        : True
```

---

### Refresh Discovery

```bash
# Re-scan entry points and refresh cache
strutex plugins refresh
```

Use after:

- Installing new plugins with pip
- Updating plugin packages
- Modifying entry points

---

### Cache Management

```bash
# Show cache status
strutex plugins cache

# Clear the cache
strutex plugins cache --clear
```

**Output:**

```
Cache file: /home/user/.cache/strutex/plugins.json
Cache valid: True
Cached plugins: 5
```

---

## Examples

### Find All Providers

```bash
strutex plugins list --type provider --json | jq '.provider[].name'
```

### Check Plugin Health

```bash
strutex plugins info gemini -t provider --json | jq '.healthy'
```

### List High-Priority Plugins

```bash
strutex plugins list --json | jq '.provider | sort_by(.priority) | reverse'
```

---

## Programmatic Equivalent

Every CLI command has a Python equivalent:

| CLI                           | Python                                            |
| ----------------------------- | ------------------------------------------------- |
| `strutex plugins list`          | `PluginRegistry.list_names("provider")`           |
| `strutex plugins info X`        | `PluginRegistry.get_plugin_info("provider", "X")` |
| `strutex plugins refresh`       | `PluginRegistry.discover(force=True)`             |
| `strutex plugins cache --clear` | `PluginDiscovery.clear_cache()`                   |

```python
from strutex.plugins import PluginRegistry
from strutex.plugins.discovery import PluginDiscovery

# List all providers
for name in PluginRegistry.list_names("provider"):
    info = PluginRegistry.get_plugin_info("provider", name)
    print(f"{name}: priority={info['priority']}")

# Clear cache
PluginDiscovery.clear_cache()
```
