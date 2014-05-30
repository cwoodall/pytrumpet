from mingus.containers.Note import Note
from mingus.midi import fluidsynth
import time

fluidsynth.init("soundfonts/trumpet.sf2", "alsa")

fluidsynth.play_Note(Note("C-4"))
time.sleep(1)
fluidsynth.stop_Note(Note("C-4"))

fluidsynth.play_Note(Note("F#-4"))
time.sleep(1)
fluidsynth.stop_Note(Note("F#-4"))

fluidsynth.play_Note(Note("G-4"))
time.sleep(1)
fluidsynth.stop_Note(Note("G-4"))

fluidsynth.play_Note(Note("C-5"))
time.sleep(1)
fluidsynth.stop_Note(Note("C-5"))
