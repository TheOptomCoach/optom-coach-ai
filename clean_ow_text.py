import os
import re

# Configuration
target_dir = r"c:\Users\Ibrar\Desktop\New Loc Scraper\OW members area scrape\text"

def clean_files():
    if not os.path.exists(target_dir):
        print(f"Directory not found: {target_dir}")
        return

    files = [f for f in os.listdir(target_dir) if f.endswith(".md")]
    print(f"Found {len(files)} markdown files.")
    
    count_header = 0
    count_footer = 0
    
    # regex for the footer
    # It starts with QUICK LINKS and ends with I Understand
    footer_pattern = re.compile(r"QUICK LINKS\n.*I Understand", re.DOTALL)

    # Secondary footer pattern (FOLLOW US ... [email])
    # Matches "FOLLOW US" ... down to an email address line.
    # We use a pattern that captures from FOLLOW US until the specific email or end of file
    footer_2_pattern = re.compile(r"FOLLOW US\nREGISTERED OFFICE\n.*?(?:@optometrywales\.com|@optometrywales\.org\.uk).*?(\n|$)", re.DOTALL | re.IGNORECASE)

    
    # regex for the header
    # It seems to be: [Title Line]\nSelect Language\nEnglish\nCymraeg\nFOLLOW US\nSearch for:\nSearch Button\nHome
    # We will match "Select Language...Home" and also try to capture the preceding line
    header_core = r"Select Language\nEnglish\nCymraeg\nFOLLOW US\nSearch for:\nSearch Button\nHome"
    
    for filename in files:
        filepath = os.path.join(target_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        original_content = content
        
        # Remove Footer
        if footer_pattern.search(content):
            content = footer_pattern.sub("", content)
            count_footer += 1
            
        # Remove Secondary Footer
        if footer_2_pattern.search(content):
            content = footer_2_pattern.sub("", content)
            # We count this as a footer removal too, or we could have a separate counter
            # For simplicity, increment the same one if not already incremented? 
            # Actually let's just let it be.
            count_footer += 1
            
        # Remove Header
        # First, try to find the core header
        match = re.search(header_core, content, re.MULTILINE)
        if match:
            # Found the core. Now finding start/end indices
            start_index = match.start()
            end_index = match.end()
            
            # Check the line before the start_index
            # We want to remove the line preceding 'Select Language' if it exists
            # We look backwards from start_index for a newline
            
            # content[0:start_index] is everything before headers
            pre_header = content[0:start_index]
            
            # Find the last newline in pre_header
            last_newline = pre_header.rfind('\n')
            
            if last_newline != -1:
                # The "Title Line" is between last_newline and start_index
                # We want to remove from last_newline (inclusive of \n) to end_index
                
                # However, we should be careful. Is the line before really a title?
                # Usually yes in this scrape format.
                
                # Let's remove from last_newline + 1 to end_index
                # Wait, we want to remove the newline too if we want the line gone?
                # Actually, correct removal:
                # content = content[:last_newline+1] + content[end_index:]
                # But 'Select Language' is at the start of a line.
                
                # Let's verify if the preceding line is the title line we want to remove.
                # The user example: "Optometry Wales Executive Board - Optometry Wales"
                
                # Let's just remove the block from last_newline to end_index + verify if we need to clean up extra newlines.
                
                # If last_newline is -1, it means the file starts with the title line (no newline before it)
                # But these files usually start with YAML or Metadata block?
                # Step 18 shows:
                # 1: # Optometry Wales Executive Board - Optometry Wales
                # ...
                # 7: Optometry Wales Executive Board - Optometry Wales
                # 8: Select Language
                
                # So we want to remove from the start of line 7.
                
                content = content[:last_newline+1] + content[end_index:]
                count_header += 1
            else:
                # No newline before? Maybe it's at the very start of the file? (unlikely given the metadata)
                # Just remove the core
                content = content[:start_index] + content[end_index:]
                count_header += 1
                
        # Write back if changed
        if content != original_content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

    print(f"Processed {len(files)} files.")
    print(f"Removed Footer from {count_footer} files.")
    print(f"Removed Header from {count_header} files.")

if __name__ == "__main__":
    clean_files()
