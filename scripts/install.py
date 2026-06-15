import os
import sys
import shutil
import platform
from pathlib import Path

PLUGIN_NAME = "JinaReader"
FILES_TO_INSTALL = [
    "jina_reader.py",
    "JinaReader.sublime-settings",
    "Default.sublime-commands",
    "Default.sublime-keymap",
    "Main.sublime-menu",
    "README.md"
]

def get_sublime_packages_dirs() -> list[Path]:
    """
    Determines the paths to the Sublime Text Packages directory
    based on the current operating system.
    """
    system = platform.system()
    home = Path.home()
    
    paths_to_check = []
    
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            paths_to_check = [
                Path(appdata) / "Sublime Text" / "Packages",
                Path(appdata) / "Sublime Text 3" / "Packages"
            ]
    elif system == "Darwin": # macOS
        paths_to_check = [
            home / "Library" / "Application Support" / "Sublime Text" / "Packages",
            home / "Library" / "Application Support" / "Sublime Text 3" / "Packages"
        ]
    elif system == "Linux":
        paths_to_check = [
            home / ".config" / "sublime-text" / "Packages",
            home / ".config" / "sublime-text-3" / "Packages"
        ]
    else:
        print(f"Unsupported operating system: {system}")
        sys.exit(1)
        
    # Find all paths that actually exist
    valid_paths = [p for p in paths_to_check if p.exists() and p.is_dir()]
            
    # If not found, default to the Sublime Text (v4) path
    if not valid_paths and paths_to_check:
        valid_paths.append(paths_to_check[0])
    
    return valid_paths

def main():
    print(f"Installing {PLUGIN_NAME} for Sublime Text...")
    
    # Get project root (assuming script is in scripts/)
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent
    
    packages_dirs = get_sublime_packages_dirs()
    if not packages_dirs:
        print("Could not determine Sublime Text packages directory.")
        sys.exit(1)
        
    installed_any = False
    
    for packages_dir in packages_dirs:
        target_dir = packages_dir / PLUGIN_NAME
        print(f"\nTarget directory: {target_dir}")
        
        try:
            # Create target dir if it doesn't exist
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy plugin files
            for filename in FILES_TO_INSTALL:
                src_file = project_root / filename
                if not src_file.exists():
                    print(f"Warning: Source file '{filename}' not found in {project_root}. Skipping.")
                    continue
                    
                dest_file = target_dir / filename
                shutil.copy2(src_file, dest_file)
                print(f"  Copied: {filename}")
                
            installed_any = True
            
        except PermissionError:
            print(f"  Error: Permission denied when trying to write to {target_dir}.")
            print("  Please ensure you have the necessary permissions or run the script as administrator.")
        except Exception as e:
            print(f"  Error during installation to {target_dir}: {e}")

    if installed_any:
        print(f"\nSuccessfully installed {PLUGIN_NAME}!")
        print("Note: You may need to restart Sublime Text if this is a first-time installation.")
    else:
        print(f"\nFailed to install {PLUGIN_NAME} to any directory.")
        sys.exit(1)

if __name__ == "__main__":
    main()
