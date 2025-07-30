import os
import argparse
import torch
import whisper
from tqdm import tqdm
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading
import time

class WhisperTranscriptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Whisper Audio Transcription")
        self.root.geometry("650x600")
        self.root.resizable(True, True)
        
        # Set style
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Arial", 10))
        self.style.configure("TLabel", font=("Arial", 10))
        self.style.configure("Header.TLabel", font=("Arial", 12, "bold"))
        
        # Variables
        self.input_path = tk.StringVar()
        self.model_var = tk.StringVar(value="base")
        self.format_var = tk.StringVar(value="txt")
        self.language_var = tk.StringVar()
        self.device_var = tk.StringVar(value="auto")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.status_var = tk.StringVar(value="Ready")
        
        # Processing flag
        self.processing = False
        
        # Create UI
        self.create_widgets()
        
        # Check GPU availability
        self.check_gpu()
    
    def check_gpu(self):
        """Check if GPU is available and update UI"""
        gpu_available, gpu_message = self.check_gpu_availability()
        self.log(gpu_message)
        
        # Update device dropdown based on availability
        values = ["auto", "cpu"]
        if gpu_available:
            values.append("cuda")
        
        self.device_dropdown['values'] = values
        
        # Set default value
        if self.device_var.get() not in values:
            self.device_var.set("auto")
    def create_widgets(self):
        """Create all UI widgets"""
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Input section
        ttk.Label(main_frame, text="Audio Input", style="Header.TLabel").grid(column=0, row=0, sticky=tk.W, pady=(0, 10))
        
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(column=0, row=1, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Entry(input_frame, textvariable=self.input_path, width=50).grid(column=0, row=0, sticky=(tk.W, tk.E))
        ttk.Button(input_frame, text="Select File", command=self.select_file).grid(column=1, row=0, padx=5)
        ttk.Button(input_frame, text="Select Folder", command=self.select_directory).grid(column=2, row=0)
        
        # Options section
        ttk.Label(main_frame, text="Transcription Options", style="Header.TLabel").grid(column=0, row=2, sticky=tk.W, pady=(0, 10))
        
        options_frame = ttk.Frame(main_frame)
        options_frame.grid(column=0, row=3, sticky=(tk.W, tk.E), pady=(0, 15))
        options_frame.columnconfigure(1, weight=1)
        options_frame.columnconfigure(3, weight=1)
        
        # Model selection
        ttk.Label(options_frame, text="Model:").grid(column=0, row=0, sticky=tk.W, padx=(0, 10))
        model_dropdown = ttk.Combobox(options_frame, textvariable=self.model_var, width=10, state="readonly")
        model_dropdown['values'] = ("tiny", "base", "small", "medium", "large")
        model_dropdown.grid(column=1, row=0, sticky=tk.W, padx=(0, 20))
        
        # Format selection
        ttk.Label(options_frame, text="Format:").grid(column=2, row=0, sticky=tk.W, padx=(0, 10))
        format_dropdown = ttk.Combobox(options_frame, textvariable=self.format_var, width=10, state="readonly")
        format_dropdown['values'] = ("txt", "srt", "vtt", "json")
        format_dropdown.grid(column=3, row=0, sticky=tk.W)
        
        # Language selection
        ttk.Label(options_frame, text="Language:").grid(column=0, row=1, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        ttk.Entry(options_frame, textvariable=self.language_var, width=10).grid(column=1, row=1, sticky=tk.W, pady=(10, 0))
        ttk.Label(options_frame, text="(e.g., 'en', 'fr', 'zh')").grid(column=2, row=1, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # Device selection
        ttk.Label(options_frame, text="Device:").grid(column=0, row=2, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.device_dropdown = ttk.Combobox(options_frame, textvariable=self.device_var, width=10, state="readonly")
        self.device_dropdown['values'] = ("auto", "cpu", "cuda")
        self.device_dropdown.grid(column=1, row=2, sticky=tk.W, pady=(10, 0))
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(column=0, row=4, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Button(button_frame, text="Start Transcription", command=self.start_transcription).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=self.cancel_transcription).pack(side=tk.LEFT)
        
        # Progress section
        ttk.Label(main_frame, text="Progress", style="Header.TLabel").grid(column=0, row=5, sticky=tk.W, pady=(0, 10))
        
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(column=0, row=6, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, length=600)
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(progress_frame, textvariable=self.status_var).pack(anchor=tk.W)
        
        # Output log
        ttk.Label(main_frame, text="Log", style="Header.TLabel").grid(column=0, row=7, sticky=tk.W, pady=(0, 10))
        
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(column=0, row=8, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = tk.Text(log_frame, height=10, width=70, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(8, weight=1)
        
    def select_file(self):
        """Open file dialog to select audio file"""
        file_path = filedialog.askopenfilename(
            title="Select an audio file",
            filetypes=(
                ("Audio files", "*.mp3 *.wav *.m4a *.flac *.ogg"),
                ("All files", "*.*")
            )
        )
        if file_path:
            self.input_path.set(file_path)
            self.log(f"Selected file: {file_path}")
    
    def select_directory(self):
        """Open dialog to select directory with audio files"""
        dir_path = filedialog.askdirectory(title="Select a directory containing audio files")
        if dir_path:
            self.input_path.set(dir_path)
            self.log(f"Selected directory: {dir_path}")
    
    def log(self, message):
        """Add message to log and scroll to end"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def check_gpu_availability(self):
        """Check if GPU is available and return device info"""
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            return True, f"GPU available: {gpu_name}"
        else:
            return False, "GPU not available, using CPU"
    
    def start_transcription(self):
        """Start the transcription process"""
        if self.processing:
            messagebox.showwarning("Warning", "Transcription already in progress!")
            return
            
        input_path = self.input_path.get()
        if not input_path:
            messagebox.showerror("Error", "Please select an audio file or directory first!")
            return
            
        if not os.path.exists(input_path):
            messagebox.showerror("Error", f"The path does not exist: {input_path}")
            return
            
        # Start transcription in a separate thread
        self.processing = True
        threading.Thread(target=self.process_transcription, daemon=True).start()
    
    def cancel_transcription(self):
        """Cancel the ongoing transcription"""
        if self.processing:
            self.processing = False
            self.status_var.set("Cancelled by user")
            self.log("Transcription cancelled by user.")
    
    def get_device(self):
        """Determine which device to use based on selection and availability"""
        device_choice = self.device_var.get()
        
        if device_choice == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device_choice
    
    def simulate_progress(self):
        """Simulate progress updates since whisper doesn't provide progress"""
        self.progress_var.set(0)
        step = 0
        
        while self.processing and step < 95:
            # Progress simulation - starts fast, slows down
            if step < 20:
                increment = 0.5
            elif step < 50:
                increment = 0.3
            elif step < 80:
                increment = 0.1
            else:
                increment = 0.05
                
            step += increment
            self.progress_var.set(step)
            time.sleep(0.1)
    
    def process_transcription(self):
        """Process the transcription task"""
        try:
            input_path = self.input_path.get()
            model_name = self.model_var.get()
            output_format = self.format_var.get()
            language = self.language_var.get() if self.language_var.get() else None
            device = self.get_device()
            
            self.progress_var.set(0)
            self.status_var.set("Starting transcription...")
            self.log(f"Starting transcription with model: {model_name} on {device}")
            
            # Start progress simulation in separate thread
            progress_thread = threading.Thread(target=self.simulate_progress, daemon=True)
            progress_thread.start()
            
            if os.path.isdir(input_path):
                self.batch_transcribe(input_path, model_name, output_format, language, device)
            else:
                self.transcribe_audio(input_path, model_name, output_format, language, device)
                
            # Ensure progress bar reaches 100%
            self.progress_var.set(100)
            
            if self.processing:  # If not cancelled
                self.status_var.set("Transcription completed!")
                self.log("Transcription completed successfully!")
                messagebox.showinfo("Success", "Transcription completed successfully!")
        except Exception as e:
            self.status_var.set("Error occurred")
            self.log(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred during transcription:\n{str(e)}")
        finally:
            self.processing = False
    
    def transcribe_audio(self, audio_path, model_name, output_format, language, device):
        """Transcribe a single audio file"""
        self.log(f"Loading model: {model_name} on {device}")
        # Load the Whisper model
        model = whisper.load_model(model_name, device=device)
        
        self.log(f"Transcribing: {audio_path}")
        # Transcribe the audio
        transcribe_options = {"fp16": device == "cuda"}  # Use half-precision for GPU
        if language:
            transcribe_options["language"] = language
        
        result = model.transcribe(audio_path, **transcribe_options)
        
        # Get base filename without extension
        base_name = os.path.splitext(audio_path)[0]
        output_file = f"{base_name}.{output_format}"
        
        # Save the transcription based on format
        if output_format == "txt":
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(result["text"])
        elif output_format in ["srt", "vtt"]:
            with open(output_file, "w", encoding="utf-8") as f:
                segments = result["segments"]
                for i, segment in enumerate(segments):
                    start_time = self.format_timestamp(segment["start"], output_format)
                    end_time = self.format_timestamp(segment["end"], output_format)
                    text = segment["text"].strip()
                    
                    if output_format == "srt":
                        f.write(f"{i+1}\n")
                        f.write(f"{start_time} --> {end_time}\n")
                        f.write(f"{text}\n\n")
                    else:  # vtt
                        if i == 0:
                            f.write("WEBVTT\n\n")
                        f.write(f"{start_time} --> {end_time}\n")
                        f.write(f"{text}\n\n")
        elif output_format == "json":
            import json
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=4)
        
        self.log(f"Transcription saved to: {output_file}")
        return output_file
    
    def batch_transcribe(self, directory, model_name, output_format, language, device):
        """Transcribe all audio files in a directory"""
        audio_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg']
        
        # Get all audio files in the directory
        audio_files = []
        for file in os.listdir(directory):
            if any(file.lower().endswith(ext) for ext in audio_extensions):
                audio_files.append(os.path.join(directory, file))
        
        if not audio_files:
            self.log("No audio files found in the directory.")
            return []
        
        self.log(f"Found {len(audio_files)} audio files to process")
        
        # Load the model once for all files
        self.log(f"Loading model: {model_name} on {device}")
        model = whisper.load_model(model_name, device=device)
        
        # Process each file
        output_files = []
        for i, audio_file in enumerate(audio_files):
            if not self.processing:  # Check if cancelled
                break
                
            try:
                self.status_var.set(f"Transcribing file {i+1} of {len(audio_files)}: {os.path.basename(audio_file)}")
                self.log(f"Transcribing: {audio_file}")
                
                # Transcribe the audio
                transcribe_options = {"fp16": device == "cuda"}
                if language:
                    transcribe_options["language"] = language
                
                result = model.transcribe(audio_file, **transcribe_options)
                
                # Get base filename without extension
                base_name = os.path.splitext(audio_file)[0]
                output_file = f"{base_name}.{output_format}"
                
                # Save the transcription based on format
                if output_format == "txt":
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(result["text"])
                elif output_format in ["srt", "vtt"]:
                    with open(output_file, "w", encoding="utf-8") as f:
                        segments = result["segments"]
                        for j, segment in enumerate(segments):
                            start_time = self.format_timestamp(segment["start"], output_format)
                            end_time = self.format_timestamp(segment["end"], output_format)
                            text = segment["text"].strip()
                            
                            if output_format == "srt":
                                f.write(f"{j+1}\n")
                                f.write(f"{start_time} --> {end_time}\n")
                                f.write(f"{text}\n\n")
                            else:  # vtt
                                if j == 0:
                                    f.write("WEBVTT\n\n")
                                f.write(f"{start_time} --> {end_time}\n")
                                f.write(f"{text}\n\n")
                elif output_format == "json":
                    import json
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(result, f, indent=4)
                
                self.log(f"Transcription saved to: {output_file}")
                output_files.append(output_file)
                
            except Exception as e:
                self.log(f"Error processing {audio_file}: {str(e)}")
        
        return output_files
    
    def format_timestamp(self, seconds, output_format):
        """Format timestamp based on output format"""
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        secs = int(seconds % 60)
        millisecs = int((seconds - int(seconds)) * 1000)
        
        if output_format == "srt":
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
        else:  # vtt
            return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Transcribe audio files using OpenAI's Whisper")
    parser.add_argument("--input", help="Audio file or directory path (optional, will open GUI if not provided)")
    parser.add_argument("--model", default="base", choices=["tiny", "base", "small", "medium", "large"],
                        help="Model size to use")
    parser.add_argument("--format", default="txt", choices=["txt", "srt", "vtt", "json"],
                        help="Output format")
    parser.add_argument("--language", help="Language code (optional, auto-detected if not specified)")
    parser.add_argument("--device", choices=["cuda", "cpu"], help="Device to use (default: auto-detect)")
    parser.add_argument("--gui", action="store_true", help="Force GUI mode even with command line arguments")
    
    args = parser.parse_args()
    
    # If input is provided and GUI not forced, use command line mode
    if args.input and not args.gui:
        # Check GPU availability
        gpu_available = torch.cuda.is_available()
        if gpu_available:
            print(f"GPU available: {torch.cuda.get_device_name(0)}")
        else:
            print("GPU not available, using CPU")
        
        # Determine device to use
        device = args.device
        if device is None:
            device = "cuda" if gpu_available else "cpu"
        
        input_path = args.input
        
        if os.path.isdir(input_path):
            batch_transcribe(input_path, args.model, args.format, args.language, device)
        elif os.path.isfile(input_path):
            transcribe_audio(input_path, args.model, args.format, args.language, device)
        else:
            print(f"Input path does not exist: {input_path}")
    else:
        # Start GUI
        root = tk.Tk()
        app = WhisperTranscriptionApp(root)
        root.mainloop()

# Command line functions (used when not in GUI mode)
def transcribe_audio(audio_path, model_name="base", output_format="txt", language=None, device=None):
    """Transcribe audio file using OpenAI's Whisper model."""
    # Determine device to use
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
    print(f"Loading model: {model_name} on {device}")
    # Load the Whisper model
    model = whisper.load_model(model_name, device=device)
    
    print(f"Transcribing: {audio_path}")
    # Transcribe the audio
    transcribe_options = {"fp16": device == "cuda"}  # Use half-precision for GPU
    if language:
        transcribe_options["language"] = language
    
    result = model.transcribe(audio_path, **transcribe_options)
    
    # Get base filename without extension
    base_name = os.path.splitext(audio_path)[0]
    output_file = f"{base_name}.{output_format}"
    
    # Save the transcription based on format
    if output_format == "txt":
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result["text"])
    elif output_format in ["srt", "vtt"]:
        with open(output_file, "w", encoding="utf-8") as f:
            segments = result["segments"]
            for i, segment in enumerate(segments):
                start_time = format_timestamp(segment["start"], output_format)
                end_time = format_timestamp(segment["end"], output_format)
                text = segment["text"].strip()
                
                if output_format == "srt":
                    f.write(f"{i+1}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{text}\n\n")
                else:  # vtt
                    if i == 0:
                        f.write("WEBVTT\n\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{text}\n\n")
    elif output_format == "json":
        import json
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4)
    
    print(f"Transcription saved to: {output_file}")
    return output_file

def format_timestamp(seconds, output_format):
    """Format timestamp based on output format"""
    hours = int(seconds / 3600)
    minutes = int((seconds % 3600) / 60)
    secs = int(seconds % 60)
    millisecs = int((seconds - int(seconds)) * 1000)
    
    if output_format == "srt":
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    else:  # vtt
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"

def batch_transcribe(directory, model_name="base", output_format="txt", language=None, device=None):
    """Transcribe all audio files in a directory"""
    audio_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg']
    
    # Get all audio files in the directory
    audio_files = []
    for file in os.listdir(directory):
        if any(file.lower().endswith(ext) for ext in audio_extensions):
            audio_files.append(os.path.join(directory, file))
    
    if not audio_files:
        print("No audio files found in the directory.")
        return []
    
    print(f"Found {len(audio_files)} audio files to process")
    
    # Process each file
    output_files = []
    for audio_file in tqdm(audio_files, desc="Transcribing files"):
        try:
            output_file = transcribe_audio(audio_file, model_name, output_format, language, device)
            output_files.append(output_file)
        except Exception as e:
            print(f"Error processing {audio_file}: {str(e)}")
    
    return output_files

if __name__ == "__main__":
    main()
