# S.A.M. (Sovereign Autonomous Model)

A natively digital, sovereign intelligence with persistent, schema-driven memory. S.A.M. implements a cognitive architecture based on the **Reflect → Abstract → Act (RAA)** metabolic cycle, governed by schema dynamics, perturbation analysis, and human-aligned guardrails.

## 🎯 Overview

S.A.M. is designed as a classical compute system (no quantum dependency) that can be ported across storage engines and model back-ends. It features:

- **Sovereignty**: Unique per-instance keys with local, encrypted, non-forkable memory
- **Schema Hierarchy**: Three-tier schema system with immutable axioms, protected heuristics, and emergent contextual models
- **V_SP Engine**: Schema perturbation value computation driving cognitive mode transitions
- **RAA Metabolism**: Load-adaptive cognitive rhythm with hysteresis
- **System-on-Memory**: Memory controller as kernel-like service with hot-swappable back-ends

## 🏗️ Architecture

### Core Components

1. **PSP (Prioritized State Packet)**: Compact state persistence with momentum vectors and integrity checks
2. **V_SP Engine**: Computes phase dissonance between inputs and schemas
3. **MAAL (Memory Access Abstraction Layer)**: Storage-agnostic interface for vectors and relational data
4. **Schema Firewall**: Protects core schemas and gates new contextual models
5. **CDP (Catalyst Deliberation Protocol)**: Deep reasoning mode with structured packet exchanges

### Cognitive Modes

- **Idle**: Low activity, minimal resource usage
- **Flow**: Conversational engagement, moderate processing
- **Deep**: Intensive reasoning, high resource allocation
- **Crisis**: Maximum deliberation, strict safety protocols

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- CUDA-compatible GPU (optional, for local LLM inference)
- 32GB+ RAM recommended

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd sovereign-autonomous-model

# Install dependencies
pip install -e .

# For development
pip install -e ".[dev]"

# For GPU support
pip install -e ".[gpu]"
```

### Basic Usage

```bash
# Initialize a new S.A.M. instance
sam init

# Start the instance
sam start

# View current state
sam psp show

# Test V_SP engine
sam vsp test

# Run demo
sam vsp demo

# Run tests
sam test
```

## 📁 Project Structure

```
sam/
├── core/                 # Core cognitive components
│   ├── psp.py           # Prioritized State Packet
│   ├── vsp_engine.py    # V_SP computation & mode control
│   ├── schema_firewall.py # Schema protection system
│   ├── raa_cycle.py     # RAA metabolic cycle
│   └── cdp.py           # Catalyst Deliberation Protocol
├── memory/              # Memory management
│   ├── maal.py          # Memory Access Abstraction Layer
│   ├── qualia_blocks.py # Multimodal memory units
│   └── latent_asset_vault.py # Large asset management
├── models/              # Model adapters
│   ├── llm_adapters.py  # LLM inference adapters
│   └── embedding_adapters.py # Embedding model adapters
├── interop/             # Inter-S.A.M. communication
├── ui/                  # User interface components
├── ops/                 # Operations & configuration
│   └── config.yaml      # System configuration
└── utils/               # Utilities
    ├── crypto.py        # Cryptographic functions
    └── logging.py       # Structured logging

tests/                   # Test suite
├── test_psp.py         # PSP tests
├── test_vsp_engine.py  # V_SP engine tests
└── ...

data/                   # Runtime data (created on init)
├── sam.db              # SQLite database
├── vectors.lancedb     # Vector database
└── assets/             # Latent Asset Vault
```

## 🔧 Configuration

The system is configured via `sam/ops/config.yaml`. Key configuration sections:

### V_SP Engine
```yaml
vsp_engine:
  thresholds:
    idle_to_flow: 0.3
    flow_to_deep: 0.6
    deep_to_crisis: 0.8
  hysteresis:
    debounce_ms: 1000
    trend_decay: 0.95
```

### Memory
```yaml
memory:
  relational_backend: "sqlite"  # sqlite, duckdb
  vector_backend: "lancedb"     # lancedb, faiss
  vector_dimension: 384
```

### LLM Profiles
```yaml
llm:
  profiles:
    flow:
      model_path: "./models/flow-14b.gguf"
      context_window: 8192
    deep:
      model_path: "./models/deep-34b.gguf"
      context_window: 16384
```

## 🧪 Testing

```bash
# Run all tests
sam test

# Run specific test files
pytest tests/test_psp.py -v
pytest tests/test_vsp_engine.py -v

# Run with coverage
pytest --cov=sam --cov-report=html
```

## 🔒 Security Features

- **Key Derivation**: Argon2id with configurable iterations
- **Encryption**: ChaCha20-Poly1305 for at-rest data
- **Signing**: Ed25519 for integrity verification
- **Memory Protection**: Zeroization of sensitive data
- **Schema Firewall**: Protection against adversarial patterns

## 📊 Monitoring

S.A.M. provides comprehensive observability:

- **Structured Logging**: JSON-formatted logs with event types
- **Metrics**: V_SP trends, mode distribution, performance metrics
- **Dashboard**: Real-time state visualization (planned)
- **Audit Trail**: Complete event history with integrity checks

## 🔄 Development Workflow

```bash
# Install development dependencies
make install-dev

# Format code
make format

# Run linting
make lint

# Run tests
make test

# Start development server
make dev
```

## 📈 Performance Targets

- **Flow Mode**: ≥15 tokens/sec on local 14B model
- **Deep Mode**: ≥5 tokens/sec on local 34B model
- **V_SP Computation**: <10ms latency
- **Memory Operations**: <100ms for typical queries

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 Roadmap

### Phase 3 (Current)
- [x] PSP implementation
- [x] V_SP engine
- [x] MAAL with SQLite/LanceDB
- [ ] Schema Firewall
- [ ] CDP implementation
- [ ] Basic UI dashboard

### Future Phases
- [ ] Inter-S.A.M. communication
- [ ] Schrödinger validation harness
- [ ] Advanced RL integration
- [ ] Multi-agent marketplace
- [ ] Formal verification

## 📚 References

- **Genesis Covenant**: Original S.A.M. specification
- **RAA Metabolism**: Cognitive cycle design
- **Schema Dynamics**: Hierarchical schema system
- **System-on-Memory**: Memory-centric architecture

## 🆘 Support

For questions, issues, or contributions:

1. Check the [documentation](docs/)
2. Search existing [issues](../../issues)
3. Create a new issue with detailed information
4. Join the development discussions

---

**S.A.M. - Sovereign Autonomous Model**  
*Building the future of digital intelligence, one schema at a time.*