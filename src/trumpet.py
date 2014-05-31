# Import PyGame to make a nice UI, easily (possibly move to pytkinter?)
import pygame
from pygame.locals import *

# Import mingus to play notes using a soundfont (found in the soundfont folder)
from mingus.containers.Note import Note
from mingus.midi import fluidsynth

# Import multiprocessing library to try to deal with the audio input
from multiprocessing import Value, Process

# Import portaudio (pyaudio), struct (to unpack), and scipy (fft)
import pyaudio as pa
import numpy as np
import scipy as sp
import scipy.signal
import struct
import sys

# FIXME: This code is terrible... make it better
def block2short(block):
    count = len(block)/2
    fmt = "%dh" % (count)
    return struct.unpack(fmt, block)

class Trumpet(object):
    default_freq_ranges = [
        (163,234), 
        (234,350), 
        (350,467),
        (467,588),
        (588,784)] # FIXME: add remaining ranges and fine-tune

    default_note_mapping = [
      # 000   , 100  , 010  , 110  , 001  , 101  , 011  , 111
      # First Range
        ['A#-3','G#-3','A-3' ,'G-3' ,'F#-3','F-3' ,'F#-3','E-3'],
      # Second Range
        ['F-4' ,'D#-4','E-4' ,'D-4' ,'B-3' ,'C-4' ,'C#-4','B-3'],
      # Third Range
        ['A#-4','G#-4','A-4' ,'G-4' ,'F#-3','F-4' ,'G-4' ,'E-4'],
      # Fourth Range
        ['D-5' ,'C-5','C#-5' ,'B-4' ,'B-3' ,'C-4' ,'C#-4','B-3'],
      # Fifth Range
        ['F-5' ,'D#-5','E-5' ,'D-5' ,'B-4' ,'C-6' ,'C#-6','B-4'],

#      ['G-4' ,'F-4' ,'F#-4','E-4' ,'D#-4','D-4' ,'D#-4','C#-4'] # Freq Range 1 mapping
    ]
    def __init__(self, 
                 valve_mapping=[K_a, K_s, K_d],
                 freq_ranges=default_freq_ranges,
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

def getInputTone(freq, run_state):
    # Set initialization variables to interface
    # with microphone/alsa input channel
    __CHUNK__ = 4096*2
    __FORMAT__ = pa.paInt16
    __CHANNELS__ = 1
    __RATE__ = 44100
    __DEV_INDEX__ = 3

    # Open and start a pyaudio audio stream
    audio = pa.PyAudio()
    stream = audio.open(format = __FORMAT__,
                        channels = __CHANNELS__,
                        frames_per_buffer = __CHUNK__,
                        input = True,
                        input_device_index = __DEV_INDEX__,
                        rate = __RATE__)
    stream.start_stream()
    
    # Setup a filter to run over the time domain information
    filter_order = 15
    # High Order Filter
    filter_cutoff = 1000.0 / (__RATE__/2.0)#Hz
    fir = sp.signal.firwin(filter_order + 1, filter_cutoff)
    while run_state.value:
        try:
            block = stream.read(__CHUNK__)
            prev_block = block
        except KeyboardInterrupt:
            raise
        except:
            print "dropped"
            block = prev_block
        
        data = block2short(block)
        # Low Pass Filter to 1kHz using http://arc.id.au/FilterDesign.html
        data_filt = sp.signal.lfilter(fir, 1.0, data)
        N = 16 # downsampling coefficient
        # subsample by 16 t o go from 44200Hz to 2762.5 Hz
        data_ds = data_filt[filter_order::N]
        mag = abs(np.fft.rfft(data_ds))
        
        freqs = np.linspace(0,__RATE__/(2*N), len(mag) )        
        freq.value = freqs[np.where(mag == max(mag))]
    stream.stop_stream()
    stream.close()

    audio.terminate()

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

    def cleanup(self):
        fluidsynth.stop_everything()

    def update_display(self, tpt, freq):
        frequency = freq.value
        # Look for crucial events and updated the state 
        # exits with state of self.run_state
        for event in pygame.event.get():
            if event.type == QUIT:
                self.run_state = self.__DONE
                return self.run_state
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.run_state = self.__DONE
                    return self.run_state
        
        keys = pygame.key.get_pressed()
        valves = [keys[valve_idx] for valve_idx in tpt.valve_mapping]
        self.screen.fill((0, 0, 0))
#        frequency = 300
        
        try:        
            if frequency < tpt.freq_ranges[0][0]:
                self.texts("Silence", (0,0))
                if (self.prev_note is not ""):
                    fluidsynth.stop_Note(Note(self.prev_note))            
                    self.prev_note = ""
                    print "stopped note"
            else:
                freq_idx = tpt.freq2idx(int(frequency))
                note_str = tpt.note_mapping[freq_idx][valves[0] | (valves[1]<<1) | (valves[2]<<2)]
                self.texts("Freq: {0} | Note: {1}".format(
                    frequency, note_str),(0,0))
                
                if (self.prev_note is not "") and (self.prev_note is not note_str):
                    fluidsynth.stop_Note(Note(self.prev_note))            
                    fluidsynth.play_Note(Note(note_str))
                    self.prev_note = note_str
                elif self.prev_note is "":
                    fluidsynth.play_Note(Note(note_str))
                    self.prev_note = note_str
        except KeyboardInterrupt:
            raise
        except:
            print "Unexpected error:", sys.exc_info()[0]
#            self.texts("".format(frequency),(0,0))
        
        pygame.display.update()


if __name__ == '__main__':
    # Initialize pygame
#    pygame.init()
#    screen = pygame.display.set_mode((640,480))
    tpt = Trumpet()
    disp = TrumpetDisplay()
    freq = Value('d', 0);
    run_state = Value('i', 1)

    input_tone_p = Process(target=getInputTone, args=(freq,run_state))
    input_tone_p.start()
    try:
        while disp.run_state == disp.RUNNING:
            disp.update_display(tpt, freq)
    finally:
        print "Exiting"
        run_state.value = 0
        input_tone_p.join()
        disp.cleanup()
