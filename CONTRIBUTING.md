# Contributing to Semantic Workbench

You can contribute to the Semantic Workbench with issues and pull requests (PRs). Simply
filing issues for problems you encounter is a great way to contribute. Contributing
code is greatly appreciated.

## Reporting Issues

We always welcome bug reports, API proposals and overall feedback. Here are a few
tips on how you can make reporting your issue as effective as possible.

### Where to Report

New issues can be reported in our [list of issues](https://github.com/microsoft/semanticworkbench/issues).

Before filing a new issue, please search the list of issues to make sure it does
not already exist.

If you do find an existing issue for what you wanted to report, please include
your own feedback in the discussion. Do consider up-voting (👍 reaction) the original
post, as this helps us prioritize popular issues in our backlog.

### Writing a Good Bug Report

Good bug reports make it easier for maintainers to verify and root cause the
underlying problem.
The better a bug report, the faster the problem will be resolved. Ideally, a bug
report should contain the following information:

- A high-level description of the problem.
- A _minimal reproduction_, i.e. the smallest size of code/configuration required
  to reproduce the wrong behavior.
- A description of the _expected behavior_, contrasted with the _actual behavior_ observed.
- Information on the environment: OS/distribution, CPU architecture, SDK version, etc.
- Additional information, e.g. Is it a regression from previous versions? Are there
  any known workarounds?

## Contributing Changes

Project maintainers will merge accepted code changes from contributors.

### DOs and DON'Ts

DO's:

- **DO** clearly state on an issue that you are going to take on implementing it.
- **DO** follow the standard coding conventions

  - [Python](https://pypi.org/project/black/)
  - [Typescript](https://typescript-eslint.io/rules/)/[React](https://github.com/jsx-eslint/eslint-plugin-react/tree/master/docs/rules)
  - [.NET](https://learn.microsoft.com/dotnet/csharp/fundamentals/coding-style/coding-conventions)

- **DO** give priority to the current style of the project or file you're changing
  if it diverges from the general guidelines.
- **DO** include tests when adding new features. When fixing bugs, start with
  adding a test that highlights how the current behavior is broken.
- **DO** keep the discussions focused. When a new or related topic comes up
  it's often better to create new issue than to side track the discussion.
- **DO** blog and tweet (or whatever) about your contributions, frequently!

DON'Ts:

- **DON'T** surprise us with big pull requests. Instead, file an issue and start
  a discussion so we can agree on a direction before you invest a large amount of time.
- **DON'T** commit code that you didn't write. If you find code that you think is a good
  fit to add to Semantic Workbench, file an issue and start a discussion before proceeding.
- **DON'T** submit PRs that alter licensing related files or headers. If you believe
  there's a problem with them, file an issue and we'll be happy to discuss it.
- **DON'T** make new features, APIs, or services without filing an issue and discussing with us first.

### Breaking Changes

Contributions must maintain API signature and behavioral compatibility. Contributions
that include breaking changes will be rejected. Please file an issue to discuss
your idea or change if you believe that a breaking change is warranted.

### Suggested Workflow

We use and recommend the following workflow:

1. Create an issue for your work.
   - You can skip this step for trivial changes.
   - Reuse an existing issue on the topic, if there is one.
   - Get agreement from the team and the community that your proposed change is
     a good one.
   - Clearly state that you are going to take on implementing it, if that's the case.
     You can request that the issue be assigned to you. Note: The issue filer and
     the implementer don't have to be the same person.
2. Create a personal fork of the repository on GitHub (if you don't already have one).
3. In your fork, create a branch off of main (`git checkout -b my_branch`).
   - Name the branch so that it clearly communicates your intentions, such as
     "issue-123" or "github_handle-issue".
4. Make and commit your changes to your branch.
5. Add new tests corresponding to your change, if applicable.
6. Run the build and tests as described in the readme for the part(s) of the Semantic Workbench your changes impact to ensure that your build is clean and all tests are passing.
7. Create a PR against the repository's **main** branch.
   - State in the description what issue or improvement your change is addressing.
   - Verify that all the Continuous Integration checks are passing.
8. Wait for feedback or approval of your changes from the code maintainers.
9. When area owners have signed off, and all checks are green, your PR will be merged.

For a detailed walkthrough of this workflow, including how to set up forks and manage your Git workflow, refer to the [Detailed Workflow Walkthrough](#detailed-workflow-walkthrough) section.

### Adding Assistants

We appreciate your interest in extending Semantic Workbench's functionality through
providing assistants in the main repo. However, we want to clarify our approach to
our GitHub repository. To maintain a clean and manageable codebase we will not be
hosting assistants directly in the Semantic Workbench GitHub repository.
Instead, we encourage contributors to host their assistants in separate
repositories under their own GitHub accounts or organization. You can then
provide a link to your assistant repository in the relevant discussions, issues,
or documentation within the Semantic Workbench repository. This approach ensures
that each assistant can be maintained independently and allows for easier tracking
of updates and issues specific to each assistant. We will only provide a few assistants for demonstrating how to build your own in this repository.

### PR - CI Process

The continuous integration (CI) system will automatically perform the required
builds and run tests (including the ones you are expected to run) for PRs. Builds
and test runs must be clean.

If the CI build fails for any reason, the PR issue will be updated with a link
that can be used to determine the cause of the failure.

### Detailed Workflow Walkthrough

This detailed guide walks you through the process of contributing to our repository via forking, cloning, and managing your Git workflow.

Start by forking the repository on GitHub. This creates a copy of the repository under your GitHub account.

Clone your forked repository to your local machine:

```bash
git clone https://github.com/YOUR_USERNAME/semanticworkbench.git
cd semanticworkbench
```

Add the original repository as an upstream remote:

```bash
git remote add upstream https://github.com/microsoft/semanticworkbench.git
```

Check your remotes to ensure you have both `origin` and `upstream`:

```bash
git remote -v
```

You should see something like this:

```
origin    https://github.com/YOUR_USERNAME/semanticworkbench.git (fetch)
origin    https://github.com/YOUR_USERNAME/semanticworkbench.git (push)
upstream  https://github.com/microsoft/semanticworkbench.git (fetch)
upstream  https://github.com/microsoft/semanticworkbench.git (push)
```

To keep your fork updated with the latest changes from upstream, configure your local `main` branch to track the upstream `main` branch:

```bash
git branch -u upstream/main main
```

Alternatively, you can edit your `.git/config` file:

```ini
[branch "main"]
    remote = upstream
    merge = refs/heads/main
```

Before starting a new feature or bug fix, ensure that your fork is up-to-date with the latest changes from upstream:

```bash
git checkout main
git pull upstream main
```

Create a new branch for your feature or bug fix:

```bash
git checkout -b feature-name
```

Make your changes in the codebase. Once you are satisfied, add and commit your changes:

```bash
git add .
git commit -m "Description of your changes"
```

Push your changes to your fork:

```bash
git push origin feature-name
```

Go to your fork on GitHub, and you should see a `Compare & pull request` button. Click it and submit your pull request (PR) against the original repository’s `main` branch.

If there are changes in the main repository after you created your branch, sync them to your branch:

```bash
git checkout main
git pull upstream main
git checkout feature-name
git rebase main
```

Once your PR is merged, you can delete your branch both locally and from GitHub.

**Locally:**

```bash
git branch -d feature-name
```

**On GitHub:**
Go to your fork and delete the branch from the `Branches` section.
