#By David
#Use the supplied impulse response for the program to function. Credit to jamespeacock4616 on freesound.org for the impulse response.

import numpy as np
import wave
import struct
from scipy.signal import convolve
from pathlib import Path

def quote(s):
    if len(s) < 2:
        return False
    return (s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")

#Asks the user to input the filepaths for the sample and impulse response.

def filePaths(s):
    while s[-4:] != ".WAV" and s[-4:] != ".wav":
        if quote(s):
            s = s[1:-1]
        if s[-4:] != ".WAV" and s[-4:] != ".wav":
            print("File type not supported, use .WAV files ONLY")
        if not Path(s).is_file():
            print("File not found, try again: ")
            s = "placeholder"
    return s

def main():
    sampleIn = "placeholder"
    sampleIn = str(input("Enter the sample filepath, ONLY .WAV files supported: "))
    filePaths(sampleIn)

    impulseResponse = "placeholder"
    impulseResponse = str(input("Enter the impulse response filepath, ONLY .WAV files supported: "))
    filePaths(impulseResponse)

    userSampleRateInput = False
    while userSampleRateInput == False:
        try:
            sampleRate = input("Enter the desired sample rate, leave blank for default (Default is 44100): ")
            if sampleRate == "":
                sampleRate = 44100
            int(sampleRate)
            userSampleRateInput = True
        except ValueError:
            print("Sample rate must be a float, try again: ")
    
    print("Working... ")

    #Reads the sample and gathers information about the frames and audio channels.

    wavFile = wave.open(sampleIn, 'r')
    wavFrames = wavFile.getnframes()
    wavChannels = wavFile.getnchannels()
    reverbFrames = wavFile.readframes(wavFrames)
    totalFrames = wavFrames * wavChannels
    wavFile.close()

    #Does the same for the impulse response.

    wavFile = wave.open(impulseResponse, 'r')
    impulseFrames = wavFile.getnframes()
    impulseChannels = wavFile.getnchannels()
    impulseData = wavFile.readframes(impulseFrames)
    totalImpulseFrames = impulseFrames * impulseChannels
    wavFile.close()

    #Unpacks the audio data and normalises them into two dimensional arrays.

    reverbFrames = struct.unpack('{n}h'.format(n=totalFrames), reverbFrames)
    reverbFrames = np.array([reverbFrames[0::2], reverbFrames[1::2]], dtype=np.float64)
    reverbFrames[0] /= np.max(np.abs(reverbFrames[0]), axis=0)
    reverbFrames[1] /= np.max(np.abs(reverbFrames[1]), axis = 0)

    impulseData = struct.unpack('{n}h'.format(n=totalImpulseFrames), impulseData)
    impulseData = np.array([impulseData[0::2], impulseData[1::2]], dtype = np.float64)
    impulseData[0] /= np.max(np.abs(impulseData[0]), axis = 0)
    impulseData[1] /= np.max(np.abs(impulseData[1]), axis = 0)

    #Asks the user for the desired wet/dry gain.

    userGainDryInput = False
    while userGainDryInput == False:
        try:
            gainDry = input("Enter the desired dry gain, leave blank for default (Default is 1): ")
            if gainDry == "":
                gainDry = 1
            int(gainDry)
            userGainDryInput = True
        except ValueError:
            print("Dry gain must be an integer, try again: ")
        
    userGainWetInput = False 
    while userGainWetInput == False:
        try:
            gainWet = input("Enter the desired wet gain, leave blank for default (Default is 1): ")
            if gainWet == "":
                gainWet = 1
            int(gainWet)
            userGainWetInput = True
        except ValueError:
            print("Wet gain must be an integer, try again: ")

    userGainOutputInput = False
    while userGainOutputInput == False:
        try:
            outputGain = input("Enter the desired output gain, leave blank for default (Default is 0.05): ")
            if outputGain == "":
                outputGain = 0.05
            float(outputGain)
            userGainOutputInput = True
        except ValueError:
            print("Output gain must be a float, try again: ")

    print("Working... Note that applying reverb can take several minutes depending on the length of the sample. ")

    #Performs the convolution and applies the gain to the output.

    impulseOut = np.zeros([2, np.shape(reverbFrames)[1] + np.shape(impulseData)[1] - 1], dtype = np.float64)
    impulseOut[0] = outputGain * (convolve(reverbFrames[0] * gainDry, impulseData[0] * gainWet, method = 'fft'))
    impulseOut[1] = outputGain * (convolve(reverbFrames[1] * gainDry, impulseData[1] * gainWet, method = 'fft'))

    #Converts the processed audio data back into 16 bit integers.

    impulseNum = np.zeros((impulseOut.shape))
    impulseNum[0] = (impulseOut[0]*int(np.iinfo(np.int16).max)).astype(np.int16)
    impulseNum[1] = (impulseOut[1]*int(np.iinfo(np.int16).max)).astype(np.int16)

    reverbRender = np.empty((impulseNum[0].size + impulseNum[1].size), dtype = np.int16)
    reverbRender[0::2] = impulseNum[0]
    reverbRender[1::2] = impulseNum[1]

    #Defines the parameters for the output .WAV file, and writes the convoluted audio data to the file.

    nFrames = totalFrames
    compressionType = "NONE"
    compressionName = "uncompressed"
    nChannels = 2
    wavWidth = 2

    wavWrite = wave.open('output.wav', 'w')
    wavWrite.setparams((nChannels, wavWidth, int(sampleRate), nFrames, compressionType, compressionName))
    for s in range(nFrames):
        wavWrite.writeframes(struct.pack('h', reverbRender[s]))
    wavWrite.close()

    print("File has finished processing as output.wav.")

main()