#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// Refresh weather data every hour
// 1000ms x 60s x 60m
const unsigned long interval = 1000 * 60 * 60;

// WIFI Credentials
const char* ssid = "your_internet_here";
const char* password = "your_internet_password_here";

// LED Display Dimensions
const int SCREEN_WIDTH = 128;
const int SCREEN_HEIGHT = 64;
const int OLED_RESET = -1;

unsigned long previousMillis = 0;

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// API Key from Weather API
String api_key = "you_key_here";
String city = "Zurich";

// API Endpoint for Weather API's "current weather" endpoint
String api_endpoint = "http://api.weatherapi.com/v1/current.json?key=" + api_key + "&q=" + city + "&aqi=no";
String UNITS = "metric"; // Can be "metric" or "imperial"

void getWeatherData();

void setup() {
  Serial.begin(9600);

  // --- Initialize OLED Display ---
  while(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("SSD1306 allocation failed"));
    Serial.println("You are trapped in an infinte loop because the display failed to initizialize");
  }

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,0);
  display.println("Initializing...");
  display.display();
  delay(1000);


  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to Wi-Fi...");
  display.setCursor(0,10);
  display.print("Connecting to WiFi...");
  display.display();
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    display.print(".");
    display.display();
  }
  Serial.println("\nConnected!");
  
  display.setCursor(0,20);
  display.println("Connected!");
  display.display();
  
  // Get initial weather data to kick things off
  getWeatherData();
}

void loop() {
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    getWeatherData();
  }
}


void updateDisplay(float temp, int humidity, String location, String units = UNITS) {
  display.clearDisplay();

  // Display Location
  display.setTextSize(2);
  display.setCursor(0, 0);
  display.print(location);
  
  // Display Temperature
  display.setTextSize(2);
  display.setCursor(0, 25);
  display.print(temp, 1); // Print with 1 decimal place
  display.print(" ");
  
  // Add Degree Symbol
  display.setTextSize(1);
  display.drawCircle(display.getCursorX() - 10, 27, 2, SSD1306_WHITE);
  display.setTextSize(2);
  display.print(units == "metric" ? "C" : "F");

  // Display Humidity
  display.setTextSize(2);
  display.setCursor(0, 48);
  display.print(humidity);
  display.print("% Hum");

  display.display();
}

void getWeatherData() {
  Serial.println("Getting Weather Data");
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi Disconnected.");
    return;
  }

  WiFiClient client;
  HTTPClient http;

  http.begin(client, api_endpoint);
  int httpResponseCode = http.GET();
  
  if (httpResponseCode == HTTP_CODE_OK) {
    String payload = http.getString();
    
    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, payload);

    if (error) {
      Serial.print(F("deserializeJson() failed: "));
      Serial.println(error.c_str());
      return;
    }

    // Extract values
    // See WeatherAPI Explorer for the return JSON format
    // https://www.weatherapi.com/api-explorer.aspx
    float temp_f = doc["current"]["temp_f"];
    float temp_c = doc["current"]["temp_c"];
    int humidity = doc["current"]["humidity"];
    String city = doc["location"]["name"];
    String country = doc["location"]["country"];


    Serial.println("--- Weather Data ---");
    Serial.print(" Temperature: ");
    Serial.println(temp_c);
    Serial.println(temp_f);
    Serial.print(" Humidity: ");
    Serial.print(humidity);
    Serial.println("%");
    Serial.println("--- Location Data ---");
    Serial.print("City: ");
    Serial.println(city);
    Serial.print("Country: ");
    Serial.println(country);

    updateDisplay(UNITS == "metric" ? temp_c : temp_f, humidity, city);

  } else {
    Serial.printf("HTTP Error code: %d\n", httpResponseCode);
    Serial.println(http.getString());
    display.clearDisplay();
    display.setCursor(0,0);
    display.println("API Request Failed");
    display.println("Check API Key or City");
    display.display();
  }

  http.end();
}