from __future__ import absolute_import, division, print_function

import os
import sys
import glob
import argparse
import time
import io

import numpy as np
import PIL.Image as pil
from PIL import Image
import matplotlib as mpl
import matplotlib.cm as cm
import pynng
from pynng import nng
import rawpy

import torch
from torchvision import transforms, datasets

import deps.monodepth2.networks as networks
from deps.monodepth2.layers import disp_to_depth
from deps.monodepth2.utils import download_model_if_doesnt_exist

from seathru import *


def load_image(image_path, args):
    """Load image with support for various formats including GPR"""
    file_ext = os.path.splitext(image_path)[1].lower()
    
    # Check if it's a RAW file (including GPR, DNG, RAW)
    if args.raw or file_ext in ['.raw', '.dng', '.gpr']:
        return Image.fromarray(rawpy.imread(image_path).postprocess())
    else:
        return pil.open(image_path).convert('RGB')

def process_single_image(image_path, output_path, encoder, depth_decoder, device, feed_width, feed_height, args):
    """Process a single image"""
    print(f"\nProcessing: {image_path}")
    
    # Load image and preprocess
    img = load_image(image_path, args)
    original_width, original_height = img.size
    
    # Only resize if image is larger than max_size (if specified)
    if args.max_size and max(original_width, original_height) > args.max_size:
        img.thumbnail((args.max_size, args.max_size), Image.ANTIALIAS)
        resized_width, resized_height = img.size
    else:
        resized_width, resized_height = original_width, original_height
    # img = exposure.equalize_adapthist(np.array(img), clip_limit=0.03)
    # img = Image.fromarray((np.round(img * 255.0)).astype(np.uint8))
    input_image = img.resize((feed_width, feed_height), pil.LANCZOS)
    input_image = transforms.ToTensor()(input_image).unsqueeze(0)
    print('Preprocessed image', flush=True)

    # PREDICTION
    input_image = input_image.to(device)
    features = encoder(input_image)
    outputs = depth_decoder(features)

    disp = outputs[("disp", 0)]
    disp_resized = torch.nn.functional.interpolate(
        disp, (resized_height, resized_width), mode="bilinear", align_corners=False)

    # Saving colormapped depth image
    disp_resized_np = disp_resized.squeeze().cpu().detach().numpy()
    mapped_im_depths = ((disp_resized_np - np.min(disp_resized_np)) / (
            np.max(disp_resized_np) - np.min(disp_resized_np))).astype(np.float32)
    print("Processed image", flush=True)
    print('Loading image...', flush=True)
    depths = preprocess_monodepth_depth_map(mapped_im_depths, args.monodepth_add_depth,
                                            args.monodepth_multiply_depth)
    recovered = run_pipeline(np.array(img) / 255.0, depths, args)
    # recovered = exposure.equalize_adapthist(scale(np.array(recovered)), clip_limit=0.03)
    sigma_est = estimate_sigma(recovered, multichannel=True, average_sigmas=True) / 10.0
    recovered = denoise_tv_chambolle(recovered, sigma_est, multichannel=True)
    im = Image.fromarray((np.round(recovered * 255.0)).astype(np.uint8))
    im.save(output_path, format='png')
    print(f'Saved: {output_path}')


def run(args):
    """Function to predict for a single image or folder of images
    """
    assert args.model_name is not None, \
        "You must specify the --model_name parameter; see README.md for an example"

    if torch.cuda.is_available() and not args.no_cuda:
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")

    download_model_if_doesnt_exist(args.model_name)
    model_path = os.path.join("models", args.model_name)
    print("-> Loading model from ", model_path)
    encoder_path = os.path.join(model_path, "encoder.pth")
    depth_decoder_path = os.path.join(model_path, "depth.pth")

    # LOADING PRETRAINED MODEL
    print("   Loading pretrained encoder")
    encoder = networks.ResnetEncoder(18, False)
    loaded_dict_enc = torch.load(encoder_path, map_location=device)

    # extract the height and width of image that this model was trained with
    feed_height = loaded_dict_enc['height']
    feed_width = loaded_dict_enc['width']
    filtered_dict_enc = {k: v for k, v in loaded_dict_enc.items() if k in encoder.state_dict()}
    encoder.load_state_dict(filtered_dict_enc)
    encoder.to(device)
    encoder.eval()

    print("   Loading pretrained decoder")
    depth_decoder = networks.DepthDecoder(
        num_ch_enc=encoder.num_ch_enc, scales=range(4))

    loaded_dict = torch.load(depth_decoder_path, map_location=device)
    depth_decoder.load_state_dict(loaded_dict)

    depth_decoder.to(device)
    depth_decoder.eval()

    # Check if input is directory or single image
    if args.input_dir:
        # Process directory
        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)
            print(f"Created output directory: {args.output_dir}")
        
        # Get all image files
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
        if args.raw:
            image_extensions.extend(['*.raw', '*.RAW', '*.dng', '*.DNG', '*.gpr', '*.GPR'])
        
        image_files = []
        for ext in image_extensions:
            image_files.extend(glob.glob(os.path.join(args.input_dir, ext)))
        
        if not image_files:
            print(f"No images found in {args.input_dir}")
            return
        
        print(f"Found {len(image_files)} images to process")
        
        # Process each image
        for idx, image_path in enumerate(image_files, 1):
            print(f"\n[{idx}/{len(image_files)}] Processing...")
            
            # Generate output filename
            base_name = os.path.basename(image_path)
            name_without_ext = os.path.splitext(base_name)[0]
            output_path = os.path.join(args.output_dir, f"{name_without_ext}_seathru.png")
            
            try:
                process_single_image(image_path, output_path, encoder, depth_decoder, 
                                   device, feed_width, feed_height, args)
            except Exception as e:
                print(f"Error processing {image_path}: {e}")
                continue
        
        print(f"\n✓ Batch processing complete! Processed {len(image_files)} images")
        print(f"Output saved to: {args.output_dir}")
    
    elif args.image:
        # Process single image
        process_single_image(args.image, args.output, encoder, depth_decoder, 
                           device, feed_width, feed_height, args)
        print('Done.')
    else:
        print("Error: Must specify either --image or --input-dir")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', help='Input image (for single image processing)')
    parser.add_argument('--output', default='output.png', help='Output filename (for single image processing)')
    parser.add_argument('--input-dir', help='Input directory (for batch processing)')
    parser.add_argument('--output-dir', default='output', help='Output directory (for batch processing)')
    parser.add_argument('--f', type=float, default=2.0, help='f value (controls brightness)')
    parser.add_argument('--l', type=float, default=0.5, help='l value (controls balance of attenuation constants)')
    parser.add_argument('--p', type=float, default=0.01, help='p value (controls locality of illuminant map)')
    parser.add_argument('--min-depth', type=float, default=0.0,
                        help='Minimum depth value to use in estimations (range 0-1)')
    parser.add_argument('--max-depth', type=float, default=1.0,
                        help='Replacement depth percentile value for invalid depths (range 0-1)')
    parser.add_argument('--spread-data-fraction', type=float, default=0.05,
                        help='Require data to be this fraction of depth range away from each other in attenuation estimations')
    parser.add_argument('--max-size', type=int, default=None, help='Maximum size for processing (default: no resizing)')
    parser.add_argument('--monodepth-add-depth', type=float, default=2.0, help='Additive value for monodepth map')
    parser.add_argument('--monodepth-multiply-depth', type=float, default=10.0,
                        help='Multiplicative value for monodepth map')
    parser.add_argument('--model-name', type=str, default="mono_1024x320",
                        help='monodepth model name')
    parser.add_argument('--output-graphs', action='store_true', help='Output graphs')
    parser.add_argument('--raw', action='store_true', help='Process RAW images (including DNG, RAW, and GPR formats)')
    parser.add_argument('--no-cuda', action='store_true', help='Force CPU processing')
    args = parser.parse_args()
    
    # Validate arguments
    if not args.image and not args.input_dir:
        parser.error('Must specify either --image for single image or --input-dir for batch processing')
    run(args)
