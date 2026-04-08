#!/usr/bin/env python3
"""
Generate images via xAI API from media/manifest.json prompts.

Usage:
  export XAI_API_KEY=your_key
  python3 generate_images.py                       # all chapters, standard model
  python3 generate_images.py --chapter 1           # chapter 1 only
  python3 generate_images.py --chapter 1 --pro     # use pro model
  python3 generate_images.py --dry-run             # show what would be generated
  python3 generate_images.py --parallel 10         # 10 concurrent requests
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed


API_URL = 'https://api.x.ai/v1/images/generations'
MODEL_STANDARD = 'grok-imagine-image'
MODEL_PRO = 'grok-imagine-image-pro'


def generate_image(entry, api_key, model, resolution='1k', aspect_ratio='16:9'):
    """Generate one image and save it to disk. Returns (id, success, message)."""
    media_id = entry['id']
    image_path = entry['image_path']
    prompt = entry['animation_prompt']

    # Skip if already exists
    if os.path.exists(image_path):
        return (media_id, True, 'already exists')

    payload = json.dumps({
        'model': model,
        'prompt': prompt,
        'n': 1,
        'response_format': 'b64_json',
        'resolution': resolution,
        'aspect_ratio': aspect_ratio,
    }).encode('utf-8')

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read())

        b64_data = body['data'][0]['b64_json']
        img_bytes = base64.b64decode(b64_data)

        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        with open(image_path, 'wb') as f:
            f.write(img_bytes)

        return (media_id, True, f'{len(img_bytes)} bytes')

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8', errors='replace')[:200]
        return (media_id, False, f'HTTP {e.code}: {error_body}')
    except Exception as e:
        return (media_id, False, str(e))


def main():
    parser = argparse.ArgumentParser(description='Generate images via xAI API')
    parser.add_argument('--chapter', type=int, help='Only generate for this chapter')
    parser.add_argument('--pro', action='store_true', help='Use pro model ($0.07/img instead of $0.02)')
    parser.add_argument('--resolution', default='1k', choices=['1k', '2k'], help='Image resolution')
    parser.add_argument('--aspect-ratio', default='16:9', help='Aspect ratio (default 16:9)')
    parser.add_argument('--parallel', type=int, default=5, help='Concurrent requests (default 5)')
    parser.add_argument('--dry-run', action='store_true', help='Show plan without generating')
    parser.add_argument('--retry-failed', action='store_true', help='Retry only previously failed items')
    args = parser.parse_args()

    api_key = os.environ.get('XAI_API_KEY', '')
    if not api_key and not args.dry_run:
        print('Error: set XAI_API_KEY environment variable')
        print('  Get one at https://console.x.ai/team/default/api-keys')
        sys.exit(1)

    with open('media/manifest.json') as f:
        manifest = json.load(f)

    # Filter
    entries = manifest
    if args.chapter:
        entries = [e for e in entries if e['chapter'] == args.chapter]

    # Skip already generated
    if not args.retry_failed:
        pending = [e for e in entries if not os.path.exists(e['image_path'])]
    else:
        pending = entries  # retry all

    model = MODEL_PRO if args.pro else MODEL_STANDARD
    cost_per = 0.07 if args.pro else 0.02
    total_cost = len(pending) * cost_per

    print(f'Model: {model}')
    print(f'Resolution: {args.resolution}, Aspect ratio: {args.aspect_ratio}')
    print(f'Total: {len(entries)} images, {len(entries) - len(pending)} already done, {len(pending)} to generate')
    print(f'Estimated cost: ${total_cost:.2f}')
    print()

    if args.dry_run:
        for e in pending:
            print(f'  {e["id"]}: {e["animation_prompt"][:80]}...')
        return

    if len(pending) == 0:
        print('Nothing to do!')
        return

    # Generate
    successes = 0
    failures = 0
    start = time.time()

    with ThreadPoolExecutor(max_workers=args.parallel) as pool:
        futures = {
            pool.submit(generate_image, e, api_key, model, args.resolution, args.aspect_ratio): e
            for e in pending
        }

        for future in as_completed(futures):
            media_id, ok, msg = future.result()
            if ok:
                successes += 1
                print(f'  OK  {media_id}: {msg}')
            else:
                failures += 1
                print(f'  ERR {media_id}: {msg}')

    elapsed = time.time() - start
    print()
    print(f'Done in {elapsed:.1f}s: {successes} succeeded, {failures} failed')
    print(f'Actual cost: ~${successes * cost_per:.2f}')


if __name__ == '__main__':
    main()
