#! python3
"""
realTimePlotter.py
--------------------------------------------------------------------------------
 Description: Creates a GUI to take values from an Arduino and plot the same on a 
 matplotlib plot. This UI uses a multiprocessing system where one process creates
 the data and the other, in parallel, plot it. A pipe is used to share the data
 between the two processes.


 Modules Used
    matplotlib
    serial
    multiprocessing
    time
    datetime
--------------------------------------------------------------------------------
Author: Mathews John
Date: 08-05-2019
"""
import matplotlib.pyplot as plt
import matplotlib.lines as lines
from matplotlib.widgets import Button
import matplotlib.legend as lgnd
import matplotlib.text as pltTxt

import serial
import multiprocessing as mp
import time
import numpy as np
from datetime import datetime as dt


pauseFlag = 0

# This class plots the data in parallel to data collection
class ProcessPlotter(object):
    """
    This is a process that plots the data. This is a modified version of an example
    that can be found in https://matplotlib.org/3.1.1/gallery/misc/multiprocess_sgskip.html
    """
    def __init__(self):
        self.x = []
        self.y = []

    def terminate(self):
        self.pipe.close()
        #plt.close('all')

    def call_back(self):
        while self.pipe.poll():
            command = self.pipe.recv()
            if command is None or command[0] is 'q':
                self.terminate()
                return False
            elif command[0] is 'r': 
                l_X = list(self.line1.get_xdata())
                l_Y_1 = list(self.line1.get_ydata())
                l_Y_2 = list(self.line2.get_ydata())
                l_Y_3 = list(self.line3.get_ydata())

                self.line1.set_xdata(l_X + [command[1]])
                self.line1.set_ydata(l_Y_1 + [command[2]])
                self.line2.set_xdata(l_X + [command[1]])
                self.line2.set_ydata(l_Y_2 + [command[3]])
                self.line3.set_xdata(l_X + [command[1]])
                self.line3.set_ydata(l_Y_3 + [command[4]])

        # Once the new data has been written, update the plot
        # This is a fast update as opposed to called plt.draw() or plt.pause()
        self.ax.draw_artist(self.ax.patch)

        self.ax.draw_artist(self.line1)
        self.ax.draw_artist(self.line2)
        self.ax.draw_artist(self.line3)

        self.txtX.set_text(str(command[1]))
        self.ax.draw_artist(self.txtX)
        self.txtY1.set_text(str(command[2]))
        self.ax.draw_artist(self.txtY1)
        self.txtY2.set_text(str(command[3]))
        self.ax.draw_artist(self.txtY2)
        self.txtY3.set_text(str(command[4]))
        self.ax.draw_artist(self.txtY3)

        # Auto update X Lim 
        self.ax.set_xlim([0, command[1]+1])

        self.fig.canvas.draw_idle()
        return True

    def __call__(self, pipe):
        print('starting plotter...')
        self.pipe = pipe
            # Commands send over the pipe take the following format
            # [command_string, sampleCount, data1, data2 ... dataN]
            # sampleCount is an int
            # data is a float
            # command_string is a string ---
            # 's'  - start
            # 'r'  - ready
            # 'q'  - quit
            # 'p'  - Pause
            # 'k'  - Resume
           
        def startReading(event):
            self.startButton.color = 'g'
            self.startButton.active = False
            self.stopButton.active = True
            self.pauseButton.active = True

            self.pipe.send(('s',None,None))
            #Initialize three lines for three channels
            self.line1 = lines.Line2D([],[], color = 'r')
            self.line2 = lines.Line2D([],[], color = 'g')
            self.line3 = lines.Line2D([],[], color = 'b')

            self.ax.add_line(self.line1)
            self.ax.add_line(self.line2)
            self.ax.add_line(self.line3)

            legend1 = lgnd.Legend(self.ax, [self.line1, self.line2, self.line3], \
                ['Channel 1', 'Channel 2', 'Channel 3'])
            self.ax.add_artist(legend1)
            self.ax.set_ylim([0, 10])

            self.timer = self.fig.canvas.new_timer(interval=100)
            self.timer.add_callback(self.call_back)
            self.timer.start()
        
        def stopReading(event):
            print('Stopping...')
            self.pipe.send(('q',None,None))
            self.timer.stop()

        def pausePlotting(event):
            print('Pausing...')
            global pauseFlag
            pauseFlag = not(pauseFlag)
            if pauseFlag:
                self.pipe.send(('p',None,None))
                self.timer.stop()
                self.pauseButton.color = 'y'
                self.stopButton.active = False
            else:
                self.pauseButton.color = '0.85'
                self.pipe.send(('k',None,None))
                self.timer.start()
                self.stopButton.active = True

        # Initialize the plot
        self.fig, self.ax = plt.subplots(figsize=(15, 5))
        self.ax.set_position([0.05,0.1,0.7,0.85])
        # Buttons
        self.axstop = plt.axes([0.85, 0.65, 0.1, 0.075])
        self.axpause = plt.axes([0.85, 0.75, 0.1, 0.075])
        self.axstart = plt.axes([0.85, 0.85, 0.1, 0.075])
        self.startButton = Button(self.axstart, 'Start')
        self.stopButton = Button(self.axstop,'Stop')
        self.pauseButton = Button(self.axpause,'Pause')
        self.startButton.on_clicked(startReading)
        self.stopButton.on_clicked(stopReading)
        self.pauseButton.active = False
        self.stopButton.active = False
        #Probably useless
        self.pauseButton.on_clicked(pausePlotting)

        #Strings
        self.ax.text(0.85,0.5,'Sample Count', transform=self.fig.transFigure)
        self.txtX = self.ax.text(0.85,0.45,'0.0', transform=self.fig.transFigure)
        self.ax.text(0.85,0.4,'Channel1', transform=self.fig.transFigure)
        self.txtY1 = self.ax.text(0.85,0.35,'0.0', transform=self.fig.transFigure)
        self.ax.text(0.85,0.3,'Channel2', transform=self.fig.transFigure)
        self.txtY2 = self.ax.text(0.85,0.25,'0.0', transform=self.fig.transFigure)
        self.ax.text(0.85,0.2,'Channel3', transform=self.fig.transFigure)
        self.txtY3 = self.ax.text(0.85,0.15,'0.0', transform=self.fig.transFigure)

        plt.show()

        print('...done')

# This is a fairly fast plot. Refresh rates are good and pretty real-time
class NBPlot(object):
    def __init__(self):
        self.X = 0
        self.Y1 = 0
        self.Y2 = 0
        self.Y3 = 0

        self.plot_pipe, plotter_pipe = mp.Pipe()
        self.plotter = ProcessPlotter()
        self.plot_process = mp.Process(
            target=self.plotter, args=(plotter_pipe,))
        self.plot_process.daemon = True
        self.plot_process.start()

    # Add ADC values here if need be
    def plot(self):
        send = self.plot_pipe.send

        data = ['r',0,1]
        data = ['r',self.X, self.Y1, self.Y2, self.Y3]
        send(data)
        
    def setData(self,x,y1,y2,y3):
        self.X = x
        self.Y1 = y1
        self.Y2 = y2
        self.Y3 = y3

    def checkPipe(self):
        while self.plot_pipe.poll():
            command = self.plot_pipe.recv()
            if command is None:
                return False
            else:
                return command[0]
            

    def closePipe(self):
        self.plot_pipe.close()


def main():


    pl = NBPlot()
    
    """
    # Uncomment for arduino functionality
    usbPort = '/dev/tty*something*' # You can find this using the Arduino IDE or ls -al /dev/tty* on terminal
    arduinoObject = serial.Serial(usbPort, baudrate=9600)
    """

    # Uncomment for UI functionality
    #savefID = open('AblationRun_'+dt.now().strftime('%m-%d-%Y__%H-%M-%S')+'.csv','w')
    #savefID.write('Sample Number, Time, Ch1, Ch2, Ch3, Temp1, Temp2, Temp3\n')
    count = 0

    #Test Case with 100000 entries
    fID = open('./../testLog.txt','r') #replace with the arduino read
    while(pl.checkPipe() is not 's' ): 
        continue #Blocking statement
    
    '''
    startbyte = bytes('\xF8') # In Python 2.7 bytes is similar to str

    # This writes to the Arduino 
    #arduinoObject.write('s')
    # Do not start until start is pressed
    temp_data = arduinoObject.read(1)

    # This needs testing. This points to the write amount of bytes. Once this is done, go into the while == True loop
    while(temp_data != startbyte):
        temp_data = arduinoObject.read(1)
    '''
    y = fID.readline()

    # All arduino data should be sent to the pl function in this while loop
    while(True and y!=''): 
        
        '''
        #needs testing
        dataReadIn = arduinoObject.read(4)
        # Raw ADC values
        dataToProcess = dataReadIn[1:3]
        # Processed float values. Make sure these are floats
        processedData = processArduinoData(dataToProcess)
        '''
        try:
            pl.setData(count, float(y),float(y),float(y)) #Add in ADC values if needed
        except:
            continue
        #pl.setData(count, float(processedData[0]),float(processedData[1]),float(processedData[2])) #Add in ADC values if needed
        #dataToWrite = ','.join([str(count), dt.now().strftime('%H-%M-%S.%f'), str(dataToProcess[0]), str(dataToProcess[1]), str(dataToProcess[2]), 
        # str(processedData[0]), str(processedData[1]), str(processedData[2])])
        #savefID.write(dataToWrite+'\n')
        count = count + 1 # Use this for sample count
        pl.plot() # Do not remove
        time.sleep(0.01) #Keep
        
        y = fID.readline()
        flag = pl.checkPipe()
        # Keep this block
        if flag is 'q':
            break
        elif flag is 'p':
            while(flag is not 'k'):
                flag = pl.checkPipe()
                continue #Blocking statement

    pl.closePipe() #Keep

    fID.close()   
    #savefID.close()
    #arduinoObject.close()



def processArduinoData():
    # Write the calibrated formula.
    # Use the math library or the np library if needed.
    # log is in the math library - https://docs.python.org/2/library/math.html
    pass

if __name__ == '__main__':
    #if plt.get_backend() == "MacOSX":
    #    mp.set_start_method("forkserver")
    main()