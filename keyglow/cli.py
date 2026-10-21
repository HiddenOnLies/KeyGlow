"""KeyGlow command line interface."""

from __future__ import annotations

import argparse
import json
import sys

from . import effects
from . import exporters
from .importers import load_any
from .layout import BUILTIN, load_layout
from .profile import Profile, Renderer
from .retarget import retarget, to_portable

DEFAULT_LAYOUT = "alloy_origins_65"


def _prepare(src: str, layout_name: str, source_name: str | None, quiet: bool = False):
    profile = load_any(src)
    target = load_layout(layout_name)
    source_name = source_name or profile.designed_for or None
    source = None
    if source_name:
        try:
            source = load_layout(source_name)
        except ValueError:
            print(f"Warning: unknown source layout '{source_name}'; "
                  "the profile will be matched by key name only.", file=sys.stderr)
    profile, report = retarget(profile, target, source)
    notable = report.unknown or report.dropped or report.filled
    if not quiet and notable:
        origin = source.title if source else "unknown layout"
        print(f"Adapting '{profile.name}' from {origin} to {target.title}:", file=sys.stderr)
        for line in report.lines():
            print("  - " + line, file=sys.stderr)
    return profile, target


def cmd_layouts(a):
    for name, factory in BUILTIN.items():
        lay = factory()
        print(f"{name:18} {lay.title}")


def cmd_layout(a):
    lay = load_layout(a.name)
    if a.json:
        print(json.dumps(lay.to_dict(), indent=2))
        return
    from .backends.preview import render_ansi
    print(lay.title)
    print("\n".join(render_ansi(lay, {k: (60, 60, 70) for k in lay.ids})))


def cmd_effects(a):
    for name, defaults in effects.describe().items():
        doc = (effects.REGISTRY[name].__doc__ or "").strip().split("\n")[0]
        print(f"{name:13} {json.dumps(defaults, ensure_ascii=False)}")
        if doc:
            print(f"{'':13} {doc}")


def cmd_preview(a):
    from .backends.preview import export_html, play_terminal
    profile, target = _prepare(a.profile, a.layout, a.source)
    renderer = Renderer(profile, target)
    if a.html:
        export_html(renderer, a.html, seconds=a.seconds or 6)
        print(f"Preview saved to {a.html}")
    else:
        play_terminal(renderer, a.seconds)


def cmd_import(a):
    if a.portable:
        raw = load_any(a.source_file)
        profile = to_portable(raw, load_layout(a.source or raw.designed_for or a.layout))
    else:
        profile, _ = _prepare(a.source_file, a.layout, a.source)
    if a.name:
        profile.name = a.name
    profile.save(a.output)
    print(f"Profile saved to {a.output}")


def cmd_export(a):
    profile, target = _prepare(a.profile, a.layout, a.source, quiet=True)
    device = None
    if a.format == "openrgb" and not a.generic:
        try:
            from .backends.openrgb import OpenRGBKeyboard
            device = OpenRGBKeyboard(a.host, a.port, a.device).describe()
        except RuntimeError as e:
            print(f"OpenRGB not available ({e}); writing a generic keyboard instead.", file=sys.stderr)
    content = exporters.export(profile, target, a.format, a.at, device)
    out = a.output or exporters.filename(profile, a.format)
    with open(out, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    print(f"Exported '{profile.name}' as {exporters.FORMATS[a.format]} to {out}")


def cmd_apply(a):
    from .backends.openrgb import OpenRGBKeyboard, run
    profile, target = _prepare(a.profile, a.layout, a.source)
    kb = OpenRGBKeyboard(a.host, a.port, a.device)
    print(f"Applying '{profile.name}' to {kb.name} (Ctrl+C to stop)")
    if kb.unmapped:
        print(f"LEDs without a recognized key (they will stay off): {', '.join(kb.unmapped)}",
              file=sys.stderr)
    run(profile, target, kb, fps=a.fps, seconds=a.seconds)


def cmd_capture(a):
    from .backends.openrgb import OpenRGBKeyboard
    kb = OpenRGBKeyboard(a.host, a.port, a.device)
    keys = kb.capture()
    Profile(name=a.name or f"Capture of {kb.name}", designed_for=a.layout,
            layers=[{"effect": "static", "params": {"keys": keys}}]).save(a.output)
    print(f"{len(keys)} keys captured to {a.output}")


def cmd_probe(a):
    from .backends.hidprobe import probe
    devices = probe(a.all)
    if not devices:
        print("No HyperX/HP HID device found.")
    for d in devices:
        print(f"{d['vid_pid']}  {d['vendor']:16} {d['product']:30} "
              f"if={d['interface']} usage_page={d['usage_page']}")


def cmd_validate(a):
    profile, target = _prepare(a.profile, a.layout, a.source)
    Renderer(profile, target).frame(0)
    print(f"OK: '{profile.name}' ({len(profile.layers)} layers)")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="keyglow", description="RGB keyboard lighting with portable profiles")
    sub = p.add_subparsers(dest="cmd", required=True)

    def target_opts(sp):
        sp.add_argument("--layout", default=DEFAULT_LAYOUT,
                        help=f"target keyboard (default {DEFAULT_LAYOUT}) or path to a layout .json")
        sp.add_argument("--from", dest="source",
                        help="layout the profile was designed for (if the profile does not say)")

    def openrgb_opts(sp):
        sp.add_argument("--host", default="127.0.0.1")
        sp.add_argument("--port", type=int, default=6742)
        sp.add_argument("--device", default="", help="part of the keyboard name in OpenRGB")

    sp = sub.add_parser("layouts", help="list the built-in keyboards")
    sp.set_defaults(func=cmd_layouts)

    sp = sub.add_parser("layout", help="draw a layout or export it to JSON for editing")
    sp.add_argument("name")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_layout)

    sp = sub.add_parser("effects", help="list effects and their parameters")
    sp.set_defaults(func=cmd_effects)

    sp = sub.add_parser("preview", help="preview a profile without hardware")
    sp.add_argument("profile", help="file or URL")
    target_opts(sp)
    sp.add_argument("--seconds", type=float, default=0, help="animation length (0 = a single frame)")
    sp.add_argument("--html", help="export an animated HTML preview")
    sp.set_defaults(func=cmd_preview)

    sp = sub.add_parser("import", help="import a profile/map from another keyboard and adapt it")
    sp.add_argument("source_file", help="file or URL (.json, .csv)")
    sp.add_argument("-o", "--output", required=True)
    sp.add_argument("--name")
    sp.add_argument("--portable", action="store_true",
                    help="save by physical position (works on any keyboard)")
    target_opts(sp)
    sp.set_defaults(func=cmd_import)

    sp = sub.add_parser("export", help="export a profile for another program (OpenRGB, web, QMK, CSV)")
    sp.add_argument("profile", help="file or URL")
    sp.add_argument("--format", choices=list(exporters.FORMATS), default="openrgb")
    sp.add_argument("-o", "--output", help="output file (default: named after the profile)")
    sp.add_argument("--at", type=float, default=0, help="moment of the animation to export, in seconds")
    sp.add_argument("--generic", action="store_true",
                    help="for --format openrgb: don't read the real keyboard from OpenRGB")
    target_opts(sp)
    openrgb_opts(sp)
    sp.set_defaults(func=cmd_export)

    sp = sub.add_parser("apply", help="apply a profile to the real keyboard through OpenRGB")
    sp.add_argument("profile")
    target_opts(sp)
    openrgb_opts(sp)
    sp.add_argument("--fps", type=float, default=30)
    sp.add_argument("--seconds", type=float, default=0, help="0 = until Ctrl+C")
    sp.set_defaults(func=cmd_apply)

    sp = sub.add_parser("capture", help="save the keyboard's current colors as a profile")
    sp.add_argument("-o", "--output", required=True)
    sp.add_argument("--name")
    sp.add_argument("--layout", default=DEFAULT_LAYOUT)
    openrgb_opts(sp)
    sp.set_defaults(func=cmd_capture)

    sp = sub.add_parser("probe", help="look for HyperX keyboards over USB/HID")
    sp.add_argument("--all", action="store_true", help="show every HID device")
    sp.set_defaults(func=cmd_probe)

    sp = sub.add_parser("validate", help="check that a profile is valid")
    sp.add_argument("profile")
    target_opts(sp)
    sp.set_defaults(func=cmd_validate)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    for stream in (sys.stdout, sys.stderr):  # la consola de Windows no siempre es UTF-8
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    try:
        args.func(args)
    except (ValueError, RuntimeError, NotImplementedError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
