import mido

def get_uds_from_midi(file_path):
    mid = mido.MidiFile(file_path)
    pitches = []

    # Extract all 'note_on' events with volume > 0
    for msg in mid:
        if msg.type == 'note_on' and msg.velocity > 0:
            pitches.append(msg.note)

    # Convert to Parsons Code (U, D, S)
    uds_string = "" 
    for i in range(1, len(pitches)):
        if pitches[i] > pitches[i-1]:
            uds_string += "U"
        elif pitches[i] < pitches[i-1]:
            uds_string += "D"
        else:
            uds_string += "S"
            
    return uds_string

# Usage
# print(get_uds_from_midi('melody.mid'))