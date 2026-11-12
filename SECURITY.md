# Security Policy

RINAVI is a privacy-first companion for government-service applications.
Security and privacy are the product, not a feature.

## Data policy

- This repository and its development environments contain **synthetic data
  only**. Never send real identity documents, real Aadhaar numbers, or other
  real personal data through issues, pull requests, or any repository channel.
- RINAVI never stores government-portal passwords, never requests Aadhaar
  OTPs or biometrics, and never submits applications on a citizen's behalf.
  If you believe any part of the system violates these boundaries, report it.

## Reporting a vulnerability

Use GitHub's **private vulnerability reporting**:

1. Go to the repository **Security** tab → **Report a vulnerability**.
2. Describe the issue, affected area (backend, web, storage, audit), and steps
   to reproduce with synthetic data.
3. You'll get an acknowledgement as soon as a maintainer triages it, and a
   status update when it is fixed or a disclosure decision is made.

Please do not open a public issue for security-sensitive findings.

## Supported versions

Only the current `main` branch is supported while RINAVI is pre-release.
