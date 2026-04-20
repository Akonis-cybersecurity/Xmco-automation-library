# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-20

### Added
- Initial release of the XMCO Yuno intake format.
- Parser for security advisory bulletins pushed by the XMCO Yuno connector.
- RFC2822 timestamp parsing for the `_created` field.
- ECS mapping: event.category=vulnerability, event.type=info for all advisory events.
- Fallback logic for event.reason: content_fr.title → content_en.title.
- vulnerability.* fields: severity, id (first CVE ref), description, scanner.vendor.
- rule.* fields: name, reference, description from advisory metadata.
- Custom fields under xmco.yuno.*: advisory_type, ref, vulnerable, exploitation_vector, damage, cve_refs, remediation.
- observer.vendor mapped from the advisory vendor field (e.g. REDHAT).
