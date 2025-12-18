# Security Policy

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not** open a public issue. Instead, please email the maintainers directly at [security@example.com] (replace with actual email).

Please include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will respond within 48 hours and work with you to address the issue.

## Security Best Practices

When using this bot:

1. **Never commit API keys or private keys** to version control
2. **Use environment variables** for sensitive configuration
3. **Start in dry-run mode** to test before live trading
4. **Use small amounts** initially
5. **Monitor actively** - don't leave unattended
6. **Keep dependencies updated** regularly
7. **Review code changes** before deploying

## Known Security Considerations

- API keys and private keys are sensitive - handle with care
- Trading involves financial risk - use at your own discretion
- Network communication should use HTTPS/WSS where possible
- Rate limiting is implemented to prevent abuse

---

**Remember**: Security is everyone's responsibility. If you see something, say something.

