#ifndef STATE_H
#define STATE_H

#include <Arduino.h>

namespace state {

enum class States {
    UNKNOWN,
    UNINITIALIZED,
    TRANSMITTING,
    CONNECTED,
    READY,
    DONE,
};

class AppState {
  public:
   explicit AppState() = default;

   void UpdateState(States state) {
    noInterrupts();
    state_ = state;
    interrupts();
   }

   void UpdateTransmitInterval(int interval) {
    noInterrupts();
    transmit_interval_ = interval;
    interrupts();
   }

   int GetTransmitInterval() const {
    int curr_interval;
    noInterrupts();
    curr_interval = transmit_interval_;
    interrupts();

    return curr_interval;
   }

   States GetState() {
    States return_state;
    noInterrupts();
    return_state = state_;
    interrupts();

    return return_state;
   }

   static char* GetStateString(States state) {
    switch (state) {
      case States::CONNECTED:
        return "CONNECTED";
      case States::DONE:
        return "DONE";
      case States::READY:
       return "READY";
      case States::TRANSMITTING:
        return "TRANSMITTING";
      case States::UNINITIALIZED:
        return "UNINITIALIZED";
      default:
        return "UNKNOWN";
    }
   }

   char* GetStateString() {
    return GetStateString(GetState());
   }

 private:
  States state_ = States::UNINITIALIZED;
  int transmit_interval_ = 10;
};

inline bool ReadyToTransmitOptions(AppState& app_state) {
  return app_state.GetState() == States::CONNECTED;
};

inline bool ReadyToTransmitTemp(AppState& app_state) {
  return app_state.GetState() == States::READY;
};

inline bool ClientSignaledDone(AppState& app_state) {
  return app_state.GetState() == States::DONE;
}

} // state

#endif STATE_H