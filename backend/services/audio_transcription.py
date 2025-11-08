import os
import tempfile
from pydub import AudioSegment
import whisper

# Загружаем модель один раз при импорте
model = whisper.load_model("base")  # можно "small" или "large" если есть GPU

def convert_to_wav(input_path: str) -> str:
    """Конвертирует аудиофайл (ogg/mp3) в wav."""
    audio = AudioSegment.from_file(input_path)
    wav_path = tempfile.mktemp(suffix=".wav")
    audio.export(wav_path, format="wav")
    return wav_path

def transcribe_audio(file_path: str, language: str = "ru") -> str:
    """
    Транскрибирует аудиофайл в текст.
    :param file_path: путь к аудиофайлу
    :param language: язык (uk / ru / en)
    :return: строка текста
    """
    try:
        # Конвертируем ogg → wav
        wav_path = convert_to_wav(file_path)

        # Транскрибируем
        result = model.transcribe(wav_path, language=language)
        text = result["text"]

        # Удаляем временный файл
        os.remove(wav_path)
        return text.strip()

    except Exception as e:
        print(f"[ERROR] Ошибка при транскрипции: {e}")
        return ""
