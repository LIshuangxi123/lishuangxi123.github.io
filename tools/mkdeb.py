#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
不用 Theos 也能打包：把 control + layout 打成一个能装到设备上的 deb

用法：
    python3 tools/mkdeb.py --control examples/hello-tweak/control --layout examples/hello-tweak/layout
    python3 tools/mkdeb.py --control control --layout layout --arch iphoneos-arm64 --out debs

说明：
  - layout 里的目录结构就是设备上的真实结构，rootless 环境要放在 layout/var/jb/ 下面
  - control 同目录里的 postinst / prerm / conffiles 等标准 control 文件会一起打进 control.tar.gz
  - 在 macOS / Linux 上打包会保留可执行权限；在 Windows 上打二进制包会丢失执行权限
"""

import argparse
import io
import os
import tarfile

DEBIAN_BINARY = b'2.0\n'
LF = chr(10)

CONTROL_MEMBERS = ('control', 'preinst', 'postinst', 'prerm', 'postrm',
                   'conffiles', 'triggers', 'md5sums')


def newest_mtime(paths):
    """取最新修改时间，内容没变时打包结果保持一致，索引不会天天变"""
    latest = 0
    for path in paths:
        try:
            latest = max(latest, int(os.path.getmtime(path)))
        except OSError:
            pass
    return latest


def collect(base):
    """遍历 layout 目录，返回 [(磁盘路径, 归档内名字)]"""
    entries = []
    for current, dirs, files in os.walk(base):
        dirs.sort()
        rel = os.path.relpath(current, base).replace(os.sep, '/')
        entries.append((current, './' if rel == '.' else './' + rel))
        for name in sorted(files):
            full = os.path.join(current, name)
            inner = os.path.relpath(full, base).replace(os.sep, '/')
            entries.append((full, './' + inner))
    return entries


def tar_bytes(entries, mtime):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz', format=tarfile.GNU_FORMAT) as tar:
        for full, inner in entries:
            info = tar.gettarinfo(full, arcname=inner)
            info.uid = 0
            info.gid = 0
            info.uname = 'root'
            info.gname = 'root'
            info.mtime = mtime
            if info.isdir():
                info.mode = 0o755
            elif info.isreg():
                info.mode = 0o755 if (info.mode & 0o111) else 0o644
            if info.isreg():
                with open(full, 'rb') as handle:
                    tar.addfile(info, handle)
            else:
                tar.addfile(info)
    return buf.getvalue()


def ar_bytes(members):
    """按 ar 格式拼出 deb 外壳"""
    out = io.BytesIO()
    out.write(b'!<arch>\n')
    for name, data in members:
        header = '%-16s%-12s%-6s%-6s%-8s%-10s' % (name, '0', '0', '0', '100644', str(len(data)))
        out.write(header.encode('ascii') + b'`\n')
        out.write(data)
        if len(data) % 2:
            out.write(b'\n')
    return out.getvalue()


def parse_control(text):
    fields = {}
    for line in text.splitlines():
        if line[:1] in (' ', '\t') or ':' not in line:
            continue
        key, _, val = line.partition(':')
        fields[key.strip().lower()] = val.strip()
    return fields


def main():
    parser = argparse.ArgumentParser(description='把 control + layout 打成 deb')
    parser.add_argument('--control', required=True, help='control 文件路径')
    parser.add_argument('--layout', required=True, help='layout 目录路径')
    parser.add_argument('--out', default='debs', help='输出目录，默认 debs')
    parser.add_argument('--arch', default=None, help='覆盖 control 里的 Architecture')
    args = parser.parse_args()

    with open(args.control, 'r', encoding='utf-8') as fh:
        control_text = fh.read()

    if args.arch:
        rebuilt = []
        for line in control_text.splitlines():
            if line.lower().startswith('architecture:'):
                line = 'Architecture: %s' % args.arch
            rebuilt.append(line)
        control_text = LF.join(rebuilt) + LF

    fields = parse_control(control_text)
    for required in ('package', 'version', 'architecture'):
        if required not in fields:
            raise SystemExit('control 里缺少 %s 字段' % required)

    control_dir = os.path.dirname(os.path.abspath(args.control))
    control_entries = []
    for name in sorted(os.listdir(control_dir)):
        full = os.path.join(control_dir, name)
        if os.path.isfile(full) and name.lower() in CONTROL_MEMBERS:
            control_entries.append((full, './' + name))
    if not control_entries:
        raise SystemExit('control 目录里没有可用的 control 文件')

    data_entries = collect(args.layout)
    mtime = newest_mtime([full for full, _ in control_entries] + [full for full, _ in data_entries])

    blob = ar_bytes([
        ('debian-binary', DEBIAN_BINARY),
        ('control.tar.gz', tar_bytes(control_entries, mtime)),
        ('data.tar.gz', tar_bytes(data_entries, mtime)),
    ])

    if not os.path.isdir(args.out):
        os.makedirs(args.out)
    filename = '%s_%s_%s.deb' % (fields['package'], fields['version'], fields['architecture'])
    out_path = os.path.join(args.out, filename)
    with open(out_path, 'wb') as fh:
        fh.write(blob)
    print('已生成 %s （%d 字节）' % (out_path, len(blob)))
    print('接着跑一次 build 重建索引即可。')


if __name__ == '__main__':
    main()
