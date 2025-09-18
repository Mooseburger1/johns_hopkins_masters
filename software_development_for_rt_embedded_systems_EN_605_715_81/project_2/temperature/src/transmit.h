#ifndef TRANSMIT_H
#define TRANSMIT_H

namespace transmit {

void TransmitOptions(WiFiUDP& udp);

void ListenForOption(WiFiUDP& udp, state::AppState& app_state);
void Transmit(WiFiUDP& udp, std::initializer_list<const char*> messages);

} // namespace transmit

#endif TRANSMIT_H

