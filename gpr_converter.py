#!/usr/bin/env python
"""
GPR to DNG/JPEG converter for Sea-Thru pipeline
Provides lossless GPR to DNG conversion and JPEG preview extraction.
"""

import os
import glob
import argparse
import subprocess
from pathlib import Path

def check_converters():
    """Check which conversion tools are available"""
    tools = {
        'gpr_tools': 'gpr_tools',  # GoPro's official converter (best for lossless DNG)
        'dnglab': 'dnglab',  # Open source DNG converter with lossless support
        'Adobe DNG Converter': '/Applications/Adobe DNG Converter.app/Contents/MacOS/Adobe DNG Converter',
        'exiftool': 'exiftool',  # Can extract embedded JPEG preview
        'dcraw': 'dcraw',  # Can convert to PPM/TIFF
    }
    
    available = {}
    for tool_name, tool_cmd in tools.items():
        try:
            # Special handling for Adobe DNG Converter
            if tool_name == 'Adobe DNG Converter':
                if os.path.exists(tool_cmd):
                    available[tool_name] = tool_cmd
            else:
                # Check if tool exists in PATH
                result = subprocess.run(['which', tool_cmd.split()[0]], capture_output=True, text=True)
                if result.returncode == 0:
                    available[tool_name] = tool_cmd
        except:
            pass
    
    return available

def convert_gpr_to_dng_lossless(gpr_path, output_path, tool_name, tool_cmd):
    """Convert GPR to DNG using lossless conversion"""
    try:
        if tool_name == 'gpr_tools':
            # GoPro's official tool - best option for lossless GPR to DNG
            cmd = [tool_cmd, '-i', gpr_path, '-o', output_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        elif tool_name == 'dnglab':
            # Open source tool with explicit lossless support
            cmd = [tool_cmd, 'convert', '--lossless', gpr_path, output_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        elif tool_name == 'Adobe DNG Converter':
            # Adobe's official converter
            # Note: Adobe DNG Converter uses lossless compression by default
            cmd = [tool_cmd, '-c', '-p0', '-o', os.path.dirname(output_path), gpr_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
    except Exception as e:
        print(f"Conversion error with {tool_name}: {e}")
    return False

def extract_preview_with_exiftool(gpr_path, output_path):
    """Extract embedded JPEG preview using exiftool (lossy but fast)"""
    try:
        cmd = ['exiftool', '-b', '-PreviewImage', gpr_path]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0 and result.stdout:
            with open(output_path, 'wb') as f:
                f.write(result.stdout)
            return True
    except Exception as e:
        print(f"exiftool error: {e}")
    return False

def convert_with_dcraw(gpr_path, output_path):
    """Convert using dcraw to PPM/TIFF (lossless intermediate format)"""
    try:
        # dcraw -T outputs TIFF (lossless), -6 uses 16-bit
        cmd = ['dcraw', '-T', '-6', '-W', '-o', '0', gpr_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            # dcraw creates a .tiff file with same base name
            tiff_path = os.path.splitext(gpr_path)[0] + '.tiff'
            if os.path.exists(tiff_path):
                # Move to desired output path
                import shutil
                shutil.move(tiff_path, output_path)
                return True
    except Exception as e:
        print(f"dcraw error: {e}")
    return False

def convert_batch(input_dir, output_dir, output_format='dng', jpeg_preview=False):
    """Convert all GPR files in a directory
    
    Args:
        input_dir: Directory containing GPR files
        output_dir: Output directory for converted files
        output_format: 'dng' for lossless DNG, 'tiff' for lossless TIFF, 'jpeg' for preview extraction
        jpeg_preview: Also extract JPEG previews alongside DNG/TIFF conversion
    """
    
    # Create output directory if needed
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Find all GPR files
    gpr_files = glob.glob(os.path.join(input_dir, '*.GPR'))
    gpr_files.extend(glob.glob(os.path.join(input_dir, '*.gpr')))
    
    if not gpr_files:
        print(f"No GPR files found in {input_dir}")
        return
    
    print(f"Found {len(gpr_files)} GPR files to convert to {output_format.upper()}")
    
    # Check available tools
    tools = check_converters()
    if not tools:
        print("\nNo conversion tools found. For lossless GPR to DNG conversion, install:")
        print("  1. gpr_tools (best): Download from https://github.com/gopro/gpr/releases")
        print("  2. dnglab: cargo install dnglab")
        print("  3. Adobe DNG Converter: Download from Adobe website")
        print("\nFor preview extraction only:")
        print("  - exiftool: brew install exiftool")
        print("  - dcraw: brew install dcraw")
        return
    
    print(f"Available converters: {', '.join(tools.keys())}\n")
    
    # Prioritize tools for lossless DNG conversion
    lossless_tools = ['gpr_tools', 'dnglab', 'Adobe DNG Converter']
    selected_tool = None
    for tool in lossless_tools:
        if tool in tools:
            selected_tool = tool
            print(f"Using {tool} for lossless conversion")
            break
    
    converted = 0
    for i, gpr_path in enumerate(gpr_files, 1):
        basename = os.path.splitext(os.path.basename(gpr_path))[0]
        
        print(f"[{i}/{len(gpr_files)}] {os.path.basename(gpr_path)}...", end=' ')
        
        success = False
        
        if output_format == 'dng' and selected_tool:
            # Lossless DNG conversion
            output_path = os.path.join(output_dir, f"{basename}.dng")
            success = convert_gpr_to_dng_lossless(gpr_path, output_path, 
                                                 selected_tool, tools[selected_tool])
            
        elif output_format == 'tiff' and 'dcraw' in tools:
            # Lossless TIFF conversion
            output_path = os.path.join(output_dir, f"{basename}.tiff")
            success = convert_with_dcraw(gpr_path, output_path)
            
        elif output_format == 'jpeg' and 'exiftool' in tools:
            # JPEG preview extraction
            output_path = os.path.join(output_dir, f"{basename}.jpg")
            success = extract_preview_with_exiftool(gpr_path, output_path)
        
        # Optionally extract JPEG preview alongside DNG/TIFF
        if success and jpeg_preview and output_format != 'jpeg' and 'exiftool' in tools:
            preview_path = os.path.join(output_dir, f"{basename}_preview.jpg")
            extract_preview_with_exiftool(gpr_path, preview_path)
        
        if success:
            print("[OK]")
            converted += 1
        else:
            print("[FAILED]")
    
    print(f"\nConverted {converted}/{len(gpr_files)} files")
    print(f"Output saved to: {output_dir}")
    
    if output_format == 'dng' and converted > 0:
        print("\nThe DNG files are now compatible with rawpy and can be processed with:")
        print(f"  python seathru-mono-e2e.py --input-dir {output_dir} --output-dir <final_output> --raw")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Lossless GPR to DNG/TIFF converter for Sea-Thru processing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Lossless GPR to DNG conversion (recommended)
  python gpr_converter.py --input-dir ./gpr_files --output-dir ./dng_files --format dng
  
  # Lossless GPR to TIFF conversion
  python gpr_converter.py --input-dir ./gpr_files --output-dir ./tiff_files --format tiff
  
  # Extract JPEG previews only (fast but lossy)
  python gpr_converter.py --input-dir ./gpr_files --output-dir ./jpeg_files --format jpeg
  
  # Convert to DNG with JPEG previews
  python gpr_converter.py --input-dir ./gpr_files --output-dir ./output --format dng --preview

Required tools:
  For lossless DNG: gpr_tools, dnglab, or Adobe DNG Converter
  For TIFF: dcraw
  For JPEG preview: exiftool
        """)
    
    parser.add_argument('--input-dir', required=True, 
                        help='Directory containing GPR files')
    parser.add_argument('--output-dir', required=True, 
                        help='Output directory for converted files')
    parser.add_argument('--format', default='dng', 
                        choices=['dng', 'tiff', 'jpeg'],
                        help='Output format: dng (lossless), tiff (lossless), jpeg (preview only)')
    parser.add_argument('--preview', action='store_true',
                        help='Also extract JPEG previews alongside DNG/TIFF conversion')
    
    args = parser.parse_args()
    
    convert_batch(args.input_dir, args.output_dir, args.format, args.preview)