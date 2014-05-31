import pyaudio as pa

import struct
import numpy as np
import matplotlib.pyplot as plt
import scipy as sp
import scipy.signal
import time

def block2short(block):
    count = len(block)/2
    fmt = "%dh" % (count)
    return struct.unpack(fmt, block)

if __name__ == "__main__":
    # fig = plt.figure()
    # plt.axis([0,128,0,1000])
    # plt.ion()
    # plt.show()
    __CHUNK__ = 4096*2
    __FORMAT__ = pa.paInt16
    __CHANNELS__ = 1
    __RATE__ = 44100

    __DEV_INDEX__ = 3


    audio = pa.PyAudio()
    stream = audio.open(format = __FORMAT__,
                        channels = __CHANNELS__,
                        frames_per_buffer = __CHUNK__,
                        input = True,
                        input_device_index = __DEV_INDEX__,
                        rate = __RATE__)
    stream.start_stream()
    filter_order = 255
 # High Order Filter
    filter_cutoff = 1000.0 / (__RATE__/2.0)#Hz
    fir = sp.signal.firwin(filter_order + 1, filter_cutoff)
    
    while 1:
        try:
            block = stream.read(__CHUNK__)
        except:
            print "dropped"
            continue
        
        data = block2short(block)
#        data = [i/2**16 for i in data]
        # Low Pass Filter to 1kHz using http://arc.id.au/FilterDesign.html
    #    data = np.convolve(data, fir)
        data_filt = sp.signal.lfilter(fir, 1.0, data)
        N = 16 # downsampling coefficient
        # subsample by 16 t o go from 44200Hz to 2762.5 Hz
        data_ds = data_filt[filter_order::N]
#        print(data)
        mag = abs(np.fft.rfft(data_ds))
        
#        pwr = [i for i in mag]
        
        freqs = np.linspace(0,__RATE__/(2*N), len(mag) )        
        print(freqs)
        # Plot the frequency and the max frequency detected
#        plt.plot(freqs,pwr)
#        plt.stem([freqs[pwr.index(max(pwr))]], [max(pwr)], '-.')
#        plt.ylim([0, .2])
        print(freqs[np.where(mag == max(mag))])

        # Decision point (coupled with key presses)
#        if 
#        plt.draw()
#        plt.pause(.1)
#        plt.cla()
#    except except:
#        stream.stop_stream()
#        stream.close()
#        audio.terminate()
               
