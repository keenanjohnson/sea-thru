# Sea-Thru
Implementation of Sea-thru by Derya Akkaynak and Tali Treibitz and made more specific by Keenan Johnson.

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

### Batch Directory Processing
Process all images in a directory:
```bash
python seathru-mono-e2e.py --input-dir ./test_images/input_JPEG --output-dir ./test_images/output_JPEG
```

Process RAW files (DNG, NEF, CR2, ARW):
```bash
python seathru-mono-e2e.py --input-dir ./test_images/input_RAW --output-dir ./test_images/output_RAW --raw
```

This will:
- Process all JPEG/PNG images in the input directory (or RAW files with --raw flag)
- Save enhanced images to the output directory with "_seathru" suffix
- Automatically create the output directory if it doesn't exist
- Show progress for each image being processed

### Processing GoPro GPR Files
GPR files require conversion to DNG first (the Docker image includes gpr_tools for this):

```bash
# Step 1: Convert GPR to DNG losslessly (inside Docker container)
python gpr_converter.py --input-dir ./test_images/input_GPR --output-dir ./test_images/input_DNG

# Step 2: Process the DNG files
python seathru-mono-e2e.py --input-dir ./test_images/input_DNG --output-dir ./test_images/output_GPR --raw
```

The Docker image includes `gpr_tools` (GoPro's official tool) for lossless GPR to DNG conversion.

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

## Description

A recent advance in underwater imaging is the Sea-Thru method, which uses a physical model of light attenuation to reconstruct
the colors in an underwater scene. This method utilizes a known
range map to estimate backscatter and wideband attenuation
coefficients. This range map is generated using structure-from-motion (SFM), which requires multiple underwater images from various perspectives and long processing time. In addition, SFM gives very accurate results, which are generally not required for this method. In this work, we implement and extend Sea-Thru to take advantage of convolutional monocular depth estimation methods, specifically the Monodepth2 network. We obtain satisfactory results with the lower-quality depth estimates with some color inconsistencies using only one image.
