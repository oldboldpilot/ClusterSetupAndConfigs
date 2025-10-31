# Default Branch Change Instructions

## Objective
Change the default branch of this repository from `main` to `master`.

## Why This Change?
The repository should use `master` as its default branch to align with project conventions and to ensure that users cloning the repository get the `master` branch by default.

## Current Status
- **Current default branch:** `main`
- **Desired default branch:** `master`
- Both branches currently point to the same commit: `48431b127773397fd7ee91904e18ffa8e0a0d583`

## How to Change the Default Branch

### Via GitHub Web Interface (Recommended)
1. Navigate to the repository on GitHub: https://github.com/oldboldpilot/ClusterSetupAndConfigs
2. Click on **Settings** (requires admin/owner access)
3. Click on **Branches** in the left sidebar
4. Under "Default branch", click the switch/swap icon next to the current default branch
5. Select `master` from the dropdown menu
6. Click **Update** to confirm the change
7. GitHub will show a warning about the implications - read and confirm

### Via GitHub CLI
If you have the GitHub CLI installed and authenticated:
```bash
gh repo edit oldboldpilot/ClusterSetupAndConfigs --default-branch master
```

### Via GitHub API
Using curl with a GitHub personal access token:
```bash
curl -X PATCH \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer YOUR_GITHUB_TOKEN" \
  https://api.github.com/repos/oldboldpilot/ClusterSetupAndConfigs \
  -d '{"default_branch":"master"}'
```

## Post-Change Verification
After changing the default branch, verify with:
```bash
git ls-remote --symref origin HEAD
```
This should show `master` as the HEAD reference.

## Impact
- New clones will automatically checkout the `master` branch
- GitHub will display the `master` branch by default in the web interface
- Pull requests will default to target the `master` branch
- Branch protection rules may need to be updated if they were configured for `main`

## Note
This repository's code does not hardcode branch names, so no code changes are required. All references to branches are dynamic or user-specified.
