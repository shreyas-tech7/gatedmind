# Environment

Probed on 2026-11-20 with `curl -sS -o /dev/null -w '%{http_code}' -m 10 <url>`.

| Host | Answer | Used for |
| --- | --- | --- |
| https://huggingface.co | 000 (proxy CONNECT refused) | FastEmbed default model source (not reachable) |
| https://storage.googleapis.com | 400 (reachable) | Old FastEmbed mirror. Not needed |
| https://chroma-onnx-models.s3.amazonaws.com | 206 | all-MiniLM-L6-v2 ONNX archive, pinned by sha256 |
| https://pypi.org, https://registry.npmjs.org | reachable | Name checks and packages |
| https://api.groq.com, https://openrouter.ai | 000 (proxy CONNECT refused) | Record mode. Not needed: the brief uses a scripted model |
| https://api.osv.dev, https://semgrep.dev | 000 (proxy CONNECT refused) | Not used. pip-audit and ruff S rules instead |

A 3-document MiniLM embed worked on 2026-11-20 (shape 3 x 384).

Machine: Intel(R) Xeon(R) Processor @ 2.10GHz, 4 cores, 15 GB RAM, Python 3.13.18, uv 0.11.32,
FastEmbed 0.9.1, mcp 2.3.0. No provider key variables were set. Latency runs use 1 core
(one process, one query at a time).
