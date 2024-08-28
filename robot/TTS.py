import edge_tts
from pydub import AudioSegment
from pydub.playback import play
import asyncio

async def generate_speech(text, filename):
    # Create an instance of the TTS engine
    communicate = edge_tts.Communicate()

    # Generate speech and save to a file
    with open(filename, 'wb') as f:
        await communicate.generate(text=text, output=f)

def play_audio(filename):
    # Load the audio file
    audio = AudioSegment.from_file(filename)

    # Play the audio
    play(audio)

async def main():
    text = "Hello, this is a test of the Edge TTS library."
    filename = "output.wav"

    # Generate speech
    await generate_speech(text, filename)

    # Play the generated audio
    play_audio(filename)

# Run the main function
asyncio.run(main())
