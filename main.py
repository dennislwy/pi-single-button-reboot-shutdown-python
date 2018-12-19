import os
import time
import signal
import logging.config
import RPi.GPIO as GPIO
from subprocess import call
from lib.newold import NewOld

#=================== Configurations ===================
# Debugging/logging flags
DEBUG = False
LOGGING = True

# GPIO pin for button
gpioPin = 24

# timing intervals
# check the state of button every X seconds
sampleSec = 0.25 # seconds

# reboot if pressed longer or equal this seconds value
rebootSec = 1 # seconds

# shutdown if pressed longer or equal this seconds value
shutdownSec = 4 # seconds

#======================================================

def main():
    try:
        setupPin()
        pressedSince = time.time()

        btn = NewOld()

        while True:
            btn.Value = GPIO.input(gpioPin) # read GPIO state

            if btn.Changed: # button state changed
                if btn.New == 1: # button pressed
                    pressedSince = time.time()
                    if LOGGING: log.info("Button pressed")
                else: # button released
                    pressedDuration = time.time() - pressedSince
                    if LOGGING: log.info("Button released after %s seconds" % pressedDuration)

                    if pressedDuration >= shutdownSec:
                        shutdown()
                    elif pressedDuration >= rebootSec:
                        reboot()
                    else:
                        if LOGGING: log.debug("No action")

            elif btn.New == 1 and time.time()-pressedSince >= shutdownSec: # button pressed and long hold
                shutdown()

            time.sleep(sampleSec)

    except KeyboardInterrupt:
        if LOGGING: log.warn("Application interrupted")

    except Exception as e:
        if LOGGING: log.error(e, exc_info=True)

def reboot(delay=0):
    if delay > 0:
        if LOGGING: log.info("Delaying %s seconds" % delay)
        time.sleep(delay)
        if LOGGING: log.info("Rebooting")
    call("sudo reboot", shell=True)

def shutdown(delay=0):
    if delay > 0:
        if LOGGING: log.info("Delaying %s seconds" % delay)
        time.sleep(delay)
    if LOGGING: log.info("Shutting down")
    call("sudo poweroff -h", shell=True)

def onTerminate(signum, frame):
    if LOGGING: log.info("Application terminated (OS shutdown/reboot)")
    exit(1)

def setupPin():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    if LOGGING: log.debug("Set GPIO %d as input" % gpioPin)
    GPIO.setup(gpioPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

if __name__ == "__main__":
    # region logging
    if LOGGING:
        # initialize logging
        currentPath = os.path.dirname(os.path.abspath(__file__))
        logFilename = "%s/%s.log" % (currentPath, os.path.splitext(os.path.basename(__file__))[0])
        logging.config.fileConfig("%s/logging.ini" % currentPath)
        log = logging.getLogger()
        fileHandler = logging.handlers.TimedRotatingFileHandler(logFilename,'D',7,1)
        logLevel = logging.DEBUG if DEBUG else logging.INFO
        log.handlers[0].level = logLevel
        fileHandler.setLevel(logLevel)
        fileHandler.setFormatter(log.handlers[0].formatter)
        log.addHandler(fileHandler)

    # starting service
    if LOGGING: log.info("Starting Reboot/Shutdown Button Monitor%s" % (' (DEBUG mode)' if DEBUG else ''))
    # endregion

    # Python detect linux shutdown and run a command before shutting down
    # credits to code_onkel
    # https://stackoverflow.com/questions/39275948/python-detect-linux-shutdown-and-run-a-command-before-shutting-down
    signal.signal(signal.SIGTERM, onTerminate)

    main()