#!/usr/bin/env python3
"""
Release script for Star Trail Generator.
This script updates version information and creates a new release tag.
"""

import os
import re
import sys
import subprocess
import argparse
from datetime import datetime

def get_current_version():
    """Extract current version from the source code"""
    with open('star_trail_app.py', 'r') as f:
        content = f.read()
        match = re.search(r"self\.root\.title\(\"Star Trail Generator v([^\"]+)\"\)", content)
        if match:
            return match.group(1)
    return "1.0.0"  # Default if not found


def update_version_in_file(file_path, new_version):
    """Update version string in the given file"""
    with open(file_path, 'r') as f:
        content = f.read()

    # Update version in window title
    content = re.sub(
        r"(self\.root\.title\(\"Star Trail Generator)( v[^\"]+)?(\"\))",
        f"\\1 v{new_version}\\3",
        content
    )

    with open(file_path, 'w') as f:
        f.write(content)


def update_changelog(version, message):
    """Update the CHANGELOG.md file with new release info"""
    today = datetime.now().strftime('%Y-%m-%d')
    new_entry = f"## [v{version}] - {today}\n\n{message}\n\n"
    
    if os.path.exists('CHANGELOG.md'):
        with open('CHANGELOG.md', 'r') as f:
            content = f.read()
        
        # Check if the file has the expected format
        if '# Changelog' in content:
            # Insert after the header
            parts = content.split('# Changelog', 1)
            content = parts[0] + '# Changelog' + '\n\n' + new_entry + parts[1].lstrip()
        else:
            # Prepend to the file
            content = new_entry + content
    else:
        # Create new changelog
        content = f"# Changelog\n\n{new_entry}"
    
    with open('CHANGELOG.md', 'w') as f:
        f.write(content)


def run_command(command):
    """Run a shell command and return output"""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error executing: {command}")
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description='Create a new release of Star Trail Generator')
    parser.add_argument('--major', action='store_true', help='Bump major version')
    parser.add_argument('--minor', action='store_true', help='Bump minor version')
    parser.add_argument('--patch', action='store_true', help='Bump patch version')
    parser.add_argument('--version', type=str, help='Specific version to set')
    parser.add_argument('--message', '-m', type=str, help='Release message')
    
    args = parser.parse_args()
    
    # Get current version
    current_version = get_current_version()
    print(f"Current version: {current_version}")
    
    # Determine new version
    if args.version:
        new_version = args.version
    else:
        # Parse current version
        try:
            major, minor, patch = map(int, current_version.split('.'))
        except ValueError:
            print(f"Error: Current version '{current_version}' doesn't follow semantic versioning")
            sys.exit(1)
        
        # Bump version according to arguments
        if args.major:
            new_version = f"{major + 1}.0.0"
        elif args.minor:
            new_version = f"{major}.{minor + 1}.0"
        elif args.patch:
            new_version = f"{major}.{minor}.{patch + 1}"
        else:
            # Default to patch bump
            new_version = f"{major}.{minor}.{patch + 1}"
    
    print(f"New version: {new_version}")
    
    # Get release message
    release_message = args.message if args.message else input("Enter release notes (or press Enter to skip): ")
    
    # Update version in source code
    update_version_in_file('star_trail_app.py', new_version)
    print(f"Updated version in star_trail_app.py")
    
    # Update changelog
    update_changelog(new_version, release_message)
    print(f"Updated CHANGELOG.md")
    
    # Commit changes
    run_command(f'git add star_trail_app.py CHANGELOG.md')
    run_command(f'git commit -m "Bump version to {new_version}"')
    print(f"Committed version changes")
    
    # Create and push tag
    tag_name = f"v{new_version}"
    run_command(f'git tag {tag_name}')
    print(f"Created tag {tag_name}")
    
    # Remind user to push
    print("\nRelease preparation complete!")
    print(f"To finalize the release, push the changes and tag:")
    print(f"  git push origin main")
    print(f"  git push origin {tag_name}")
    print("\nThis will trigger the GitHub Actions workflow to build and publish the release.")


if __name__ == "__main__":
    main()

