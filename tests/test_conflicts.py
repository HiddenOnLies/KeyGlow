from keyglow.app import conflicts


def test_match_by_executable_name():
    assert conflicts.match(["explorer.exe", "LightingService.exe", "iCUE.exe", "ArmouryCrate.exe"]) == [
        "ASUS Armoury Crate", "ASUS Aura (Armoury Crate)", "Corsair iCUE"]


def test_with_a_keyboard_only_its_brand_matters():
    apps = ["ASUS Armoury Crate", "SteelSeries GG", "SignalRGB"]
    assert conflicts.for_keyboard(apps, "HyperX Alloy Origins 65 (HP)") == ["SignalRGB"]
    assert conflicts.for_keyboard(apps, "ASUS ROG Azoth 2.4GHz") == ["ASUS Armoury Crate", "SignalRGB"]


def test_process_list_works_here():
    assert isinstance(conflicts.process_names(), list)
