# Contributing to Polymarket-Kalshi Arbitrage Bot

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

### 1. Fork and Clone

```bash
git clone https://github.com/yourusername/polymarket-kalshi-arbitrage-bot.git
cd polymarket-kalshi-arbitrage-bot
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
# Install in development mode with dev dependencies
make install-dev

# Or manually:
pip install -e ".[dev]"
pre-commit install
```

## Development Workflow

### Code Style

We use:
- **Black** for code formatting (line length: 100)
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

### Running Checks

```bash
# Format code
make format

# Run linters
make lint

# Type checking
make type-check

# Run all checks
make check
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test
pytest tests/test_models.py -v
```

## Making Changes

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation
- `refactor/description` - Code refactoring
- `test/description` - Test additions

### Commit Messages

Follow conventional commits:

```
feat: Add support for new API endpoint
fix: Resolve issue with market matching
docs: Update README with new features
refactor: Improve error handling
test: Add tests for order validation
```

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Write or update tests
4. Ensure all checks pass: `make check`
5. Update documentation if needed
6. Submit a pull request with:
   - Clear description
   - Reference to related issues
   - Screenshots (if UI changes)

## Code Quality Standards

### Type Hints

Always use type hints:

```python
def calculate_profit(price: float, size: float) -> float:
    """Calculate profit."""
    return price * size
```

### Docstrings

Use Google-style docstrings:

```python
def process_order(order: Order) -> bool:
    """Process a trading order.
    
    Args:
        order: The order to process
        
    Returns:
        True if successful, False otherwise
        
    Raises:
        InvalidOrderError: If order is invalid
    """
    ...
```

### Error Handling

Use custom exceptions:

```python
from arbitrage_bot.exceptions import InvalidOrderError

if price <= 0:
    raise InvalidOrderError(f"Invalid price: {price}")
```

### Testing

- Write tests for all new features
- Aim for >80% code coverage
- Test edge cases and error conditions
- Use descriptive test names

## Project Structure

```
arbitrage_bot/
├── api/          # API clients
├── core/         # Core trading logic
├── models/       # Data models
├── ui/           # User interfaces
├── utils/        # Utilities
└── exceptions.py # Custom exceptions
```

## Areas for Contribution

### High Priority

- Market matching improvements
- Risk management enhancements
- Performance optimizations
- Test coverage improvements
- Documentation improvements

### Feature Ideas

- Support for additional platforms
- Machine learning for matching
- Advanced order types
- Backtesting framework
- Real-time alerting

## Questions?

- Open an issue for discussion
- Check existing issues and PRs
- Review code comments

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Respect different viewpoints

Thank you for contributing! 🚀
