#include <Arduino.h>

#include "morse_code.h"
#include "pulse.h"

// Main entry point for pulsing a message in morse code
//
// IMPORTANT: Configure which pins you want to be activated in the int PULSE_PINS[] array
//
// Multiple pins can be configured such that they are activated for each pulse in a letter. To
// adjust the timing of ONE_UNIT to be longer or shorter, thus the timing of all other units, the
// value can be updated in morse_code.h
namespace {

using arduino::String;
using morse::ONE_UNITS;
using morse::THREE_UNITS;
using morse::SEVEN_UNITS;
using morse::TERMINATING_INT;
using pulse::PulseWords;


// Configure which pins should be pulsed for morse code
// Array should always end with TERMINATING_INT
constexpr int PULSE_PINS[] = {3, 6, TERMINATING_INT};

const char SENTINEL_CHAR = '\x1A'; // ASCII value for Ctrl+Z

void ConfigurePinModes(const int* pins, int mode) {
  int pin_index = 0;
  while (pins[pin_index] != TERMINATING_INT) {
    pinMode(pins[pin_index], mode);
    ++pin_index;
  }
}

} // namespace

void setup()
{
  ConfigurePinModes(PULSE_PINS, OUTPUT);
  Serial.begin(9600);
}

void loop()
{
  while (true) {
    if (Serial.available()) {
      char incoming_char = Serial.read();

      // Check for the sentinel character first
      if (incoming_char == SENTINEL_CHAR) {
        Serial.println("Exiting Loop");
        break;
      }

      // If it's not the sentinel, read the rest of the line
      String msg_to_encode = String(incoming_char);
      msg_to_encode += Serial.readStringUntil('\n');
      msg_to_encode.trim();

      PulseWords(msg_to_encode, PULSE_PINS);
    }
  }
}