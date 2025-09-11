#include <Arduino.h>
#include <WiFiS3.h>

#include "RTC.h"
#include "state.h"

namespace rtc_config {
namespace {
char myPacket[255];
int dataLen;

RTCTime ParseTimeFromUdp(char myPacket[]) {

}


} // namespace

void WaitForClockConfiguration(WiFiUDP& udp, state::AppState& app_state) {
  while(app_state.GetState() == state::States::UNINITIALIZED) {
    Serial.println("Waiting for UDP Connection...");

    if (udp.parsePacket()) {
        dataLen = udp.available();
        udp.read(myPacket, 255);
        myPacket[dataLen] = 0;
        Serial.println(myPacket);

        RTCTime config_time = ParseTimeFromUdp(myPacket);

         // Initialize the RTC
        RTC.begin();

        // Create an RTCTime object with the desired start time
        RTCTime startTime(12, Month::SEPTEMBER, 2025, 12, 0, 0, DayOfWeek::FRIDAY, SaveLight::SAVING_TIME_ACTIVE);

        // Set the RTC's time using the RTCTime object
        RTC.setTime(startTime);

  Serial.println("RTC time has been set.");

        app_state.UpdateState(state::States::CONNECTED);
    }

    delay(500);
  }
}


} // rtc_config
