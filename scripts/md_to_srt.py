import re
from datetime import timedelta

md_path = "transcript.md"
srt_path = "transcript.srt"

def sec_to_srt_time(sec):
    td = timedelta(seconds=sec)
    h, remainder = divmod(td.seconds, 3600)
    m, s = divmod(remainder, 60)
    ms = int(td.microseconds / 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def parse_md(md_path):
    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()
    blocks = []
    i = 0
    while i < len(lines):
        # Match time stamp (e.g. 0:00 or 12:05)
        m = re.match(r"^(\d{1,2}):(\d{2})", lines[i])
        if m:
            start_min = int(m.group(1))
            start_sec = int(m.group(2))
            start_time = start_min * 60 + start_sec
            # Find next timestamp for end
            j = i + 1
            while j < len(lines):
                m2 = re.match(r"^(\d{1,2}):(\d{2})", lines[j])
                if m2:
                    break
                j += 1
            end_time = None
            if j < len(lines):
                end_min = int(m2.group(1))
                end_sec = int(m2.group(2))
                end_time = end_min * 60 + end_sec
            else:
                end_time = start_time + 6  # default 6s if last block
            # Get text
            text = "".join(lines[i+1:j]).strip()
            blocks.append((start_time, end_time, text))
            i = j
        else:
            i += 1
    return blocks

def write_srt(blocks, srt_path):
    with open(srt_path, "w", encoding="utf-8") as f:
        for idx, (start, end, text) in enumerate(blocks, 1):
            f.write(f"{idx}\n")
            f.write(f"{sec_to_srt_time(start)} --> {sec_to_srt_time(end)}\n")
            f.write(f"{text}\n\n")

if __name__ == "__main__":
    blocks = parse_md(md_path)
    write_srt(blocks, srt_path)
    print(f"Arquivo SRT gerado: {srt_path}")
