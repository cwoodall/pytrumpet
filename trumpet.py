import pyaudio as pa
import numpy as np
import struct
import matplotlib.pyplot as plt
import time

def block2short(block):
    count = len(block)/2
    fmt = "%dh" % (count)
    return struct.unpack(fmt, block)

if __name__ == "__main__":
    fig = plt.figure()
    plt.axis([0,128,0,1000])
    plt.ion()
    plt.show()
    __CHUNK__ = 4096
    __FORMAT__ = pa.paInt16
    __CHANNELS__ = 1
    __RATE__ = 44200

    __DEV_INDEX__ = 0

    audio = pa.PyAudio()
    stream = audio.open(format = __FORMAT__,
                        channels = __CHANNELS__,
                        frames_per_buffer = __CHUNK__,
                        input = True,
                        input_device_index = __DEV_INDEX__,
                        rate = __RATE__)
    stream.start_stream()

    fir = [0.000198,
           0.000524,
           0.001090,
           0.001979,
           0.003267,
           0.005022,
           0.007290,
           0.010087,
           0.013393,
           0.017145,
           0.021238,
           0.025527,
           0.029835,
           0.033963,
           0.037702,
           0.040856,
           0.043248,
           0.044741,
           0.045249,
           0.044741,
           0.043248,
           0.040856,
           0.037702,
           0.033963,
           0.029835,
           0.025527,
           0.021238,
           0.017145,
           0.013393,
           0.010087,
           0.007290,
           0.005022,
           0.003267,
           0.001979,
           0.001090,
           0.000524,
           0.000198]


    while 1:
        try:
            block = stream.read(__CHUNK__)
        except:
            print "dropped"
            continue
        
        data = block2short(block)
        # Low Pass Filter to 1kHz using http://arc.id.au/FilterDesign.html
        data = np.convolve(data, fir)
            
        # subsample by 16 to go from 44200Hz to 2762.5 Hz
        data = data[::16]
#        print(data)
        mag = abs(np.fft.rfft(data))
#        pwr = [i**2 for i in mag]
        

        plt.plot(mag)
        plt.draw()
        plt.pause(.1)
        plt.cla()
        #        time.sleep(.5)
#            downsample(
#    except except:
#        stream.stop_stream()
#        stream.close()
#        audio.terminate()
               
