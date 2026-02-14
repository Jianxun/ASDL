# T-277 - extension worker integration

## Objective
Connect VS Code completion provider to the Python worker and add graceful
fallback suggestions when worker is unavailable.

## Constraints
- Keep editor responsive; avoid blocking UI on worker errors/timeouts.
- Preserve snippet/structural completions as fallback.

## DoD
- Completion provider routes requests to worker and maps results to VS Code items.
- Integration tests cover worker success and fallback paths.
