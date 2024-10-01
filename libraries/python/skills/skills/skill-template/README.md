# Create a New Skill using this Template directory

## Getting Started

- Copy this directory to a new directory with the name of your new skill.

  - The name of this directory will be `<skill-name>-skill`. Be sure to use a hyphen.

- Rename the `your_skill` subdirectory.

  - The name of this directory will be `<skill_name>_skill`. Be sure to use an underscore.

- Open `pyproject.toml` to edit:

  - Update the `name = "your-skill"` to `name = "<skill-name>-skill"`. Be sure to use a hyphen. This will be the name of the skill package created and installed in the .venv directory of your new skill directory.
  - Update the `description = "MADE:Exploration Template-Rename skill"` to `description = "<Description of your skill>"`.
  - Add any other additional dependency packages under '[tool.poetry.dependencies]' section.

- Under your newly renamed `your_skill` subdirectory:

  - Open `skill.py`:
    - Update the class name to match the new skill name.
    - Update the `NAME`, `CLASS_NAME`, `DESCRIPTION`, and `INSTRUCTIONS`.
  - Open `__init__.py`:
    - Replace all instances of `YourSkill` with `<SkillName>Skill`.

- Confirm your new skill builds:

  - Open a terminal
    - Recommended `cmd` or `bash`, but `PowerShell` appears to work too.
  - From within the new skill directory, run `make`.
    - This will build the skill and install it in the `.venv` directory of your new skill directory.
  - Activate the .venv environment by running:
    - cmd: `.\.venv\Scripts\activate.bat`
    - bash: `source .venv/bin/activate`
    - PowerShell: `.\.venv\Scripts\Activate.ps1`
  - Reload the VS Code window (`ctrl+shift+p`, then type `Reload Window`).

## Next Steps

- Open `skill.py`:
  - Update the action(s) and routine(s).
  - Keep the chat driver code or comment it out if not using.
