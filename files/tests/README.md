# File Manager Tests

## Running Tests

### All tests
```bash
python manage.py test files/tests/
```

### With pytest
```bash
pytest files/tests/ -v
```

### With coverage
```bash
pytest files/tests/ --cov=files --cov-report=html
```

### Specific test files
```bash
# Validators
pytest files/tests/test_validators.py -v

# Models
pytest files/tests/test_models.py -v

# Admin
pytest files/tests/test_admin.py -v

# Integration
pytest files/tests/test_integration.py -v

# Management commands
pytest files/tests/test_management_commands.py -v

# Performance
pytest files/tests/test_performance.py -v
```

### Fast tests only (exclude slow tests)
```bash
pytest files/tests/ -m "not slow"
```

## Test Structure

```
tests/
├── __init__.py
├── fixtures.py                      # Test data generators
├── test_validators.py               # Validator tests (64 tests)
├── test_models.py                   # Model tests (72 tests)
├── test_admin.py                    # Admin tests (40 tests)
├── test_integration.py              # Integration tests (28 tests)
├── test_management_commands.py      # Command tests (24 tests)
└── test_performance.py              # Performance tests (20 tests)
```

Total: **248 comprehensive tests**

## Coverage Goals

- Overall: > 90%
- Models: > 95%
- Validators: > 95%
- Admin: > 85%

## Writing New Tests

1. Use fixtures from `fixtures.py` for test data
2. Follow naming convention: `test_<what>_<scenario>`
3. Add docstrings explaining what test validates
4. Use appropriate assertions
5. Mock external dependencies (storage, etc.)

## Continuous Integration

Tests run automatically on:
- Every push to main/develop
- Every pull request
- Multiple Python versions (3.10-3.14)
- Multiple Django versions (5.2.12-6.0.3)
