import sys
import os
import time

# Add the modules directory to sys.path
sys.path.append(r'c:\Users\Lucien\Documents\GitHub\ChroLens-Mimic\main\modules')

try:
    from text_script_editor import TextScriptEditor
    from recorder import CoreRecorder
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

# Dummy Logger
def mock_logger(msg):
    print(f"LOGGER: {msg}")

# Initialize Recorder
recorder = CoreRecorder(logger=mock_logger)

# Sample script with labels
script_content = """
#主循環
>隨機跳轉>#A, #B, #C
>延遲100ms

#A
>按A
>>#主循環

#B
>按B
>>#主循環

#C
>按C
>>#主循環
"""

# Simulate parsing
editor = TextScriptEditor()
events = editor.parse_text_to_events(script_content)
print(f"Parsed {len(events)} events.")

# Set events directly to recorder
recorder.events = events
recorder.playing = True

# We need to mock _execute_event to avoid actual keyboard actions
def mock_execute_event(event):
    if event['type'] == 'keyboard':
        print(f"EXECUTING: Press {event['name']}")
    return None

recorder._execute_event = mock_execute_event

# Mock time.sleep to speed up test
import time
original_sleep = time.sleep
def fast_sleep(s):
    pass
time.sleep = fast_sleep

# Run a few rounds
print("Starting simulation...")
for i in range(10):
    print(f"--- Round {i+1} ---")
    # Simulate _execute_single_round logic manually since it has a while loop
    # or just call it if we can
    try:
        # We need to handle the infinite loop or just run a portion
        # Let's manually step through indices to observe jumps
        idx = 0
        safety_break = 0
        while idx < len(events) and safety_break < 5:
            event = events[idx]
            result = recorder._execute_event_with_mode(event)
            
            if result and isinstance(result, tuple) and result[0] == 'jump':
                target = result[1]
                # Find label index
                found = False
                for j, e in enumerate(events):
                    if e.get('type') == 'label' and e.get('name') == target:
                        idx = j
                        found = True
                        break
                if not found:
                    print(f"Label {target} not found!")
                    break
            else:
                idx += 1
            safety_break += 1
    except Exception as ex:
        print(f"Error during simulation: {ex}")

time.sleep = original_sleep
print("Test completed.")
