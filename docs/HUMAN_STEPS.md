# Human steps

These are the steps only Shreyas can do, in order. The build ran with no GitHub CLI, no tag pushes and no way to create `main`.

Release commit: `7cdf4ce32fc6bd2c445e98b3bc519f7c857ae7c1`

Branch: `claude/build-gatedmind`

1. Create `main` on GitHub from the branch's first commit, `4c0fc1a9bbb01b9313875ed5847806057efe9f3e`. On the repo page, open the branch menu, type `main` and pick "Create branch from claude/build-gatedmind", or run `git push origin 4c0fc1a9bbb01b9313875ed5847806057efe9f3e:refs/heads/main`. Then set `main` as the default branch in Settings, General.
2. Open a pull request from `claude/build-gatedmind` into `main`. Read the diff. Wait for the CI check to pass. Merge with a merge commit, so the release commit stays in the history of `main`.
3. Create the tag on the release commit:

   ```
   git fetch origin
   git tag -a v0.1.0-rc1 7cdf4ce32fc6bd2c445e98b3bc519f7c857ae7c1 -m "Release candidate 1"
   git push origin v0.1.0-rc1
   ```

   Or create a pre-release named `v0.1.0-rc1` on that commit on the Releases page.
4. Run the secret scan once more: `gitleaks git -v .` in a fresh clone.
5. Make the repo public. Done 2026-11-26: the repo is public.
6. Turn on Pages in Settings, Pages, from `main` and the `/docs` folder. The results page is `docs/index.html`.
7. Upload `docs/social-preview.png` in Settings, General, Social preview.
8. Fill in the About box with the text in `docs/GITHUB_ABOUT.md` and the topics in `docs/topics.txt`, if they are not already set.
9. Pin the repo on the profile, or list it in the profile README.
10. Publish to PyPI with trusted publishing, if you want the package on PyPI. Add a trusted publisher for `shreyas-tech7/gatedmind` at https://pypi.org/manage/account/publishing/ and add a release workflow. The name `gatedmind` was free on 2026-11-19.
11. Optional: run the benchmark with a real model. This build used a scripted model, so no provider key was needed. A real model run needs a provider key that you add yourself.
12. Decide whether `docs/build/BUILD_PROMPT.md` stays public.
13. Point the CI badge in the README at `main`. Done 2026-11-26.
14. Mark the human checks in the README as done once you have read the code and run `./init.sh` yourself.
