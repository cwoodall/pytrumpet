#!/usr/bin/python
## 
# trumpet.py : Play trumpet using your computer through python
# 
# trumpet.py allows you to play a sound font by using your keyboard as valves,
# and your microphone to listen to the sound produced by a mouthpiece. Using
# these two features a note is played using Fluidsynth (via mingus) from a 
# soundfont.
#
# Developers: Christopher Woodall <chris.j.woodall@gmail.com>
# Date: June 02, 2014
# Version: 0.1
##
# Import multiprocessing library to try to deal with the audio input
from multiprocessing import Value, Process

# Import PyGame to make a nice UI, easily (possibly move to pytkinter?)
import pygame
from pygame.locals import *

# Import mingus to play notes using a soundfont (found in the soundfont folder)
from mingus.containers.Note import Note
from mingus.midi import fluidsynth

# Import portaudio bindings (pyaudio), struct (to unpack), and scipy and numpy
# (fft and signal processing helper functions)
import pyaudio as pa
import numpy as np
import scipy as sp
import scipy.signal
import struct

import sys, argparse, operator

def block2short(block):
    """
    Take a binary block produced by pyaudio and turn it into an array of
    shorts. Assumes the pyaudio.paInt16 datatype is being used.
    """
    # Each entry is 2 bytes long and block appears as a binary string (array 
    # of 1 byte characters). So the length of our final binary string is the
    # length of the block divided by 2.
    sample_len = len(block)/2 
    fmt = "%dh" % (sample_len) # create the format string for unpacking
    return struct.unpack(fmt, block)

class Trumpet(object):
    """
    Trumpet class which plays notes and also contains the logic for turning a
    pygame keystate array into a valve position, and for determining which 
    harmonic should be triggered.

    At the time the actual slotting is not implemented so long as a tone within
    a harmonic range is being sent the note will play in tune. Future versions 
    should allow for detuning a note and volume control. (FIXME)
    """
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
        """
        Initialize Trumpet
        """
        self.valve_mapping = valve_mapping # Valve to key map
        self.freq_ranges = freq_ranges     # Freq range to harmonic series
        # Note mapping indexed as [freq range index][valve combo (index)]
        self.note_mapping = note_mapping  

        # Initialize Fluidsynth
        self.soundfont_file = soundfont_file
        self.soundfont_driver = soundfont_driver
        fluidsynth.init(soundfont_file, soundfont_driver)

        # Keep track of the current note state
        self.current_note = "" 


    def play_Note(self, freq, keys, vol=1):
        """
        """

        next_note = self.lookup_Note(freq, keys)
        if next_note != self.current_note:
            if self.current_note:
                fluidsynth.stop_Note(Note(self.current_note),1)
            print "playing note"
            fluidsynth.play_Note(Note(next_note),1)
            self.current_note = next_note

    def stop_Note(self):
        """
        """

        if self.current_note:
            fluidsynth.stop_Note(Note(self.current_note),1)
            print "stopping note"
        self.current_note = ""

    def lookup_Note(self, freq, keys):
        """
        """

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

def getInputTone(freq, run_state, dev_idx=3, rate=44100):
    """
    """
    # Set initialization variables to interface
    # with microphone/alsa input channel
    __CHUNK__ = 4096
    __FORMAT__ = pa.paInt16
    __CHANNELS__ = 1
    __RATE__ = rate
    __DEV_INDEX__ = dev_idx  

    # Open and start a pyaudio audio stream
    audio = pa.PyAudio()
    print audio.get_default_host_api_info()
    stream = audio.open(format = __FORMAT__,
                        channels = __CHANNELS__,
                        frames_per_buffer = __CHUNK__,
                        input = True,
                        input_device_index = __DEV_INDEX__,
                        rate = __RATE__)

    # Setup a filter to run over the time domain information. Cutoff at 1kHz
    filter_order = 255
    filter_cutoff = 1000.0 / (__RATE__/2.0)#Hz
    fir = sp.signal.firwin(filter_order + 1, filter_cutoff)
    N = 16 # downsampling coefficient
    # Setup index to frequency mapping (taking into account downsampling)
    freqs = np.linspace(0,__RATE__/(2*N), __CHUNK__/(2*N))

    # Start audiostream
    stream.start_stream()
    previous_block = []
    while run_state.value:
        try:
            # Retrieve stream data.
            block = stream.read(__CHUNK__)
            prev_block = block
        except KeyboardInterrupt:
            raise
        except:
            print "dropped"
            block = prev_block
        
        # turn block of binary data into an array of ints that can be
        # processed using scipy and numpy
        data = block2short(block)

        # Apply anti-aliasing low pass filter with cutoff of 1kHz
        data_filt = sp.signal.lfilter(fir, 1.0, data)

        # subsample by 16 to go from 44200Hz to 2762.5 Hz. 
        # This is much closer to the sampling rate an embedded device might
        # have considering that we actually don't need to see frequencies about
        # 1kHz or so.
        data_ds = data_filt[0::N]

        # Take the FFT and extract the magnitude.
        mag = abs(np.fft.rfft(data_ds))

        # Find the max frequency spike. Let us just sort of assume this is
        # in the frequency range of the harmonic we want to play. This
        # appears to be mostly accurate for trumpet mouhtpieces. Completely
        # inaccurate for whistling though.
        freq.value = freqs[np.where(mag == max(mag))]

    # Stop and close the stream then exit the function when the
    # state changes.
    stream.stop_stream()
    stream.close()
    audio.terminate()

class TrumpetDisplay(object):
    """
    """
    __RUNNING = True
    __DONE = False
    def texts(self, text_str, pos):
        """
        """
        font=pygame.font.Font(None,30)
        scoretext=font.render(text_str, 1, (255,255,255))
        self.screen.blit(scoretext, pos)

    def __init__(self, xy=(400,35)):
        """
        """
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
        print "Quitting pygame"

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
    cli_argparser.add_argument('-s', '--soundfont', 
                               action='store', default='default.sf2')
    cli_argparser.add_argument('-d', '--dev-idx', 
                               action='store', default='3')
    cli_argparser.add_argument('-r', '--rate', 
                               action='store', default='44100')
    cli_args = cli_argparser.parse_args(sys.argv[1:])

    # Initialize Trumpet and TrumpetDisplay
    tpt = Trumpet(cli_args.soundfont)
    disp = TrumpetDisplay()

    # Start state variables for frequency and run_state. These will
    # be updated inside of the getInputTone "function"/process.
    freq = Value('d', 0);
    run_state = Value('i', 1)
    
    # Start running the getInputTone function as a process with shared memory
    # (run_state) and freq. for freq getInputTone is a producer and nothing 
    # else should write to freq. However, for run_state it is a consumer and 
    # does not write to it. The process will exit when run_state becomes false.
    input_tone_p = Process(target=getInputTone, args=(freq,run_state, int(cli_args.dev_idx), int(cli_args.rate)))
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
