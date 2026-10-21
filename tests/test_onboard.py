import pytest

from keyglow.onboard import AUTOMATIC_SAVE, MANUAL_SAVE, MODE_SPECIFIC, PER_LED, Mode, can_save, plan

DIRECT = Mode("Direct", 32, PER_LED)
STATIC = Mode("Static", 64 | MANUAL_SAVE, MODE_SPECIFIC, 1, 1)
BREATHING = Mode("Breathing", 64 | MANUAL_SAVE, MODE_SPECIFIC, 1, 2)
RAINBOW = Mode("Rainbow Wave", 1 | MANUAL_SAVE)
CUSTOM = Mode("Custom", 32 | AUTOMATIC_SAVE, PER_LED)


def layer(effect, keys=None, **params):
    out = {"effect": effect, "params": params}
    if keys:
        out["keys"] = keys
    return out


def test_keyboard_without_save_support():
    assert not can_save([DIRECT])
    with pytest.raises(ValueError, match="can't store"):
        plan({"layers": [layer("solid", color="#ff0000")]}, [DIRECT])


def test_simple_effect_uses_equivalent_mode():
    p = plan({"layers": [layer("breathing", colors=["#ff0000", "#00ff00", "#0000ff"])]},
             [DIRECT, STATIC, BREATHING])
    assert p.mode == 2 and not p.per_led and p.manual_save
    assert p.colors == [(255, 0, 0), (0, 255, 0)]  # el modo admite dos colores
    assert plan({"layers": [layer("rainbow_wave")]}, [DIRECT, RAINBOW]).mode == 1


def test_complex_profile_falls_back_to_per_key():
    profile = {"layers": [layer("solid", color="#101010"), layer("solid", ["@wasd"], color="#ff0000")]}
    p = plan(profile, [DIRECT, STATIC, CUSTOM])
    assert p.mode == 2 and p.per_led and not p.manual_save


def test_no_matching_mode():
    with pytest.raises(ValueError, match="only store its own modes"):
        plan({"layers": [layer("fire")]}, [DIRECT, STATIC])
