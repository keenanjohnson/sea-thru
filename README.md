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

Process a GoPro GPR file (note: GPR support with limitations):
```bash
python seathru-mono-e2e.py --image input.GPR --raw --output enhanced.png
```

### Batch Directory Processing
Process all images in a directory:
```bash
python seathru-mono-e2e.py --input-dir ./test_images/input_JPEG --output-dir ./test_images/output_JPEG
```

Process GPR files (will show helpful error messages for unsupported compression):
```bash
python seathru-mono-e2e.py --input-dir ./test_images/input_GPR --output-dir ./test_images/output_GPR --raw
```

This will:
- Process all JPEG/PNG/GPR images in the input directory
- Save enhanced images to the output directory with "_seathru" suffix
- Automatically create the output directory if it doesn't exist
- Show progress for each image being processed
- Provide helpful guidance for GPR files that cannot be processed directly

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

This version includes experimental support for GoPro GPR files. However, there are important limitations:

**Current Status:**
- GPR files are detected and processed automatically
- Most GPR files use JBIG compression which is not supported by standard Python libraries
- The system will provide helpful error messages and conversion suggestions

**Recommended Workflow for GPR Files:**
1. **Best Quality**: Convert GPR to DNG format using Adobe DNG Converter
2. **Alternative**: Use GoPro Quik app to export as TIFF or JPEG
3. **Command Line**: Use `dcraw` or `RawTherapee` to convert GPR files
4. **Quick Preview**: Extract embedded JPEG preview using `exiftool` (lower quality)

**Example GPR Processing:**
```bash
# This will attempt to process GPR files and show helpful guidance if they can't be read
python seathru-mono-e2e.py --input-dir ./gpr_files --output-dir ./processed --raw
```

**Why GPR Files Are Challenging:**
GPR files use JBIG compression within TIFF containers, which requires specialized libraries not commonly available in Python. The system provides clear guidance on alternative conversion methods to maintain the RAW quality benefits you're seeking.

## Description

A recent advance in underwater imaging is the Sea-Thru method, which uses a physical model of light attenuation to reconstruct
the colors in an underwater scene. This method utilizes a known
range map to estimate backscatter and wideband attenuation
coefficients. This range map is generated using structure-from-motion (SFM), which requires multiple underwater images from various perspectives and long processing time. In addition, SFM gives very accurate results, which are generally not required for this method. In this work, we implement and extend Sea-Thru to take advantage of convolutional monocular depth estimation methods, specifically the Monodepth2 network. We obtain satisfactory results with the lower-quality depth estimates with some color inconsistencies using only one image.
