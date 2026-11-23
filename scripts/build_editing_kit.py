"""Build a portable editing kit from this repository; Python standard library only."""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    target = args.output.resolve()
    if target == root or root in target.parents or target in root.parents:
        parser.error('Output must be outside the repository.')
    if target.exists():
        parser.error('Output already exists. Choose a new directory; no files will be overwritten.')
    mappings = [
        ('assets/intro_outro/kirQQn_intro_short_1080p60.mp4','01_Intro/intro_short.mp4'),
        ('assets/intro_outro/current_cta','02_Outro'),
        ('assets/sfx','03_Sounds'),
        ('resolve_pack','04_Overlays'),
        ('assets/logo_emotions_avatars','05_Logos'),
        ('assets/fonts','06_Fonts'),
        ('constructors','07_Constructors'),
        ('templates','08_Templates'),
        ('guidelines','09_Guidelines'),
        ('brandbook/web','10_Brandbook'),
        ('guidelines/МОНТАЖНИЙ_КОМПЛЕКТ.md','START_HERE.md'),
        ('AI_INSTRUCTIONS.md','AI_INSTRUCTIONS.md'),
    ]
    files = []
    for source, dest in mappings:
        src = root / source
        if not src.exists():
            raise FileNotFoundError(source)
        for p in sorted(src.rglob('*')) if src.is_dir() else [src]:
            if not p.is_file() or any(x in p.parts for x in ('__pycache__','.git','node_modules')):
                continue
            relative = Path(dest) / p.relative_to(src) if src.is_dir() else Path(dest)
            files.append((p, relative))
    target.mkdir(parents=True)
    manifest = []
    for src, relative in files:
        dst = target / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        digest = hashlib.sha256(src.read_bytes()).hexdigest()
        if hashlib.sha256(dst.read_bytes()).hexdigest() != digest:
            raise RuntimeError(f'Copy mismatch: {relative}')
        manifest.append(dict(file=relative.as_posix(), source=src.relative_to(root).as_posix(), bytes=dst.stat().st_size, sha256=digest))
    commit = subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    (target/'MANIFEST.json').write_text(json.dumps(dict(commit=commit,files=manifest),ensure_ascii=False,indent=2),encoding='utf8')
    print(f'Copied and verified {len(manifest)} files to {target}')

if __name__ == '__main__':
    main()
