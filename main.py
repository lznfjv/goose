# Duckiebot Motor Test Script (Blinka-Free)
#
# This script is designed to test ONLY the motors of a Duckiebot
# running on a Jetson Nano, without using the Adafruit Blinka library.
#
# --- SETUP INSTRUCTIONS ---
#
# 1. Install system-level dependencies for pip:
# sudo apt-get update
# sudo apt-get install python3-pip
#
# 2. Upgrade pip and install base tools:
# pip3 install --upgrade setuptools wheel
#
# 3. Install required I2C and motor driver libraries:
# pip3 install smbus2
# pip3 install pca9685-driver
#
# --- HOW TO RUN ---
#
# No special environment variables are needed for this version.
# Simply run the script with python3:
# python3 duckiebot_test.py
#

import time
from smbus2 import SMBus
from pca9685_driver import PCA9685

print("Duckiebot Motor Test Initializing...")

# --- Component Initialization ---

# 1. Motor Controller (PCA9685)
# I2C Address: 0x60 (Motor Driver HAT)
# Jetson Nano GPIO I2C bus is typically 1
try:
    # Initialize the PCA9685 controller
    pca = PCA9685(bus_num=1, address=0x60)
    pca.set_pwm_frequency(1600) # Set frequency for motor driver
    print("Motor controller initialized successfully.")
    
    # This setup is specific to the DRV8833 driver on the Duckietown HAT
    # We use a custom motor class to simplify control
    class DuckieMotor:
        def __init__(self, controller, in1_ch, in2_ch, pwm_ch):
            self.controller = controller
            self.in1_ch = in1_ch
            self.in2_ch = in2_ch
            self.pwm_ch = pwm_ch
            self._throttle = 0

        @property
        def throttle(self):
            return self._throttle

        @throttle.setter
        def throttle(self, value):
            value = max(min(value, 1.0), -1.0)
            self._throttle = value
            
            # PCA9685 uses 12-bit resolution (0-4095)
            speed = int(abs(value) * 4095)
            self.controller.set_pwm(self.pwm_ch, 0, speed)

            if value > 0:  # Forward
                self.controller.set_pwm(self.in1_ch, 0, 4095)
                self.controller.set_pwm(self.in2_ch, 0, 0)
            elif value < 0:  # Backward
                self.controller.set_pwm(self.in1_ch, 0, 0)
                self.controller.set_pwm(self.in2_ch, 0, 4095)
            else:  # Stop/Brake
                self.controller.set_pwm(self.in1_ch, 0, 4095)
                self.controller.set_pwm(self.in2_ch, 0, 4095)

    # Motor channels on the Duckietown HAT
    left_motor = DuckieMotor(pca, in1_ch=10, in2_ch=9, pwm_ch=8)
    right_motor = DuckieMotor(pca, in1_ch=5, in2_ch=6, pwm_ch=7)

    motors_ok = True
except Exception as e:
    print("Could not initialize motor controller: {}".format(e))
    print("Ensure I2C is enabled and the HAT is connected properly.")
    motors_ok = False
    
# --- Test Functions ---

def test_motors():
    if not motors_ok:
        print("Motors not initialized, skipping test.")
        return
        
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

def main():
    try:
        test_motors()
        print("\n--- Motor Test Complete ---")

    except Exception as e:
        print("An error occurred during testing: {}".format(e))

    finally:
        # --- Cleanup ---
        # Ensure all components are turned off safely on exit.
        print("Cleaning up and shutting down motors...")
        if motors_ok:
            pca.cleanup()
        print("Cleanup complete. Exiting.")

if __name__ == "__main__":
    main()

