#ifndef RTC_CONFIG_H
#define RTC_CONFIG_H

#include <Arduino.h>
#include <WiFiS3.h>

#include "RTC.h"
#include "state.h"

namespace rtc_config {

void WaitForClockConfiguration(WiFiUDP& udp,
                    state::AppState& app_state, state::States transition_state);

} // rtc_config

#endif RTC_CONFIG_H