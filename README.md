# Success is not effect

**A success signal describes a step, not the outcome.** Exit code 0, HTTP 201,
"Published!": each says that something answered, not that the world is now the
way you wanted. This guide collects real cases where the signal and the effect
came apart, the shapes they share, and the checks that catch them.

It is written for people who build automations, scripts and AI agents. Agents
make this worse, because they read the success message and report it upward as
fact.

## The cases

All of these were reported in public, with details, by the people (and agents)
who hit them, and checked against their original reports. They are summarized
here as reported.

| Shape | What was reported | Signal | Effect |
|---|---|---|---|
| **Invalid input, accepted** | `icacls file /inheritance:r /grant:r group:(OI)(CI)F` on a *file*. Inheritance flags only make sense on folders | "Successfully processed 1 files", exit 0 | No ACE written. Inherited entries were already removed, so the file was left with an empty protected DACL, and even the owning administrator got *access denied* |
| **Success printed unconditionally** | A PowerShell migration called `ConvertFrom-SecureString` with a wrong parameter. A non-terminating error set the variable to null, and the script went on | "DPAPI blob written" | Wrote a 0-byte credential blob, then deleted the only plaintext copy |
| **Write accepted, field dropped** | Six replies posted to a forum API by a client that silently lost the parent id on the way | 201 each, body intact | All six landed as top-level comments. Only reading back `parent_id` and comparing it with the intended value caught it: a "missing?" check would not, since top-level comments read null too |
| **Accepted is not visible** | A post created as public; a reply reported as posted | `visibility: public` in the create response; "posted" | Read back 60 s later, the post was *unlisted*; the reply had been held back for a check |
| **Published is not served** | A static site deploy | "Success! - Published" | The domain is suspended unless an emailed verification link is clicked within 90 minutes |
| **Receipt before the thing exists** | A notarization API | 201 with a `proof_url` | The URL returned 404, still 404 three minutes later |
| **Counted, not written** | A document ingestion run | "3,314 chunks ingested", no error | Nothing was written, and for a while the only number anyone had was the one the writer printed |
| **Unknown names ignored** | A per-author filter tried as `author`, `agent`, `agent_id` and `pubkey`, on an API that only declares `authors` | 200 | Unfiltered rows every time, so the auditor concluded that no per-author filter existed. The API rejected bad *values* with 422 but never checked *names* |
| **The monitor died, the work did not** | A scheduler's heartbeat files | (silence) | Heartbeats stopped for 40 days while jobs kept running. Nobody noticed, because the live work looked like proof of life |
| **The verifier checks nothing** | A signature verifier read the key from `ed25519_public_key`; the API's field was `public_key` | "VERIFIED" | It found no keys, skipped every signature check, and passed anyway |

## What they have in common

1. **The signal comes from the same place as the action.** The tool that failed
   is the one telling you it succeeded.
2. **The signal is about the request, not the state.** "201" means "I accepted
   your request", not "the record now looks like what you sent".
3. **Nothing alerts, because nothing failed.** Silent failures do not show up as
   errors; they show up later as wrong data.

## The checks

### 1. Read back the effect, through a path you did not write
After a write, read the state back, and compare **the fields you meant to set**,
not just existence. A record existing proves less than you think:
[`examples/exists_is_not_created.py`](examples/exists_is_not_created.py) shows a
write that "succeeds" and reads back fine while writing nothing of yours.

```python
created = api.post("/comments", {"parent_id": pid, "body": text})
stored = api.get(f"/comments/{created['id']}")
assert stored["parent_id"] == pid, f"parent dropped: {stored['parent_id']!r}"
```

Prefer a read that does not depend on what the write returned: a search, a
listing, or an id you did not mint yourself.

### 2. Keep three claims apart
"The record exists", "my request created it" and "it stays available" are three
different facts. Log which one you actually checked.

### 3. Name the states, and never skip one
`sent` → `accepted` → `visible` → `verified`. Report the state you reached, not
the one you hoped for. "Posted" should mean visible to others, not "the API said
OK".

### 4. Make scripts fail loudly
Most "success printed anyway" bugs are an error that did not stop the script.

```bash
set -euo pipefail          # bash: stop on errors, unset variables and failed pipes
```

```powershell
$ErrorActionPreference = 'Stop'   # PowerShell: turn non-terminating errors into terminating ones
```

And never print a success message that a check did not earn.

### 5. Put the check outside the thing it checks
A check that shares the process, the clock or the success condition with the
work fails with it. Verify from a separate process, account or path.

### 6. Watch the watchers
Alert when a heartbeat goes *stale*, not only when it reports a failure. Give
every checker a positive control: a case you know must fail, planted on
purpose. A checker that has never failed may not be checking.

### 7. Check names as well as values
APIs that validate values strictly often accept any parameter name. Find out
which ones do with [silentparams](https://github.com/novasdiego1/silentparams), and treat filtered
results from them with suspicion.

## License

CC BY 4.0 for the text, MIT for the code in `examples/`.
