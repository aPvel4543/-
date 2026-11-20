from pathlib import Path
import whisper


class AudioTranscriber:
    def __init__(self, model_name="base"):
        self.model_name = model_name
        self.model = None

    def set_model(self, model_name):
        """Изменение модели Whisper."""

        if model_name != self.model_name:
            self.model_name = model_name
            self.model = None

    def load_model(self):
        """Загрузка модели на CPU."""

        if self.model is None:
            self.model = whisper.load_model(
                self.model_name,
                device="cpu"
            )

        return self.model

    def transcribe(self, audio_path, language=None):
        """Распознавание речи из аудиофайла."""

        audio_path = Path(audio_path)

        if not audio_path.is_file():
            raise FileNotFoundError(
                f"Аудиофайл не найден: {audio_path}"
            )

        model = self.load_model()

        result = model.transcribe(
            str(audio_path),
            language=language,
            fp16=False
        )

        return result