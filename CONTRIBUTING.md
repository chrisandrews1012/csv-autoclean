# Contributing

This repo uses a lightweight Gitflow: `main` is the release branch, `dev` is
the integration branch. Every change is traceable end to end: issue →
branch → PR → merge → issue closed.

## Workflow

1. **File an issue first.** No branch gets cut for untracked work, even
   small fixes get an issue, so history stays traceable. Use the issue
   template; pick a `Type` (fix / feature / chore / docs / refactor).
2. **Branch naming**: `<type>/<issue#>-<kebab-topic>`, cut from `origin/dev`.
   Example: `fix/5-streamable-http-client-rename`.
3. **Commit messages** follow [Conventional Commits](https://www.conventionalcommits.org/):

   ```
   type(scope): imperative summary
   ```

   - `type` matches the branch type.
   - `scope` is the area of the codebase touched (not the issue number).
   - Lowercase, imperative mood, no trailing period.
   - Don't put `Closes #N` in the commit body, that belongs in the PR only.

4. **Open a PR into `dev`**, not `main`, using the PR template. Fill in the
   real diff summary and test evidence; don't leave the template's HTML
   comments unfilled.
5. **Merge strategy is squash merge.** The PR's commits get collapsed into
   one commit on `dev`.
6. **After merging**, the linked issue is closed explicitly (not left to
   auto-close, since `dev` isn't the repo's default branch) and the branch
   is deleted once confirmed.

## Local setup

This is a [uv](https://docs.astral.sh/uv/)-managed Python project targeting
3.11, laid out under `src/`.

```bash
uv sync
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg
```

## Checks

- **Lint/format**: `uv run ruff check .` / `uv run ruff format .`
- **Types**: `uv run mypy .` (strict mode)
- **Tests**: `uv run pytest`

All of the above also run automatically via pre-commit on `git commit`.
Commits are never pushed with `--no-verify`; if a hook is wrong, fix the
hook, don't bypass it.
