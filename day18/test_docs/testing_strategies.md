# Software Testing Strategies

## Types of Testing

### Unit Testing
Testing individual components or functions in isolation.

```python
def test_add_function():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0
```

**Best Practices:**
- Test one thing at a time
- Use descriptive test names
- Keep tests fast and independent
- Aim for high code coverage

### Integration Testing
Testing how different modules work together.

```python
def test_user_registration_flow():
    # Test database + API + email service
    user = register_user("test@example.com", "password123")
    assert user.id is not None
    assert email_service.sent_count == 1
```

### End-to-End Testing
Testing complete user workflows from start to finish.

```javascript
// Using Cypress
describe('Login Flow', () => {
  it('should login successfully', () => {
    cy.visit('/login')
    cy.get('#email').type('user@example.com')
    cy.get('#password').type('password123')
    cy.get('button[type="submit"]').click()
    cy.url().should('include', '/dashboard')
  })
})
```

## Test-Driven Development (TDD)

The TDD cycle:
1. **Red**: Write a failing test
2. **Green**: Write minimal code to pass
3. **Refactor**: Improve code quality

Benefits:
- Better code design
- Fewer bugs in production
- Living documentation
- Confidence to refactor

## Mocking and Stubbing

**Mock**: Fake object that verifies interactions
**Stub**: Fake object that returns predetermined responses

```python
from unittest.mock import Mock, patch

def test_api_call():
    mock_client = Mock()
    mock_client.get.return_value = {"status": "success"}

    result = process_api_data(mock_client)
    assert result["status"] == "success"
    mock_client.get.assert_called_once()
```

## Testing Pyramid

```
      /\
     /E2E\       <- Few, slow, expensive
    /------\
   /  INT   \    <- Moderate number
  /----------\
 / UNIT TESTS \  <- Many, fast, cheap
/--------------\
```

**Guidelines:**
- 70% Unit tests (fast, isolated)
- 20% Integration tests (medium speed)
- 10% E2E tests (slow, fragile)

## Code Coverage

Measure what percentage of code is executed during tests.

```bash
# Python
pytest --cov=myapp tests/

# JavaScript
npm test -- --coverage
```

**Important:** 100% coverage doesn't mean bug-free code! Focus on testing critical paths and edge cases.

## Common Testing Mistakes

1. **Testing implementation details** - Test behavior, not internals
2. **Slow tests** - Keep tests fast to run frequently
3. **Flaky tests** - Non-deterministic tests destroy trust
4. **No test data cleanup** - Each test should be independent
5. **Testing third-party code** - Mock external dependencies

## Continuous Testing

Integrate tests into CI/CD pipeline:

```yaml
# GitHub Actions
- name: Run tests
  run: |
    npm install
    npm test
    npm run test:integration
```

Run tests on:
- Every commit
- Pull requests
- Before deployment
- On schedule (nightly builds)
