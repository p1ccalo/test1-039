from backend.services.audio_transcription import transcribe_audio
from backend.services.extract_client_answers import extract_answers

# 1. Расшифровка аудио
text = transcribe_audio("c:/Users/p1ccalo/Desktop/ortho_spin/record_out.ogg")
print(text)

# 2. Извлечение ответов
answers = extract_answers(text)
print(answers)
