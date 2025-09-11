#ifndef WIFI_SETUP_H
#define WIFI_SETUP_H

#include <Arduino.h>
#include <WiFiS3.h>

#include "configurations.h"

namespace wifi_utils {

using StartUpMessage = void();
using ConnectedMessage = void();

struct WiFiConfigurations {
  const char* ssid;
  const char* password;
  const StartUpMessage* startup_message;
  const ConnectedMessage* connected_message;
};

inline int SetupWiFi(const WiFiConfigurations& configs) {
  if (configs.startup_message != nullptr) {
    configs.startup_message();
  }

  if (!WiFi.begin(config::SSID, config::PASSWORD)) {
    return 1;
  };

  while(WiFi.status() != WL_CONNECTED && WiFi.status() != WL_CONNECT_FAILED) {
    delay(100);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECT_FAILED) {
    Serial.println("Failed to connect to WiFi!");
    return 1;
  }

  Serial.print("Arduino WiFi IP Address: ");
  Serial.println(WiFi.localIP());

  if (configs.connected_message != nullptr) {
    configs.connected_message();
  }

  return 0;
};

} // wifi_utils

#endif WIFI_SETUP_H