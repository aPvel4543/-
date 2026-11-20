import customtkinter as ctk

import json
from datetime import datetime

from tkinter import filedialog, messagebox
from pathlib import Path
from threading import Thread
from queue import Queue, Empty


from transcriber import AudioTranscriber


class AudioTranscriberApp:
    def __init__(self):
        self.window = ctk.CTk()

        self.window.title("AudioTranscriber")
        self.window.geometry("950x700")
        self.window.minsize(700, 550)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.audio_path = None
        self.last_result = None

        # Обработчик аудио
        self.transcriber = AudioTranscriber("base")

        # Очередь результатов распознавания
        self.result_queue = Queue()

        self.history = []

        self.project_dir = Path(__file__).resolve().parent

        if self.project_dir.name == "app":
            self.project_dir = self.project_dir.parent

        self.history_file = (
                self.project_dir / "audio" / "output" / "history.json"
        )

        self.load_history()

        # Настройки программы
        self.settings = {
            "model": "base",
            "theme": "Тёмная",
            "timestamps": False,
            "output_format": "TXT",
            "save_folder": str(Path.home() / "AudioTranscriber")
        }

        self.create_interface()



    # --------------------------------------------------
    # ОСНОВНОЙ ИНТЕРФЕЙС
    # --------------------------------------------------

    def create_interface(self):

        # Верхняя панель
        self.top_panel = ctk.CTkFrame(
            self.window,
            fg_color="transparent"
        )
        self.top_panel.pack(
            fill="x",
            padx=20,
            pady=(15, 10)
        )

        # Заголовок
        title_frame = ctk.CTkFrame(
            self.top_panel,
            fg_color="transparent"
        )
        title_frame.pack(side="left")

        title = ctk.CTkLabel(
            title_frame,
            text="AudioTranscriber",
            font=("Arial", 26, "bold")
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_frame,
            text="Распознавание речи из аудиофайлов"
        )
        subtitle.pack(anchor="w")

        # Кнопка настроек
        self.settings_button = ctk.CTkButton(
            self.top_panel,
            text="⚙ Настройки",
            width=120,
            height=38,
            command=self.open_settings
        )
        self.settings_button.pack(side="right")

        self.history_button = ctk.CTkButton(
            self.top_panel,
            text="История",
            width=100,
            height=38,
            command=self.open_history
        )
        self.history_button.pack(side="right", padx=10)

        # Панель выбора аудио
        file_frame = ctk.CTkFrame(
            self.window,
            fg_color="transparent"
        )
        file_frame.pack(pady=15)

        self.file_button = ctk.CTkButton(
            file_frame,
            text="Выбрать аудиофайл",
            command=self.select_audio
        )
        self.file_button.pack(pady=5)

        self.file_label = ctk.CTkLabel(
            file_frame,
            text="Файл не выбран"
        )
        self.file_label.pack(pady=5)

        # Выбор языка
        language_frame = ctk.CTkFrame(
            self.window,
            fg_color="transparent"
        )
        language_frame.pack(pady=10)

        self.language_label = ctk.CTkLabel(
            language_frame,
            text="Язык аудио:"
        )
        self.language_label.pack(pady=5)

        self.language_menu = ctk.CTkOptionMenu(
            language_frame,
            values=[
                "Автоопределение",
                "Русский",
                "English"
            ],
            width=180
        )
        self.language_menu.pack()

        # Кнопка распознавания
        self.recognize_button = ctk.CTkButton(
            self.window,
            text="Распознать речь",
            command=self.recognize_audio,
            width=180
        )
        self.recognize_button.pack(pady=15)

        # Статус
        self.status_label = ctk.CTkLabel(
            self.window,
            text="Ожидание"
        )
        self.status_label.pack(pady=5)

        # Результат
        result_label = ctk.CTkLabel(
            self.window,
            text="Результат распознавания:",
            font=("Arial", 15, "bold")
        )
        result_label.pack(pady=(10, 5))

        self.result_box = ctk.CTkTextbox(
            self.window,
            height=300
        )
        self.result_box.pack(
            padx=20,
            pady=5,
            fill="both",
            expand=True
        )

        # Кнопка сохранения
        self.save_button = ctk.CTkButton(
            self.window,
            text="Сохранить результат",
            command=self.save_result,
            width=180
        )
        self.save_button.pack(pady=15)

    # --------------------------------------------------
    # ВЫБОР АУДИО
    # --------------------------------------------------

    def select_audio(self):

        path = filedialog.askopenfilename(
            filetypes=[
                ("Аудиофайлы", "*.mp3 *.wav"),
                ("Все файлы", "*.*")
            ]
        )

        if path:
            self.audio_path = path
            self.last_result = None

            self.file_label.configure(
                text=Path(path).name
            )

            self.result_box.delete("1.0", "end")

            self.status_label.configure(
                text="Аудиофайл выбран"
            )

    # --------------------------------------------------
    # ИСТОРИЯ РАСПОЗНАВАНИЙ
    # --------------------------------------------------

    def load_history(self):
        """Загрузка истории из JSON."""

        try:
            if self.history_file.exists():
                with open(
                        self.history_file,
                        "r",
                        encoding="utf-8"
                ) as file:
                    data = json.load(file)

                    if isinstance(data, list):
                        self.history = data
                    else:
                        self.history = []

        except (OSError, json.JSONDecodeError) as error:
            self.history = []
            print(f"Ошибка загрузки истории: {error}")

    def save_history(self):
        """Сохранение истории в JSON."""

        try:
            self.history_file.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            with open(
                    self.history_file,
                    "w",
                    encoding="utf-8"
            ) as file:
                json.dump(
                    self.history,
                    file,
                    ensure_ascii=False,
                    indent=4
                )

        except OSError as error:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось сохранить историю:\n{error}"
            )

    def add_history_entry(
            self,
            result,
            audio_path,
            language,
            model
    ):
        """Добавление нового распознавания."""

        entry = {
            "date": datetime.now().strftime(
                "%d.%m.%Y %H:%M:%S"
            ),
            "audio_name": Path(audio_path).name,
            "audio_path": str(audio_path),
            "language": language or "Автоопределение",
            "detected_language": result.get("language", ""),
            "model": model,
            "result": result
        }

        self.history.insert(0, entry)

        self.save_history()

    def open_history(self):
        """Открытие окна истории."""

        history_window = ctk.CTkToplevel(self.window)

        history_window.title("История распознаваний")
        history_window.geometry("650x500")
        history_window.minsize(500, 350)

        history_window.transient(self.window)

        title = ctk.CTkLabel(
            history_window,
            text="История распознаваний",
            font=("Arial", 22, "bold")
        )
        title.pack(pady=15)

        scroll_frame = ctk.CTkScrollableFrame(
            history_window
        )
        scroll_frame.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=10
        )

        if not self.history:
            empty_label = ctk.CTkLabel(
                scroll_frame,
                text="История пока пуста."
            )
            empty_label.pack(pady=30)

        else:
            for index, entry in enumerate(self.history):
                item_frame = ctk.CTkFrame(
                    scroll_frame
                )
                item_frame.pack(
                    fill="x",
                    padx=5,
                    pady=5
                )

                info_frame = ctk.CTkFrame(
                    item_frame,
                    fg_color="transparent"
                )
                info_frame.pack(
                    side="left",
                    fill="both",
                    expand=True,
                    padx=10,
                    pady=8
                )

                name_label = ctk.CTkLabel(
                    info_frame,
                    text=entry["audio_name"],
                    font=("Arial", 14, "bold"),
                    anchor="w"
                )
                name_label.pack(anchor="w")

                details = (
                    f'{entry["date"]} | '
                    f'Модель: {entry["model"]} | '
                    f'Язык: {entry["language"]}'
                )

                details_label = ctk.CTkLabel(
                    info_frame,
                    text=details,
                    font=("Arial", 11),
                    text_color="gray",
                    anchor="w"
                )
                details_label.pack(anchor="w")

                buttons_frame = ctk.CTkFrame(
                    item_frame,
                    fg_color="transparent"
                )
                buttons_frame.pack(
                    side="right",
                    padx=10
                )

                open_button = ctk.CTkButton(
                    buttons_frame,
                    text="Открыть",
                    width=80,
                    command=lambda i=index: self.open_history_entry(i)
                )
                open_button.pack(pady=3)

                delete_button = ctk.CTkButton(
                    buttons_frame,
                    text="Удалить",
                    width=80,
                    fg_color="#9B3030",
                    hover_color="#702020",
                    command=lambda i=index, w=history_window:
                    self.delete_history_entry(i, w)
                )
                delete_button.pack(pady=3)

        # Кнопка очистки
        clear_button = ctk.CTkButton(
            history_window,
            text="Очистить историю",
            fg_color="#9B3030",
            hover_color="#702020",
            command=lambda: self.clear_history(history_window)
        )
        clear_button.pack(pady=12)

    def open_history_entry(self, index):
        """Открытие результата из истории."""

        entry = self.history[index]

        self.audio_path = entry["audio_path"]

        self.file_label.configure(
            text=entry["audio_name"]
        )

        self.last_result = entry["result"]

        self.result_box.delete(
            "1.0",
            "end"
        )

        self.update_result_display()

        self.status_label.configure(
            text=f'Загружен результат: {entry["audio_name"]}'
        )

        self.window.lift()

    def delete_history_entry(self, index, history_window):
        """Удаление одной записи."""

        self.history.pop(index)

        self.save_history()

        history_window.destroy()

        self.open_history()

    def clear_history(self, history_window):
        """Полная очистка истории."""

        if not self.history:
            return

        answer = messagebox.askyesno(
            "Подтверждение",
            "Удалить всю историю распознаваний?",
            parent=history_window
        )

        if answer:
            self.history.clear()

            self.save_history()

            history_window.destroy()

            self.open_history()

    # --------------------------------------------------
    # НАСТРОЙКИ
    # --------------------------------------------------

    def open_settings(self):

        settings_window = ctk.CTkToplevel(self.window)

        settings_window.title("Настройки AudioTranscriber")
        settings_window.geometry("480x540")
        settings_window.resizable(False, False)

        settings_window.transient(self.window)
        settings_window.grab_set()

        title = ctk.CTkLabel(
            settings_window,
            text="Настройки программы",
            font=("Arial", 22, "bold")
        )
        title.pack(pady=(20, 15))

        # Переменные настроек
        model_var = ctk.StringVar(
            value=self.settings["model"]
        )

        theme_var = ctk.StringVar(
            value=self.settings["theme"]
        )

        timestamps_var = ctk.BooleanVar(
            value=self.settings["timestamps"]
        )

        format_var = ctk.StringVar(
            value=self.settings["output_format"]
        )

        folder_var = ctk.StringVar(
            value=self.settings["save_folder"]
        )

        # Модель Whisper
        ctk.CTkLabel(
            settings_window,
            text="Модель распознавания:"
        ).pack(pady=(5, 3))

        ctk.CTkOptionMenu(
            settings_window,
            variable=model_var,
            values=["tiny", "base", "small"],
            width=200
        ).pack(pady=5)

        # Тема
        ctk.CTkLabel(
            settings_window,
            text="Тема оформления:"
        ).pack(pady=(12, 3))

        ctk.CTkOptionMenu(
            settings_window,
            variable=theme_var,
            values=["Тёмная", "Светлая", "Системная"],
            width=200
        ).pack(pady=5)

        # Временные метки
        ctk.CTkCheckBox(
            settings_window,
            text="Добавлять временные метки в TXT",
            variable=timestamps_var
        ).pack(pady=15)

        # Формат сохранения
        ctk.CTkLabel(
            settings_window,
            text="Формат сохранения:"
        ).pack(pady=(5, 3))

        ctk.CTkOptionMenu(
            settings_window,
            variable=format_var,
            values=["TXT", "SRT"],
            width=200
        ).pack(pady=5)

        # Папка сохранения
        ctk.CTkLabel(
            settings_window,
            text="Папка сохранения:"
        ).pack(pady=(15, 5))

        folder_frame = ctk.CTkFrame(
            settings_window,
            fg_color="transparent"
        )
        folder_frame.pack(
            fill="x",
            padx=20
        )

        folder_entry = ctk.CTkEntry(
            folder_frame,
            textvariable=folder_var
        )
        folder_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 5)
        )

        def choose_folder():

            folder = filedialog.askdirectory(
                initialdir=folder_var.get()
            )

            if folder:
                folder_var.set(folder)

        ctk.CTkButton(
            folder_frame,
            text="Обзор",
            width=75,
            command=choose_folder
        ).pack(side="right")

        # Информация
        info = ctk.CTkLabel(
            settings_window,
            text=(
                "Модель small требует больше ресурсов.\n"
                "На CPU распознавание может занимать больше времени."
            ),
            text_color="gray",
            font=("Arial", 11)
        )
        info.pack(pady=15)

        # Кнопки
        button_frame = ctk.CTkFrame(
            settings_window,
            fg_color="transparent"
        )
        button_frame.pack(pady=10)

        def apply_settings():

            new_folder = folder_var.get().strip()

            if not new_folder:
                messagebox.showwarning(
                    "Внимание",
                    "Укажите папку сохранения!",
                    parent=settings_window
                )
                return

            # Изменение модели
            self.transcriber.set_model(
                model_var.get()
            )

            # Сохранение настроек
            self.settings = {
                "model": model_var.get(),
                "theme": theme_var.get(),
                "timestamps": timestamps_var.get(),
                "output_format": format_var.get(),
                "save_folder": new_folder
            }

            # Изменение темы
            self.change_theme(theme_var.get())

            # Обновление отображения результата
            self.update_result_display()

            settings_window.destroy()

        ctk.CTkButton(
            button_frame,
            text="Сохранить настройки",
            command=apply_settings,
            width=160
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="Отмена",
            command=settings_window.destroy,
            width=100,
            fg_color="gray"
        ).pack(side="left", padx=5)

    # --------------------------------------------------
    # ТЕМА
    # --------------------------------------------------

    def change_theme(self, choice):

        themes = {
            "Тёмная": "dark",
            "Светлая": "light",
            "Системная": "system"
        }

        ctk.set_appearance_mode(
            themes[choice]
        )

    # --------------------------------------------------
    # РАСПОЗНАВАНИЕ
    # --------------------------------------------------

    def recognize_audio(self):

        if not self.audio_path:
            messagebox.showwarning(
                "Внимание",
                "Сначала выберите аудиофайл!"
            )
            return

        languages = {
            "Автоопределение": None,
            "Русский": "ru",
            "English": "en"
        }

        language = languages[
            self.language_menu.get()
        ]

        # Блокируем кнопки на время обработки
        self.recognize_button.configure(
            state="disabled",
            text="Распознавание..."
        )

        self.settings_button.configure(
            state="disabled"
        )

        self.status_label.configure(
            text="Загрузка модели и обработка аудио..."
        )

        self.result_box.delete("1.0", "end")
        self.last_result = None

        thread = Thread(
            target=self.transcription_worker,
            args=(
                self.audio_path,
                language,
                self.transcriber.model_name
            ),
            daemon=True
        )

        thread.start()

        self.check_transcription_result()

    def transcription_worker(self, audio_path, language, model):

        try:
            result = self.transcriber.transcribe(
                audio_path,
                language=language
            )

            self.result_queue.put(
                (
                    "success",
                    result,
                    audio_path,
                    language,
                    model
                )
            )

        except Exception as error:
            self.result_queue.put(
                ("error", str(error))
            )

    def check_transcription_result(self):

        try:
            data = self.result_queue.get_nowait()

            status = data[0]
            result = data[1]

            if status == "success":

                self.last_result = result

                # Добавляем результат в историю
                self.add_history_entry(
                    result,
                    data[2],
                    data[3],
                    data[4]
                )

                self.update_result_display()

                self.status_label.configure(
                    text="Распознавание завершено!"
                )

            else:

                self.status_label.configure(
                    text="Ошибка распознавания"
                )

                messagebox.showerror(
                    "Ошибка",
                    result
                )

            self.recognize_button.configure(
                state="normal",
                text="Распознать речь"
            )

            self.settings_button.configure(
                state="normal"
            )

        except Empty:

            self.window.after(
                100,
                self.check_transcription_result
            )
    # --------------------------------------------------
    # ФОРМАТИРОВАНИЕ РЕЗУЛЬТАТА
    # --------------------------------------------------

    @staticmethod
    def format_timestamp(seconds, srt=False):

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds_part = seconds % 60

        separator = "," if srt else "."

        return (
            f"{hours:02}:{minutes:02}:"
            f"{seconds_part:06.3f}".replace(".", separator)
        )

    def format_txt(self):

        if not self.last_result:
            return ""

        segments = self.last_result.get("segments", [])

        if not self.settings["timestamps"]:
            return self.last_result.get("text", "").strip()

        lines = []

        for segment in segments:

            timestamp = self.format_timestamp(
                segment["start"]
            )

            text = segment["text"].strip()

            lines.append(
                f"[{timestamp}] {text}"
            )

        return "\n".join(lines)

    def format_srt(self):

        if not self.last_result:
            return ""

        segments = self.last_result.get("segments", [])

        subtitles = []

        for index, segment in enumerate(segments, start=1):

            start = self.format_timestamp(
                segment["start"],
                srt=True
            )

            end = self.format_timestamp(
                segment["end"],
                srt=True
            )

            text = segment["text"].strip()

            subtitles.append(
                f"{index}\n"
                f"{start} --> {end}\n"
                f"{text}"
            )

        return "\n\n".join(subtitles)

    def update_result_display(self):

        if not self.last_result:
            return

        text = self.format_txt()

        self.result_box.delete(
            "1.0",
            "end"
        )

        self.result_box.insert(
            "1.0",
            text
        )

    # --------------------------------------------------
    # СОХРАНЕНИЕ
    # --------------------------------------------------

    def save_result(self):

        if not self.last_result:

            messagebox.showwarning(
                "Внимание",
                "Сначала выполните распознавание!"
            )
            return

        output_format = self.settings["output_format"]

        if output_format == "SRT":
            text = self.format_srt()
            extension = ".srt"

            file_types = [
                ("Файлы субтитров", "*.srt")
            ]

        else:
            text = self.format_txt()
            extension = ".txt"

            file_types = [
                ("Текстовые файлы", "*.txt")
            ]

        if not text.strip():
            messagebox.showwarning(
                "Внимание",
                "Нет текста для сохранения!"
            )
            return

        save_folder = Path(
            self.settings["save_folder"]
        )

        try:
            save_folder.mkdir(
                parents=True,
                exist_ok=True
            )
        except OSError as error:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось создать папку:\n{error}"
            )
            return

        default_name = "transcription" + extension

        path = filedialog.asksaveasfilename(
            initialdir=str(save_folder),
            initialfile=default_name,
            defaultextension=extension,
            filetypes=file_types
        )

        if path:

            try:
                with open(
                    path,
                    "w",
                    encoding="utf-8"
                ) as file:
                    file.write(text)

                messagebox.showinfo(
                    "Готово",
                    f"Результат сохранён:\n{Path(path).name}"
                )

            except OSError as error:

                messagebox.showerror(
                    "Ошибка сохранения",
                    str(error)
                )

    # --------------------------------------------------
    # ЗАПУСК
    # --------------------------------------------------

    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    app = AudioTranscriberApp()
    app.run()