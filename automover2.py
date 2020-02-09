import pickle
import logging
import re
import os
import filetype
import tvdb_api
import shutil
from collections import namedtuple
from collections import defaultdict


def get_files(path, ignore):
    for root, dirs, files in os.walk(path):
        if root == ignore:
            continue

        for f in files:
            yield os.path.join(root, f)


def is_video(path):
    try:
        return filetype.guess(path).mime.split('/')[0] == 'video'
    except:
        return False


def get_extension(path):
    return filetype.guess(path).extension


def get_episode(file):
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
        if title not in tvdb_cache:
            tvdb_cache[title] = tvdb.search(title)
        tvdb_result = tvdb_cache[title]
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
    return Episode(
        file_name=file_name,
        directory_name=f'Season {season}',
        series_name=series_name,
        season=season,
        episode=episode)


def move(cleanup_dir, series_name, move_details, copy=False, dry_run=True):
    logger.info('----')
    logger.info(series_name)
    dest_directory = move_details[0][1]
    if not os.path.exists(dest_directory):
        logger.info(f'Creating directory {dest_directory}')
        os.makedirs(dest_directory, exist_ok=True)

    for original_path, _, episode in move_details:
        new_path = os.path.join(dest_directory, episode.file_name)

        if copy:
            logger.info(f' Copying file')
            logger.info(f'   source = "{original_path}"')
            logger.info(f'   dest   = "{new_path}"')
            if not dry_run:
                shutil.copy2(original_path, new_path)
        else:
            logger.info(f' Hard linking file')
            logger.info(f'  source........ "{original_path}"')
            logger.info(f'  destination... "{new_path}"')
            if not dry_run:
                os.link(original_path, new_path)

        cleaned_up_path = os.path.join(cleanup_dir, os.path.basename(original_path))
        logger.info(f' Moving "{original_path}" to "{cleaned_up_path}"')
        if not dry_run:
            os.rename(original_path, cleaned_up_path)


def run(cleanup_dir, path, dest, copy, dry_run):
    files = get_files(path, ignore=cleanup_dir)
    moves = defaultdict(list)
    for file in files:
        if not is_video(file):
            continue

        episode = get_episode(file)
        if not episode:
            continue

        original_path = os.path.join(path, file)
        dest_directory = os.path.join(dest, episode.series_name, episode.directory_name)
        moves[episode.series_name].append((original_path, dest_directory, episode))

    if len(moves):
        if not os.path.exists(cleanup_dir):
            os.mkdir(cleanup_dir)

        for series_name, move_details in moves.items():
            move(cleanup_dir, series_name, move_details, copy, dry_run)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--cleanup-dir', '-c', action='store', help='Where to move the files after copying them to their destination', default='./finished')
    parser.add_argument('--copy', '-L', action='store_true', help='Copy the file instead of doing a hard-link')
    parser.add_argument('--cache', '-x', action='store', default='/tmp', help='Cache file directory. Defaults to /tmp/')
    parser.add_argument('--dry-run', '-n', action='store_true', help="Don't do any file system operations")
    parser.add_argument('path', action='store', help='The path to the root of all the files that need to be renamed')
    parser.add_argument('dest', action='store', help="The path to destination of the files after they've been renamed")
    args = parser.parse_args()

    logging.addLevelName(logging.ERROR, "\033[1;31mERROR")
    logging.addLevelName(logging.WARNING, "\033[1;33mWARN")
    logging.addLevelName(logging.INFO, "\033[1;0mINFO")

    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    logging.captureWarnings(True)

    Episode = namedtuple('Episode', 'file_name, series_name, directory_name, season, episode')
    Move = namedtuple('Move', 'episode, original_path')

    if args.dry_run:
        logger.info('Running in dry-run mode. Nothing will actually be moved.')

    try:
        with open(os.path.join(args.cache, 'tvdb_cache.pyo'), 'rb') as cache:
            tvdb_cache = pickle.load(cache)
        logger.info('Loaded TVDB episode cache')
    except:
        logger.info('Failed to load cache.')
        tvdb_cache = defaultdict(list)

    tvdb = tvdb_api.Tvdb()
    run(
        cleanup_dir=args.cleanup_dir,
        path=args.path,
        dest=args.dest,
        copy=args.copy,
        dry_run=args.dry_run
    )

    try:
        with open(os.path.join(args.cache, 'tvdb_cache.pyo'), 'wb') as cache:
            pickle.dump(tvdb_cache, cache)
    except Exception as e:
        logger.error('Failed to write cache. TVDB episode data will be lost.')
        logger.error(e)
