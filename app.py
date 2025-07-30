from flask import Flask, request, jsonify, render_template
import whisper
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')  # Serve the front-end HTML page

@app.route('/transcribe', methods=['POST'])
def transcribe():
    audio_file = request.files['file']
    model_name = request.form.get('model', 'base')
    output_format = request.form.get('format', 'txt')
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    # Save the uploaded file temporarily
    file_path = f'temp/{audio_file.filename}'
    audio_file.save(file_path)

    # Load Whisper model and transcribe
    model = whisper.load_model(model_name, device=device)
    result = model.transcribe(file_path)

    # Clean up temporary file
    os.remove(file_path)

    # Return the transcription
    return jsonify({'text': result['text']})

if __name__ == '__main__':
    app.run(debug=True)
