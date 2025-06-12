import cv2
import numpy as np
import pygame
import random
import time
import mediapipe as mp

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Setup screen
screen_width, screen_height = 1024, 768
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Fruit Ninja Clone with Hand Detection')

clock = pygame.time.Clock()

# Load sounds
try:
    pygame.mixer.music.load('background.wav')
    pygame.mixer.music.play(-1)
    cut_sound = pygame.mixer.Sound('cut.wav')
except:
    print("Sound files not found, continuing without audio")

# Load images
try:
    fruit_images = ['apple.jpg', 'banana.jpg', 'cherry.jpg']
    bomb_image = 'bomb.jpeg'
except:
    print("Image files not found, using colored circles instead")

# Fruit Class
class Fruit:
    def __init__(self):
        if random.random() < 0.2:
            try:
                self.image = pygame.image.load(bomb_image)
                self.is_bomb = True
            except:
                self.image = None
                self.is_bomb = True
                self.color = (0, 0, 0)
        else:
            try:
                self.image = pygame.image.load(random.choice(fruit_images))
                self.is_bomb = False
            except:
                self.image = None
                self.is_bomb = False
                self.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        if self.image:
            self.image = pygame.transform.scale(self.image, (50, 50))
        self.x = random.randint(50, screen_width - 50)
        self.y = screen_height
        self.speed = random.randint(7, 12)
        self.rect = pygame.Rect(self.x - 25, self.y - 25, 50, 50) if not self.image else self.image.get_rect(center=(self.x, self.y))
        self.cut = False

    def move(self):
        self.y -= self.speed
        self.rect.center = (self.x, self.y)

    def draw(self):
        if not self.cut:
            if self.image:
                screen.blit(self.image, self.rect)
            else:
                pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 25)

# Hand Detection using Mediapipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)
mp_draw = mp.solutions.drawing_utils

def detect_hand(frame):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(frame_rgb)
    hand_rect = None
    if result.multi_hand_landmarks:
        for landmarks in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, landmarks, mp_hands.HAND_CONNECTIONS)
            x_min, y_min = 1e6, 1e6
            x_max, y_max = 0, 0
            for landmark in landmarks.landmark:
                x, y = int(landmark.x * frame.shape[1]), int(landmark.y * frame.shape[0])
                x_min, y_min = min(x_min, x), min(y_min, y)
                x_max, y_max = max(x_max, x), max(y_max, y)
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            hand_rect = (x_min, y_min, x_max - x_min, y_max - y_min)
    return frame, hand_rect

def level_screen(level):
    screen.fill((0, 0, 0))
    font = pygame.font.Font(None, 74)
    text = font.render(f'Level {level}', True, (255, 255, 255))
    screen.blit(text, (screen_width//2 - text.get_width()//2, screen_height//2 - text.get_height()//2))
    pygame.display.update()
    time.sleep(2)

def game_loop():
    level = 1
    score = 0
    fruits = []
    start_time = time.time()
    points_to_advance = 20
    game_time = 60

    level_screen(level)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        return

    cam_width, cam_height = 320, 240
    cam_x, cam_y = screen_width - cam_width - 10, 10

    while True:
        elapsed_time = time.time() - start_time
        remaining_time = int(game_time - elapsed_time)

        screen.fill((255, 255, 255))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                cap.release()
                cv2.destroyAllWindows()
                return

        ret, frame = cap.read()
        if not ret:
            print("Can't receive frame. Exiting ...")
            break

        frame = cv2.flip(frame, 1)
        frame_with_landmarks, hand = detect_hand(frame)

        frame_resized = cv2.resize(frame_with_landmarks, (cam_width, cam_height))
        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
        screen.blit(frame_surface, (cam_x, cam_y))

        if random.randint(1, 20) == 1:
            fruits.append(Fruit())

        for fruit in fruits[:]:
            fruit.move()
            fruit.draw()

            if hand:
                hx, hy, hw, hh = hand
                hand_x = hx * (screen_width / frame.shape[1])
                hand_y = hy * (screen_height / frame.shape[0])
                hand_w = hw * (screen_width / frame.shape[1])
                hand_h = hh * (screen_height / frame.shape[0])

                hand_rect = pygame.Rect(hand_x, hand_y, hand_w, hand_h)
                if fruit.rect.colliderect(hand_rect) and not fruit.cut:
                    fruit.cut = True
                    fruits.remove(fruit)
                    try:
                        cut_sound.play()
                    except:
                        pass
                    score += 1 if not fruit.is_bomb else -1

            if fruit.y < -50:
                fruits.remove(fruit)

        font = pygame.font.Font(None, 36)
        text = font.render(f'Score: {score}', True, (0, 0, 0))
        screen.blit(text, (10, 10))

        timer_text = font.render(f'Time: {remaining_time}s', True, (255, 0, 0))
        screen.blit(timer_text, (screen_width - 150, 10))

        cam_label = font.render('Hand Detection:', True, (0, 0, 0))
        screen.blit(cam_label, (cam_x, cam_y - 30))

        pygame.display.update()

        if remaining_time <= 0:
            if score >= points_to_advance:
                level += 1
                points_to_advance *= 2
                fruits.clear()
                start_time = time.time()
                level_screen(level)
            else:
                screen.fill((0, 0, 0))
                over_font = pygame.font.Font(None, 74)
                over_text = over_font.render('Game Over', True, (255, 0, 0))
                screen.blit(over_text, (screen_width//2 - over_text.get_width()//2, screen_height//2 - over_text.get_height()//2))
                pygame.display.update()
                time.sleep(3)
                pygame.quit()
                cap.release()
                cv2.destroyAllWindows()
                return

        clock.tick(60)

def instructions_screen():
    while True:
        screen.fill((0, 0, 0))
        font = pygame.font.Font(None, 50)
        lines = [
            "Instructions:",
            "- Use your HAND to cut fruits.",
            "- Avoid touching bombs!",
            "- Each fruit = +1 point.",
            "- Each bomb = -1 point.",
            "Reach the target score to level up.",
            "Good luck!"
        ]
        for i, line in enumerate(lines):
            text = font.render(line, True, (255, 255, 255))
            screen.blit(text, (50, 50 + i*60))

        back_button = pygame.Rect(10, screen_height - 60, 120, 50)
        pygame.draw.rect(screen, (200, 0, 0), back_button)
        back_text = pygame.font.Font(None, 36).render('Back', True, (255, 255, 255))
        screen.blit(back_text, (back_button.x + 20, back_button.y + 10))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):
                    return  # Go back to main menu

def main_menu():
    while True:
        screen.fill((50, 150, 200))
        font = pygame.font.Font(None, 74)
        title = font.render('Fruit Ninja Clone', True, (255, 255, 255))
        screen.blit(title, (screen_width//2 - title.get_width()//2, 100))

        play_button = pygame.Rect(screen_width//2 - 100, 250, 200, 50)
        instructions_button = pygame.Rect(screen_width//2 - 100, 350, 200, 50)
        quit_button = pygame.Rect(screen_width//2 - 100, 450, 200, 50)

        pygame.draw.rect(screen, (0, 200, 0), play_button)
        pygame.draw.rect(screen, (0, 0, 200), instructions_button)
        pygame.draw.rect(screen, (200, 0, 0), quit_button)

        font_small = pygame.font.Font(None, 36)
        play_text = font_small.render('Play', True, (255, 255, 255))
        instructions_text = font_small.render('Instructions', True, (255, 255, 255))
        quit_text = font_small.render('Quit', True, (255, 255, 255))

        screen.blit(play_text, (play_button.x + 60, play_button.y + 10))
        screen.blit(instructions_text, (instructions_button.x + 25, instructions_button.y + 10))
        screen.blit(quit_text, (quit_button.x + 60, quit_button.y + 10))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_button.collidepoint(event.pos):
                    game_loop()
                if instructions_button.collidepoint(event.pos):
                    instructions_screen()
                if quit_button.collidepoint(event.pos):
                    pygame.quit()
                    quit()

if __name__ == "__main__":
    main_menu()
