import logging
import re
import os
import filetype
import sys
import tvdb_api


def get_files(path):
    for root, dirs, files in os.walk(path):
        for f in files:
            yield os.path.join(root, f)


def is_video(path):
    try:
        return filetype.guess(path).mime.split('/')[0] == 'video'
    except:
        return False


def get_extension(path):
    return filetype.guess(path).extension


def get_real_file_parts(file):
    true_extension = get_extension(file)

    search = re.search(r"([\w\.\'\-\s\?!\(\)]*)(S(\d+)E(\d+)|(\d+)x(\d+))(.*)", file, re.IGNORECASE)
    if not search:
        logger.warning(f'Match failed for {file}')
        return None

    title, season_group, s1, e1, s2, e2, _ = search.groups()
    season = s1 or s2
    episode = e1 or e2
    logger.debug(f'Matched {file} to: "{title}" "{season}" "{episode}"')

    title = title.replace('.', ' ')

    try:
        season = int(season)
        episode = int(episode)
    except:
        logger.error("Couldn't cast season or episode to an int!")
        return None

    try:
        tvdb_result = tvdb.search(title)
    except tvdb_api.tvdb_exception:
        logger.error(f'Series not found for "{title}"')
        return None

    series_name = tvdb_result[0]['seriesName']

    if len(tvdb_result) > 1:
        logger.warning(f'More than one result found for {title}. Defaulting to the first one, which is: {series_name}')

    try:
        episode_name = tvdb[series_name][season][episode]['episodeName']
    except:
        logger.error(f"Couldn't find episode {episode} ({series_name} season {season}) ")
        return None

    file_name = f'{series_name} S{season:02}E{episode:02} {episode_name}.{true_extension}'
    return series_name, file_name


def run(cleanup_dir, path, dest, tvdb):
    files = get_files(path)
    for file in files:
        if not is_video(file):
            continue

        parts = get_real_file_parts(file)
        if not parts:
            continue

        series_name, file_name = parts

        original_path = os.path.join(path, file)
        dest_directory = os.path.join(dest, series_name)
        new_path = os.path.join(dest, series_name, file_name)
        logger.info(f'{original_path} -> {new_path}')


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--cleanup-dir", "-c", action="store", help="Where to move the files after copying them to their destination", default="./finished")
    parser.add_argument("path", action="store", help="The path to the root of all the files that need to be renamed")
    parser.add_argument("dest", action="store", help="The path to destination of the files after they've been renamed")
    args = parser.parse_args()

    logging.addLevelName(logging.ERROR, "\033[1;31mERROR\033[1;0m")
    logging.addLevelName(logging.WARNING, "\033[1;33mWARN\033[1;0m")

    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    logging.captureWarnings(True)
    tvdb = tvdb_api.Tvdb()
    run(
        cleanup_dir=args.cleanup_dir,
        path=args.path,
        dest=args.dest,
        tvdb=tvdb
    )
