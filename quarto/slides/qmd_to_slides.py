#!/usr/bin/env python3
"""
Convert QMD files to Jupyter notebooks with slide metadata.
- Replaces {pyodide} cells with {python}
- Removes ::: div blocks
- Tags cells with ## headers as Slide cells
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def preprocess_qmd(qmd_content: str) -> str:
    """Preprocess QMD content before conversion."""
    # Replace {pyodide} with {python}
    content = re.sub(r'\{pyodide\}', '{python}', qmd_content)
    
    return content


def convert_qmd_to_ipynb(qmd_path: Path) -> Path:
    """Use Quarto to convert QMD to IPYNB format."""
    output_path = qmd_path.with_suffix('.ipynb')
    
    try:
        # Use quarto convert for proper QMD handling
        subprocess.run(
            ['quarto', 'convert', str(qmd_path)],
            check=True,
            capture_output=True,
            text=True
        )
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error converting with Quarto: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'quarto' command not found. Please install Quarto.", file=sys.stderr)
        sys.exit(1)


def clean_notebook(ipynb_path: Path, title=None) -> None:
    """Clean up the notebook by removing YAML frontmatter and ::: directives."""
    with open(ipynb_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)

    cleaned_cells = []
    # Insert title slide if found
    if title:
        cleaned_cells.append({
            'cell_type': 'markdown',
            'metadata': {'slideshow': {'slide_type': 'slide'}},
            'source': [f'# {title}\n']
        })

    for cell in notebook.get('cells', []):
        # Get cell source
        source = cell.get('source', [])
        
        # Convert to list if string
        if isinstance(source, str):
            source = source.split('\n')
            cell['source'] = source
        
        # Skip empty cells
        if not source or all(not line.strip() for line in source):
            continue
        
        # For markdown cells, check if it's YAML frontmatter or has ::: directives
        if cell.get('cell_type') == 'markdown':
            # Skip cells that are pure YAML frontmatter (starts with ---)
            first_content = ''.join(source).strip()
            if first_content.startswith('---') and 'title:' in first_content:
                continue
            
            # Remove only lines that are pure ::: or :::: markers, keep all other lines including column attributes
            cleaned_source = []
            for line in source:
                # Remove lines that are only ::: or :::: (no attributes)
                if re.match(r'^:::+\s*$', line.rstrip()):
                    continue
                # Keep lines with attributes (e.g., ::: {.column width="50%"})
                # Skip horizontal rules (---) that are standalone
                if line.strip() == '---':
                    continue
                cleaned_source.append(line)
            
            # Only keep if there's meaningful content left
            if cleaned_source and any(line.strip() for line in cleaned_source):
                cell['source'] = cleaned_source
                cleaned_cells.append(cell)
        else:
            # Keep all code cells
            cleaned_cells.append(cell)
    
    notebook['cells'] = cleaned_cells
    
    # Write back
    with open(ipynb_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
        f.write('\n')


def split_and_tag_slides(ipynb_path: Path) -> None:
    """Split markdown cells at ## headers and tag them as slides."""
    with open(ipynb_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    
    new_cells = []
    
    for cell in notebook.get('cells', []):
        if cell.get('cell_type') == 'markdown':
            source = cell.get('source', [])
            if isinstance(source, str):
                source = source.split('\n')
            # Split at ## headers, always preserve all lines
            current_chunk = []
            for line in source:
                if line.strip().startswith('## '):
                    # Save previous chunk if it exists
                    if current_chunk:
                        new_cell = {
                            'cell_type': 'markdown',
                            'metadata': cell.get('metadata', {}).copy(),
                            'source': current_chunk
                        }
                        # Tag as slide if starts with ##
                        if current_chunk[0].strip().startswith('## '):
                            if 'slideshow' not in new_cell['metadata']:
                                new_cell['metadata']['slideshow'] = {}
                            new_cell['metadata']['slideshow']['slide_type'] = 'slide'
                        new_cells.append(new_cell)
                    current_chunk = [line]
                else:
                    current_chunk.append(line)
            # Save final chunk
            if current_chunk:
                new_cell = {
                    'cell_type': 'markdown',
                    'metadata': cell.get('metadata', {}).copy(),
                    'source': current_chunk
                }
                if current_chunk[0].strip().startswith('## '):
                    if 'slideshow' not in new_cell['metadata']:
                        new_cell['metadata']['slideshow'] = {}
                    new_cell['metadata']['slideshow']['slide_type'] = 'slide'
                new_cells.append(new_cell)
        else:
            new_cells.append(cell)
    
    notebook['cells'] = new_cells
    
    # Write back to file
    with open(ipynb_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
        f.write('\n')


def main():
    parser = argparse.ArgumentParser(
        description='Convert QMD to IPYNB with slide metadata'
    )
    parser.add_argument(
        'input_qmd',
        type=Path,
        help='Input QMD file path'
    )
    parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Output IPYNB file path (default: same name as input with .ipynb extension)'
    )
    
    args = parser.parse_args()
    
    # Validate input file
    if not args.input_qmd.exists():
        print(f"Error: Input file '{args.input_qmd}' not found.", file=sys.stderr)
        sys.exit(1)
    
    if args.input_qmd.suffix != '.qmd':
        print("Warning: Input file does not have .qmd extension", file=sys.stderr)
    
    # Read and process QMD content
    print(f"Reading {args.input_qmd}...")
    with open(args.input_qmd, 'r', encoding='utf-8') as f:
        qmd_content = f.read()
    # Extract title from YAML frontmatter
    title = None
    yaml_match = re.search(r'^---(.*?)---', qmd_content, re.DOTALL | re.MULTILINE)
    if yaml_match:
        yaml_block = yaml_match.group(1)
        title_match = re.search(r'title:\s*([^\n]+)', yaml_block)
        if title_match:
            title = title_match.group(1).strip('`\"')
    print("THE TITLE IS:", title)
    
    # Preprocess: replace pyodide cells
    print("Preprocessing QMD (replacing {pyodide} with {python})...")
    modified_content = preprocess_qmd(qmd_content)
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.qmd', delete=False, encoding='utf-8') as f:
        f.write(modified_content)
        temp_qmd = Path(f.name)
    
    try:
        # Convert to IPYNB using Quarto
        print("Converting to IPYNB with Quarto...")
        ipynb_path = convert_qmd_to_ipynb(temp_qmd)
        
        # Clean the notebook
        print("Cleaning notebook (removing YAML frontmatter and ::: directives)...")
        clean_notebook(ipynb_path, title)
        
        # Split at ## headers and tag as slides
        print("Splitting at ## headers and tagging as slides...")
        split_and_tag_slides(ipynb_path)
        
        # Move to output path if specified
        final_path = ipynb_path
        if args.output:
            ipynb_path.rename(args.output)
            final_path = args.output
        
        print(f"✓ Successfully created {final_path}")
        
    finally:
        # Clean up temp file
        temp_qmd.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
