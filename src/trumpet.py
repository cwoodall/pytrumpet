# Import PyGame to make a nice UI, easily (possibly move to pytkinter?)
import pygame
from pygame.locals import *
# Import mingus to play notes using a soundfont (found in the soundfont folder)
from mingus.containers.Note import Note
from mingus.midi import fluidsynth

# FIXME: This code is terrible... make it better

class Trumpet(object):
    default_note_mapping = [
            ['C-4','A#-3','B-3','A-3','G#-3','G-3','G#-3', 'G-3'],      # Freq Range 0 mapping
            ['G-4','F-4', 'F#-4', 'E-4', 'D#-4', 'D-4', 'D#-4', 'C#-4'] # Freq Range 1 mapping
        ]
    def __init__(self, 
                 valve_mapping=[K_a, K_s, K_d],
                 freq_ranges=[(180,260), (260,392)], # FIXME: add remaining ranges and fine-tune
                 note_mapping=default_note_mapping):
        self.valve_mapping = valve_mapping # Valve to key map
        self.freq_ranges = freq_ranges
        self.note_mapping = note_mapping
        
        fluidsynth.init("soundfonts/trumpet.sf2", "alsa")


    def freq2idx(self, freq):
        for idx, freq_range in enumerate(self.freq_ranges):
            if (freq >= freq_range[0]) and (freq <= freq_range[1]):
                return idx
        raise Exception()

class TrumpetDisplay(object):
    __RUNNING = True
    __DONE = False
    def texts(self, text_str, pos):
        font=pygame.font.Font(None,30)
        scoretext=font.render(text_str, 1, (255,255,255))
        self.screen.blit(scoretext, pos)

    def __init__(self, xy=(640,480)):
        self.RUNNING = True
        self.DONE = False
        self.run_state = self.__RUNNING
        self.xy = xy
        pygame.init()
        self.screen = pygame.display.set_mode(xy)
        self.keys = []
        self.stop_timer = 0
        self.prev_note = ""

    def update_display(self, tpt):
        # Look for crucial events and updated the state 
        # exits with state of self.run_state
        for event in pygame.event.get():
            if event.type == QUIT:
                self.run_state = self.__DONE
                return self.run_state
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.run_sate = self.__DONE
                    return self.run_state
        
        keys = pygame.key.get_pressed()
        valves = [keys[valve_idx] for valve_idx in tpt.valve_mapping]
        self.screen.fill((0, 0, 0))
        frequency = 300
        
        try:
            freq_idx = tpt.freq2idx(frequency)
            note_str = tpt.note_mapping[freq_idx][valves[0] | (valves[1]<<1) | (valves[2]<<2)]
            self.texts("Freq: {0} | Note: {1}".format(
                frequency, note_str),(0,0))
            
            if (self.prev_note is not "") and (self.prev_note is not note_str):
                fluidsynth.stop_Note(Note(self.prev_note))            
                fluidsynth.play_Note(Note(note_str))
                self.stop_timer = 0
            elif self.stop_timer == 500:
                fluidsynth.stop_Note(Note(self.prev_note))            
            self.prev_note = note_str
            self.stop_timer += 1
        except:
            self.texts("Silence",(0,0))
        
        pygame.display.update()


if __name__ == '__main__':
    # Initialize pygame
#    pygame.init()
#    screen = pygame.display.set_mode((640,480))
    tpt = Trumpet()
    disp = TrumpetDisplay()
    
    while disp.run_state == disp.RUNNING:
        disp.update_display(tpt)
