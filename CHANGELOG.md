# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [1.0.0] - 2025-12-27

### Added
- Deterministic irrigation planning endpoint (`POST /irrigation/plan`)
- AI agent orchestration endpoint (`POST /agent/run`) using Google Gemini 2.5 Flash
- SQLite cache for forecast data with offline mode support
- Geospatial nearest-point selection (Haversine distance)
- FAO-56 stage-based crop coefficient catalog (5 crops: tomato, pepper, avocado, citrus, cucumber)
- Plant profile support (herbs, succulents, houseplants, etc.)
- Comprehensive test suite with token-safe LLM testing (opt-in only)
- FastAPI production-quality API layer with error handling, rate limiting, and CORS
- Demo scenarios and smoke test script

### Technical Details
- Pure domain engine (deterministic, no I/O)
- MoAG forecast adapter with retry logic and Chrome-like headers
- Strands agent framework with structured output
- Pydantic-based request/response validation
- Quality gates: ruff linting, pytest test suite

