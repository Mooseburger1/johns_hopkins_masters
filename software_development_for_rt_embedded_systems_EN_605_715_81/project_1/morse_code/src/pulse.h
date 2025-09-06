#ifndef PULSE_H
#define PULSE_H

#include "ascii_helpers.h"
#include "morse_code.h"

namespace pulse {
namespace {

using morse::ONE_UNITS;
using morse::THREE_UNITS;
using morse::SEVEN_UNITS;
using morse::TERMINATING_INT;

} // namespace

// Iterates through an array of pins and writes the value to them. The array is expected to have
// the sentinel TERMINATING_INT to determine when to stop iterating and writing.
void WritePins(const int* pins, int value) {
  int i = 0;
  while (pins[i] != TERMINATING_INT) {
    digitalWrite(pins[i], value);
    i++;
  }
}

// Iterates through an array of pulses for a letter. Ensures each configured pin is activated for
// the appropriate pulse length before deactivating. Respects the morse code rules of ONE_UNIT of
// pause between consecutive pulses for the letter.
void PulseLetters(const int* letter_pulses, const int* pins) {
  int i = 0;
  while (letter_pulses[i] != TERMINATING_INT) {
    int pulse_length = letter_pulses[i];

    Serial.print("Pulse for ");
    Serial.println(pulse_length);
    WritePins(pins, HIGH);
    delay(pulse_length);
    WritePins(pins, LOW);

    // If this is the last pulse for the letter, we don't want to add an extra ONE_UNIT delay
    // to the delay between two letters. Conversely we don't want to add an extra ONE_UNIT delay
    // between words if this is the last letter in a word.
    if (letter_pulses[i + 1] != TERMINATING_INT) {
      delay(ONE_UNITS);
    }
    i++;
  }
  Serial.println("Finished with letter");
}

// Iterates through an array of characters that make up words in a sentence. Pulse each character in
// a word. Applies the morse code rules of THREE_UNITs of pause between each letter that makes
// up a word. Also applies the rule of SEVEN_UNITS between each word. The start of a new word is
// identified as the first char seen AFTER a ' ' character.
void PulseWords(String words, const int* pins) {
  char word_separator = ' ';
  for (const auto& letter : words) {
    Serial.print("Letter ");
    Serial.println(letter);
    if (word_separator == letter) {
      delay(SEVEN_UNITS);
      continue;
    }

    const int* letter_pulses = morse::MORSE_CODES[ascii::AsciiToIndex(letter)];
    PulseLetters(letter_pulses, pins);
    delay(THREE_UNITS);
  }
}
} // pulse

#endif PULSE_H