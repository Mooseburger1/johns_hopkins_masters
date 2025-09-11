#include <Arduino.h>
#include <WiFiS3.h>

#include "configurations.h"
#include "wifi_setup.h"
#include "RTC.h"
#include "rtc_config.h"

namespace {
int PORT = 12345;

WiFiUDP udp;

char myPacket[255];
int dataLen;
String color;

wifi_utils::WiFiConfigurations wifi_configs = {
    .ssid=config::SSID,
    .password=config::PASSWORD,
    .startup_message=[](){
      Serial.print("Connecting to SSID: ");
      Serial.println(config::SSID);
    },
    .connected_message=[](){
        Serial.print("Arduino WiFi IP Address: ");
        Serial.println(WiFi.localIP());;
    }
};

state::AppState app_state;

} // namespace


void setup() {
  Serial.begin(9600);

  while (wifi_utils::SetupWiFi(wifi_configs)) {
    Serial.println("Unable to connect to Wifi..."
    "You are currently trapped in an infinite loop!!!");
  }

  udp.begin(PORT);
  Serial.print("UDP Server started on port: ");
  Serial.print(PORT);

  rtc_config::WaitForClockConfiguration(udp, app_state);
}

void loop() {
  if (udp.parsePacket()) {
    dataLen=udp.available();
    Serial.println(dataLen);
    udp.read(myPacket, 255);
    Serial.println(myPacket);
    myPacket[dataLen]=0;
    Serial.println(myPacket);
    color=String(color);
    color.trim();
    Serial.println("Received color: " + color);
    String response = "Here is your " + color + " Marble";
    udp.print(response);
    udp.endPacket();
    Serial.println("SENT: " + response);
  }
}