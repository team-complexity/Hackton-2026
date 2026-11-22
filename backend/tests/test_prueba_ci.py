"""Prueba que falla a propósito para comprobar que el CI bloquea el PR (spec 003, T014, CE-006).

Este archivo nunca se une a main: el PR se cierra sin unir y la rama se borra.
"""


def test_el_ci_bloquea_un_pr_con_una_prueba_que_falla() -> None:
    """Falla siempre, para ver `servidor` en rojo (spec 003, RF-036, RF-037)."""
    # Ruff rechaza `assert False` (B011) y el CI fallaría en el lint, no en pytest.
    assert 1 + 1 == 3, "Falla a propósito (T014): este PR no se debe poder unir."
