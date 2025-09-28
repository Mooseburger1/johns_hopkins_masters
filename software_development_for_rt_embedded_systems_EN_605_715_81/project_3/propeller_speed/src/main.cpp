#include <Arduino.h>
#include <WiFiS3.h>
#include <WiFiUdp.h>

#include "configurations.h"
#include "rtc_config.h"

// Pin used exclusively to be a 5V power supply for the phototransistor
const int PD_POWER_PIN = 2;
// Pin to read high / low when the propeller breaks the IR beam
const int SENSOR_PIN = 3;
const int PROPELLER_BLADES = 2;

const unsigned long RPM_CALCULATION_INTERVAL_MS = 1000;
const unsigned long TRANSMIT_INTERVAL_MS = 1000;
const unsigned long STOPPED_THRESHOLD_MS = 2000;

volatile unsigned long bladePassCount = 0;
volatile unsigned long lastBladePassTime = 0;

volatile int ready_to_transmit = 0;
float currentRpm = 0.0;
unsigned long lastCalcTime = 0;

WiFiUDP udp;

using TaskFunction = void (*)();

struct Task{
    TaskFunction function;
    unsigned long interval;
    unsigned long lastExecuted;
};

void calculateRPM();
void transmitRPM();

Task taskQueue[] = {
    {calculateRPM, RPM_CALCULATION_INTERVAL_MS, 0},
    {transmitRPM, TRANSMIT_INTERVAL_MS, 0},
};

const int numTasks = sizeof(taskQueue) / sizeof(Task);

void CountBladePassIsrFunction() {
    ++bladePassCount;
    lastBladePassTime = millis();
}

void calculateRPM() {
    unsigned long currentTime = millis();
    unsigned long elapsedTime = currentTime - lastCalcTime;

    noInterrupts();
    unsigned long count = bladePassCount;
    unsigned long lastPassTime = lastBladePassTime;
    bladePassCount = 0;
    interrupts();

    if (lastPassTime != 0 && (currentTime - lastPassTime) >= STOPPED_THRESHOLD_MS) {
        currentRpm = 0.0;
        lastCalcTime = currentTime;
        return;
    }


    if (elapsedTime > 0) {
        float revolutions = (float)count / PROPELLER_BLADES;
        currentRpm = (revolutions / (elapsedTime / 1000.0)) * 60.0;
        lastCalcTime = currentTime;
    }
}

void transmitRPM() {
    RTCTime curr_time;
    RTC.getTime(curr_time);
    auto payload = curr_time.toString() + ", " + String(currentRpm, 2);

    udp.beginPacket(udp.remoteIP(), udp.remotePort());
    udp.print(payload);
    udp.endPacket();

    Serial.println(payload);
}

// The runScheduluer loops through all tasks in the queue and exeuctes them if their last executed
// time is greater than or equal to their expected scheduled interval. The tasks are not dequed from
// the queue. Instead their last execution time is persisted within and checked at each execution.
// This removes the need to constantly enqueue the same tasks when it will only ever be these two.
void runScheduluer() {
    unsigned long now = millis();
    for (int i = 0; i < numTasks; ++i) {
        if (now - taskQueue[i].lastExecuted >= taskQueue[i].interval) {
            taskQueue[i].function();
            taskQueue[i].lastExecuted = now;
        }
    }
}

void setup() {
    Serial.begin(9600);

    pinMode(PD_POWER_PIN, OUTPUT);
    digitalWrite(PD_POWER_PIN, HIGH);

    pinMode(SENSOR_PIN, INPUT);


    while (wifi_configs::ConnectToWiFi(wifi_configs::SSID, wifi_configs::PWD)) {
        Serial.println("Unable to connect to Wifi..."
        "You are currently trapped in an infinite loop!!!");
    }

    udp.begin(wifi_configs::PORT);
    Serial.print("UDP Server started on port: ");
    Serial.println(wifi_configs::PORT);

    while(!ready_to_transmit) {
        config::WaitForClockConfiguration(udp, [](){
        ready_to_transmit = 1;
        });
    }

    attachInterrupt(digitalPinToInterrupt(SENSOR_PIN), CountBladePassIsrFunction, RISING);

    lastCalcTime = millis();
}

void loop() {
    runScheduluer();
}