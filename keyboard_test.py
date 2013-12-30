import pygame
from pygame.locals import *
import random

pygame.init()
screen = pygame.display.set_mode((640,480))

valve_map = [K_a, K_s, K_d]
frequency_ranges = [(180, 260),(261, 392)]
note_map = [
    ['C4','Bb3','B3','A3','Ab3','G3','Ab3', 'G3'],
    ['G4','F4', 'Gb4', 'E4', 'Eb4', 'D4', 'Eb4', 'Db4']]
done = False    
def texts(screen, text_str, pos):
   font=pygame.font.Font(None,30)
   scoretext=font.render(text_str, 1, (255,255,255))
   screen.blit(scoretext, pos)

def freq2idx(freq, freq_ranges):
    for idx, freq_range in enumerate(freq_ranges):
        if (freq >= freq_range[0]) and (freq <= freq_range[1]):
            return idx
    raise Exception()
time = 0
frequency = 0


while not done:
    for event in pygame.event.get():
        # any other key event input
        if event.type == QUIT:
            done = True        
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                done = True

    # get key current state
    keys = pygame.key.get_pressed()
    valves = [keys[valve_idx] for valve_idx in valve_map]
#    print(valves)
#    print("\n")
    screen.fill((0, 0, 0))
    if time == 40:
        frequency = random.randint(180,392)
        time = 0
    else:
        time += 1

    try:
        freq_idx = freq2idx(frequency,frequency_ranges)
        note_str = note_map[freq_idx][valves[0] | (valves[1]<<1) | (valves[2]<<2)]
        texts(screen, "Freq: {0} | Note: {1}".format(
            frequency, note_str),(0,0))
    except:
        texts(screen, "Silence",(0,0))


    pygame.display.update()