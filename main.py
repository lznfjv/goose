# Duckiebot Bare-Metal Motor Test
#
# GOAL: Move the left wheel with the absolute minimum number of libraries.
#
# This script talks directly to the PCA9685 PWM controller chip.
# It does NOT use Adafruit Blinka, pca9685-driver, or any other high-level library.
#
# --- SETUP (The only dependency) ---
#
# 1. Open a terminal on your Duckiebot.
#
# 2. Install the I2C communication library:
#    pip3 install smbus2
#
# --- HOW TO RUN ---
#
# python3 minimal_motor_test.py
#
# The left wheel should move forward for 2 seconds, then stop.
#

import time
from smbus2 import SMBus

# --- PCA9685 Configuration ---
# This is the I2C address of the motor driver HAT
PCA9685_ADDRESS = 0x60

# These are the memory addresses (registers) inside the chip that control it
MODE1_REG = 0x00
PRESCALE_REG = 0xFE
# Each channel's ON/OFF time is controlled by 4 registers (L=Low byte, H=High byte)
# We calculate the starting register for a channel and write 4 bytes from there.
# For example, Channel 8's registers start at 0x26.
LED0_ON_L_REG = 0x06

# --- Duckiebot Motor Channel Assignments ---
# These are the channels on the PCA9685 that control the LEFT motor
LEFT_MOTOR_PWM = 8  # Controls speed
LEFT_MOTOR_IN2 = 9  # Controls direction pin 2
LEFT_MOTOR_IN1 = 10 # Controls direction pin 1


def main():
    try:
        # Get a handle to the I2C bus. On Jetson Nano, it's almost always bus 1.
        bus = SMBus(1)
        print("Successfully opened I2C bus.")

        # --- Initialize the PCA9685 Chip ---
        
        # 1. Reset the chip
        bus.write_byte_data(PCA9685_ADDRESS, MODE1_REG, 0x00)
        time.sleep(0.01) # Wait for reset
        
        # 2. Set the PWM frequency (1600 Hz is typical for this motor driver)
        prescale_val = int(25000000.0 / (4096 * 1600) - 1)
        
        # To set the frequency, we have to put the chip to sleep first
        old_mode = bus.read_byte_data(PCA9685_ADDRESS, MODE1_REG)
        new_mode = (old_mode & 0x7F) | 0x10  # Set the SLEEP bit
        bus.write_byte_data(PCA9685_ADDRESS, MODE1_REG, new_mode)
        
        # Now we can set the frequency
        bus.write_byte_data(PCA9685_ADDRESS, PRESCALE_REG, prescale_val)
        
        # Wake the chip back up
        bus.write_byte_data(PCA9685_ADDRESS, MODE1_REG, old_mode)
        time.sleep(0.01) # Wait for oscillator to stabilize
        
        # Enable auto-incrementing of registers, which lets us write all 4 bytes for a channel at once
        bus.write_byte_data(PCA9685_ADDRESS, MODE1_REG, old_mode | 0xA0)
        print("PCA9685 motor controller initialized.")

        # --- Move the Left Wheel ---
        print("\nMoving LEFT wheel forward for 2 seconds...")

        # The PCA9685 works on a 4096-tick cycle (12-bit).
        # We set a channel's "ON" time (0-4095) and "OFF" time (0-4095).
        # - Full ON is (0, 4095)
        # - Full OFF is (0, 0)
        
        # 1. Set direction to FORWARD
        # IN1 = ON, IN2 = OFF
        # The 4 bytes are: ON_L, ON_H, OFF_L, OFF_H
        bus.write_i2c_block_data(PCA9685_ADDRESS, LED0_ON_L_REG + 4 * LEFT_MOTOR_IN1, [0, 0, 0xFF, 0x0F]) # (0, 4095)
        bus.write_i2c_block_data(PCA9685_ADDRESS, LED0_ON_L_REG + 4 * LEFT_MOTOR_IN2, [0, 0, 0, 0])      # (0, 0)

        # 2. Set PWM speed to ~50%
        # 50% of 4095 is ~2048
        speed_l = 0x00       # Low byte of 2048
        speed_h = 0x08       # High byte of 2048
        bus.write_i2c_block_data(PCA9685_ADDRESS, LED0_ON_L_REG + 4 * LEFT_MOTOR_PWM, [0, 0, speed_l, speed_h])

        # Let the motor run
        time.sleep(2)

    except FileNotFoundError:
        print("ERROR: I2C bus not found. Ensure I2C is enabled on your Jetson Nano.")
    except Exception as e:
        print("An error occurred: {}".format(e))
    finally:
        # --- Cleanup: Stop the motor ---
        print("Stopping motor and cleaning up.")
        try:
            # Set all motor channels to OFF to guarantee it stops.
            bus.write_i2c_block_data(PCA9685_ADDRESS, LED0_ON_L_REG + 4 * LEFT_MOTOR_PWM, [0, 0, 0, 0])
            bus.close()
            print("Cleanup complete.")
        except NameError:
            # This happens if 'bus' failed to initialize
            print("I2C bus was not opened, no cleanup needed.")

if __name__ == "__main__":
    main()
