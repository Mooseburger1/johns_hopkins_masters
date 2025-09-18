#include <Arduino.h>
#include <DHT.h>
#define DHTPIN 11;
#define DHTTYPE DHT11;

#include <WiFiS3.h>

#include "configurations.h"
#include "RTC.h"
#include "rtc_config.h"
#include "transmit.h"
#include "wifi_setup.h"
#include "FspTimer.h"


const int PORT = 12345;

volatile bool readyToReadTemp = false;
volatile bool stableTemp = false;
volatile uint8_t tickCount = 0;

state::AppState app_state;
FspTimer temp_timer;
WiFiUDP udp;

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

void timer_callback(timer_callback_args_t __attribute__((unused)) *p_args) {
  tickCount++;
  if (tickCount >= 10) {
    tickCount = 0;
    readyToReadTemp = true;
  }
}

bool BeginTimer(float rate_hz) {
  uint8_t timer_type = GPT_TIMER;
  int8_t tindex = FspTimer::get_available_timer(timer_type, true); 

  if (tindex < 0) {
    return false;
  }

  if (!temp_timer.begin(TIMER_MODE_PERIODIC, timer_type, tindex, rate_hz, 0.0f, timer_callback)) {
    Serial.println("begin() failed");
    return false;
  }

  if (!temp_timer.setup_overflow_irq() || !temp_timer.open() || !temp_timer.start()) {
    Serial.println("failed to start timer");
    return false;
  }

  return true;
}


void setup() {
  if (app_state.GetState() == state::States::UNINITIALIZED) {
    Serial.begin(9600);

    while (wifi_utils::SetupWiFi(wifi_configs)) {
      Serial.println("Unable to connect to Wifi..."
      "You are currently trapped in an infinite loop!!!");
    }

    udp.begin(PORT);
    Serial.print("UDP Server started on port: ");
    Serial.println(PORT);

    if (!BeginTimer(1.0)) {
    Serial.println("Timer failed to start");
    }
  }

  rtc_config::WaitForClockConfiguration(udp, app_state, state::States::CONNECTED);

}

void loop() {

  if (state::ReadyToTransmitOptions(app_state)) {
    app_state.UpdateState(state::States::READY);
    transmit::TransmitOptions(udp);
    return;
  }

  if (state::ReadyToTransmitTemp(app_state)) {
    transmit::ListenForOption(udp, app_state);
    return;
  }

  if (state::ClientSignaledDone(app_state)) {
    setup();
    return;
  }

  if (app_state.GetState() == state::States::TRANSMITTING) {
    if (readyToReadTemp) {
      readyToReadTemp = false;
      float temp_f = 72.5;

      RTCTime curr_time;
      RTC.getTime(curr_time);
      auto payload = curr_time.toString() + ", " + String(temp_f, 2);
      
      transmit::Transmit(udp, {payload.c_str()});
    }
  }
}


