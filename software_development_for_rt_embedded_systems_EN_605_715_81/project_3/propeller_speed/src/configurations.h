#ifndef CONFIGURATIONS_H
#define CONFIGURATIONS_H

#include <Arduino.h>

namespace wifi_configs {

inline constexpr char* SSID = "FibreBox_X6-421B57";
inline constexpr char* PWD = "Enter Your Password Here";
inline constexpr int PORT = 12345;

inline int ConnectToWiFi(const char* ssid = SSID, const char* password = PWD) {
    if (!WiFi.begin(ssid, password)) {
        return 1;
    }

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

    return 0;
};

}  // namespace wifi_configs

#endif CONFIGURATIONS_H