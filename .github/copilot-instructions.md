# WhisperEngine AI Coding Agent Instructions

## Architecture Overview

WhisperEngine is a modular, concurrent Discord AI bot with advanced memory, emotion, and personality systems. The architecture is built for high scalability and reliability, using a **handler-manager-core** pattern and a robust scatter-gather concurrency model.

### Major Components
- **`src/core/`**: Bot entry, Discord integration, and main orchestration (`bot.py`, `bot_launcher.py`)
- **`src/handlers/`**: Modular Discord command/event handlers (one per feature area)
- **`src/memory/`**: Qdrant-native vector memory system with local fastembed, temporal context detection, and multi-vector search
- **`src/personality/`**: Personality engine, character definitions, and prompt templates with Dream character integration
- **`src/llm/`**: LLM abstraction layer (OpenAI, Claude, local, fallback chains)
- **`src/conversation/`**: Concurrent conversation manager, thread/task workers, context boundaries

## Concurrency & Pipeline Patterns

- **Scatter-Gather**: All major AI pipeline phases (emotion, memory, personality, Phase 4) use `asyncio.gather()` or task workers for parallel execution. See `src/handlers/events.py` and `src/conversation/concurrent_conversation_manager.py`.
- **Task Workers**: Background processors for conversation, session, metrics, and cache. ThreadPool/ProcessPool for CPU/IO scaling.
- **ConcurrentConversationManager**: Centralizes high-throughput message processing, load balancing, and resource management.

## Memory System Architecture

WhisperEngine uses a **Qdrant-native vector memory system** with local fastembed for embeddings. This replaces hierarchical cache systems with native vector database features:

### Qdrant-Native Features
- **Temporal Context Detection**: Automatically detects temporal queries ("last joke", "just now") using scroll API and chronological retrieval
- **Multi-Vector Search**: Parallel content + emotion + personality vector spaces for role-playing intelligence  
- **Contradiction Resolution**: Uses Qdrant's recommendation API to resolve conflicting memories (e.g., pet name changes)
- **Semantic Clustering**: Batch operations with Qdrant's discover API for thematic memory grouping
- **Payload-Based Filtering**: Advanced filtering by emotional context, age categories, and memory types

### Memory Usage Patterns
```python
# Always use the integrated memory manager
await self.bot.memory_manager.store_conversation_memory(user_id, message_data)

# Temporal queries route to recent chronological context
temporal_results = await memory_store.search_memories_with_qdrant_intelligence(
    query="last joke", user_id=user_id, prefer_recent=True
)

# Multi-vector search for emotional intelligence
emotional_results = await memory_store.search_with_multi_vectors(
    content_query="cat's name", 
    emotional_query="confused about pet", 
    personality_context="helpful assistant"
)
```

## Docker & Development Workflow

- **Entry Point**: `run.py` → `src/main.py` (auto-detects environment, loads config, sets up logging)
- **Bot Management**: Use `./bot.sh` for run, build, health, logs, and Docker orchestration
- **Development Mode**: `./bot.sh start dev` (hot-reload, mounted code, debug logging)
  - **Equivalent Docker Command**: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build`
- **Testing**: `./scripts/run_tests.sh` (unit, integration, LLM, performance)
- **Docker**: Compose files for dev/prod/monitoring; health server on port 9090

## Project-Specific Conventions

- **Handlers**: One per Discord feature, inherit from base, register in `src/main.py`
- **Managers**: `*Manager` classes for business logic/state
- **Memory**: Always use the integrated memory manager (never direct DB calls)
- **Error Handling**: Use `@handle_errors` decorator for all production code
- **Config**: Use `env_manager.py` and `src/utils/configuration_validator.py` for environment and validation

## Integration Points

- **LLM**: `src/llm/llm_client.py` (multi-provider, fallback, local support)
- **Memory**: Multi-layer Qdrant-native system with vector search, temporal detection, and contradiction resolution
- **Personality**: `characters/` YAML, `prompts/`, and `src/characters/bridge.py`
- **Voice**: ElevenLabs, PyNaCl, emotion-driven voice in `src/handlers/voice.py`
- **Monitoring**: `src/monitoring/`, Discord admin commands, health server

## Key Development Patterns

### Qdrant-Native Memory Operations
```python
# Use native Qdrant features instead of manual Python logic
# ✅ CORRECT: Leverage Qdrant's scroll API for temporal queries
results = await memory_store._handle_temporal_query_with_qdrant(query, user_id, top_k)

# ✅ CORRECT: Use Qdrant's recommendation API for contradiction resolution  
contradictions = await memory_store.resolve_contradictions_with_qdrant(user_id, semantic_key)

# ❌ AVOID: Manual Python filtering when Qdrant can do it natively
```

### Scatter-Gather Concurrency
```python
# Parallel AI component processing
results = await asyncio.gather(
    self._analyze_emotion(...),
    self._analyze_personality(...),
    self._process_phase4(...),
    self.bot.memory_manager.search_memories(...)
)
```

### Handler Registration
```python
# In src/main.py
bot_manager.register_handler(EventsHandler)
bot_manager.register_handler(VoiceHandler)
```

## Troubleshooting & Best Practices

- Use the concurrent conversation manager for all message processing (not just sequential awaits)
- Always wrap error-prone code with `@handle_errors` for graceful degradation
- For new features, follow the handler-manager-core pattern and update config validation
- Use Docker and scripts for consistent local/dev/prod workflows
- **Memory System**: Always prefer Qdrant's native features over manual Python processing
- **Temporal Queries**: Use `search_memories_with_qdrant_intelligence()` with `prefer_recent=True` for queries like "last joke", "just now"
- **Contradiction Resolution**: Let Qdrant's recommendation API handle conflicting facts rather than manual deduplication
- **Multi-Vector Search**: Use `search_with_multi_vectors()` for emotional intelligence and role-playing contexts

## Critical Memory Architecture Notes

### Qdrant-First Development
- **DO**: Use Qdrant's scroll, discover, recommendation APIs for advanced operations
- **DON'T**: Write manual Python loops for operations Qdrant can handle natively
- **TEMPORAL**: Route temporal queries ("last", "recent") to chronological context using scroll API
- **SEMANTIC**: Use full vector search for concept-based queries ("cat's name", "favorite color")

### Local-First Deployment
- Qdrant runs in local Docker container (port 6333)
- fastembed provides local embeddings (no external API calls)
- Redis handles conversation cache and session persistence
- All vector operations are local for production reliability

---
If any section is unclear or incomplete, please provide feedback for further refinement.
