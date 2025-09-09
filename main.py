# Duckiebot Hardware Test Script
#
# This script is designed to test the main hardware components of a Duckiebot
# running on a Jetson Nano. It will test the motors, OLED display,
# front LEDs, ToF distance sensor, and the camera.
#
# --- SETUP INSTRUCTIONS ---
#
# 1. Install system-level dependencies using apt for better compatibility:
# sudo apt-get update
# sudo apt-get install python3-pip python3-pil python3-numpy python3-opencv
#
# 2. Upgrade pip and install base tools:
# pip3 install --upgrade setuptools wheel
#
# 3. Install Adafruit libraries using pip, avoiding their conflicting dependencies:
# pip3 install --no-deps adafruit-blinka==6.15.0
# pip3 install --no-deps adafruit-circuitpython-pca9685
# pip3 install --no-deps adafruit-circuitpython-motor
# pip3 install --no-deps adafruit-circuitpython-ssd1306
# pip3 install --no-deps adafruit-circuitpython-vl53l0x
# pip3 install --no-deps adafruit-circuitpython-dotstar
#
# --- HOW TO RUN ---
#
# The Adafruit Blinka library needs to know it's running on a Jetson Nano.
# You MUST set the following environment variable before running the script.
#
# In your terminal, run this command ONCE:
# export BLINKA_JETSON_NANO=1
#
# Then, run the script:
# python3 duckiebot_test.py
#

import time
import os

# --- Environment Check for Adafruit Blinka ---
# This check MUST come before importing board or busio.
if os.environ.get('BLINKA_JETSON_NANO') is None:
    print("---------------------------------------------------------------------")
    print("ERROR: Blinka environment variable not set!")
    print("The 'board' and 'busio' libraries require this to be set.")
    print("Please run the following command in your terminal and then try again:")
    print("export BLINKA_JETSON_NANO=1")
    print("---------------------------------------------------------------------")
    exit()

import board
import busio
from PIL import Image, ImageDraw, ImageFont
import cv2

# Adafruit Libraries for hardware components
import adafruit_pca9685
from adafruit_motor import motor
import adafruit_ssd1306
import adafruit_vl53l0x
import adafruit_dotstar

print("Duckiebot Hardware Test Initializing...")

# --- I2C and SPI Bus Setup ---
# As per the pinout guide, we are using I2C Bus 1 (pins 3 and 5) and SPI Bus 1 (pins 19, 23)
try:
    i2c = busio.I2C(board.SCL, board.SDA)
    spi = busio.SPI(board.SCK, MOSI=board.MOSI)
    print("I2C and SPI buses initialized successfully.")
except Exception as e:
    print("Error initializing I2C/SPI buses: {}".format(e))
    print("Please ensure you have run 'sudo pip3 install adafruit-blinka' and configured it for Jetson Nano.")
    exit()

# --- Component Initialization ---
# Initialize each hardware component using the buses defined above.

# 1. Motor Controller (PCA9685)
# I2C Address: 0x40 (PCA9685) and 0x60 (Motor Driver HAT)
try:
    pca = adafruit_pca9685.PCA9685(i2c, address=0x60)
    pca.frequency = 1600 # Frequency for motor driver

    # Motor channels on the Duckietown HAT
    # Left Motor
    motor_a1 = pca.channels[10]
    motor_a2 = pca.channels[9]
    motor_a_pwm = pca.channels[8]
    # Right Motor
    motor_b1 = pca.channels[5]
    motor_b2 = pca.channels[6]
    motor_b_pwm = pca.channels[7]
    
    # This setup is specific to the DRV8833 driver on the Duckietown HAT
    # We use a custom motor class to simplify control
    class DuckieMotor:
        def __init__(self, in1, in2, pwm):
            self._in1 = in1
            self._in2 = in2
            self._pwm = pwm
            self._throttle = 0

        @property
        def throttle(self):
            return self._throttle

        @throttle.setter
        def throttle(self, value):
            value = max(min(value, 1.0), -1.0)
            self._throttle = value
            speed = abs(value) * 65535
            self._pwm.duty_cycle = int(speed)

            if value > 0: # Forward
                self._in1.duty_cycle = 65535
                self._in2.duty_cycle = 0
            elif value < 0: # Backward
                self._in1.duty_cycle = 0
                self._in2.duty_cycle = 65535
            else: # Stop/Brake
                self._in1.duty_cycle = 65535
                self._in2.duty_cycle = 65535

    left_motor = DuckieMotor(motor_a1, motor_a2, motor_a_pwm)
    right_motor = DuckieMotor(motor_b1, motor_b2, motor_b_pwm)

    print("Motor controller initialized.")
    motors_ok = True
except Exception as e:
    print("Could not initialize motor controller: {}".format(e))
    motors_ok = False

# 2. OLED Display
# I2C Address: 0x3C
try:
    display = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
    display.fill(0)
    display.show()
    # Create a blank image for drawing.
    image = Image.new("1", (display.width, display.height))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    print("OLED display initialized.")
    oled_ok = True
except Exception as e:
    print("Could not initialize OLED display: {}".format(e))
    oled_ok = False

# 3. Time-of-Flight Sensor
# I2C Address: 0x29
try:
    tof = adafruit_vl53l0x.VL53L0X(i2c)
    print("ToF sensor initialized.")
    tof_ok = True
except Exception as e:
    print("Could not initialize ToF sensor: {}".format(e))
    tof_ok = False

# 4. Front LEDs (DotStar)
try:
    # The Duckietown HAT uses 5 LEDs.
    leds = adafruit_dotstar.DotStar(spi, 5, brightness=0.2, auto_write=True)
    print("Front LEDs initialized.")
    leds_ok = True
except Exception as e:
    print("Could not initialize front LEDs: {}".format(e))
    leds_ok = False
    

# --- Test Functions ---

def test_oled():
    if not oled_ok: return
    print("\n--- Testing OLED Display ---")
    draw.rectangle((0, 0, display.width, display.height), outline=0, fill=0)
    draw.text((5, 5), "Hello Duckie!", font=font, fill=255)
    display.image(image)
    display.show()
    time.sleep(2)
    
    draw.rectangle((0, 0, display.width, display.height), outline=0, fill=0)
    draw.text((5, 5), "Display Test OK", font=font, fill=255)
    display.image(image)
    display.show()
    time.sleep(2)
    
    display.fill(0)
    display.show()

def test_leds():
    if not leds_ok: return
    print("\n--- Testing Front LEDs ---")
    print("Red...")
    leds.fill((255, 0, 0))
    time.sleep(1)
    
    print("Green...")
    leds.fill((0, 255, 0))
    time.sleep(1)
    
    print("Blue...")
    leds.fill((0, 0, 255))
    time.sleep(1)
    
    print("White...")
    leds.fill((255, 255, 255))
    time.sleep(1)

    leds.fill((0, 0, 0)) # Turn off

def test_tof():
    if not tof_ok: return
    print("\n--- Testing ToF Sensor ---")
    print("Reading distance for 5 seconds. Put your hand in front of the bot.")
    for _ in range(25):
        print("Distance: {} mm".format(tof.range))
        time.sleep(0.2)

def test_motors():
    if not motors_ok: return
    print("\n--- Testing Motors ---")
    speed = 0.5 # Use a moderate speed
    
    print("Forward...")
    left_motor.throttle = speed
    right_motor.throttle = speed
    time.sleep(1)

    print("Backward...")
    left_motor.throttle = -speed
    right_motor.throttle = -speed
    time.sleep(1)

    print("Turn Right...")
    left_motor.throttle = speed
    right_motor.throttle = -speed
    time.sleep(1)

    print("Turn Left...")
    left_motor.throttle = -speed
    right_motor.throttle = speed
    time.sleep(1)
    
    print("Stopping motors.")
    left_motor.throttle = 0
    right_motor.throttle = 0

def gstreamer_pipeline(
    capture_width=1280,
    capture_height=720,
    display_width=640,
    display_height=360,
    framerate=30,
    flip_method=2, # Use 2 for Duckiebots as camera is often upside down
):
    return (
        "nvarguscamerasrc ! "
        "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, format=(string)NV12, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

def test_camera():
    print("\n--- Testing Camera ---")
    pipeline = gstreamer_pipeline()
    cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

    if cap.isOpened():
        print("Camera opened successfully. Taking one picture.")
        ret, frame = cap.read()
        if ret:
            cv2.imwrite("camera_test.jpg", frame)
            print("Saved image to 'camera_test.jpg'.")
        else:
            print("Failed to capture frame from camera.")
        cap.release()
    else:
        print("Failed to open camera. Check GStreamer pipeline and camera connection.")


def main():
    try:
        test_oled()
        test_leds()
        test_tof()
        test_motors()
        test_camera()
        print("\n--- All Tests Complete ---")

    except Exception as e:
        print("An error occurred during testing: {}".format(e))

    finally:
        # --- Cleanup ---
        # Ensure all components are turned off safely on exit.
        print("Cleaning up and shutting down components...")
        if motors_ok:
            left_motor.throttle = 0
            right_motor.throttle = 0
        if leds_ok:
            leds.fill((0, 0, 0))
        if oled_ok:
            display.fill(0)
            display.show()
        print("Cleanup complete. Exiting.")

if __name__ == "__main__":
    main()

