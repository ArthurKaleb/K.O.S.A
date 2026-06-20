import cv2
import mediapipe as mp
import pyautogui
import math
import threading
import tkinter as tk
import keyboard  # Lembre-se de instalar se necessário: pip install keyboard

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

cap = cv2.VideoCapture(0)
hands = mp.solutions.hands.Hands(max_num_hands=2, min_detection_confidence=0.7)

screen_w, screen_h = pyautogui.size()

# =========================
# ESTADOS GERAIS
# =========================
paused = False          
PINCH_THRESHOLD = 0.07  # Área de clique maior mantida para ambas as mãos

# =========================
# CURSOR SUAVE
# =========================
pos = {"x": 0.0, "y": 0.0}
alpha = 0.18
deadzone = 1.2

# =========================
# ESTADOS DAS MÃOS
# =========================
left_down = False
right_down = False
zoom_base = None

# =========================
# ATALHO DE PAUSA (TECLA F)
# =========================
def toggle_pause(e):
    global paused
    paused = not paused

keyboard.on_press_key("f", toggle_pause)

# =========================
# FUNÇÕES
# =========================
def dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)

def pinch(lm):
    return dist(lm[4], lm[8])

# =========================
# OVERLAY (STATUS DA BOLINHA)
# =========================
def overlay():
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-transparentcolor", "black")

    w, h = screen_w, screen_h
    root.geometry(f"{w}x{h}+0+0")

    canvas = tk.Canvas(root, width=w, height=h, bg="black", highlightthickness=0)
    canvas.pack()

    def draw():
        canvas.delete("all")

        # Bolinha Vermelha se pausado, Verde se ativo
        status_color = "red" if paused else "green"
        canvas.create_oval(15, 15, 75, 75, fill=status_color, outline=status_color)

        root.after(16, draw)

    draw()
    root.mainloop()

threading.Thread(target=overlay, daemon=True).start()

# =========================
# LOOP PRINCIPAL
# =========================
while True:
    ok, frame = cap.read()
    if not ok:
        continue

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = hands.process(rgb)

    left = None
    right = None

    if res.multi_hand_landmarks and res.multi_handedness:
        for lm, h in zip(res.multi_hand_landmarks, res.multi_handedness):
            if h.classification[0].label == "Left":
                left = lm.landmark
            else:
                right = lm.landmark

    # =========================
    # VERIFICAÇÃO DE PAUSA (TECLA F)
    # =========================
    if paused:
        if left_down:
            pyautogui.mouseUp(button="left")
            left_down = False
        if right_down:
            pyautogui.mouseUp(button="right")
            right_down = False
        continue

    # =========================
    # VERIFICAÇÃO DE ZOOM (DUAS PINÇAS)
    # =========================
    is_zooming = False
    if left and right:
        if pinch(left) < PINCH_THRESHOLD and pinch(right) < PINCH_THRESHOLD:
            is_zooming = True

    if is_zooming:
        if left_down:
            pyautogui.mouseUp(button="left")
            left_down = False
        if right_down:
            pyautogui.mouseUp(button="right")
            right_down = False

        d = dist(left[20], right[20])
        if zoom_base is None:
            zoom_base = d

        delta = d - zoom_base
        pyautogui.scroll(int(delta * 80))
        zoom_base = d

        continue  
    else:
        zoom_base = None

    # =========================
    # CONTROLE DE MOVIMENTO E SELEÇÃO
    # =========================
    right_is_moving = False

    # MÃO DIREITA: Move o cursor E segura o botão direito apenas se estiver em pinça
    if right:
        if pinch(right) < PINCH_THRESHOLD:
            rx = right[8].x * screen_w
            ry = right[8].y * screen_h

            # CORREÇÃO DO ARRASTO: Se acabou de ativar a pinça, atualiza a posição 
            # na hora para onde a mão está agora, evitando saltos ou deslizamentos lentos.
            if not right_down:
                pos["x"] = rx
                pos["y"] = ry
                pyautogui.moveTo(int(rx), int(ry))
                pyautogui.mouseDown(button="right")
                right_down = True

            # Movimentação suave contínua a partir do ponto atual da mão
            pos["x"] = pos["x"] + (rx - pos["x"]) * alpha
            pos["y"] = pos["y"] + (ry - pos["y"]) * alpha

            if abs(rx - pos["x"]) > deadzone or abs(ry - pos["y"]) > deadzone:
                pyautogui.moveTo(int(pos["x"]), int(pos["y"]))
            
            right_is_moving = True  

        else:
            if right_down:
                pyautogui.mouseUp(button="right")
                right_down = False

    # MÃO ESQUERDA: Move normalmente (se a direita não estiver controlando) + Clique Esquerdo
    if left:
        if not right_is_moving:
            lx = left[8].x * screen_w
            ly = left[8].y * screen_h

            pos["x"] = pos["x"] + (lx - pos["x"]) * alpha
            pos["y"] = pos["y"] + (ly - pos["y"]) * alpha

            if abs(lx - pos["x"]) > deadzone or abs(ly - pos["y"]) > deadzone:
                pyautogui.moveTo(int(pos["x"]), int(pos["y"]))

        if pinch(left) < PINCH_THRESHOLD:
            if not left_down:
                pyautogui.mouseDown(button="left")
                left_down = True
        else:
            if left_down:
                pyautogui.mouseUp(button="left")
                left_down = False