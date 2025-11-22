#include <Arduino.h>
#include <Wire.h>
#include <cstdint>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <Arduino_FreeRTOS.h>

Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28, &Wire);

struct IMUData {
  float orientation_x;
  float orientation_y;
  float orientation_z;
};

QueueHandle_t imuQueue;
TaskHandle_t hSensorTask;
TaskHandle_t hCommsTask;

const uint32_t BAUD_RATE_DEBUG = 115200;
const int QUEUE_LEN = 10;

void TaskSampleIMU(void *pvParameters) {
    vTaskDelay(pdMS_TO_TICKS(100));
    
    TickType_t xLastWakeTime = xTaskGetTickCount();
    const TickType_t xFrequency = pdMS_TO_TICKS(20); // 50Hz

    for (;;) {
        // Tiny delay to prevent bus congestion
        vTaskDelay(pdMS_TO_TICKS(2)); 
        
        sensors_event_t event;
        bno.getEvent(&event);

        IMUData dataPacket;
        dataPacket.orientation_x = event.orientation.x;
        dataPacket.orientation_y = event.orientation.y;
        dataPacket.orientation_z = event.orientation.z;

        // Send to Queue
        xQueueSend(imuQueue, &dataPacket, (TickType_t)0);


        vTaskDelayUntil(&xLastWakeTime, xFrequency);
    }
}

void TaskTransmit(void *pvParameters) {
  Serial.println(" [Transmit Task] started.");
  IMUData receivedData;

  for (;;) {
    if (xQueueReceive(imuQueue, &receivedData, 2000) == pdPASS) {
      Serial.print(receivedData.orientation_x, 4);
      Serial.print(",");
      Serial.print(receivedData.orientation_y, 4);
      Serial.print(",");
      Serial.println(receivedData.orientation_z, 4);
    }
  }
}

void setup() {
  Serial.begin(BAUD_RATE_DEBUG);

  Serial.println("--- System Booting ---");

  // Wait for BNO hardware to power up
  // The BNO055 needs ~400ms after power-on to be ready for I2C.
  // The Arduino R4 boots in ~100ms. We must wait.
  delay(2000); 

  Wire.begin();
  Wire.setClock(100000); 

  if (!bno.begin(OPERATION_MODE_CONFIG)) {
      Serial.println("Error: BNO055 init failed. Check Wiring!");
      while (1);
  }
  
  // 5. Switch to NDOF Mode
  Serial.println("Switching to NDOF Mode...");
  bno.setMode(OPERATION_MODE_NDOF);
  delay(200); 
  bno.setExtCrystalUse(true);
  delay(1000);

  // 6. Verify Status
  uint8_t system_status, self_test_results, system_error;
  bno.getSystemStatus(&system_status, &self_test_results, &system_error);
  
  Serial.print("System Status: "); Serial.print(system_status, HEX);
  Serial.println(" (Target: 5)");
  Serial.print("System Error:  "); Serial.println(system_error, HEX);

  if (system_status == 5) {
      Serial.println("Sensor Locked. Starting Scheduler.");
      imuQueue = xQueueCreate(10, sizeof(IMUData));
      xTaskCreate(TaskSampleIMU, "SampleIMU", 768, NULL, 2, &hSensorTask);
      xTaskCreate(TaskTransmit,  "Transmit",  768, NULL, 1, &hCommsTask);
      vTaskStartScheduler(); 
  } else {
      Serial.println("FATAL: Sensor still refusing NDOF. Check Voltage (VIN vs 3Vo).");
  }

  imuQueue = xQueueCreate(QUEUE_LEN, sizeof(IMUData));
  if (imuQueue == NULL) {
    Serial.println("Failed to create queue");
    while(1);
  }

  xTaskCreate(
    TaskSampleIMU,
    "SampleIMU",
    600,
    NULL,
    2,
    &hSensorTask
  );

  xTaskCreate(
    TaskTransmit,
    "Transmit",
    600,
    NULL,
    1,
    &hCommsTask
  );

  Serial.println("Starting scheduler");

  vTaskStartScheduler();
}

void loop(){
  Serial.println("hello world");
}
