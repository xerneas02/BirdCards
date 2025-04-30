import ffmpeg
import io

def convert_wav_to_mp3(wav_io):
    """
    Convertit un flux BytesIO contenant un fichier WAV en flux BytesIO MP3
    en utilisant ffmpeg-python.
    """
    try:
        # Lire le contenu du flux WAV
        wav_data = wav_io.read()
        # Utiliser ffmpeg pour convertir le flux (via pipe)
        process = (
            ffmpeg
            .input('pipe:0')
            .output('pipe:1', format='mp3')
            .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
        )
        stdout_data, stderr_data = process.communicate(input=wav_data)
        # Place le MP3 converti dans un BytesIO
        mp3_io = io.BytesIO(stdout_data)
        mp3_io.seek(0)
        return mp3_io
    except Exception as e:
        print(f"Erreur lors de la conversion avec ffmpeg-python: {e}")
        return None