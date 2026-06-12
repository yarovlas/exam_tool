from dataclasses import dataclass
from typing import Literal


ProductRole = Literal["required", "choice", "surprise"]


@dataclass(frozen=True)
class ProductGroupRule:
    role: ProductRole
    order: int
    label: str
    category: str | None


@dataclass(frozen=True)
class ProgramRules:
    program_code: str
    required_groups: tuple[ProductGroupRule, ...]
    choice_groups: tuple[ProductGroupRule, ...]


PROGRAM_RULES: dict[str, ProgramRules] = {
    "ZWBA": ProgramRules(
        program_code="ZWBA",
        required_groups=(
            ProductGroupRule("required", 1, "Gebak en Taarten", "Gebak en taarten ZWBA en ZWBB"),
            ProductGroupRule("required", 2, "Chocolade", "Chocolade ZWBA"),
        ),
        choice_groups=(
            ProductGroupRule("choice", 1, "Stukwerk beslag", "Stukwerk Beslag ZWBA/ZWBB"),
            ProductGroupRule("choice", 1, "Stukwerk korstdeeg", "Stukwerk Korst ZWBA/ZWBB"),
            ProductGroupRule("choice", 1, "Stukwerk zanddeeg", "Stukwerk Zand ZWBA/ZWBB"),
        ),
    ),
    "ZWBB": ProgramRules(
        program_code="ZWBB",
        required_groups=(
            ProductGroupRule("required", 1, "Gebak en Taarten", "Gebak en taarten ZWBA en ZWBB"),
            ProductGroupRule("required", 2, "Gistdeeg ongevuld grootbrood", "Gistdeeg Ong. Grootbrood ZWBR en ZWBB"),
        ),
        choice_groups=(
            ProductGroupRule("choice", 1, "Stukwerk beslag", "Stukwerk Beslag ZWBA/ZWBB"),
            ProductGroupRule("choice", 1, "Stukwerk korstdeeg", "Stukwerk Korst ZWBA/ZWBB"),
            ProductGroupRule("choice", 1, "Stukwerk zanddeeg", "Stukwerk Zand ZWBA/ZWBB"),
        ),
    ),
    "ZWBR": ProgramRules(
        program_code="ZWBR",
        required_groups=(
            ProductGroupRule("required", 1, "Gistdeeg ongevuld grootbrood", "Gistdeeg Ong. Grootbrood ZWBR en ZWBB"),
            ProductGroupRule("required", 2, "Gistdeegspecialiteiten", "Gistdeeg specialiteiten en gevuld brood"),
        ),
        choice_groups=(
            ProductGroupRule("choice", 1, "Getoerd gerezen", "Getoerd Gerezen"),
            ProductGroupRule("choice", 1, "Pizza", "Pizza"),
        ),
    ),
    "UBA": ProgramRules(
        program_code="UBA",
        required_groups=(
            ProductGroupRule("required", 1, "Gebak en Taarten", "Gebak en taarten UBB & UBA"),
        ),
        choice_groups=(
            ProductGroupRule("choice", 1, "Stukwerk beslag", "Stukwerk Beslag UBA"),
            ProductGroupRule("choice", 1, "Stukwerk korstdeeg", "Stukwerk Korst UBA"),
            ProductGroupRule("choice", 1, "Stukwerk zanddeeg", "Stukwerk Boterdeeg UBA"),
            ProductGroupRule("choice", 1, "Koek korstdeeg", "Koek Korst UBA"),
            ProductGroupRule("choice", 1, "Koek zanddeeg", "Koek Boterdeeg UBA"),
        ),
    ),
    "UBR": ProgramRules(
        program_code="UBR",
        required_groups=(
            ProductGroupRule("required", 1, "Gevuld kleinbrood", "Gevuld kleinbrood - UBR & UBB"),
        ),
        choice_groups=(
            ProductGroupRule("choice", 1, "Ongevuld zacht kleinbrood", "Ongevuld Zacht kleinbrood - UBR"),
            ProductGroupRule("choice", 1, "Ongevuld krokant kleinbrood", "Ongevuld Krokant kleinbrood - UBR"),
        ),
    ),
    "UBB": ProgramRules(
        program_code="UBB",
        required_groups=(
            ProductGroupRule("required", 1, "Gevuld kleinbrood", "Gevuld kleinbrood - UBR & UBB"),
            ProductGroupRule("required", 2, "Taarten en Gebak", "Gebak en taarten UBB & UBA"),
        ),
        choice_groups=(),
    ),
}


def get_program_rules(program_code: str) -> ProgramRules | None:
    return PROGRAM_RULES.get(program_code.upper())


def get_star_norms(program_code: str, phase: str) -> tuple[int, int]:
    is_advanced = phase == "Gevorderd"

    if program_code.upper().startswith("ZW"):
        return (8, 11) if is_advanced else (9, 12)

    return (5, 7) if is_advanced else (5, 8)
