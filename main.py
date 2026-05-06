import cv2
import streamlink
import pytesseract
import pymysql
import serial
import time
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Config:
    """Classe para gerenciar configurações da aplicação."""
    DB_HOST = os.getenv('DB_HOST')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_DATABASE = os.getenv('DB_DATABASE')
    ARDUINO_PORT = os.getenv('ARDUINO_PORT', 'COM6')
    ARDUINO_BAUDRATE = int(os.getenv('ARDUINO_BAUDRATE', 9600))
    STREAM_URL = os.getenv('STREAM_URL', 'https://www.twitch.tv/gaules')

class Database:
    """Classe para gerenciar conexões com o banco de dados."""
    def __init__(self):
        self.host = Config.DB_HOST
        self.user = Config.DB_USER
        self.password = Config.DB_PASSWORD
        self.database = Config.DB_DATABASE

    def connect(self):
        """Estabelece conexão com o banco de dados."""
        try:
            connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            logging.info("Conexão com banco de dados estabelecida com sucesso.")
            return connection
        except pymysql.Error as e:
            logging.error(f"Erro ao conectar ao banco de dados: {e}")
            return None

    def check_plate(self, plate):
        """Verifica se a placa está autorizada no banco."""
        connection = self.connect()
        if not connection:
            return None
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT placa_automovel FROM pessoas WHERE placa_automovel = %s", (plate,))
                result = cursor.fetchone()
                return result[0].strip().upper() if result else None
        except pymysql.Error as e:
            logging.error(f"Erro ao consultar placa: {e}")
            return None
        finally:
            connection.close()

    def log_event(self, message):
        """Registra evento no banco de dados."""
        connection = self.connect()
        if not connection:
            return
        try:
            with connection.cursor() as cursor:
                cursor.execute('INSERT INTO logs VALUES (DEFAULT, %s)', (message,))
                connection.commit()
                logging.info("Evento registrado no log.")
        except pymysql.Error as e:
            logging.error(f"Erro ao registrar log: {e}")
        finally:
            connection.close()

class ArduinoController:
    """Classe para controlar o Arduino."""
    def __init__(self):
        try:
            self.serial = serial.Serial(Config.ARDUINO_PORT, Config.ARDUINO_BAUDRATE)
            logging.info("Conexão com Arduino estabelecida.")
        except serial.SerialException as e:
            logging.error(f"Erro ao conectar ao Arduino: {e}")
            self.serial = None

    def open_gate(self):
        """Envia comando para abrir a cancela."""
        if self.serial:
            try:
                self.serial.write(b'0')
                time.sleep(5)
                self.serial.write(b'1')
                logging.info("Comando para abrir cancela enviado.")
            except serial.SerialException as e:
                logging.error(f"Erro ao enviar comando para Arduino: {e}")
        else:
            logging.warning("Arduino não conectado. Simulando abertura.")

class ImageProcessor:
    """Classe para processamento de imagens e OCR."""
    def __init__(self):
        self.stream_url = Config.STREAM_URL

    def capture_frame(self):
        """Captura um frame do stream."""
        try:
            if self.stream_url.startswith('http'):
                streams = streamlink.streams(self.stream_url)
                url = streams["best"].url
            else:
                url = self.stream_url  # Para webcam local, ex: 0
            cap = cv2.VideoCapture(url)
            ret, frame = cap.read()
            cap.release()
            time.sleep(2)
            return frame if ret else None
        except Exception as e:
            logging.error(f"Erro ao capturar frame: {e}")
            return None

    def detect_plate_region(self, frame):
        """Detecta a região da placa na imagem."""
        if frame is None:
            return None

        image_resized = cv2.resize(frame, (800, 400))
        gray_image = cv2.cvtColor(image_resized, cv2.COLOR_BGR2GRAY)
        _, binary_image = cv2.threshold(gray_image, 90, 255, cv2.THRESH_BINARY)
        blur_img = cv2.GaussianBlur(binary_image, (3, 3), 0)
        contours, _ = cv2.findContours(blur_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            if perimeter > 300:
                approx = cv2.approxPolyDP(contour, 0.03 * perimeter, True)
                if len(approx) == 4:
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(image_resized, (x, y), (x + w, y + h), (90, 255, 35), 3)
                    roi = image_resized[y:y + h, x:x + w]
                    return roi
        return None

    def preprocess_roi(self, roi):
        """Pré-processa a ROI para OCR."""
        if roi is None:
            return None

        max_width, max_height = 800, 400
        current_height, current_width = roi.shape[:2]
        if current_width > max_width or current_height > max_height:
            roi = cv2.resize(roi, (max_width, max_height), interpolation=cv2.INTER_CUBIC)
        roi_resized = cv2.resize(roi, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        gray_roi = cv2.cvtColor(roi_resized, cv2.COLOR_BGR2GRAY)
        _, binary_roi = cv2.threshold(gray_roi, 70, 255, cv2.THRESH_BINARY)
        blur_roi = cv2.GaussianBlur(binary_roi, (5, 5), 0)
        return blur_roi

    def ocr_plate(self, roi):
        """Realiza OCR na ROI."""
        if roi is None:
            return ''

        roi_resized = cv2.resize(roi, (800, 400))
        config = r'-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 --psm 6'
        try:
            text = pytesseract.image_to_string(roi_resized, lang='eng', config=config)
            return text.strip().upper()
        except pytesseract.pytesseract.TesseractNotFoundError:
            logging.error("Tesseract não encontrado.")
            return ''

class ALPRApp:
    """Classe principal da aplicação ALPR."""
    def __init__(self):
        self.db = Database()
        self.arduino = ArduinoController()
        self.image_processor = ImageProcessor()

    def process_frame(self):
        """Processa um frame completo."""
        frame = self.image_processor.capture_frame()
        if frame is None:
            return

        roi = self.image_processor.detect_plate_region(frame)
        preprocessed = self.image_processor.preprocess_roi(roi)
        plate_text = self.image_processor.ocr_plate(preprocessed)

        if plate_text:
            logging.info(f"Placa detectada: {plate_text}")
            authorized_plate = self.db.check_plate(plate_text)
            if authorized_plate and plate_text == authorized_plate:
                logging.info("Placa autorizada. Abrindo cancela.")
                self.arduino.open_gate()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_message = f"{timestamp} - Cancela aberta - Placa {plate_text}"
                self.db.log_event(log_message)
            else:
                logging.info("Placa não autorizada.")
        else:
            logging.debug("Nenhuma placa detectada neste frame.")

    def run(self):
        """Loop principal da aplicação."""
        logging.info("Iniciando sistema ALPR.")
        while True:
            try:
                self.process_frame()
                time.sleep(1)  # Ajustar intervalo conforme necessário
            except KeyboardInterrupt:
                logging.info("Aplicação interrompida pelo usuário.")
                break
            except Exception as e:
                logging.error(f"Erro inesperado: {e}")

if __name__ == '__main__':
    app = ALPRApp()
    app.run()
