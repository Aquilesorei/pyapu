# CLI Commands

Manage plugins and inspect pyapu from the command line.

!!! note "Requires cli extra"
`bash
    pip install pyapu[cli]
    `

---

## Plugin Commands

### List Plugins

```bash
# List all plugins
pyapu plugins list

# Filter by type
pyapu plugins list --type provider

# JSON output for scripting
pyapu plugins list --json

# Only show loaded plugins
pyapu plugins list --loaded-only
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
pyapu plugins info gemini --type provider

# JSON output
pyapu plugins info gemini --type provider --json
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
pyapu plugins refresh
```

Use after:

- Installing new plugins with pip
- Updating plugin packages
- Modifying entry points

---

### Cache Management

```bash
# Show cache status
pyapu plugins cache

# Clear the cache
pyapu plugins cache --clear
```

**Output:**

```
Cache file: /home/user/.cache/pyapu/plugins.json
Cache valid: True
Cached plugins: 5
```

---

## Examples

### Find All Providers

```bash
pyapu plugins list --type provider --json | jq '.provider[].name'
```

### Check Plugin Health

```bash
pyapu plugins info gemini -t provider --json | jq '.healthy'
```

### List High-Priority Plugins

```bash
pyapu plugins list --json | jq '.provider | sort_by(.priority) | reverse'
```

---

## Programmatic Equivalent

Every CLI command has a Python equivalent:

| CLI                           | Python                                            |
| ----------------------------- | ------------------------------------------------- |
| `pyapu plugins list`          | `PluginRegistry.list_names("provider")`           |
| `pyapu plugins info X`        | `PluginRegistry.get_plugin_info("provider", "X")` |
| `pyapu plugins refresh`       | `PluginRegistry.discover(force=True)`             |
| `pyapu plugins cache --clear` | `PluginDiscovery.clear_cache()`                   |

```python
from pyapu.plugins import PluginRegistry
from pyapu.plugins.discovery import PluginDiscovery

# List all providers
for name in PluginRegistry.list_names("provider"):
    info = PluginRegistry.get_plugin_info("provider", name)
    print(f"{name}: priority={info['priority']}")

# Clear cache
PluginDiscovery.clear_cache()
```
