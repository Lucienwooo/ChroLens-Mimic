import sys
import os

main_dir = r"c:\Users\Lucien\Documents\GitHub\ChroLens-Mimic\main"
sys.path.insert(0, main_dir)
sys.path.insert(0, os.path.join(main_dir, "modules"))

import text_script_editor
import tkinter as tk

root = tk.Tk()
editor = text_script_editor.TextCommandEditor(parent=root, script_path=None)

# 1. Test Repeat Loop (normal & infinite)
sample_loops = {
    "events": [
        {
            "type": "loop_start",
            "loop_type": "repeat",
            "max_count": 10,
            "time": 0.0
        },
        {
            "type": "loop_end",
            "loop_type": "repeat",
            "time": 0.1
        },
        {
            "type": "loop_start",
            "loop_type": "repeat",
            "max_count": 999999,
            "time": 0.2
        },
        {
            "type": "loop_end",
            "loop_type": "repeat",
            "time": 0.3
        }
    ]
}

text_loops = editor._json_to_text(sample_loops)
print("Repeat Loops Text Output (repr):", repr(text_loops))
if "無限" not in text_loops or "10次" not in text_loops or "重複結束" not in text_loops:
    print("FAILED: Repeat loops formatting is incorrect!")
    sys.exit(1)

parsed_loops = editor._text_to_json(text_loops)
print("Parsed Repeat Loops count:", len(parsed_loops.get("events", [])))
events = parsed_loops.get("events", [])
if len(events) != 4:
    print("FAILED: Repeat loops roundtrip parsing size is incorrect!")
    sys.exit(1)
if events[0]["max_count"] != 10 or events[2]["max_count"] != 999999:
    print("FAILED: Parsed max counts do not match!")
    sys.exit(1)

print("SUCCESS: Repeat loops roundtrip is 100% correct!")

# 2. Test Condition Loops (當圖片存在 & 當圖片消失)
sample_while_loops = {
    "events": [
        {
            "type": "loop_start",
            "loop_type": "while",
            "condition": {
                "type": "image_exists",
                "image": "loading"
            },
            "time": 0.0
        },
        {
            "type": "loop_end",
            "loop_type": "while",
            "time": 0.1
        },
        {
            "type": "loop_start",
            "loop_type": "while",
            "condition": {
                "type": "image_missing",
                "image": "loading"
            },
            "time": 0.2
        },
        {
            "type": "loop_end",
            "loop_type": "while",
            "time": 0.3
        }
    ]
}

text_while = editor._json_to_text(sample_while_loops)
print("While Loops Text Output (repr):", repr(text_while))
if "當圖片存在" not in text_while or "當圖片消失" not in text_while or "迴圈結束" not in text_while:
    print("FAILED: While loops formatting is incorrect!")
    sys.exit(1)

parsed_while = editor._text_to_json(text_while)
print("Parsed While Loops count:", len(parsed_while.get("events", [])))
while_events = parsed_while.get("events", [])
if len(while_events) != 4:
    print("FAILED: While loops roundtrip parsing size is incorrect!")
    sys.exit(1)
if while_events[0]["condition"]["type"] != "image_exists" or while_events[2]["condition"]["type"] != "image_missing":
    print("FAILED: Parsed condition types do not match!")
    sys.exit(1)

print("SUCCESS: While loops roundtrip is 100% correct!")

# 3. Test Random Delay
sample_delay = {
    "events": [
        {
            "type": "random_delay",
            "min_ms": 100,
            "max_ms": 500,
            "time": 0.0
        }
    ]
}

text_delay = editor._json_to_text(sample_delay)
print("Random Delay Text Output (repr):", repr(text_delay))
if "0s100" not in text_delay or "0s500" not in text_delay or "ms" in text_delay:
    print("FAILED: Random delay formatting is incorrect!")
    sys.exit(1)

parsed_delay = editor._text_to_json(text_delay)
print("Parsed Random Delay count:", len(parsed_delay.get("events", [])))
delay_events = parsed_delay.get("events", [])
if len(delay_events) != 1:
    print("FAILED: Random delay roundtrip parsing size is incorrect!")
    sys.exit(1)
if delay_events[0]["min_ms"] != 100 or delay_events[0]["max_ms"] != 500:
    print("FAILED: Parsed random delay bounds do not match!")
    sys.exit(1)

print("SUCCESS: Random delay roundtrip is 100% correct!")
print("ALL TESTS PASSED SUCCESSFULLY!")
sys.exit(0)
