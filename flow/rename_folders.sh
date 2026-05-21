#!/bin/sh

# Loop through all directories matching the pattern
for dir in */asap7/cva6/baseline*; do
    # Check if the directory actually exists to avoid errors if no match is found
    if [ -d "$dir" ]; then
        # Generate the new name by substituting 'baseline' with 'modified'
        new_dir=$(echo "$dir" | sed 's/baseline/modified/')
        
        # Rename the directory
        mv "$dir" "$new_dir"
        echo "Renamed: $dir -> $new_dir"
    fi
done
