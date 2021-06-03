from random import randrange as rnd
import socket
import pygame as pg
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt
import time

HOST = "localhost"
PORT = 1883
MQTT_USER = "user"
MQTT_PASS = "password"

Client = mqtt.Client('client1')
Client.username_pw_set(MQTT_USER,MQTT_PASS)

Client.connect(HOST,PORT)
Client.loop_start()
UDP_IP = "127.0.0.1"
UDP_PORT = 8094
WIDTH, HEIGHT = 800, 600

#Координаты

ball_coordinates = []
movement_coordinates = []

#Определение функции

def check_if_coordinate_exist(coordinate, list_of_coordinates):
    if not list_of_coordinates:
        return False
    last_cor = list_of_coordinates[-1]
    if last_cor["x"] == coordinate["x"] and last_cor["y"] == coordinate["y"]:
        return True
    return False

def draw(coordinates):
    plt.gca().invert_yaxis()
    x_list = [cor["x"] for cor in coordinates]
    y_list = [cor["y"] for cor in coordinates]
    plt.plot(x_list, y_list)
    plt.show()

fps = 60

#Параметры движения

movement_w = 330
movement_h = 35
movement_speed = 15
movement = pg.Rect(WIDTH // 2 - movement_w // 2, HEIGHT - movement_h - 10, movement_w, movement_h)

#Параметры мяча

ball_radius = 20
ball_speed = 6
ball_rect = int(ball_radius * 2 ** 0.5)
ball = pg.Rect(WIDTH // 2 - movement_w // 2, HEIGHT - movement_h - 10, ball_rect, ball_rect)
dx, dy = 1, -1

#Параметры блоков

block_list = [pg.Rect(10 + 120 * i, 2 + 72 * j, 110, 70) for i in range(10) for j in range(4)]
color_list = [(rnd(30, 256), rnd(30, 256), rnd(30, 256)) for i in range(10) for j in range(4)]

pg.init()
sc = pg.display.set_mode((WIDTH, HEIGHT))
clock = pg.time.Clock()

#Настройка цвета

bg = pg.Surface((WIDTH, HEIGHT))
bg.fill((21, 21, 21))

#Определение действий

def detect_collision(dx, dy, ball, rect):
    if dx > 0:
        delta_x = ball.right - rect.left
    else:
        delta_x = rect.right - ball.left
    if dy > 0:
        delta_y = ball.bottom - rect.top
    else:
        delta_y = rect.bottom - ball.top

    if abs(delta_x - delta_y) < 10:
        dx, dy = -dx, -dy
    elif delta_x > delta_y:
        dy = -dy
    elif delta_y > delta_x:
        dx = -dx
    return dx, dy


while True:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            exit()
    sc.blit(bg, (0, 0))
    [pg.draw.rect(sc, color_list[color], block) for color, block in enumerate(block_list)]
    pg.draw.rect(sc, pg.Color(49,160,49), movement)
    pg.draw.circle(sc, pg.Color('white'), ball.center, ball_radius)
    ball.x += ball_speed * dx
    ball.y += ball_speed * dy
    if ball.centerx < ball_radius or ball.centerx > WIDTH - ball_radius:
        dx = -dx
    if ball.centery < ball_radius:
        dy = -dy
    if ball.colliderect(movement) and dy > 0:
        dx, dy = detect_collision(dx, dy, ball, movement)
    hit_index = ball.collidelist(block_list)
    if hit_index != -1:
        hit_rect = block_list.pop(hit_index)
        hit_color = color_list.pop(hit_index)
        dx, dy = detect_collision(dx, dy, ball, hit_rect)
        hit_rect.inflate_ip(ball.width * 3, ball.height * 3)
        pg.draw.rect(sc, hit_color, hit_rect)
        fps += 2
    if ball.bottom > HEIGHT:
        print('GAME OVER!')
        draw(ball_coordinates)
        draw(movement_coordinates)
        exit()
    elif not len(block_list):
        print('WIN!!!')
        exit()
    key = pg.key.get_pressed()
    if key[pg.K_LEFT] and movement.left > 0:
        movement.left -= movement_speed
    if key[pg.K_RIGHT] and movement.right < WIDTH:
        movement.right += movement_speed
        
# Информация о положении

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    movement_cor = {"x": movement.centerx, "y": movement.centery}
    ball_cor = {"x": ball.centerx, "y": ball.centery}
    if not check_if_coordinate_exist(movement_cor, movement_coordinates):
        movement_coordinates.append(movement_cor)
        MESSAGE_MOVE = b"coord,obj=movement x_coord=%d,y_coord=%d " % (movement.centerx, movement.centery)
        sock.sendto(MESSAGE_MOVE, (UDP_IP, UDP_PORT))
        Client.publish("TOPIC_Move", f"x={movement.centerx},y={movement.centery}")
    if not check_if_coordinate_exist(ball_cor, ball_coordinates):
        ball_coordinates.append(ball_cor)
        MESSAGE_BALL = b"coord,obj=ball x_coord=%d,y_coord=%d " % (ball.centerx, ball.centery)
        sock.sendto(MESSAGE_BALL, (UDP_IP, UDP_PORT))
        Client.publish("TOPIC_BALL",f"x={ball.centerx},y={ball.centery}")
        
    pg.display.flip()
    clock.tick(fps)