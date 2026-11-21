# Contributing

Thanks for looking. This is a small demo repo, so the rules are short.

1. Run `./init.sh` before and after your change. It must pass.
2. Write a test that fails first, then the code that makes it pass.
3. Never edit `data/seed*/`, the questions or a test to make code pass. Fix the code.
4. A leak in mode 1 or 2 is a bug in the enforcement code. Open an issue with the seed, the identity and the question.
5. Never type a number into the README. Run `gatedmind readme` and commit the result.
6. Keep secrets out. Run `gitleaks git --pre-commit --redact --staged --verbose` before you commit.
7. New ideas go to [docs/PROPOSALS.md](docs/PROPOSALS.md) first.
