# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

## 2026-04-20 - 1.0.0

### Added

- Initial release of the XMCO Yuno connector
- YunoAdvisoryConnector: periodic pull of advisory bulletins with severity filter and cursor-based pagination
- YunoTicketConnector: periodic pull of Yuno tickets with cursor-based pagination
- GetAdvisoryAction: retrieve an advisory bulletin by ID
- GetVulnerabilityAction: retrieve a vulnerability by ID
- GetCVEAction: retrieve a CVE by ID
- GetFollowedCpeNameAction: list followed CPE technology names
- UpdateYunoTicketAction: update status and severity of a Yuno ticket (with If-Match ETag support)
