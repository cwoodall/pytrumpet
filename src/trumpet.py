# Import multiprocessing library to try to deal with the audio input
from multiprocessing import Value, Process

# Import PyGame to make a nice UI, easily (possibly move to pytkinter?)
import pygame
from pygame.locals import *

# Import mingus to play notes using a soundfont (found in the soundfont folder)
from mingus.containers.Note import Note
from mingus.midi import fluidsynth

# Import portaudio (pyaudio), struct (to unpack), and scipy (fft)
import pyaudio as pa
import numpy as np
import scipy as sp
import scipy.signal
import struct

import sys, argparse, operator

# FIXME: This code is terrible... make it better
def block2short(block):
    count = len(block)/2
    fmt = "%dh" % (count)
    return struct.unpack(fmt, block)

class Trumpet(object):
    default_freq_ranges = [(163,234), 
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
    default_valve_mapping=[K_a, K_s, K_d]

    def __init__(self, 
                 soundfont_file,
                 soundfont_driver="alsa",
                 valve_mapping=default_valve_mapping,
                 freq_ranges=default_freq_ranges,
                 note_mapping=default_note_mapping):
        self.valve_mapping = valve_mapping # Valve to key map
        self.freq_ranges = freq_ranges
        self.note_mapping = note_mapping
        self.current_note = ""

        fluidsynth.init(soundfont_file, "alsa")

    def play_Note(self, freq, keys, vol=1):
        next_note = self.lookup_Note(freq, keys)
        if next_note != self.current_note:
            if self.current_note:
                fluidsynth.stop_Note(Note(self.current_note),1)
            print "playing note"
            fluidsynth.play_Note(Note(next_note),1)
            self.current_note = next_note

    def stop_Note(self):
        if self.current_note:
            fluidsynth.stop_Note(Note(self.current_note),1)
            print "stopping note"
        self.current_note = ""

    def lookup_Note(self, freq, keys):
        return self.note_mapping[self.freq2idx(freq)][self.keys2valve_idx(keys)]

    def keys2valve_idx(self, keys):
        """
        Turns a pygame keys status array into a index for indexing into the 
        note_mapping array. Uses the indexe in keys specified by the
        valve_mapping array.
        """
        return reduce(operator.or_, [keys[self.valve_mapping[i]]<<i for i in range(3)])

    def freq2idx(self, freq):
        """
        Convert a frequency input to an index for indexing into the 
        note_mapping array

        TODO: - Make it handle out of range frequencies better.
        """
        for idx, freq_range in enumerate(self.freq_ranges):
            if (freq >= freq_range[0]) and (freq < freq_range[1]):
                return idx
        return 0

def getInputTone(freq, run_state):
    # Set initialization variables to interface
    # with microphone/alsa input channel
    __CHUNK__ = 4096
    __FORMAT__ = pa.paInt16
    __CHANNELS__ = 1
    __RATE__ = 44100
    __DEV_INDEX__ =3

    # Open and start a pyaudio audio stream
    audio = pa.PyAudio()
    print audio.get_default_host_api_info()
    stream = audio.open(format = __FORMAT__,
                        channels = __CHANNELS__,
                        frames_per_buffer = __CHUNK__,
                        input = True,
                        input_device_index = __DEV_INDEX__,
                        rate = __RATE__)
    stream.start_stream()
    
    # Setup a filter to run over the time domain information
    filter_order = 255
    # High Order Filter
    filter_cutoff = 1000.0 / (__RATE__/2.0)#Hz
    fir = sp.signal.firwin(filter_order + 1, filter_cutoff)
    N = 16 # downsampling coefficient

    freqs = np.linspace(0,__RATE__/(2*N), __CHUNK__/(16*2))
    
    while run_state.value:
        try:
            block = stream.read(__CHUNK__)
            prev_block = block
        except KeyboardInterrupt:
            raise
        except:
            print "dropped"
#            continue
            block = prev_block
        
        data = block2short(block)
        # Low Pass Filter to 1kHz using http://arc.id.au/FilterDesign.html
        data_filt = sp.signal.lfilter(fir, 1.0, data)

        # subsample by 16 t o go from 44200Hz to 2762.5 Hz
#        data_ds = data_filt[filter_order::N]
        data_ds = data_filt[0::N]
        mag = abs(np.fft.rfft(data_ds))

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

    def __init__(self, xy=(400,35)):
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
        pygame.quit()
        print "Stop all notes"

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
        self.screen.fill((0, 0, 0))
        try:
            if frequency < tpt.freq_ranges[0][0]:
                self.texts("Silence", (5,5))
                tpt.stop_Note()
            else:
                tpt.play_Note(frequency, keys)
                self.texts("Freq: {0} | Note: {1}".format(
                    frequency, tpt.current_note),(5,5))
        except KeyboardInterrupt:
            raise
        except:
            print "Unexpected error:", sys.exc_info()[0]
            raise
        pygame.display.update()

if __name__ == '__main__':
    
    cli_argparser = argparse.ArgumentParser(description='Play trumpet using your computer')
    cli_argparser.add_argument('-s', '--soundfont', action='store', default='default.sf2')
    cli_args = cli_argparser.parse_args(sys.argv[1:])
    # Initialize pygame
    tpt = Trumpet(cli_args.soundfont)
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
        tpt.stop_Note()
        disp.cleanup()
