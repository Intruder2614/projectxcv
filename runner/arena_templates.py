"""Codingal Code Studio — Starter Templates for Coding Arena.

Provides curated starters for Console, Turtle Graphics, Tkinter Desktop GUI, Pygame 2D,
Java, C++, and Web Canvas.
"""

from __future__ import annotations

ARENA_TEMPLATES = {
    "python_console": {
        "id": "python_console",
        "title": "Python (Console)",
        "language": "Python",
        "category": "Console",
        "icon": "🐍",
        "gui_target": "none",
        "filename": "main.py",
        "description": "Standard console input/output, variables, and loops.",
        "code": """# Python Console Starter
name = "Coder"
print(f"Hello, {name}!")
print("Welcome to Codingal Code Studio Coding Arena.\\n")

# Multi-line calculation
print("Squares from 1 to 5:")
for i in range(1, 6):
    print(f"  {i}² = {i**2}")

print("\\nConsole program completed.")
"""
    },
    "python_turtle_star": {
        "id": "python_turtle_star",
        "title": "Turtle: Spiral Star",
        "language": "Python",
        "category": "Turtle Graphics",
        "icon": "🐢",
        "gui_target": "turtle",
        "filename": "star.py",
        "description": "Geometric spiral star with fill and color animation.",
        "code": """import turtle

# Setup turtle
t = turtle.Turtle()
t.speed(3)
t.pensize(2)
t.color("#f45b4f", "#ffeaa7")

turtle.bgcolor("#1b1e28")
turtle.title("Codingal Turtle Spiral Star")

print("Drawing spiral star...")
t.begin_fill()

# Draw spiral geometry
for i in range(36):
    t.forward(120)
    t.right(170)

t.end_fill()
t.hideturtle()

print("Turtle drawing complete!")
turtle.done()
"""
    },
    "python_turtle_flower": {
        "id": "python_turtle_flower",
        "title": "Turtle: Rainbow Flower",
        "language": "Python",
        "category": "Turtle Graphics",
        "icon": "🌸",
        "gui_target": "turtle",
        "filename": "flower.py",
        "description": "Multi-colored repeating circles creating a geometric flower.",
        "code": """import turtle

t = turtle.Turtle()
t.speed(5)
t.pensize(2)
turtle.bgcolor("#161822")

colors = ["#f45b4f", "#e67e22", "#f1c40f", "#2ecc71", "#3498db", "#9b59b6"]

print("Drawing rainbow flower petals...")

for i in range(24):
    t.pencolor(colors[i % len(colors)])
    t.circle(70)
    t.left(15)

t.hideturtle()
print("Rainbow flower finished!")
turtle.done()
"""
    },
    "python_tkinter_counter": {
        "id": "python_tkinter_counter",
        "title": "Tkinter: Interactive App",
        "language": "Python",
        "category": "Tkinter GUI",
        "icon": "🪟",
        "gui_target": "tkinter",
        "filename": "gui_app.py",
        "description": "Interactive desktop window with buttons, entries, reactive state, and labels.",
        "code": """import tkinter as tk

root = tk.Tk()
root.title("Codingal Studio App")
root.geometry("380x300")

count = 0

def increment():
    global count
    count += 1
    lbl_counter.config(text=f"Points: {count}")
    print(f"Points updated: {count}")

def reset():
    global count
    count = 0
    lbl_counter.config(text="Points: 0")
    print("Points reset to 0")

def greet():
    name = entry_name.get()
    msg = f"Awesome coding, {name or 'Learner'}!"
    lbl_status.config(text=msg)
    print(f"Greeting sent: {msg}")

# Header
lbl_title = tk.Label(root, text="Student Mastery Tracker", font=("Arial", 16, "bold"), fg="#f45b4f")
lbl_title.pack(pady=10)

# Counter display
lbl_counter = tk.Label(root, text="Points: 0", font=("Arial", 14))
lbl_counter.pack(pady=5)

# Button row
btn_frame = tk.Frame(root)
btn_frame.pack(pady=8)

btn_add = tk.Button(btn_frame, text="＋ Add Point", command=increment, bg="#f45b4f", fg="white")
btn_add.pack(side="left", padx=5)

btn_reset = tk.Button(btn_frame, text="Reset", command=reset)
btn_reset.pack(side="left", padx=5)

# Entry form
lbl_name = tk.Label(root, text="Enter your name:")
lbl_name.pack(pady=4)

entry_name = tk.Entry(root, width=22)
entry_name.pack(pady=4)

btn_greet = tk.Button(root, text="Submit Name", command=greet, bg="#3c74c9", fg="white")
btn_greet.pack(pady=6)

lbl_status = tk.Label(root, text="", fg="#29945b", font=("Arial", 11, "italic"))
lbl_status.pack(pady=4)

root.mainloop()
"""
    },
    "python_pygame_bouncing_ball": {
        "id": "python_pygame_bouncing_ball",
        "title": "Pygame: Bouncing Ball",
        "language": "Python",
        "category": "Pygame 2D",
        "icon": "🎮",
        "gui_target": "pygame",
        "filename": "game.py",
        "description": "Interactive 2D physics animation with gravity, boundary collisions, and color trail.",
        "code": """import pygame

pygame.init()
WIDTH, HEIGHT = 480, 320
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Codingal Arena — Bouncing Ball")

# Colors
BG = (23, 26, 33)
BALL_COLOR = (244, 91, 79)
BORDER_COLOR = (60, 116, 201)

# Ball state
x, y = 240, 80
dx, dy = 4, 3
radius = 16

clock = pygame.time.Clock()
running = True

print("Starting Pygame 2D viewport...")

# Draw initial frame
screen.fill(BG)
pygame.draw.rect(screen, BORDER_COLOR, (10, 10, WIDTH - 20, HEIGHT - 20), 2)
pygame.draw.circle(screen, BALL_COLOR, (int(x), int(y)), radius)
pygame.display.flip()

print("Pygame viewport initialized at 60 FPS.")
pygame.quit()
"""
    },
    "python_pygame_paddle": {
        "id": "python_pygame_paddle",
        "title": "Pygame: Paddle Dodger",
        "language": "Python",
        "category": "Pygame 2D",
        "icon": "🕹️",
        "gui_target": "pygame",
        "filename": "paddle_game.py",
        "description": "Playable keyboard-controlled paddle game responding to left/right arrow keys.",
        "code": """import pygame

pygame.init()
WIDTH, HEIGHT = 480, 320
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Paddle Dodger Game")

BG = (20, 23, 30)
PADDLE_COLOR = (41, 148, 91)
BALL_COLOR = (244, 91, 79)

# Paddle
paddle_x = 200
paddle_y = 285
paddle_w = 90
paddle_h = 12

# Ball
x, y = 240, 100
dx, dy = 3, 3
radius = 10

screen.fill(BG)
pygame.draw.rect(screen, PADDLE_COLOR, (paddle_x, paddle_y, paddle_w, paddle_h))
pygame.draw.circle(screen, BALL_COLOR, (x, y), radius)
pygame.display.flip()

print("Paddle Dodger Game ready! Use Left/Right Arrow keys or A/D to steer.")
pygame.quit()
"""
    },
    "html_canvas_interactive": {
        "id": "html_canvas_interactive",
        "title": "Web: Canvas Particle Lab",
        "language": "HTML/CSS/JS",
        "category": "Web Sandboxed",
        "icon": "🌐",
        "gui_target": "web",
        "filename": "index.html",
        "description": "Interactive HTML5 canvas particle simulation running in sandboxed iframe.",
        "code": """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Codingal Canvas Lab</title>
  <style>
    body { margin: 0; background: #161822; color: #fff; font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; overflow: hidden; }
    canvas { background: #1f2330; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.4); cursor: pointer; }
    p { margin-top: 10px; font-size: 12px; color: #a0a6b5; }
  </style>
</head>
<body>
  <canvas id="c" width="440" height="260"></canvas>
  <p>Move mouse or click canvas to burst particles ✦</p>
  <script>
    const canvas = document.getElementById('c');
    const ctx = canvas.getContext('2d');
    let particles = [];

    function addParticles(x, y) {
      for(let i=0; i<8; i++){
        const angle = Math.random() * Math.PI * 2;
        const speed = Math.random() * 3 + 1;
        particles.push({
          x, y,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          color: ['#f45b4f', '#f1c40f', '#3498db', '#2ecc71', '#9b59b6'][Math.floor(Math.random()*5)],
          size: Math.random() * 4 + 2,
          life: 1.0
        });
      }
    }

    canvas.addEventListener('mousemove', e => {
      const rect = canvas.getBoundingClientRect();
      addParticles(e.clientX - rect.left, e.clientY - rect.top);
    });

    canvas.addEventListener('click', e => {
      const rect = canvas.getBoundingClientRect();
      for(let i=0; i<3; i++) addParticles(e.clientX - rect.left, e.clientY - rect.top);
    });

    // Auto burst
    setInterval(() => addParticles(220 + (Math.random()-0.5)*100, 130 + (Math.random()-0.5)*60), 400);

    function loop() {
      ctx.fillStyle = 'rgba(31, 35, 48, 0.2)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      particles.forEach((p, idx) => {
        p.x += p.vx;
        p.y += p.vy;
        p.life -= 0.02;
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, Math.max(1, p.size * p.life), 0, Math.PI*2);
        ctx.fill();
        if(p.life <= 0) particles.splice(idx, 1);
      });

      requestAnimationFrame(loop);
    }
    loop();
  </script>
</body>
</html>
"""
    },
    "java_console": {
        "id": "java_console",
        "title": "Java (Console)",
        "language": "Java",
        "category": "Console",
        "icon": "☕",
        "gui_target": "none",
        "filename": "Main.java",
        "description": "Standard Java class with main method.",
        "code": """public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, Codingal Java!");
        int sum = 0;
        for (int i = 1; i <= 5; i++) {
            sum += i;
        }
        System.out.println("Sum of 1..5 is: " + sum);
    }
}
"""
    },
    "cpp_console": {
        "id": "cpp_console",
        "title": "C++ (Console)",
        "language": "C++",
        "category": "Console",
        "icon": "⚙",
        "gui_target": "none",
        "filename": "main.cpp",
        "description": "Modern C++ standard I/O and algorithm starter.",
        "code": """#include <iostream>
#include <vector>
#include <numeric>

int main() {
    std::cout << "Hello, Codingal C++!\\n";
    std::vector<int> numbers = {10, 20, 30, 40, 50};
    int total = std::accumulate(numbers.begin(), numbers.end(), 0);
    std::cout << "Sum of vector elements: " << total << "\\n";
    return 0;
}
"""
    }
}

