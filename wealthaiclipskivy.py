import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.videoplayer import VideoPlayer
from moviepy.editor import VideoFileClip, concatenate_videoclips
import librosa
import numpy as np


class VideoEditorLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 10
        self.padding = 10

        # Add controls
        self.main_video_btn = Button(text="Select Main Video", on_press=self.select_main_video)
        self.additional_videos_btn = Button(text="Select Additional Videos", on_press=self.select_additional_videos)
        self.start_process_btn = Button(text="Start Processing", on_press=self.process_videos)
        self.reset_process_btn = Button(text="Reset Process", on_press=self.reset_process)

        self.add_widget(self.main_video_btn)
        self.add_widget(self.additional_videos_btn)
        self.add_widget(self.start_process_btn)
        self.add_widget(self.reset_process_btn)

        self.progress_bar = ProgressBar(max=100)
        self.add_widget(self.progress_bar)

        self.status_label = Label(text="Ready to process.")
        self.add_widget(self.status_label)

        # Video-related data
        self.main_video_path = None
        self.additional_video_paths = []

    def select_main_video(self, instance):
        # Popup file chooser to select the main video
        self.file_chooser = FileChooserListView(on_submit=self._set_main_video)
        popup = Popup(title="Select Main Video", content=self.file_chooser, size_hint=(0.8, 0.8))
        popup.open()

    def _set_main_video(self, filechooser, selection, touch):
        # Set the main video path from selection
        if selection:
            self.main_video_path = selection[0]
            self.status_label.text = f"Selected: {self.main_video_path}"
            self.main_clip = VideoFileClip(self.main_video_path)

    def select_additional_videos(self, instance):
        # Popup file chooser to select additional videos
        self.file_chooser = FileChooserListView(on_submit=self._set_additional_videos)
        popup = Popup(title="Select Additional Videos", content=self.file_chooser, size_hint=(0.8, 0.8))
        popup.open()

    def _set_additional_videos(self, filechooser, selection, touch):
        # Set additional video paths from selection
        if selection:
            self.additional_video_paths = selection
            self.status_label.text = f"Selected {len(selection)} additional videos."

    def process_videos(self, instance):
        if not self.main_video_path or not self.additional_video_paths:
            self.status_label.text = "Please select the main video and additional videos."
            return

        self.status_label.text = "Processing..."
        self.progress_bar.value = 10

        # Step 1: Extract audio and detect beats
        self.extract_audio_and_detect_beats()

        self.progress_bar.value = 30

        # Step 2: Manipulate video clips based on detected beats
        self.manipulate_videos()

        self.progress_bar.value = 60

        # Step 3: Export the final video with audio
        self.export_final_video()

        self.progress_bar.value = 100
        self.status_label.text = "Processing complete."

    def extract_audio_and_detect_beats(self):
        # Extract audio from the main video
        audio_path = "main_audio.wav"
        self.main_clip.audio.write_audiofile(audio_path)  # Extract audio

        # Detect tempo and beats using librosa
        y, sr = librosa.load(audio_path)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)

        # Convert beat frames to time intervals
        self.beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    def manipulate_videos(self):
        # Load additional video clips and standardize their size and frame rate
        additional_clips = [
            VideoFileClip(path).resize(newsize=self.main_clip.size).set_fps(24)
            for path in self.additional_video_paths
        ]

        self.final_clips = []
        for beat_start, beat_end in zip(self.beat_times, self.beat_times[1:]):
            if not additional_clips:
                break

            random_clip = np.random.choice(additional_clips)
            additional_clips.remove(random_clip)

            clip_duration = random_clip.duration
            mid_point = clip_duration / 2

            subclip_start = max(0, mid_point - (beat_end - beat_start) / 2)
            subclip_end = min(clip_duration, mid_point + (beat_end - beat_start) / 2)

            trimmed_clip = random_clip.subclip(subclip_start, subclip_end).without_audio()
            self.final_clips.append(trimmed_clip)

    def export_final_video(self):
        final_video = concatenate_videoclips(self.final_clips)

        if final_video.duration > self.main_clip.duration:
            final_video = final_video.subclip(0, self.main_clip.duration)

        final_video = final_video.set_audio(self.main_clip.audio.subclip(0, final_video.duration))

        save_path = "final_video.mp4"
        final_video.write_videofile(save_path)
        self.status_label.text = f"Final video saved at {save_path}"

    def reset_process(self, instance):
        self.main_video_path = None
        self.additional_video_paths = []
        self.status_label.text = "Ready to process."
        self.progress_bar.value = 0


class VideoEditorApp(App):
    def build(self):
        return VideoEditorLayout()


if __name__ == "__main__":
    VideoEditorApp().run()
