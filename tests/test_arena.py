"""Tests for Coding Arena Engine and APIs."""

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import (
    app,
    SessionLocal,
    get_arena_capabilities,
    get_arena_templates,
    validate_arena_code,
    run_arena,
    ArenaRunIn,
    ArenaValidateIn,
)
from runner.arena_executor import detect_arena_target, execute_arena_code


def test_detect_arena_target():
    assert detect_arena_target("print('Hello')", "Python") == "console"
    assert detect_arena_target("import turtle\nt = turtle.Turtle()", "Python") == "turtle"
    assert detect_arena_target("from turtle import *", "Python") == "turtle"
    assert detect_arena_target("import tkinter as tk\nroot = tk.Tk()", "Python") == "tkinter"
    assert detect_arena_target("import pygame\npygame.init()", "Python") == "pygame"
    assert detect_arena_target("<h1>Hello</h1>", "HTML/CSS/JS") == "web"


def test_execute_console():
    res = execute_arena_code("print('Line 1')\nprint('Line 2')")
    assert res["status"] == "succeeded"
    assert res["mode"] == "console"
    assert "Line 1\nLine 2" in res["output"]


def test_execute_turtle_spiral():
    code = """import turtle
t = turtle.Turtle()
t.color('#f45b4f')
for _ in range(4):
    t.forward(50)
    t.right(90)
"""
    res = execute_arena_code(code)
    assert res["status"] == "succeeded"
    assert res["mode"] == "gui"
    assert res["gui_target"] == "turtle"
    assert res["gui_payload"] is not None
    assert len(res["gui_payload"]["actions"]) == 4


def test_execute_tkinter_app():
    code = """import tkinter as tk
root = tk.Tk()
root.title('Test App')
root.geometry('300x200')
lbl = tk.Label(root, text='Score: 0')
lbl.pack()
btn = tk.Button(root, text='Increment')
btn.pack()
entry = tk.Entry(root)
entry.pack()
"""
    res = execute_arena_code(code)
    assert res["status"] == "succeeded"
    assert res["mode"] == "gui"
    assert res["gui_target"] == "tkinter"
    assert res["gui_payload"]["title"] == "Test App"
    assert len(res["gui_payload"]["widgets"]) == 3


def test_execute_pygame_simulation():
    code = """import pygame
pygame.init()
screen = pygame.display.set_mode((480, 320))
screen.fill((20, 20, 25))
pygame.draw.rect(screen, (40, 150, 90), (200, 280, 80, 10))
pygame.draw.circle(screen, (244, 91, 79), (240, 100), 12)
"""
    res = execute_arena_code(code)
    assert res["status"] == "succeeded"
    assert res["mode"] == "gui"
    assert res["gui_target"] == "pygame"
    assert len(res["gui_payload"]["draw_commands"]) == 3


def test_capabilities_endpoint():
    cap = get_arena_capabilities()
    assert "turtle" in [t["id"] for t in cap["gui_targets"]]
    assert "tkinter" in [t["id"] for t in cap["gui_targets"]]
    assert "pygame" in [t["id"] for t in cap["gui_targets"]]
    assert len(cap["standalone_editors"]) >= 4


def test_templates_endpoint():
    tmpl = get_arena_templates()
    assert len(tmpl["items"]) >= 7
    targets = {t["gui_target"] for t in tmpl["items"]}
    assert "turtle" in targets
    assert "tkinter" in targets
    assert "pygame" in targets


def test_validate_endpoint():
    good = validate_arena_code(ArenaValidateIn(language="Python", code="x = 10\nprint(x)"))
    assert good["valid"] is True
    assert good["detected_target"] == "console"

    bad = validate_arena_code(ArenaValidateIn(language="Python", code="def oops(:\n  pass"))
    assert bad["valid"] is False
    assert len(bad["errors"]) > 0


def test_run_arena_endpoint():
    db = SessionLocal()
    try:
        # Run Turtle
        r = run_arena(ArenaRunIn(
            language="Python",
            code="import turtle\nt = turtle.Turtle()\nt.forward(80)"
        ), db=db)
        assert r["status"] == "succeeded"
        assert r["gui_target"] == "turtle"
        assert r["gui_payload"] is not None

        # Run Tkinter
        r2 = run_arena(ArenaRunIn(
            language="Python",
            code="import tkinter as tk\nroot = tk.Tk()\nl = tk.Label(root, text='Hi')\nl.pack()"
        ), db=db)
        assert r2["status"] == "succeeded"
        assert r2["gui_target"] == "tkinter"

        # Run Pygame
        r3 = run_arena(ArenaRunIn(
            language="Python",
            code="import pygame\npygame.init()\nscreen = pygame.display.set_mode((400, 300))\nscreen.fill((0,0,0))"
        ), db=db)
        assert r3["status"] == "succeeded"
        assert r3["gui_target"] == "pygame"
    finally:
        db.close()


if __name__ == "__main__":
    test_detect_arena_target()
    test_execute_console()
    test_execute_turtle_spiral()
    test_execute_tkinter_app()
    test_execute_pygame_simulation()
    test_capabilities_endpoint()
    test_templates_endpoint()
    test_validate_endpoint()
    test_run_arena_endpoint()
    print("ALL 9 ARENA TESTS PASSED!")
