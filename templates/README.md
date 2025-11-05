# Cluster Configuration Templates

## Purpose
This directory contains **cluster infrastructure configuration templates** used by `config_template_manager.py` to set up the HPC cluster environment. These are system-level configuration files for runtime environments, SSH, and workload managers.

**For benchmark-related templates** (source code, runtime configs, build systems), see `cluster_modules/templates/`.

## Directory Structure

```
templates/
├── mpi/                      # MPI runtime configuration
│   ├── hostfile.j2           # MPI hostfile template
│   └── mca-params.conf.j2    # OpenMPI MCA parameters
├── ssh/                      # SSH configuration
│   ├── config.j2             # SSH client configuration
│   └── setup_keys.sh.j2      # SSH key setup automation
├── slurm/                    # Slurm workload manager
│   └── slurm.conf.j2         # Slurm configuration
└── README.md                 # This file
```

## Template Categories

### 1. MPI Configuration (`mpi/`)
**Purpose:** MPI runtime environment configuration  
**Used by:** `config_template_manager.py`

**Templates:**
- **hostfile.j2** - MPI hostfile generation
  - Node listing with CPU slots
  - Process placement
  
- **ssh/** - SSH client configuration
  - Host aliases
  - Connection parameters
  - Key management
  
- **slurm/** - Workload manager configuration
  - Node definitions
  - Partition setup
  - Resource limits

### 2. Benchmark Templates (`cluster_modules/templates/`)
**Purpose:** Source code templates for performance benchmarks  
**Used by:** `benchmark_manager.py`  
**Location:** `cluster_modules/templates/` directory

**Categories:**

#### Benchmarks by Framework
- **benchmarks/upcxx/** - UPC++ PGAS benchmarks
  - Point-to-point latency
  - Bandwidth measurements
  
- **benchmarks/mpi/** - MPI parallel benchmarks
  - Latency tests
  - Communication patterns
  
- **benchmarks/openshmem/** - OpenSHMEM PGAS benchmarks
  - PUT/GET operations
  - Latency measurements
  
- **benchmarks/berkeley_upc/** - Berkeley UPC benchmarks
  - Shared memory operations
  - Latency tests
  
- **benchmarks/openmp/** - OpenMP shared memory benchmarks
  - Parallel regions
  - Thread scaling
  
- **benchmarks/hybrid/** - Hybrid MPI+OpenMP benchmarks
  - Multi-level parallelism
  - Combined scaling tests

#### Build System Templates
- **build/** - Build and execution templates
  - Makefile generation
  - Benchmark runner scripts

## Usage

### Configuration Templates
```bash
# Generate and deploy MPI configuration
uv run python cluster_modules/config_template_manager.py generate mpi-mca
uv run python cluster_modules/config_template_manager.py deploy mpi-mca

# Generate hostfile
uv run python cluster_modules/config_template_manager.py generate mpi-hostfile
```

### Benchmark Templates
```python
from cluster_modules.benchmark_manager import BenchmarkManager

# Create manager
mgr = BenchmarkManager(
    username="user",
    password="",
    master_ip="192.168.1.136",
    worker_ips=["192.168.1.139", "192.168.1.96"]
)

# Generate benchmarks from templates
mgr.create_upcxx_latency_benchmark()
mgr.create_mpi_latency_benchmark()
mgr.create_makefile()
mgr.create_run_script()
```

## Template Naming Convention

### Configuration Templates
Format: `<component>.j2` or `<component>.<ext>.j2`

Examples:
- `hostfile.j2` - Simple filename
- `mca-params.conf.j2` - With extension
- `config.j2` - Generic configuration

### Benchmark Templates
Format: `<framework>_<benchmark_type>.<ext>.j2`

Examples:
- `upcxx_latency.cpp.j2` - UPC++ latency benchmark (C++)
- `mpi_latency.cpp.j2` - MPI latency benchmark (C++)
- `berkeley_upc_latency.c.j2` - Berkeley UPC benchmark (C)
- `Makefile.j2` - Build system template
- `run_benchmarks.sh.j2` - Shell script template

## Adding New Templates

### Adding a Configuration Template
1. Create template in appropriate `templates/` subdirectory
2. Add generation logic to `config_template_manager.py`
3. Add deployment logic if needed
4. Update documentation

### Adding a Benchmark Template
1. Create template in appropriate `cluster_modules/templates/benchmarks/` subdirectory
2. Add creation method to `benchmark_manager.py`
3. Follow naming convention: `<framework>_<type>.<ext>.j2`
4. Update Makefile and run script templates if needed

## Template Best Practices

### 1. Use Clear Variable Names
```jinja
{# Good #}
{% for node in cluster_nodes %}
  {{ node.hostname }} slots={{ node.cpus }}
{% endfor %}

{# Avoid #}
{% for n in nodes %}
  {{ n.h }} slots={{ n.c }}
{% endfor %}
```

### 2. Add Comments
```jinja
{# Network configuration for multi-homed nodes #}
{% if use_exact_ips %}
btl_tcp_if_include = {{ cluster_ips_cidr }}
{% endif %}
```

### 3. Provide Defaults
```jinja
{% set timeout = timeout | default(60) %}
{% set iterations = iterations | default(1000) %}
```

### 4. Use Conditionals for Flexibility
```jinja
{% if enable_feature %}
# Feature enabled
feature_param = {{ feature_value }}
{% endif %}
```

### 5. Keep Templates Focused
- One template per configuration file
- Separate concerns (MPI, SSH, Slurm)
- Group related benchmarks

## Maintenance

### Regular Tasks
- Review template organization quarterly
- Update templates when frameworks are upgraded
- Remove obsolete templates
- Document template parameters

### Version Control
- All templates are in git
- Use meaningful commit messages
- Review template changes carefully
- Test generated output before committing

## Related Documentation
- `docs/configuration/TEMPLATE_SYSTEM.md` - Template system usage
- `QUICK_REFERENCE.md` - Common workflows
- `docs/development/DEVELOPMENT_LOG.md` - Development history
