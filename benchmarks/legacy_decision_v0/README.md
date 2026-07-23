# Legacy JSON Decision Benchmark

These assets support only the pre-migration scenario runner in `run.py`.
They are not part of the production maintenance lifecycle.

The production `maintenance_v1` contract has no output JSON schema, grammar,
cause vocabulary, or assistant text response. It provides one native
OpenAI-compatible function tool named `bash`; llama-server parses the model's
tool call into the response envelope.
