# Independent pre-commit review

Status: all findings fixed; parent re-verification and the bounded final independent review passed. Review covered staged source, not a production release. It did not treat documented missing product features as regressions.

## Blocking findings

1. `check_integration.py`: default urllib transport can inherit an external proxy and carry the isolated session-token header to it. Use explicit no-proxy transport, parsed loopback-origin validation, and off-origin redirect rejection.
2. Both frontend adapters: Refresh keeps a stale selected activity run when another client advances it or a new-run response is lost. Reconcile or invalidate selection while preserving an uncertain submission's original identity.
3. `run.py`: a user-supplied relative Hermes source path is interpreted again after the child working directory changes. Resolve it before constructing the isolated environment.

## Narrow suggestions included in the fix scope

- Clear uncertain-delivery UI state when readback proves the exact submitted context/run/answer committed.
- Return a consistent client error for whitespace-only labels on `/start`, rather than an unhandled server error.

## Guardrails

The fix pass was limited to these issues, adding six stdlib Python regressions and six dependency-free renderer recovery checks. The parent reran all ten Python tests and all six renderer checks successfully. No new test framework was introduced.

The parent also re-staged and restarted only the owned test backend, verified exact restart state, passed all ten actual HTTP/registry checks using a relative source path, re-exercised real web recovery with an intentionally dropped successful response, and re-exercised read-only mounting/navigation in the real isolated Electron shell. Final screenshots were recaptured and adapter copies compared byte-for-byte. See [recovery evidence](recovery.json), [integration evidence](integration.json), and [desktop evidence](desktop.json).

The bounded re-review accepted the five application fixes and identified one CI-only dependency setup omission: the API regression imports FastAPI/Pydantic, but the clean runner did not provision them. A final narrow workflow fix provisions Python and the tested API dependencies. The parent verified all ten Python tests in a fresh venv with those dependencies installed. Final independent workflow review passed with empty security/error/suggestion lists. Pinned actions, read-only job permissions, and disabled checkout credential persistence were preserved. Full-product/manual limits remain unchanged.
