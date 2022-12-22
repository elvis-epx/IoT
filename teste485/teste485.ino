//Programa: Comunicação RS485 com Arduino - Transmissor
//Autor: Arduino e Cia

#include <SoftwareSerial.h>

//Pinos de comunicacao serial do modulo RS485
#define Pino_RS485_RX    D4
#define Pino_RS485_TX    D7

//Pino de controle transmissao/recepcao
#define SerialControl1 D5
#define SerialControl2 D6

#define RS485Transmit    HIGH
#define RS485Receive     LOW

//Cria a serial por sofware para conexao com modulo RS485
SoftwareSerial RS485Serial(Pino_RS485_RX, Pino_RS485_TX);

void setup()
{
  //Inicializa a serial do Arduino
  Serial.begin(9600);
  Serial.println("Modulo Transmissor");

  pinMode(SerialControl1, OUTPUT);
  pinMode(SerialControl2, OUTPUT);

  //Inicializa a serial do modulo RS485ttw

  RS485Serial.begin(9600);
  digitalWrite(SerialControl1, RS485Receive);
  digitalWrite(SerialControl2, RS485Receive);
}


void loop()
{
  int x = -1;
    while (RS485Serial.available() > 0) {
        x = RS485Serial.read();
    }
    if (x > 0) {
      Serial.println("recebido byte, tentando transmitir");
      delay(500);
      digitalWrite(SerialControl1, RS485Transmit);
      digitalWrite(SerialControl2, RS485Transmit);
      delay(50);
      RS485Serial.write(x + 1);
      delay(50);
      digitalWrite(SerialControl1, RS485Receive);
      digitalWrite(SerialControl2, RS485Receive);
    }    
}