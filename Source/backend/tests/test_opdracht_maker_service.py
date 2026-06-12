"""
Unit tests for app/services/opdracht_maker.py

Tests worden uitgevoerd zonder database — alleen pure Python logica.
"""

import pytest
from app.services.opdracht_maker import (
    PROGRAM_RULES,
    ProgramRules,
    get_program_rules,
    get_star_norms,
)


# ---------------------------------------------------------------------------
# get_program_rules
# ---------------------------------------------------------------------------


class TestGetProgramRules:
    def test_returns_rules_for_known_programs(self):
        for code in ("ZWBA", "ZWBB", "ZWBR", "UBA", "UBR", "UBB"):
            rules = get_program_rules(code)
            assert rules is not None, f"Expected rules for {code}"
            assert isinstance(rules, ProgramRules)

    def test_case_insensitive(self):
        assert get_program_rules("zwba") is not None
        assert get_program_rules("Zwba") is not None
        assert get_program_rules("ZWBA") is not None

    def test_returns_none_for_unknown_program(self):
        assert get_program_rules("XYZ") is None
        assert get_program_rules("") is None
        assert get_program_rules("zwbc") is None

    def test_zwba_has_two_required_groups(self):
        rules = get_program_rules("ZWBA")
        assert len(rules.required_groups) == 2

    def test_zwba_has_three_choice_groups(self):
        rules = get_program_rules("ZWBA")
        assert len(rules.choice_groups) == 3

    def test_ubb_has_no_choice_groups(self):
        """UBB mag geen keuze-opdracht insturen."""
        rules = get_program_rules("UBB")
        assert len(rules.choice_groups) == 0

    def test_required_groups_have_unique_orders(self):
        """Elk verplicht slot moet een unieke volgorde-index hebben."""
        for code, rules in PROGRAM_RULES.items():
            orders = [g.order for g in rules.required_groups]
            assert len(orders) == len(set(orders)), (
                f"Duplicate required-group orders for {code}: {orders}"
            )

    def test_all_groups_have_non_empty_category(self):
        """Elke groep met producten moet een categorie hebben."""
        for code, rules in PROGRAM_RULES.items():
            for group in (*rules.required_groups, *rules.choice_groups):
                assert group.category, (
                    f"Group '{group.label}' in {code} has no category"
                )


# ---------------------------------------------------------------------------
# get_star_norms
# ---------------------------------------------------------------------------


class TestGetStarNorms:
    def test_zwba_gevorderd(self):
        assert get_star_norms("ZWBA", "Gevorderd") == (8, 11)

    def test_zwba_competent(self):
        assert get_star_norms("ZWBA", "Competent") == (9, 12)

    def test_zwba_herkansing_competent(self):
        assert get_star_norms("ZWBA", "Herkansing Competent") == (9, 12)

    def test_zwbb_gevorderd(self):
        assert get_star_norms("ZWBB", "Gevorderd") == (8, 11)

    def test_zwbr_competent(self):
        assert get_star_norms("ZWBR", "Competent") == (9, 12)

    def test_uba_gevorderd(self):
        assert get_star_norms("UBA", "Gevorderd") == (5, 7)

    def test_uba_competent(self):
        assert get_star_norms("UBA", "Competent") == (5, 8)

    def test_ubr_gevorderd(self):
        assert get_star_norms("UBR", "Gevorderd") == (5, 7)

    def test_ubb_competent(self):
        assert get_star_norms("UBB", "Competent") == (5, 8)

    def test_min_regular_lte_min_total(self):
        """min_regular mag nooit groter zijn dan min_total."""
        for code in ("ZWBA", "ZWBB", "ZWBR", "UBA", "UBR", "UBB"):
            for phase in ("Gevorderd", "Competent"):
                min_reg, min_tot = get_star_norms(code, phase)
                assert min_reg <= min_tot, (
                    f"{code}/{phase}: min_regular ({min_reg}) > min_total ({min_tot})"
                )

    def test_norms_are_positive(self):
        for code in ("ZWBA", "ZWBB", "ZWBR", "UBA", "UBR", "UBB"):
            for phase in ("Gevorderd", "Competent"):
                min_reg, min_tot = get_star_norms(code, phase)
                assert min_reg > 0
                assert min_tot > 0
