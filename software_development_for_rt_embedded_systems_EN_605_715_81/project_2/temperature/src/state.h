#ifndef STATE_H
#define STATE_H

#include <Arduino.h>

namespace state {

enum class States {
    UNKNOWN,
    UNINITIALIZED,
    READY,
    CONNECTED,
    FAILED,
};

class AppState {
  public:
   explicit AppState() = default;

   void UpdateState(States state) {
    noInterrupts();
    state_ = state;
    interrupts();
   }

   States GetState() {
    States return_state;
    noInterrupts();
    return_state = state_;
    interrupts();

    return return_state;
   }

 private:
  States state_ = States::UNINITIALIZED;
};

} // state

#endif STATE_H