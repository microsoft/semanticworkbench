class Routine:
    def __init__(
        self,
        name: str,
        skill_name: str,
        description: str,
    ) -> None:
        self.name = name
        self.skill_name = skill_name
        self.description = description

    def fullname(self) -> str:
        return f"{self.skill_name}.{self.name}"

    def __str__(self) -> str:
        return self.fullname()
