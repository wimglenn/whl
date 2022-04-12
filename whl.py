#!/usr/bin/env python
import argparse
import base64
import hashlib
import logging
import os
import zipfile


__version__ = "0.0.2"


log = logging.getLogger(__name__)


# https://packaging.python.org/specifications/core-metadata/
METADATA_TEMPLATE = """\
Metadata-Version: 2.1
Name: {name}
Version: {version}
"""


# https://www.python.org/dev/peps/pep-0427/
WHEEL_TEMPLATE = """\
Wheel-Version: 1.0
Generator: whl {__version__}
Root-Is-Purelib: true
"""


class WhlError(Exception):
    pass


def get_version(fname):
    with open(fname) as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=", 1)[-1].strip().strip("'").strip('"')
    raise WhlError("Failed to autodetect __version__")


def get_record(path, data=None, arcname=None):
    if data is None:
        with open(path, "rb") as f:
            data = f.read()
    checksum = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=")
    if path.startswith("./"):
        path = path[2:]
    if arcname is None:
        arcname = path
    line = "{},sha256={},{}".format(arcname, checksum.decode(), len(data))
    return line


def get_dist_files(src):
    if src is None:
        return []
    if src.endswith(".py"):
        return [src]
    blacklist = {"README.rst", "setup.py", "setup.cfg", ".coverage"}
    dist_files = []
    for root, dirs, fnames in os.walk(src):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fname in fnames:
            if fname not in blacklist and not fname.endswith((".whl", ".pyc")):
                relpath = os.path.join(root, fname)
                dist_files.append(relpath)
    return dist_files


def make_wheel(
    src=None,
    name=None,
    version=None,
    # dynamic
    platform=None,
    # supported_platform
    summary=None,
    description=None,
    # description_content_type
    # keywords
    home_page=None,
    # download_url
    author=None,
    author_email=None,
    # maintainer
    # maintainer_email
    license=None,
    classifier=None,
    requires_dist=None,
    # requires_python
    # requires_external
    # project_url
    # provides_extra
    # provides_dist
    # obsoletes_dist
    py2=True,
    py3=True,
    output_dir=".",
):
    METADATA = METADATA_TEMPLATE.format(name=name, version=version)
    metadata_lines = []
    if summary is not None:
        metadata_lines.append("Summary: {}".format(summary))
    if home_page is not None:
        metadata_lines.append("Home-page: {}".format(home_page))
    if requires_dist is not None:
        if isinstance(requires_dist, str):
            requires_dist = [requires_dist]
        metadata_lines.extend("Requires-Dist: {}".format(r) for r in requires_dist)
    if author is not None:
        metadata_lines.append("Author: {}".format(author))
    if author_email is not None:
        metadata_lines.append("Author-email: {}".format(author_email))
    if license is not None:
        metadata_lines.append("License: {}".format(license))
    if platform is not None:
        if isinstance(platform, str):
            platform = [platform]
        metadata_lines.extend("Platform: {}".format(p) for p in platform)
    if classifier is not None:
        if isinstance(classifier, str):
            classifier = [classifier]
        metadata_lines.extend("Classifier: {}".format(c) for c in classifier)
    if metadata_lines:
        METADATA += "\n".join(metadata_lines) + "\n"
    if description is not None:
        METADATA += "\n" + description

    WHEEL = WHEEL_TEMPLATE.format(__version__=__version__)
    if py2:
        WHEEL += "Tag: py2-none-any\n"
    if py3:
        WHEEL += "Tag: py3-none-any\n"

    tags = "py2.py3"
    if py2 and not py3:
        tags = "py2"
    elif py3 and not py2:
        tags = "py3"

    whl_name = "{}-{}-{}-none-any.whl".format(name.replace("-", "_"), version, tags)
    dist_info_name = "{}-{}.dist-info".format(name.replace("-", "_"), version)
    whl_path = os.path.join(output_dir, whl_name)

    RECORD = []
    zf = zipfile.ZipFile(whl_path, "w")
    if src:
        if isinstance(src, (list, tuple)):
            dist_files = src
            parent = os.path.dirname(os.path.abspath(src[0]))
        else:
            dist_files = get_dist_files(src)
            parent = os.path.dirname(os.path.abspath(src))
        for path in dist_files:
            arcname = os.path.relpath(path, parent)
            zf.write(path, arcname)
            record = get_record(path, arcname=arcname)
            RECORD.append(record)
            log.info(record)

    info_metadata = os.path.join(dist_info_name, "METADATA")
    RECORD.append(get_record(info_metadata, data=METADATA.encode()))
    zf.writestr(info_metadata, METADATA)

    info_wheel = os.path.join(dist_info_name, "WHEEL")
    RECORD.append(get_record(info_wheel, data=WHEEL.encode()))
    zf.writestr(info_wheel, WHEEL)

    RECORD.append("{},,".format(os.path.join(dist_info_name, "RECORD")))
    zf.writestr(os.path.join(dist_info_name, "RECORD"), "\n".join(RECORD))

    zf.close()
    return whl_path


def main():
    parser = argparse.ArgumentParser(
        prog="whl.py", description="Minimalist wheel building"
    )
    parser.add_argument("-2", dest="py2", action="store_true")
    parser.add_argument("-3", dest="py3", action="store_true")
    parser.add_argument(
        "-o",
        "--output-dir",
        default=".",
        help="Where to put the generated .whl file (default: %(default)s)",
    )
    parser.add_argument(
        "src",
        default=".",
        nargs="?",
        help=(
            "Directory of files to pack into wheel (default: %(default)s), "
            "the dirname will be used as the distribution name. "
            "This can also be a single .py file"
        ),
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s {}".format(__version__)
    )
    parser.add_argument("-v", "--verbose", action="count", default=0)
    args = parser.parse_args()
    if args.verbose >= 2:
        level = logging.DEBUG
    elif args.verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(level=level)
    py2 = args.py2
    py3 = args.py3
    if not (py2 or py3):
        # universal by default
        py2 = py3 = True
    assert py2 or py3

    src = os.path.abspath(args.src)
    name = os.path.basename(src)
    if os.path.isdir(args.src):
        init = os.path.join(src, "__init__.py")
        if not os.path.isfile(init):
            raise WhlError("{} must contain an __init__.py".format(src))
        version = get_version(init)
    elif os.path.isfile(src):
        version = get_version(src)
        if name.endswith(".py"):
            name = name[:-3]
    else:
        raise WhlError("Unknown source: {}".format(src))

    whl_path = make_wheel(
        src=src,
        name=name,
        version=version,
        py2=py2,
        py3=py3,
        output_dir=args.output_dir,
    )
    print(whl_path)


if __name__ == "__main__":
    main()
