# Tips for optimizing your Codespaces experience

The Semantic Workbench project is optimized for use with GitHub Codespaces. The following tips will help you get the most out of your Codespaces experience.

## Prebuild the Codespace

To speed up the process of creating a Codespace, you can prebuild it. This will create a snapshot of the Codespace that can be used to quickly recreate it in the future. This is already enabled on the Semantic Workbench project, but the following steps will show you how to prebuild a Codespace in your own fork of the project.

To prebuild a Codespace:

- Navigate to your fork of the Semantic Workbench project
- Click on `Settings` for the repository
- Click on `Codespaces` in the left sidebar
- Click the `Set up prebuild` button
- Select the branch you want to prebuild (suggested: `main`, it should then apply to any branch built from `main`)
- [optional]
  - Change the options in `Region availability` to deselect all but the region closest to you
- Click the `Create` button

## Using a Dotfiles Repository for Codespaces Configuration

You can use a dotfiles repository to manage your Codespaces configuration. GitHub allows you to specify a repository that contains your dotfiles, which will be cloned into your Codespace when it is created. This is useful for managing your environment variables, shell configuration, editor settings, and other tools that you use in your Codespaces.

Suggested items for your dotfiles repository (so they are pre-loaded into all of your Codespaces)

- Set your environment variables in `.bashrc` or `.zshrc` instead of using the project `.env` files
- Set your editor settings in `.editorconfig` or `.vscode/settings.json`
- Set your .gitconfig to have your git settings, like your name and email, and any aliases you use

To use a dotfiles repository:

- Click on your profile picture in the top right corner of GitHub
- Click on `Settings`
- Click on `Codespaces` in the left sidebar
- Click the `Automatically install dotfiles` checkbox
- Choose your dotfiles repository from the dropdown
  - If not yet created, follow the link for `Learn how to set up your dotfiles for Codespaces` to set up a dotfiles repository
  - Alternatively, consider creating a new `dotfiles` repository exclusively for use with this project if you want to keep your personal dotfiles separate
