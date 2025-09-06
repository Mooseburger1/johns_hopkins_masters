#ifndef ASCII_HELPERS_H
#define ASCII_HELPERS_H

// Helper functions to manage the ASCII conversions needed to appropriately map a character
// to its index position in the MORSE_CODES array in morse_code.h

namespace ascii {

// Checks if the provide ASCII value is an integer char. E.g. "0"
bool IsNumber(int int_letter) {
  if ((int_letter >= 48) & (int_letter <= 57)) {
   return true;
  }
  
  return false;
}

// Checks if the provided ASCII value is an upper case letter. E.g. "A"
bool IsUpperCase(int int_letter) {
 if ((int_letter >= 65) & (int_letter <= 90)) {
   return true;
  }
  
  return false;
}

// Checks if the provided ASCII value is a lower case letter. E.g. "a"
bool IsLowerCase(int int_letter) {
 if ((int_letter >= 97) & (int_letter <= 122)) {
   return true;
  }
  
  return false;
}

// Converts the ASCII value of a number to its index position in MORSE_CODES array
int NumberToIndex(int int_letter) {
  return int_letter - 48;
}

// Converts the ASCII value of a capital letter to its index position in MORSE_CODES array
int CaptialLetterToIndex(int int_letter) {
  return int_letter - 55;
}

// Converts a lower letter to a captial by subtracting 32 from its ASCII value.
int ToUpper(int int_letter) {
  return int_letter - 32;
}

// Maps a char to its index position in the MORSE_CODES array
int AsciiToIndex(const char letter) {
  int int_letter(letter);
  
  if (IsNumber(int_letter)) {
    return NumberToIndex(int_letter);
  }
      
  if (IsUpperCase(int_letter)) {
    return CaptialLetterToIndex(int_letter);    
  }
      
  if (IsLowerCase(int_letter)) {
    return CaptialLetterToIndex(ToUpper(int_letter));    
  }
  
  return -1;
}

} // ascii


#endif ASCII_HELPERS_H