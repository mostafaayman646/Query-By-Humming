import os

from mid_to_string import get_uds_from_midi
from wav_to_mid_convertor import wav_to_clean_uds
from Compare import edit_distance

#1. Creating our DB
music_db = {}
db_folder = 'database/'
print("Analyzing database... this might take a second.")
for file in os.listdir(db_folder):
    if file.endswith(".mid"):
        path = os.path.join(db_folder, file)
        music_db[file] = get_uds_from_midi(path)

# 2. Process your Hum
print("Analyzing your humming...")
user_hum_uds = wav_to_clean_uds("ta7ya_masr.wav")

# 3. Match
results = []
for song_name, song_uds in music_db.items():
    dist = edit_distance(user_hum_uds, song_uds)
    results.append((song_name, dist))

# 4. Show Top Matches
# Lower distance = Better match
ranked = sorted(results, key=lambda x: x[1])

print("\n--- TOP MATCHES ---")
for name, score in ranked[:5]:
    print(f"Song: {name} | Match Score (Lower is better): {score}")