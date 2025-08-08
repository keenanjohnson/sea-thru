# Sea-Thru
Implementation of Sea-thru by Derya Akkaynak and Tali Treibitz

__Forked from https://github.com/hainh/sea-thru__

This fork's only aim is to standardize the dependencies and environment with [Docker](https://docs.docker.com/get-docker/) and [Anaconda](https://www.anaconda.com/) to make it so that anyone can use it without deep technical knowledge of python.

Additionally, in order to make this an all-in-one package, the [Monodepth2 submodule](https://github.com/nianticlabs/monodepth2/tree/b676244e5a1ca55564eb5d16ab521a48f823af31) has been cloned and commited directly into this repo, preserving the commit history and original authors.

## Prerequisites

[Docker](https://docs.docker.com/get-docker/)

## Setup

1. Run `docker compose up --build`
    - This can take around 2 hours the first time; from then onwards you only need to run `docker compose up` to get the container running and it'll boot up instantly.
2. Once the container is built and running, in a separate terminal run `docker exec -it seathru /bin/bash`
    - Replace `seathru` in that command if you've modified the `SERVICE` enviornment variable in `.env`
3. From within the container you can now run the image processing commands (see Usage section below)
    - This root directory is mounted into the container each time you bring it up via `docker compose up`, meaning any files you add on your host machine to this directory will _also_ be available within the container.

## Usage

### Single Image Processing
Process a single underwater image:
```bash
python seathru-mono-e2e.py --image ${PATH_TO_IMAGE}
```

With custom output filename:
```bash
python seathru-mono-e2e.py --image input.jpg --output enhanced.png
```

Process a GoPro GPR file:
```bash
python seathru-mono-e2e.py --image input.GPR --raw --output enhanced.png
```

### Batch Directory Processing
Process all images in a directory:
```bash
python seathru-mono-e2e.py --input-dir ./test_images/input_JPEG --output-dir ./test_images/output_JPEG
```

Process GPR files:
```bash
python seathru-mono-e2e.py --input-dir ./test_images/input_GPR --output-dir ./test_images/output_GPR --raw
```

This will:
- Process all JPEG/PNG/RAW images in the input directory (including GPR files when using --raw flag)
- Save enhanced images to the output directory with "_seathru" suffix
- Automatically create the output directory if it doesn't exist
- Show progress for each image being processed

### Advanced Options
- `--max-size`: Limit maximum image dimension (default: no resizing)
  ```bash
  python seathru-mono-e2e.py --image input.jpg --max-size 2000
  ```
- `--f`: Control brightness (default: 2.0)
- `--l`: Control balance of attenuation constants (default: 0.5)
- `--p`: Control locality of illuminant map (default: 0.01)
- `--output-graphs`: Generate debug visualization graphs
- `--no-cuda`: Force CPU processing if CUDA is unavailable
- `--raw`: Process RAW images (including DNG, RAW, and GPR formats)

### GPR File Support

This version includes support for GoPro GPR files through the rawpy library. GPR files are a variation of DNG (Digital Negative) format and store Bayer-pattern data.

**Usage:**
- Use the `--raw` flag when processing GPR files
- rawpy will demosaic the Bayer-pattern data and output RGB images
- GPR files are treated as standard RAW files

**Example GPR Processing:**
```bash
# Process GPR files using rawpy
python seathru-mono-e2e.py --input-dir ./gpr_files --output-dir ./processed --raw

# Single GPR file processing
python seathru-mono-e2e.py --image underwater.GPR --raw --output enhanced.png
```

**Technical Details:**
- GPR files contain Bayer-pattern data that requires demosaicing
- rawpy handles the conversion from Bayer pattern to RGB automatically
- The resulting images maintain the quality advantages of RAW processing

## Description

A recent advance in underwater imaging is the Sea-Thru method, which uses a physical model of light attenuation to reconstruct
the colors in an underwater scene. This method utilizes a known
range map to estimate backscatter and wideband attenuation
coefficients. This range map is generated using structure-from-motion (SFM), which requires multiple underwater images from various perspectives and long processing time. In addition, SFM gives very accurate results, which are generally not required for this method. In this work, we implement and extend Sea-Thru to take advantage of convolutional monocular depth estimation methods, specifically the Monodepth2 network. We obtain satisfactory results with the lower-quality depth estimates with some color inconsistencies using only one image.
