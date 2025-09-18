#include <Arduino.h>
#include <WiFiS3.h>

#include "RTC.h"
#include "state.h"

namespace rtc_config {
namespace {
char udp_packet[255];
int dataLen;

time_t ParseTimeFromUdp(const char* packet) {
  // Convert string to unsigned long (time_t)
  char* end_ptr;
  unsigned long epoch = strtoul(packet, &end_ptr, 10);
  Serial.print("Converted unix timestamp: ");
  Serial.println(epoch);

  // Basic validation
  if (*end_ptr != '\0') {
    Serial.println("Error: Non-numeric characters in timestamp");
    return 0;
  }
  if (epoch < 946684800UL || epoch > 4102444800UL) { 
    // sanity check ~2000-01-01 to ~2100-01-01
    Serial.println("Error: Epoch timestamp out of valid range");
    return 0;
  }

  return (time_t)epoch;
}

} // namespace

void WaitForClockConfiguration(WiFiUDP& udp,
                    state::AppState& app_state, state::States transition_state) {

  char udp_packet[256];
  
  auto curr_state = app_state.GetState();
  while (curr_state == state::States::UNINITIALIZED || curr_state == state::States::DONE) {
    Serial.println("Waiting for UDP Connection...");

    if (udp.parsePacket()) {
      int dataLen = udp.available();
      udp.read(udp_packet, 255);
      udp_packet[dataLen] = '\0';
      Serial.print("Received epoch: ");
      Serial.println(udp_packet);

      time_t config_epoch = ParseTimeFromUdp(udp_packet);

      if (config_epoch != 0) {
        RTC.begin();
        RTCTime config_time_from_udp(config_epoch);
        RTC.setTime(config_time_from_udp);
        Serial.println("RTC time has been set.");

        udp.beginPacket(udp.remoteIP(), udp.remotePort());
        udp.print("OK");
        udp.endPacket();

        app_state.UpdateState(transition_state);
        return;
      }

    }

    delay(500);
  }
}


} // rtc_config
