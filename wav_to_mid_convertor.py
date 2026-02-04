# import librosa
# import numpy as np
# from midiutil import MIDIFile

# def process_audio_to_uds(wav_path, midi_output_path="output.mid", threshold_cents=50):
#     # 1. Load the WAV file
#     y, sr = librosa.load(wav_path, sr=None)
    
#     # 2. Extract Pitch using pYIN
#     # hop_length of 512 is standard (approx 11ms at 44.1kHz)
#     hop_length = 512
#     f0, voiced_flag, voiced_probs = librosa.pyin(y, 
#                                                  fmin=librosa.note_to_hz('C2'), 
#                                                  fmax=librosa.note_to_hz('C7'),
#                                                  sr=sr,
#                                                  hop_length=hop_length)
    
#     # --- STEP: SAVE TO MIDI ---
#     # Create the MIDI object (1 track, default tempo 120)
#     midi = MIDIFile(1)
#     midi.addTempo(0, 0, 120)
    
#     # Convert Hz to MIDI note numbers (e.g., 440Hz -> 69)
#     # We use a very short duration for each frame to capture the contour
#     frame_duration = hop_length / sr 
    
#     for i, pitch in enumerate(f0):
#         if not np.isnan(pitch):
#             midi_note = int(round(librosa.hz_to_midi(pitch)))
#             # addNote(track, channel, pitch, time, duration, volume)
#             midi.addNote(0, 0, midi_note, i * frame_duration, frame_duration, 100)
            
#     with open(midi_output_path, "wb") as output_file:
#         midi.writeFile(output_file)
#     print(f"MIDI file saved to: {midi_output_path}")
    
#     # --- STEP: CONVERT TO UDS ---
#     pitches = f0[~np.isnan(f0)]
#     if len(pitches) == 0:
#         return "No pitch detected"

#     uds_string = "*"
#     current_note_pitch = pitches[0]
    
#     for next_pitch in pitches[1:]:
#         diff_cents = 1200 * np.log2(next_pitch / current_note_pitch)
        
#         if diff_cents > threshold_cents:
#             uds_string += "U"
#             current_note_pitch = next_pitch
#         elif diff_cents < -threshold_cents:
#             uds_string += "D"
#             current_note_pitch = next_pitch
#         else:
#             # We skip 'S' for frame-by-frame to keep the string clean, 
#             # unless the pitch is stable over many frames.
#             pass 

#     return uds_string

# # Example execution:
# result = process_audio_to_uds("record.wav")
# print(f"UDS Result: {result}")

import librosa
import numpy as np
from midiutil import MIDIFile
import scipy.ndimage

def wav_to_clean_uds(wav_path, midi_out="debug.mid", threshold_cents=100):
    # 1. Load and Clean Audio
    y, sr = librosa.load(wav_path, sr=None)
    # Simple noise gate: remove dead silence
    y, _ = librosa.effects.trim(y, top_db=20)
    
    # 2. Extract Pitch (pYIN)
    f0, voiced_flag, voiced_probs = librosa.pyin(y, 
                                                 fmin=librosa.note_to_hz('C2'), 
                                                 fmax=librosa.note_to_hz('C7'),
                                                 sr=sr)
    
    # 3. Smooth the Pitch (Crucial to avoid "bad" output)
    # This removes the tiny tremors in a human voice
    f0_smoothed = scipy.ndimage.median_filter(f0, size=11)
    
    # 4. Group Frames into Discrete Notes
    notes = []
    if len(f0_smoothed) > 0:
        temp_note_frames = []
        for p in f0_smoothed:
            if np.isnan(p):
                if temp_note_frames:
                    notes.append(np.median(temp_note_frames))
                    temp_note_frames = []
                continue
            
            if not temp_note_frames:
                temp_note_frames.append(p)
            else:
                # If pitch changes by more than the threshold, it's a new note
                diff = 1200 * np.log2(p / np.median(temp_note_frames))
                if abs(diff) > threshold_cents:
                    notes.append(np.median(temp_note_frames))
                    temp_note_frames = [p]
                else:
                    temp_note_frames.append(p)
        if temp_note_frames:
            notes.append(np.median(temp_note_frames))

    # 5. Save Clean MIDI
    midi = MIDIFile(1)
    midi.addTempo(0, 0, 120)
    for i, n in enumerate(notes):
        midi_pitch = int(round(librosa.hz_to_midi(n)))
        # Each note is given a fixed length (0.5s) for easy listening
        midi.addNote(0, 0, midi_pitch, i * 0.5, 0.4, 100)
    
    with open(midi_out, "wb") as f:
        midi.writeFile(f)
    print(f"--- MIDI saved to {midi_out} ---")

    # 6. Generate UDS String from grouped notes
    uds = ["*"]
    for i in range(1, len(notes)):
        diff = 1200 * np.log2(notes[i] / notes[i-1])
        if diff > threshold_cents: uds.append("U")
        elif diff < -threshold_cents: uds.append("D")
        else: uds.append("S")
    
    return "".join(uds)

# # Run:
# print(wav_to_clean_uds("record.wav"))