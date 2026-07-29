# Development Guidelines

Welcome to the SaaS Platform project.

This project is built with a strong focus on **simplicity**, **maintainability**, and **production-ready quality**. Every architectural decision should favor clarity over unnecessary abstraction.

---

# Core Principles

## 1. Keep It Simple

Prefer the simplest solution that solves the problem well.

Avoid introducing new patterns, libraries, or abstractions unless they provide clear long-term value.

---

## 2. Build Incrementally

Development happens in small, testable steps.

Each step should:

- Have a single objective
- Be fully functional
- Be tested before moving forward
- End with a Git commit

Do not build multiple features in one iteration.

---

## 3. Production Quality from Day One

Temporary code has a habit of becoming permanent.

Every commit should be production quality.

Avoid:

- TODOs without issues
- Dead code
- Commented-out code
- Unused dependencies
- Placeholder implementations

---

## 4. Modular Monolith

This project follows a **Modular Monolith** architecture.

Everything runs inside a single backend application.

Do not introduce microservices unless there is a proven need.

---

## 5. Separation of Responsibilities

Each layer has a single responsibility.

```
API
    ↓
Service
    ↓
Repository
    ↓
Database
```

### API

- Receive requests
- Validate input
- Call services
- Return responses

### Service

- Business logic
- Validation
- Workflows
- Permissions

### Repository

- Database access only

### Models

- Database schema only

---

# Development Workflow

Every feature follows this process:

```
Planning
    ↓
Architecture Review
    ↓
Implementation
    ↓
Manual Review
    ↓
Testing
    ↓
Git Commit
    ↓
Documentation
```

Never skip testing.

---

# Project Structure

```
backend/
frontend/
docs/
```

Additional directories should only be added when needed.

Avoid creating folders for future ideas.

---

# Coding Standards

## General

- Prefer readability over cleverness.
- Write self-explanatory code.
- Keep functions small.
- Keep classes focused.
- Remove unused code immediately.

---

## Naming

### Python

- Files: snake_case.py
- Variables: snake_case
- Functions: snake_case
- Classes: PascalCase

### TypeScript

- Components: PascalCase
- Variables: camelCase
- Hooks: useSomething
- Files: PascalCase.tsx for components

### Environment Variables

```
UPPER_CASE
```

---

# Git Workflow

## Branches

```
main
develop
feature/*
```

---

## Commit Messages

Use Conventional Commits.

Examples:

```
feat: add workspace creation

fix: validate email input

refactor: simplify auth service

docs: update setup guide

test: add workspace tests

chore: initialize backend
```

---

# Testing

Every feature should be manually tested before committing.

When automated tests exist, they must pass before merging.

Never merge broken code.

---

# Documentation

Documentation evolves with the project.

Important architectural decisions should be recorded in:

```
docs/adr/
```

Documentation should explain **why**, not just **what**.

---

# Dependencies

Before adding a new dependency, ask:

- Can this be solved with existing tools?
- Is the dependency actively maintained?
- Does it significantly improve the project?
- Is the added complexity justified?

Avoid dependency bloat.

---

# AI Assistance

AI tools (Cursor, ChatGPT, etc.) are used as development assistants—not as decision makers.

Generated code must always be:

- Reviewed
- Understood
- Simplified when necessary
- Tested before committing

Never merge code you do not understand.

---

# Future-Proofing

Design for extension, not prediction.

Avoid building features for hypothetical future requirements.

Instead:

- Build the current requirement well.
- Extend when a real need appears.

---

# Open Source Philosophy

This project aims to become a reusable SaaS platform.

Every contribution should strive to be:

- Simple
- Well documented
- Maintainable
- Reusable
- Consistent

When in doubt, choose the simpler solution.