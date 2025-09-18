#include <Arduino.h>
#include <WiFiS3.h>

#include "state.h"

namespace transmit {

void Transmit(WiFiUDP& udp, std::initializer_list<const char*> messages) {
    udp.beginPacket(udp.remoteIP(), udp.remotePort());
    for (const char* msg : messages) {
        udp.print(msg);
    }
    udp.endPacket();
}

void TransmitOptions(WiFiUDP& udp) {
    Serial.println("Transmitting options");
    Transmit(udp, {"Menu Options:\n",
                  "1. Start Temperature Transmission\n",
                  "2. End Temperature Transmission\n"});
};

void ListenForOption(WiFiUDP& udp, state::AppState& app_state) {
    state::States curr_state = app_state.GetState();
    if (curr_state != state::States::READY) {
        Serial.print("Current state: ");
        Serial.print(app_state.GetStateString(curr_state));
        Serial.println(" is not valid state for listening for options");

        return;
    }

    char udp_packet[256];

    if (udp.parsePacket()) {
        int dataLen = udp.available();
        udp.read(udp_packet, 255);
        udp_packet[dataLen] = '\0';

        Serial.print("Received option ");
        Serial.println(udp_packet);

        char* end_ptr;
        unsigned int option = strtol(udp_packet, &end_ptr, 10);

        if (option == 1) {
            app_state.UpdateState(state::States::TRANSMITTING);
            Transmit(udp, {"Option 1 Accepted"});
            Serial.println("Option 1 Selected");
            return;
        }

        if (option == 2) {
            app_state.UpdateState(state::States::DONE);
            Transmit(udp, {"Option 2 Accepted"});
            Serial.println("Option 2 Selected");
            return;
        }

        Transmit(udp, {"Invalid option provided: ", udp_packet});
        return;
    }
};

} // transmit