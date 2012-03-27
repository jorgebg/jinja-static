import os
import sys
import argparse

import yaml
import jinja2
import logging
import jinjatag

import staticlib

def run():
    p = argparse.ArgumentParser(description="Compile static templates")
    p.add_argument('-s', '--source', required=True,
                   help="Source file or directory.")
    p.add_argument('-d', '--dest',
                   help="Destination file or directory.")
    p.add_argument('-w', '--watch', action="store_true", default=False,
                   help="Watch for changed files.")
    p.add_argument('-f', '--full', action="store_true", default=False,
                   help="Do not perform an incremental compilation, and do everything.")
    p.add_argument('-p', '--production', action="store_true", default=False,
                   help="Minify and compile static files for use in production.")
    p.add_argument('-c', '--config', default='config.yml',
                   help='Name of config file with settings.')
    args = p.parse_args()

    config = {}
    if os.path.exists(args.config):
        with open(p.conf) as f:
            config = yaml.load(f.read())

    if args.watch:
        print("Not supported yet")
        return

    compile_jinja(args.source, args.dest, config, not args.full and not args.production, not args.production)


def compile_jinja(source, dest, config, incremental, debug):
    jinja_tag = jinjatag.JinjaTag()
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(source), extensions=[jinja_tag])
    jinja_tag.init()

    staticlib.clear_data()

    staticlib.set_config(debug, config)
    if not debug:
        walk_and_compile(env, source, dest, incremental, save=False)
        staticlib.compile(source, 'output')
    walk_and_compile(env, source, dest, incremental, save=True)

def walk_and_compile(env, source, dest, incremental, save=True):
    for dirpath, dirnames, filenames in os.walk(source, followlinks=True):
        reldir = dirpath[len(source) + 1:]
        for filename in filenames:
            if not filename.lower().endswith('.html'):
                continue
            if save:
                target_file = os.path.join(dest, reldir, filename)
            else:
                target_file = None
            try:
                compile_file(env, os.path.join(reldir, filename),
                             os.path.join(dirpath, filename), target_file, incremental)
            except Exception as e:
                logging.error("   In file {0}: {1}".format(os.path.join(reldir, filename),
                                                        str(e)), exc_info=True)


def compile_file(env, source_name, source_file, dest_file, incremental):
    if incremental and os.stat(source_file).st_mtime <= os.stat(dest_file).st_mtime:
        return
    result = env.get_template(source_name).render().encode('utf8')
    if not dest_file:
        return
    with open(dest_file, 'w+') as f:
        f.write(result)


if __name__ == '__main__':
    run()