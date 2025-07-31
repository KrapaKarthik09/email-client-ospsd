---
name: Bug Report
about: Create a report to help us improve the email client
title: '[BUG] '
labels: ['bug', 'needs-triage']
assignees: ''
---

## Bug Description

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Initialize client with '...'
2. Call method '....'
3. With parameters '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Actual behavior**
A clear and concise description of what actually happened.

## Environment

**Component affected:**
- [ ] Email Client API (interface)
- [ ] Gmail Client Implementation  
- [ ] Email Analytics (if applicable)
- [ ] Integration/E2E tests
- [ ] Documentation
- [ ] CI/CD Pipeline

**System Information:**
- OS: [e.g. macOS 14.0, Ubuntu 22.04]
- Python version: [e.g. 3.11.5]
- Package version: [e.g. 0.1.0]
- Gmail API client version: [if applicable]

## Error Details

**Error message/traceback:**
```
Paste the full error message and traceback here
```

**Log output:**
```
Paste relevant log output here (remove sensitive information)
```

## Code Sample

**Minimal code to reproduce the issue:**
```python
# Paste minimal Python code that reproduces the issue
from gmail_client_impl import GmailClient
# ... rest of the code
```

**Configuration files (if relevant):**
```yaml
# Paste relevant configuration (pyproject.toml, .env.example, etc.)
# DO NOT include actual credentials or secrets
```

## Additional Context

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Related Issues**
Link to any related issues or discussions.

**Workaround**
If you found a temporary workaround, please describe it here.

**Impact**
- [ ] Blocks development
- [ ] Blocks testing
- [ ] Performance issue
- [ ] Documentation issue
- [ ] Minor inconvenience

## Checklist

- [ ] I have searched existing issues to ensure this is not a duplicate
- [ ] I have provided a minimal code example that reproduces the issue
- [ ] I have included all relevant error messages and logs
- [ ] I have removed any sensitive information (credentials, personal data)
- [ ] I have specified which component is affected
- [ ] I have tested with the latest version of the package
