#ifndef MORSE_CODE_H
#define MORSE_CODE_H

// This file contains the mapping of letter to morse code pulses. 
//
// IMPORTANT: Only the character set [A-Za-z0-9]+ is supported
//
// Each character is mapped to an index position in the array `int* MORSE_CODES[]` by its ASCII
// value. The values 0-9 are queued first in the array, followed by A-Z. E.g "0" is at index
// position 0 of the array MORSE_CODES[] and "A" is at index 10.
//
// String numbers are converted to their index values by subtracing 48 from their ASCII Ordinal
// value. This is because "0" - "9" are 48 - 57 respecitvely. E.g. "5" ASCII integer value is 53;
// 53 - 48 = 5;
//
// Capital letters are converted to their index values by subtracting 55 from their ASCII Ordinal
// value. This is because A-Z are 65 - 90 respecitvely. Because "0" - "9" consume the first 9
// indicies in the array, this means A must start at index position 10. E.g. A ASCII integer values
// is 65; 65 - 55 = 10.
//
// Lower case letter are first converted to upper case letters by subtracting 32 from their ASCII
// Ordinal value. E.g. "a" is 97; 97 - 32 = 65 = A. Then the above logic follows.
//
// See ascii_helpers.h for Atoi conversions as discussed here.

namespace morse {

inline constexpr int ONE_UNITS = 300; // milliseconds
inline constexpr int THREE_UNITS = ONE_UNITS * 3;
inline constexpr int SEVEN_UNITS = ONE_UNITS * 7;
inline constexpr int TERMINATING_INT = 999;

inline constexpr int zero[] = {THREE_UNITS, THREE_UNITS, THREE_UNITS, THREE_UNITS, THREE_UNITS, TERMINATING_INT};
inline constexpr int one[] = {ONE_UNITS, THREE_UNITS, THREE_UNITS, THREE_UNITS, THREE_UNITS, TERMINATING_INT};
inline constexpr int two[] = {ONE_UNITS, ONE_UNITS, THREE_UNITS, THREE_UNITS, THREE_UNITS, TERMINATING_INT};
inline constexpr int three[] = {ONE_UNITS, ONE_UNITS, ONE_UNITS, THREE_UNITS, THREE_UNITS, TERMINATING_INT};
inline constexpr int four[] = {ONE_UNITS, ONE_UNITS, ONE_UNITS, ONE_UNITS, THREE_UNITS, TERMINATING_INT};
inline constexpr int five[] = {ONE_UNITS, ONE_UNITS, ONE_UNITS, ONE_UNITS, ONE_UNITS, TERMINATING_INT};
inline constexpr int six[] = {THREE_UNITS, ONE_UNITS, ONE_UNITS, ONE_UNITS, ONE_UNITS, TERMINATING_INT};
inline constexpr int seven[] = {THREE_UNITS, THREE_UNITS, ONE_UNITS, ONE_UNITS, ONE_UNITS, TERMINATING_INT};
inline constexpr int eight[] = {THREE_UNITS, THREE_UNITS, THREE_UNITS, ONE_UNITS, ONE_UNITS, TERMINATING_INT};
inline constexpr int nine[] = {THREE_UNITS, THREE_UNITS, THREE_UNITS, THREE_UNITS, ONE_UNITS, TERMINATING_INT};
inline constexpr int A[] = {ONE_UNITS, THREE_UNITS, TERMINATING_INT};
inline constexpr int B[] = {THREE_UNITS, ONE_UNITS, ONE_UNITS, ONE_UNITS, TERMINATING_INT};
inline constexpr int C[] = {THREE_UNITS, ONE_UNITS, THREE_UNITS, ONE_UNITS, TERMINATING_INT};
inline constexpr int D[] = {THREE_UNITS, ONE_UNITS, ONE_UNITS, TERMINATING_INT};
inline constexpr int E[] = {ONE_UNITS, TERMINATING_INT};
inline constexpr int F[] = {ONE_UNITS, ONE_UNITS, THREE_UNITS, ONE_UNITS, TERMINATING_INT};
inline constexpr int G[] = {THREE_UNITS, THREE_UNITS, ONE_UNITS, TERMINATING_INT};
inline constexpr int H[] = {ONE_UNITS, ONE_UNITS, ONE_UNITS, ONE_UNITS, TERMINATING_INT};
inline constexpr int I[] = {ONE_UNITS, ONE_UNITS, TERMINATING_INT};
inline constexpr int J[] = {ONE_UNITS ,THREE_UNITS , THREE_UNITS, THREE_UNITS, TERMINATING_INT};
inline constexpr int K[] = {THREE_UNITS, ONE_UNITS, THREE_UNITS, TERMINATING_INT};
inline constexpr int L[] = {ONE_UNITS, THREE_UNITS, ONE_UNITS, ONE_UNITS, TERMINATING_INT};
inline constexpr int M[] = {THREE_UNITS, THREE_UNITS, TERMINATING_INT};
inline constexpr int N[] = {THREE_UNITS, ONE_UNITS, TERMINATING_INT};
inline constexpr int O[] = {THREE_UNITS, THREE_UNITS, THREE_UNITS, TERMINATING_INT};
inline constexpr int P[] = {ONE_UNITS, THREE_UNITS, THREE_UNITS, ONE_UNITS, TERMINATING_INT};
inline constexpr int Q[] = {THREE_UNITS, THREE_UNITS, ONE_UNITS, THREE_UNITS, TERMINATING_INT};
inline constexpr int R[] = {ONE_UNITS, THREE_UNITS, ONE_UNITS, TERMINATING_INT};
inline constexpr int S[] = {ONE_UNITS, ONE_UNITS, ONE_UNITS, TERMINATING_INT};
inline constexpr int T[] = {THREE_UNITS, TERMINATING_INT};
inline constexpr int U[] = {ONE_UNITS, ONE_UNITS, THREE_UNITS, TERMINATING_INT};
inline constexpr int V[] = {ONE_UNITS, ONE_UNITS, ONE_UNITS, THREE_UNITS, TERMINATING_INT};
inline constexpr int W[] = {ONE_UNITS, THREE_UNITS, THREE_UNITS, TERMINATING_INT};
inline constexpr int X[] = {THREE_UNITS, ONE_UNITS, ONE_UNITS, THREE_UNITS, TERMINATING_INT};
inline constexpr int Y[] = {THREE_UNITS, ONE_UNITS, THREE_UNITS, THREE_UNITS, TERMINATING_INT};
inline constexpr int Z[] = {THREE_UNITS, THREE_UNITS, ONE_UNITS, ONE_UNITS, TERMINATING_INT};


inline constexpr const int* MORSE_CODES[] = {
    zero, one, two, three, four, five, six, seven, eight, nine, A, B, C, D, E, F, G, H, I, J, K, L,
    M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z
};

} // morse

#endif MORSE_CODE_H