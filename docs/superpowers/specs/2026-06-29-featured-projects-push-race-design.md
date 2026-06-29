# Featured Projects Push Race Fix

## Problem

The workflow commits its generated README update successfully, but a concurrent
commit can reach `main` before the workflow pushes. GitHub then correctly rejects
the non-fast-forward push. The current pre-push rebase narrows this race window
but does not eliminate it.

## Design

Keep the existing workflow-level concurrency control and replace the single
rebase-and-push sequence with a bounded retry loop. Each attempt fetches the
latest remote `main`, rebases the generated commit onto it, and performs a normal
push. If the push loses another race, the workflow retries. It exits with a clear
error after three unsuccessful pushes.

The workflow will never force-push. Concurrent user commits therefore remain
protected. A genuine rebase conflict will stop the job immediately instead of
silently overwriting README content.

## Verification

Add a focused automated test that inspects the workflow and initially fails
because the retry behavior is absent. It will require:

- a bounded three-attempt loop;
- a fetch and rebase on every attempt;
- a normal push with success terminating the loop;
- a non-zero exit after the final rejected push;
- no force-push option.

Run the regression test, parse the workflow as YAML where tooling permits, and
run Python syntax validation for the generator.
