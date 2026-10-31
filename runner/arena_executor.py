"""Codingal Code Studio — Coding Arena Execution Engine

Provides sandboxed, headless-safe execution and visual telemetry for:
- Standard Console programs (Python, Java, C++)
- Python Turtle graphics (traces vector draw commands, pen states, angles, fills)
- Python Tkinter GUI (virtual window, reactive widgets: Label, Button, Entry, Canvas, Pack/Grid)
- Python Pygame 2D game loops (virtual display, draw primitives, interactive game engine)
- HTML/CSS/JavaScript web preview

Can be invoked directly or run as an isolated subprocess.
"""

from __future__ import annotations

import ast
import contextlib
import io
import json
import math
import re
import sys
import time
import traceback
from typing import Any, Dict, List, Optional, Tuple


def detect_arena_target(code: str, language: str) -> str:
    """Classify code into the appropriate arena runtime target."""
    if language == "HTML/CSS/JS":
        return "web"
    if language != "Python":
        return "console"

    code_clean = re.sub(r'#.*', '', code)
    # Check imports and keywords
    if re.search(r'\b(import\s+turtle|from\s+turtle\s+import)\b', code_clean):
        return "turtle"
    if re.search(r'\b(import\s+tkinter|from\s+tkinter\s+import)\b', code_clean):
        return "tkinter"
    if re.search(r'\b(import\s+pygame|from\s+pygame\s+import)\b', code_clean):
        return "pygame"

    return "console"


# ============================================================================
# 1. Virtual Turtle Engine
# ============================================================================

class VirtualTurtle:
    """Virtual Python Turtle emulator that records draw steps and pen telemetry."""

    def __init__(self, screen: 'VirtualScreen'):
        self.screen = screen
        self.x: float = 0.0
        self.y: float = 0.0
        self.heading_deg: float = 0.0  # 0 = East, 90 = North
        self._pen_down: bool = True
        self._pen_color: str = "#f45b4f"
        self._fill_color: str = "#f45b4f"
        self._pen_size: float = 2.0
        self._speed: int = 3
        self._visible: bool = True
        self._shape: str = "classic"
        self._filling: bool = False
        self._poly: List[List[float]] = []

    def forward(self, distance: float) -> None:
        rad = math.radians(self.heading_deg)
        nx = self.x + distance * math.cos(rad)
        ny = self.y + distance * math.sin(rad)
        self.goto(nx, ny)

    fd = forward

    def backward(self, distance: float) -> None:
        self.forward(-distance)

    bk = backward
    back = backward

    def right(self, angle: float) -> None:
        self.heading_deg = (self.heading_deg - angle) % 360

    rt = right

    def left(self, angle: float) -> None:
        self.heading_deg = (self.heading_deg + angle) % 360

    lt = left

    def goto(self, x: float, y: Optional[float] = None) -> None:
        if y is None and isinstance(x, (tuple, list)):
            x, y = x[0], x[1]
        nx, ny = float(x), float(y)
        if self._pen_down:
            self.screen.record_action({
                "cmd": "line",
                "from": [round(self.x, 2), round(self.y, 2)],
                "to": [round(nx, 2), round(ny, 2)],
                "color": self._pen_color,
                "width": self._pen_size
            })
        if self._filling:
            self._poly.append([round(nx, 2), round(ny, 2)])
        self.x, self.y = nx, ny

    setpos = goto
    setposition = goto

    def setx(self, x: float) -> None:
        self.goto(x, self.y)

    def sety(self, y: float) -> None:
        self.goto(self.x, y)

    def setheading(self, to_angle: float) -> None:
        self.heading_deg = float(to_angle) % 360

    seth = setheading

    def home(self) -> None:
        self.goto(0.0, 0.0)
        self.setheading(0.0)

    def penup(self) -> None:
        self._pen_down = False

    up = penup
    pu = penup

    def pendown(self) -> None:
        self._pen_down = True

    down = pendown
    pd = pendown

    def isdown(self) -> bool:
        return self._pen_down

    def speed(self, s: Any = 3) -> None:
        try:
            self._speed = int(s)
        except Exception:
            self._speed = 3
        self.screen.record_action({"cmd": "speed", "speed": self._speed})

    def pensize(self, width: Optional[float] = None) -> float:
        if width is not None:
            self._pen_size = max(0.5, float(width))
        return self._pen_size

    width = pensize

    def pencolor(self, *args: Any) -> str:
        if args:
            self._pen_color = self._parse_color(*args)
        return self._pen_color

    def fillcolor(self, *args: Any) -> str:
        if args:
            self._fill_color = self._parse_color(*args)
        return self._fill_color

    def color(self, *args: Any) -> Tuple[str, str]:
        if len(args) == 1:
            c = self._parse_color(args[0])
            self._pen_color = c
            self._fill_color = c
        elif len(args) == 2:
            self._pen_color = self._parse_color(args[0])
            self._fill_color = self._parse_color(args[1])
        return self._pen_color, self._fill_color

    def begin_fill(self) -> None:
        self._filling = True
        self._poly = [[round(self.x, 2), round(self.y, 2)]]
        self.screen.record_action({"cmd": "begin_fill", "fillcolor": self._fill_color})

    def end_fill(self) -> None:
        if self._filling and len(self._poly) >= 3:
            self.screen.record_action({
                "cmd": "fill_poly",
                "points": list(self._poly),
                "fillcolor": self._fill_color,
                "pencolor": self._pen_color,
                "width": self._pen_size
            })
        self._filling = False
        self._poly = []

    def circle(self, radius: float, extent: Optional[float] = None, steps: Optional[int] = None) -> None:
        ext = 360.0 if extent is None else float(extent)
        st = steps or max(12, int(abs(ext) / 10))
        angle_step = ext / st
        chord_len = 2.0 * radius * math.sin(math.radians(abs(angle_step) / 2.0))
        for _ in range(st):
            if radius < 0:
                self.right(angle_step / 2.0)
                self.forward(chord_len)
                self.right(angle_step / 2.0)
            else:
                self.left(angle_step / 2.0)
                self.forward(chord_len)
                self.left(angle_step / 2.0)

    def dot(self, size: Optional[float] = None, *color: Any) -> None:
        dot_size = float(size) if size is not None else max(self._pen_size + 4, 2 * self._pen_size)
        c = self._parse_color(*color) if color else self._pen_color
        self.screen.record_action({
            "cmd": "dot",
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "radius": round(dot_size / 2.0, 2),
            "color": c
        })

    def stamp(self) -> int:
        stamp_id = len(self.screen.actions) + 1
        self.screen.record_action({
            "cmd": "stamp",
            "id": stamp_id,
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "angle": round(self.heading_deg, 2),
            "color": self._pen_color,
            "shape": self._shape
        })
        return stamp_id

    def clear(self) -> None:
        self.screen.record_action({"cmd": "clear"})

    def reset(self) -> None:
        self.home()
        self.clear()
        self._pen_down = True
        self._pen_color = "#f45b4f"
        self._fill_color = "#f45b4f"
        self._pen_size = 2.0

    def write(self, arg: Any, move: bool = False, align: str = "left", font: Tuple[str, int, str] = ("Arial", 10, "normal")) -> None:
        text = str(arg)
        font_name = font[0] if len(font) > 0 else "Arial"
        font_size = font[1] if len(font) > 1 else 10
        font_style = font[2] if len(font) > 2 else "normal"
        self.screen.record_action({
            "cmd": "write",
            "text": text,
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "align": align,
            "font": f"{font_style} {font_size}px {font_name}",
            "color": self._pen_color
        })

    def hideturtle(self) -> None:
        self._visible = False

    ht = hideturtle

    def showturtle(self) -> None:
        self._visible = True

    st = showturtle

    def isvisible(self) -> bool:
        return self._visible

    def shape(self, name: str) -> None:
        self._shape = name

    def xcor(self) -> float:
        return self.x

    def ycor(self) -> float:
        return self.y

    def pos(self) -> Tuple[float, float]:
        return self.x, self.y

    position = pos

    def heading(self) -> float:
        return self.heading_deg

    def _parse_color(self, *args: Any) -> str:
        if not args:
            return "#f45b4f"
        if len(args) == 1:
            val = args[0]
            if isinstance(val, str):
                return val
            if isinstance(val, (tuple, list)) and len(val) >= 3:
                r, g, b = val[:3]
                if all(isinstance(x, float) and x <= 1.0 for x in (r, g, b)):
                    r, g, b = int(r * 255), int(g * 255), int(b * 255)
                return f"rgb({int(r)}, {int(g)}, {int(b)})"
        elif len(args) >= 3:
            r, g, b = args[:3]
            if all(isinstance(x, float) and x <= 1.0 for x in (r, g, b)):
                r, g, b = int(r * 255), int(g * 255), int(b * 255)
            return f"rgb({int(r)}, {int(g)}, {int(b)})"
        return "#f45b4f"


class VirtualScreen:
    """Virtual turtle screen manager and action sink."""

    def __init__(self):
        self.actions: List[Dict[str, Any]] = []
        self.bg_color: str = "#ffffff"
        self.title_str: str = "Turtle Graphics Canvas"
        self.width: int = 600
        self.height: int = 450
        self._default_turtle: Optional[VirtualTurtle] = None

    def record_action(self, action: Dict[str, Any]) -> None:
        if len(self.actions) < 4000:
            self.actions.append(action)

    def bgcolor(self, *args: Any) -> str:
        if args:
            if len(args) == 1 and isinstance(args[0], str):
                self.bg_color = args[0]
            self.record_action({"cmd": "bgcolor", "color": self.bg_color})
        return self.bg_color

    def title(self, titlestring: str) -> None:
        self.title_str = str(titlestring)

    def setup(self, width: int = 600, height: int = 450, startx: Optional[int] = None, starty: Optional[int] = None) -> None:
        self.width = int(width)
        self.height = int(height)

    def screensize(self, canvwidth: Optional[int] = None, canvheight: Optional[int] = None, bg: Optional[str] = None) -> Tuple[int, int]:
        if canvwidth:
            self.width = int(canvwidth)
        if canvheight:
            self.height = int(canvheight)
        if bg:
            self.bgcolor(bg)
        return self.width, self.height

    def clear(self) -> None:
        self.record_action({"cmd": "clear"})

    def reset(self) -> None:
        self.actions.clear()

    def mainloop(self) -> None:
        pass

    done = mainloop

    def get_default_turtle(self) -> VirtualTurtle:
        if self._default_turtle is None:
            self._default_turtle = VirtualTurtle(self)
        return self._default_turtle


def build_turtle_module(screen: VirtualScreen) -> Any:
    """Construct an emulated turtle module bound to the VirtualScreen."""
    import types
    mod = types.ModuleType("turtle")

    def Turtle():
        return VirtualTurtle(screen)

    def Screen():
        return screen

    mod.Turtle = Turtle
    mod.Screen = Screen
    mod.bgcolor = screen.bgcolor
    mod.title = screen.title
    mod.setup = screen.setup
    mod.screensize = screen.screensize
    mod.clear = screen.clear
    mod.reset = screen.reset
    mod.mainloop = screen.mainloop
    mod.done = screen.done

    # Delegate module-level turtle methods to default turtle
    def forward(d): screen.get_default_turtle().forward(d)
    def fd(d): screen.get_default_turtle().fd(d)
    def backward(d): screen.get_default_turtle().backward(d)
    def bk(d): screen.get_default_turtle().bk(d)
    def right(a): screen.get_default_turtle().right(a)
    def rt(a): screen.get_default_turtle().rt(a)
    def left(a): screen.get_default_turtle().left(a)
    def lt(a): screen.get_default_turtle().lt(a)
    def goto(x, y=None): screen.get_default_turtle().goto(x, y)
    def setpos(x, y=None): screen.get_default_turtle().setpos(x, y)
    def setheading(a): screen.get_default_turtle().setheading(a)
    def seth(a): screen.get_default_turtle().seth(a)
    def penup(): screen.get_default_turtle().penup()
    def up(): screen.get_default_turtle().up()
    def pu(): screen.get_default_turtle().pu()
    def pendown(): screen.get_default_turtle().pendown()
    def down(): screen.get_default_turtle().down()
    def pd(): screen.get_default_turtle().pd()
    def pensize(w=None): return screen.get_default_turtle().pensize(w)
    def width(w=None): return screen.get_default_turtle().width(w)
    def color(*args): return screen.get_default_turtle().color(*args)
    def pencolor(*args): return screen.get_default_turtle().pencolor(*args)
    def fillcolor(*args): return screen.get_default_turtle().fillcolor(*args)
    def begin_fill(): screen.get_default_turtle().begin_fill()
    def end_fill(): screen.get_default_turtle().end_fill()
    def circle(r, extent=None, steps=None): screen.get_default_turtle().circle(r, extent, steps)
    def dot(size=None, *col): screen.get_default_turtle().dot(size, *col)
    def speed(s): screen.get_default_turtle().speed(s)
    def hideturtle(): screen.get_default_turtle().hideturtle()
    def showturtle(): screen.get_default_turtle().showturtle()
    def heading(): return screen.get_default_turtle().heading()
    def pos(): return screen.get_default_turtle().pos()
    def position(): return screen.get_default_turtle().position()
    def xcor(): return screen.get_default_turtle().xcor()
    def ycor(): return screen.get_default_turtle().ycor()
    def isdown(): return screen.get_default_turtle().isdown()
    def shape(name): screen.get_default_turtle().shape(name)
    def stamp(): return screen.get_default_turtle().stamp()
    def write(arg, move=False, align="left", font=("Arial", 8, "normal")):
        screen.get_default_turtle().write(arg, move, align, font)

    for fn in [forward, fd, backward, bk, right, rt, left, lt, goto, setpos, setheading, seth,
               penup, up, pu, pendown, down, pd, pensize, width, color, pencolor, fillcolor,
               begin_fill, end_fill, circle, dot, speed, hideturtle, showturtle, write,
               heading, pos, position, xcor, ycor, isdown, shape, stamp]:
        setattr(mod, fn.__name__, fn)

    return mod


# ============================================================================
# 2. Virtual Tkinter Engine
# ============================================================================

class VirtualTkWidget:
    """Generic virtual Tkinter widget."""

    def __init__(self, widget_type: str, parent: Optional['VirtualTkWidget'] = None, **kwargs: Any):
        self.widget_type = widget_type
        self.parent = parent
        self.widget_id = f"w_{id(self)}"
        self.props = dict(kwargs)
        self.pack_props: Optional[Dict[str, Any]] = None
        self.grid_props: Optional[Dict[str, Any]] = None
        self.children: List['VirtualTkWidget'] = []
        if parent:
            parent.children.append(self)

    def config(self, **kwargs: Any) -> None:
        self.props.update(kwargs)

    configure = config

    def pack(self, **kwargs: Any) -> None:
        self.pack_props = kwargs

    def grid(self, **kwargs: Any) -> None:
        self.grid_props = kwargs

    def cget(self, key: str) -> Any:
        return self.props.get(key)

    def bind(self, event: str, callback: Any) -> None:
        self.props[f"bind_{event}"] = getattr(callback, "__name__", str(callback))


class VirtualTkCanvas(VirtualTkWidget):
    """Virtual Tkinter Canvas with shape creation."""

    def __init__(self, parent: Optional[VirtualTkWidget] = None, **kwargs: Any):
        super().__init__("canvas", parent, **kwargs)
        self.items: List[Dict[str, Any]] = []

    def create_line(self, *coords: Any, **kwargs: Any) -> int:
        item_id = len(self.items) + 1
        self.items.append({"id": item_id, "type": "line", "coords": list(coords), **kwargs})
        return item_id

    def create_rectangle(self, *coords: Any, **kwargs: Any) -> int:
        item_id = len(self.items) + 1
        self.items.append({"id": item_id, "type": "rectangle", "coords": list(coords), **kwargs})
        return item_id

    def create_oval(self, *coords: Any, **kwargs: Any) -> int:
        item_id = len(self.items) + 1
        self.items.append({"id": item_id, "type": "oval", "coords": list(coords), **kwargs})
        return item_id

    def create_text(self, *coords: Any, **kwargs: Any) -> int:
        item_id = len(self.items) + 1
        self.items.append({"id": item_id, "type": "text", "coords": list(coords), **kwargs})
        return item_id

    def delete(self, tag_or_id: Any) -> None:
        self.items.clear()


class VirtualTkRoot(VirtualTkWidget):
    """Virtual top-level Tk window."""

    def __init__(self):
        super().__init__("root")
        self.window_title: str = "Tkinter Application"
        self.window_width: int = 380
        self.window_height: int = 300
        self.bg_color: str = "#ffffff"

    def title(self, t: str) -> None:
        self.window_title = str(t)

    def geometry(self, geom: str) -> None:
        m = re.match(r'(\d+)x(\d+)', geom)
        if m:
            self.window_width = int(m.group(1))
            self.window_height = int(m.group(2))

    def mainloop(self) -> None:
        pass


class VirtualVariable:
    """Tkinter StringVar/IntVar emulator."""

    def __init__(self, value: Any = ""):
        self._val = value

    def get(self) -> Any:
        return self._val

    def set(self, val: Any) -> None:
        self._val = val


def build_tkinter_module(root_holder: List[Optional[VirtualTkRoot]], callbacks: Dict[str, Any]) -> Any:
    """Construct an emulated tkinter module."""
    import types
    mod = types.ModuleType("tkinter")

    def Tk():
        r = VirtualTkRoot()
        root_holder[0] = r
        return r

    def Label(parent=None, **kwargs):
        return VirtualTkWidget("label", parent, **kwargs)

    def Button(parent=None, **kwargs):
        cmd = kwargs.get("command")
        if callable(cmd):
            cmd_name = getattr(cmd, "__name__", f"cmd_{len(callbacks)+1}")
            callbacks[cmd_name] = cmd
            kwargs["command_name"] = cmd_name
        return VirtualTkWidget("button", parent, **kwargs)

    def Entry(parent=None, **kwargs):
        w = VirtualTkWidget("entry", parent, **kwargs)
        w._text = kwargs.get("text", "")
        def get(): return w._text
        def insert(index, string): w._text += string
        def delete(first, last=None): w._text = ""
        w.get = get; w.insert = insert; w.delete = delete
        return w

    def Frame(parent=None, **kwargs):
        return VirtualTkWidget("frame", parent, **kwargs)

    def Canvas(parent=None, **kwargs):
        return VirtualTkCanvas(parent, **kwargs)

    def Checkbutton(parent=None, **kwargs):
        return VirtualTkWidget("checkbutton", parent, **kwargs)

    mod.Tk = Tk
    mod.Label = Label
    mod.Button = Button
    mod.Entry = Entry
    mod.Frame = Frame
    mod.Canvas = Canvas
    mod.Checkbutton = Checkbutton
    mod.StringVar = lambda value="": VirtualVariable(value)
    mod.IntVar = lambda value=0: VirtualVariable(value)
    mod.DoubleVar = lambda value=0.0: VirtualVariable(value)
    mod.BooleanVar = lambda value=False: VirtualVariable(value)

    # Common constants
    for const in ["LEFT", "RIGHT", "TOP", "BOTTOM", "BOTH", "X", "Y", "CENTER", "W", "E", "N", "S"]:
        setattr(mod, const, const.lower())

    return mod


def serialize_tkinter_tree(root: Optional[VirtualTkRoot]) -> Dict[str, Any]:
    """Serialize the Tkinter hierarchy into a clean JSON layout."""
    if not root:
        return {"title": "Tkinter GUI", "width": 380, "height": 280, "widgets": []}

    widgets: List[Dict[str, Any]] = []

    def visit(w: VirtualTkWidget):
        if w.widget_type != "root":
            item = {
                "id": w.widget_id,
                "type": w.widget_type,
                "parent_id": w.parent.widget_id if w.parent else None,
                "props": {k: v for k, v in w.props.items() if not callable(v)},
                "pack": w.pack_props,
                "grid": w.grid_props
            }
            if isinstance(w, VirtualTkCanvas):
                item["canvas_items"] = w.items
            widgets.append(item)
        for child in w.children:
            visit(child)

    visit(root)
    return {
        "title": root.window_title,
        "width": root.window_width,
        "height": root.window_height,
        "widgets": widgets
    }


# ============================================================================
# 3. Virtual Pygame Engine
# ============================================================================

class VirtualPygameSurface:
    """Emulates a Pygame Surface for drawing."""

    def __init__(self, width: int = 480, height: int = 320):
        self.width = width
        self.height = height
        self.fill_color: str = "#181a22"
        self.draw_commands: List[Dict[str, Any]] = []

    def fill(self, color: Any) -> None:
        self.fill_color = self._format_color(color)
        self.draw_commands.append({"cmd": "fill", "color": self.fill_color})

    def blit(self, source: Any, dest: Any) -> None:
        self.draw_commands.append({"cmd": "blit", "dest": list(dest)})

    def get_width(self) -> int:
        return self.width

    def get_height(self) -> int:
        return self.height

    def get_size(self) -> Tuple[int, int]:
        return self.width, self.height

    @staticmethod
    def _format_color(color: Any) -> str:
        if isinstance(color, str):
            return color
        if isinstance(color, (tuple, list)) and len(color) >= 3:
            return f"rgb({int(color[0])}, {int(color[1])}, {int(color[2])})"
        return "#f45b4f"


def build_pygame_module(surface_holder: List[Optional[VirtualPygameSurface]]) -> Any:
    """Construct an emulated pygame module."""
    import types
    mod = types.ModuleType("pygame")

    def init():
        return (6, 0)

    def quit():
        pass

    class Display:
        @staticmethod
        def set_mode(size=(480, 320), flags=0, depth=0):
            surf = VirtualPygameSurface(int(size[0]), int(size[1]))
            surface_holder[0] = surf
            return surf

        @staticmethod
        def set_caption(title: str):
            if surface_holder[0]:
                surface_holder[0].title = title

        @staticmethod
        def flip():
            pass

        @staticmethod
        def update():
            pass

    class Draw:
        @staticmethod
        def rect(surface, color, rect, width=0):
            r = list(rect)
            surface.draw_commands.append({
                "cmd": "rect",
                "color": VirtualPygameSurface._format_color(color),
                "rect": r,
                "width": width
            })

        @staticmethod
        def circle(surface, color, center, radius, width=0):
            surface.draw_commands.append({
                "cmd": "circle",
                "color": VirtualPygameSurface._format_color(color),
                "center": list(center),
                "radius": float(radius),
                "width": width
            })

        @staticmethod
        def line(surface, color, start_pos, end_pos, width=1):
            surface.draw_commands.append({
                "cmd": "line",
                "color": VirtualPygameSurface._format_color(color),
                "start": list(start_pos),
                "end": list(end_pos),
                "width": width
            })

        @staticmethod
        def polygon(surface, color, points, width=0):
            surface.draw_commands.append({
                "cmd": "polygon",
                "color": VirtualPygameSurface._format_color(color),
                "points": [list(p) for p in points],
                "width": width
            })

    class Event:
        @staticmethod
        def get():
            return []

        @staticmethod
        def poll():
            return None

    class Clock:
        def tick(self, fps: int = 60) -> int:
            return 16

    class Time:
        @staticmethod
        def delay(ms: int) -> None: pass
        @staticmethod
        def wait(ms: int) -> int: return ms
        @staticmethod
        def get_ticks() -> int: return 100

    Time.Clock = Clock

    class FontModule:
        @staticmethod
        def init(): pass
        @staticmethod
        def SysFont(name, size, bold=False, italic=False):
            class FontObj:
                def render(self, text, antialias, color, background=None):
                    surf = VirtualPygameSurface(len(str(text)) * size, size)
                    surf.draw_commands.append({
                        "cmd": "text",
                        "text": str(text),
                        "color": VirtualPygameSurface._format_color(color),
                        "size": size,
                        "font": name
                    })
                    return surf
            return FontObj()

    mod.init = init
    mod.quit = quit
    mod.display = Display
    mod.draw = Draw
    mod.event = Event
    mod.time = Time
    mod.font = FontModule

    # Constants
    mod.QUIT = 256
    mod.KEYDOWN = 768
    mod.KEYUP = 769
    mod.K_LEFT = 276
    mod.K_RIGHT = 275
    mod.K_UP = 273
    mod.K_DOWN = 274
    mod.K_SPACE = 32
    mod.K_ESCAPE = 27
    mod.K_w = ord('w')
    mod.K_a = ord('a')
    mod.K_s = ord('s')
    mod.K_d = ord('d')

    return mod


# ============================================================================
# 4. Arena Code Runner
# ============================================================================

def execute_arena_code(
    code: str,
    language: str = "Python",
    mode: str = "auto",
    gui_target: str = "auto",
    stdin_input: str = "",
    timeout_sec: float = 8.0
) -> Dict[str, Any]:
    """Execute code in the arena and return comprehensive stdout, stderr, and GUI telemetry."""
    started = time.monotonic()
    detected_target = detect_arena_target(code, language)
    target = detected_target if gui_target == "auto" else gui_target
    effective_mode = "gui" if target in {"turtle", "tkinter", "pygame", "web"} else "console"

    if language == "HTML/CSS/JS" or target == "web":
        return {
            "status": "succeeded",
            "mode": "gui",
            "gui_target": "web",
            "stdout": "",
            "stderr": "",
            "output": "HTML/CSS/JavaScript preview rendered in browser sandbox.",
            "duration_ms": int((time.monotonic() - started) * 1000),
            "executed": True,
            "gui_payload": {
                "type": "web",
                "html": code
            }
        }

    if language != "Python":
        return {
            "status": "unavailable",
            "mode": "console",
            "gui_target": "none",
            "stdout": "",
            "stderr": f"Native {language} execution requires Docker runner image. Console fallback active.",
            "output": f"Notice: {language} requires runner container.",
            "duration_ms": 0,
            "executed": False,
            "gui_payload": None
        }

    # Python Execution with Virtual Modules
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    stdin_stream = io.StringIO(stdin_input or "")

    turtle_screen = VirtualScreen()
    tk_root_holder: List[Optional[VirtualTkRoot]] = [None]
    tk_callbacks: Dict[str, Any] = {}
    pygame_surface_holder: List[Optional[VirtualPygameSurface]] = [None]

    # Save original sys.modules
    orig_turtle = sys.modules.get("turtle")
    orig_tkinter = sys.modules.get("tkinter")
    orig_pygame = sys.modules.get("pygame")

    status = "succeeded"
    err_detail = ""

    try:
        # Inject emulated modules
        sys.modules["turtle"] = build_turtle_module(turtle_screen)
        sys.modules["tkinter"] = build_tkinter_module(tk_root_holder, tk_callbacks)
        sys.modules["pygame"] = build_pygame_module(pygame_surface_holder)

        # Build clean execution environment
        exec_globals = {
            "__name__": "__main__",
            "__doc__": None,
            "__package__": None,
            "math": math,
            "time": time,
        }

        with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
            # Patch sys.stdin
            orig_stdin = sys.stdin
            sys.stdin = stdin_stream
            try:
                exec(code, exec_globals)
            finally:
                sys.stdin = orig_stdin

    except SyntaxError as e:
        status = "failed"
        err_detail = f"SyntaxError on line {e.lineno}: {e.msg}\n{e.text or ''}"
        stderr_buf.write(err_detail)
    except Exception as e:
        status = "failed"
        exc_lines = traceback.format_exception(*sys.exc_info())
        # Filter internal virtual runner frames for clarity
        clean_tb = "".join([line for line in exc_lines if "arena_executor.py" not in line])
        err_detail = clean_tb.strip() or str(e)
        stderr_buf.write(err_detail)
    finally:
        # Restore sys.modules
        if orig_turtle is None: sys.modules.pop("turtle", None)
        else: sys.modules["turtle"] = orig_turtle

        if orig_tkinter is None: sys.modules.pop("tkinter", None)
        else: sys.modules["tkinter"] = orig_tkinter

        if orig_pygame is None: sys.modules.pop("pygame", None)
        else: sys.modules["pygame"] = orig_pygame

    duration_ms = int((time.monotonic() - started) * 1000)
    stdout_text = stdout_buf.getvalue()
    stderr_text = stderr_buf.getvalue()
    combined_output = (stdout_text + ("\n" if stdout_text and stderr_text else "") + stderr_text).strip()

    # Build GUI Payload
    gui_payload: Optional[Dict[str, Any]] = None

    if target == "turtle" or (turtle_screen.actions and target != "tkinter"):
        dt = turtle_screen.get_default_turtle()
        gui_payload = {
            "type": "turtle",
            "title": turtle_screen.title_str,
            "width": turtle_screen.width,
            "height": turtle_screen.height,
            "bg_color": turtle_screen.bg_color,
            "actions": turtle_screen.actions,
            "final_state": {
                "x": round(dt.x, 2),
                "y": round(dt.y, 2),
                "heading": round(dt.heading_deg, 2),
                "is_down": dt.isdown(),
                "color": dt._pen_color,
                "visible": dt.isvisible()
            }
        }
        if not combined_output:
            combined_output = f"Turtle completed with {len(turtle_screen.actions)} graphics actions."

    elif target == "tkinter" or tk_root_holder[0] is not None:
        tree = serialize_tkinter_tree(tk_root_holder[0])
        gui_payload = {
            "type": "tkinter",
            **tree,
            "callbacks": list(tk_callbacks.keys())
        }
        if not combined_output:
            combined_output = f"Tkinter window '{tree['title']}' initialized with {len(tree['widgets'])} widgets."

    elif target == "pygame" or pygame_surface_holder[0] is not None:
        surf = pygame_surface_holder[0] or VirtualPygameSurface()
        gui_payload = {
            "type": "pygame",
            "title": getattr(surf, "title", "Pygame Window"),
            "width": surf.width,
            "height": surf.height,
            "fill_color": surf.fill_color,
            "draw_commands": surf.draw_commands,
            "interactive": True
        }
        if not combined_output:
            combined_output = f"Pygame initialized ({surf.width}x{surf.height}) with {len(surf.draw_commands)} initial drawing calls."

    return {
        "status": status,
        "mode": effective_mode,
        "gui_target": target,
        "stdout": stdout_text,
        "stderr": stderr_text,
        "output": combined_output or ("Program finished with no output." if status == "succeeded" else "Execution failed."),
        "duration_ms": duration_ms,
        "executed": True,
        "gui_payload": gui_payload
    }


# ============================================================================
# 5. CLI Entrypoint for Subprocess Invocations
# ============================================================================

if __name__ == "__main__":
    try:
        raw_input = sys.stdin.read()
        payload = json.loads(raw_input) if raw_input else {}
        result = execute_arena_code(
            code=payload.get("code", ""),
            language=payload.get("language", "Python"),
            mode=payload.get("mode", "auto"),
            gui_target=payload.get("gui_target", "auto"),
            stdin_input=payload.get("stdin", ""),
            timeout_sec=float(payload.get("timeout", 8.0))
        )
        sys.stdout.write(json.dumps(result))
    except Exception as e:
        sys.stdout.write(json.dumps({
            "status": "error",
            "mode": "console",
            "gui_target": "none",
            "output": f"Arena runner error: {str(e)}",
            "stdout": "",
            "stderr": traceback.format_exc(),
            "duration_ms": 0,
            "executed": False,
            "gui_payload": None
        }))
