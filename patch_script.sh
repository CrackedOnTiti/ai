echo "Applying fix to stone collection loop in src/ai/ai_controller.py..."

# Read the content of the file
original_content=$(cat src/ai/ai_controller.py)

# Define the section to find (part of Priority 4)
# We're looking for the 'Take stone_name' line within the stone collection logic
# print(f"💎 Collecting {stone_name} from current tile")
# self.client.send_command(f"Take {stone_name}")
# return  <-- We want to insert before this return or modify behavior around it.

# Using awk to insert 'self.last_vision_data = None' and 'self.need_vision_update = True'
# after 'self.client.send_command(f"Take {stone_name}")'
# The indentation (20 spaces) is crucial for Python.

awk '
{ print $0 }
/self.client.send_command\(f"Take \{stone_name\}"\)/ {
    # Check if the next line is the 'return' associated with this block.
    # This is a heuristic check. A more robust solution might involve counting braces or indentation levels.
    # For now, we assume the 'return' is immediately after or within a few lines if there are comments.
    # The main goal is to insert the lines within the correct 'if stone_name in current_tile:' block.
    print "                    self.last_vision_data = None"
    print "                    self.need_vision_update = True"
}
' src/ai/ai_controller.py > src/ai/ai_controller.py.tmp

if [ -s src/ai/ai_controller.py.tmp ]; then
    # Check if the temporary file actually changed anything meaningfully
    # by looking for one of the inserted lines.
    if grep -q "self.last_vision_data = None" src/ai/ai_controller.py.tmp; then
        mv src/ai/ai_controller.py.tmp src/ai/ai_controller.py
        echo "Applied fix using awk."
        fixed_content=$(cat src/ai/ai_controller.py)
    else
        echo "Error: awk script failed to apply the change meaningfully."
        rm src/ai/ai_controller.py.tmp
        # Fallback or error
        echo "Automated patching failed. The awk script did not insert the expected lines."
        # exit 1
    fi
else
    echo "Error: awk script created an empty file."
    if [ -f src/ai/ai_controller.py.tmp ]; then rm src/ai/ai_controller.py.tmp; fi
    # exit 1
fi

echo "--- Diff of changes ---"
diff -u <(echo "$original_content") <(echo "$fixed_content")
echo "--- End of Diff ---"

echo "Verifying the fix by searching for the added lines..."
if grep -q "self.last_vision_data = None" src/ai/ai_controller.py && grep -q "self.need_vision_update = True" src/ai/ai_controller.py; then
    echo "Fix confirmed in the file."
else
    echo "Error: Fix not found in the file after modification attempts."
    # Restore original content if fix failed
    echo "$original_content" > src/ai/ai_controller.py
    echo "Restored original content."
    # exit 1
fi

echo "Final check on the relevant code block after modification:"
grep -C 5 "Collecting {stone_name} from current tile" src/ai/ai_controller.py
