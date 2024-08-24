#include "esp_camera.h"
#include <WiFi.h>
#include "fd_forward.h" // Biblioteca necesaria para la detección de rostros
#include "fr_forward.h" // Biblioteca para el reconocimiento facial

#define CAMERA_MODEL_AI_THINKER
#include "camera_pins.h"

//const char* ssid = "ITRANS";
//const char* password = "C17raN52016";

const char* ssid = "MEGACABLE-2.4G-33A3";
const char* password = "6qWawtuMYN";



void startCameraServer();

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  if(psramFound()){
    config.frame_size = FRAMESIZE_SVGA;  // Configura la resolución a XGA (1024x768)
    config.jpeg_quality = 10;  // Calidad de la imagen
    config.fb_count = 2;  // Número de framebuffers
  } else {
    config.frame_size = FRAMESIZE_SVGA;  // Configura la resolución a XGA (1024x768)
    config.jpeg_quality = 12;  // Calidad de la imagen
    config.fb_count = 1;  // Número de framebuffers
  }

  // Inicialización de la cámara
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Error al inicializar la cámara: 0x%x", err);
    return;
  }

  sensor_t * s = esp_camera_sensor_get();
  if (s->id.PID == OV3660_PID) {
    s->set_vflip(s, 1);  // Voltea la imagen verticalmente
    s->set_brightness(s, 1);  // Aumenta el brillo
    s->set_saturation(s, -2);  // Reduce la saturación
  }

  // Configura el tamaño de la imagen
  s->set_framesize(s, FRAMESIZE_SVGA);  // Asegúrate de que la resolución sea XGA (1024x768)

  // Configuración de WiFi
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi conectado");

  startCameraServer();

  Serial.print("¡Cámara lista! Usa 'http://");
  Serial.print(WiFi.localIP());
  Serial.println("' para conectar");
}

void loop() {
  delay(10000);
}
