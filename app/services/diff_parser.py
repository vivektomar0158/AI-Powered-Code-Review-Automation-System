import re
from typing import List, Dict, Any

class DiffParser:
    """Parses raw git diffs to structure them for LLMs and ignore noise."""
    
    IGNORE_EXTENSIONS = {
        '.min.js', '.min.css', '.map', '.lock', 
        '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg',
        '.pyc', '.pyo', '.pyd'
    }
    
    IGNORE_FILES = {
        'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'poetry.lock',
        '.gitignore', '.dockerignore'
    }
    
    def parse(self, raw_diff: str) -> List[Dict[str, Any]]:
        """Parse raw diff into structured files with hunks."""
        files = []
        current_file = None
        
        lines = raw_diff.split('\n')
        
        for line in lines:
            if line.startswith('diff --git'):
                if current_file and self._should_process(current_file['new_path']):
                    files.append(current_file)
                    
                # Extract filename
                parts = line.split(' ')
                old_path = parts[2][2:] if len(parts) > 2 else ""
                new_path = parts[3][2:] if len(parts) > 3 else ""
                
                current_file = {
                    'old_path': old_path,
                    'new_path': new_path,
                    'hunks': [],
                    'is_binary': False
                }
                
            elif current_file:
                if line.startswith('Binary files'):
                    current_file['is_binary'] = True
                elif line.startswith('@@'):
                    # Start of a new hunk
                    current_file['hunks'].append([line])
                elif current_file['hunks']:
                    # Append to current hunk
                    current_file['hunks'][-1].append(line)
                    
        # Append the last file
        if current_file and self._should_process(current_file['new_path']):
            files.append(current_file)
            
        return files
        
    def _should_process(self, filepath: str) -> bool:
        if not filepath:
            return False
            
        # Ignore by exact name
        filename = filepath.split('/')[-1]
        if filename in self.IGNORE_FILES:
            return False
            
        # Ignore by extension
        for ext in self.IGNORE_EXTENSIONS:
            if filepath.endswith(ext):
                return False
                
        # Ignore generated paths
        if 'node_modules/' in filepath or 'dist/' in filepath or 'build/' in filepath:
            return False
            
        return True
        
    def format_for_llm(self, parsed_files: List[Dict[str, Any]]) -> str:
        """Format the parsed diff back into a cleaner string for the LLM."""
        output = []
        for file in parsed_files:
            if file['is_binary']:
                continue
                
            output.append(f"File: {file['new_path']}")
            for hunk in file['hunks']:
                output.append('\n'.join(hunk))
            output.append("\n" + "="*50 + "\n")
            
        return "\n".join(output)
