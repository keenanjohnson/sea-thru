#!/usr/bin/env python
"""
GPR to DNG converter for Sea-Thru pipeline
Provides lossless GPR to DNG conversion using gpr_tools.
"""

import os
import glob
import argparse
import subprocess
from pathlib import Path

def check_gpr_tools():
    """Check if gpr_tools is available"""
    try:
        # Try running gpr_tools directly with help flag (Python 3.6 compatible)
        # Note: gpr_tools returns exit code 1 for -h/--help, but writes to stdout
        result = subprocess.run(['gpr_tools', '-h'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE, 
                              timeout=2)
        # gpr_tools exists if we can run it (even if it returns non-zero for help)
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        # If we get FileNotFoundError, gpr_tools is not in PATH
        pass
    
    # Fallback: check common locations
    common_paths = ['/usr/local/bin/gpr_tools', '/usr/bin/gpr_tools']
    for path in common_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return True
    
    return False

def convert_gpr_to_dng(gpr_path, output_path):
    """Convert GPR to DNG using gpr_tools (lossless conversion)"""
    try:
        # GoPro's official tool for lossless GPR to DNG conversion
        cmd = ['gpr_tools', '-i', gpr_path, '-o', output_path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0 and result.stderr:
            print(f"  Error: {result.stderr.decode('utf-8').strip()}")
        return result.returncode == 0
    except Exception as e:
        print(f"  Conversion error: {e}")
        return False

def convert_batch(input_dir, output_dir):
    """Convert all GPR files in a directory to DNG format
    
    Args:
        input_dir: Directory containing GPR files
        output_dir: Output directory for DNG files
    """
    
    # Create output directory if needed
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Find all GPR files
    gpr_files = glob.glob(os.path.join(input_dir, '*.GPR'))
    gpr_files.extend(glob.glob(os.path.join(input_dir, '*.gpr')))
    
    if not gpr_files:
        print(f"No GPR files found in {input_dir}")
        return
    
    print(f"Found {len(gpr_files)} GPR files to convert to DNG")
    
    # Check if gpr_tools is available
    if not check_gpr_tools():
        print("\nError: gpr_tools not found!")
        print("To install gpr_tools:")
        print("  1. In Docker: It should be pre-installed")
        print("  2. On Linux/Mac: Run ./install_gpr_tools.sh")
        print("  3. Manual: Build from https://github.com/gopro/gpr")
        return
    
    print("Using gpr_tools for lossless GPR to DNG conversion\n")
    
    converted = 0
    for i, gpr_path in enumerate(gpr_files, 1):
        basename = os.path.splitext(os.path.basename(gpr_path))[0]
        output_path = os.path.join(output_dir, f"{basename}.dng")
        
        print(f"[{i}/{len(gpr_files)}] {os.path.basename(gpr_path)}...", end=' ')
        
        if convert_gpr_to_dng(gpr_path, output_path):
            print("[OK]")
            converted += 1
        else:
            print("[FAILED]")
    
    print(f"\nConverted {converted}/{len(gpr_files)} files")
    print(f"Output saved to: {output_dir}")
    
    if converted > 0:
        print("\nThe DNG files are now compatible with rawpy and can be processed with:")
        print(f"  python seathru-mono-e2e.py --input-dir {output_dir} --output-dir <final_output> --raw")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Lossless GPR to DNG converter for Sea-Thru processing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python gpr_converter.py --input-dir ./test_images/input_GPR --output-dir ./test_images/input_DNG
  
This tool uses gpr_tools for lossless GPR to DNG conversion.
The DNG files can then be processed with seathru-mono-e2e.py using the --raw flag.
        """)
    
    parser.add_argument('--input-dir', required=True, 
                        help='Directory containing GPR files')
    parser.add_argument('--output-dir', required=True, 
                        help='Output directory for DNG files')
    
    args = parser.parse_args()
    
    convert_batch(args.input_dir, args.output_dir)
