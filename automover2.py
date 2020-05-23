import pickle
import logging
import json
import re
import os
import filetype
import tvdb_api
import traceback
import shutil
from collections import namedtuple
from collections import defaultdict


def get_files(path, ignore):
    for root, dirs, files in os.walk(path):
        if root == ignore:
            continue

        for f in files:
            yield os.path.join(root, f)


def is_video(path, negative_search_re):
    try:
        if negative_search_re.search(path):
            return False

        return filetype.guess(path).mime.split('/')[0] == 'video'
    except Exception:
        return False


def get_extension(path):
    return filetype.guess(path).extension


def get_episode(file, search_re, interactive):
    true_extension = get_extension(file)

    search = search_re.search(file)
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
        if title not in TVDB_CACHE:
            TVDB_CACHE[title] = tvdb.search(title)
        tvdb_result = TVDB_CACHE[title]
    except tvdb_api.tvdb_exception:
        logger.error(f'Series not found for "{title}"')
        return None

    if len(tvdb_result) == 1:
        tvdb_result, = tvdb_result
    elif len(tvdb_result) > 1:
        if interactive:
            if title in CHOICES_CACHE:
                choice = CHOICES_CACHE[title]
            else:
                logger.warning(f'More than one result found for {title}. Please choose the correct one:')
                for idx, result in enumerate(tvdb_result):
                    logger.warning(f'[{idx}] {result["seriesName"]}')

                while True:
                    choice = input('Choose [0]: ')
                    try:
                        choice = int(choice)
                        assert 0 <= choice < len(tvdb_result)
                        break
                    except:
                        self.logger.warning(f'Invalid option. Please choose a number between 0 and {len(tvdb_result)-1}')
                CHOICES_CACHE[title] = choice
            tvdb_result = tvdb_result[choice]
        else:
            tvdb_result = [t for t in tvdb_result if t['network'] is not None]
            logger.warning(f'More than one result found for {title}! Run in interactive mode to resolve.')
            return None
    series_name = tvdb_result['seriesName']
    series_id = tvdb_result['id']

    try:
        episode_name = tvdb[series_id][season][episode]['episodeName']
    except:
        logger.error(f"Couldn't find episode {episode} ({series_name} season {season}). Season details follow:")
        logger.error(json.dumps(tvdb[series_id], indent=2))
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

    for original_path, dest_directory, episode in move_details:
        if not os.path.exists(dest_directory):
            logger.info(f'Creating directory {dest_directory}')
            os.makedirs(dest_directory, exist_ok=True)

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
                try:
                    os.link(original_path, new_path)
                except:
                    logger.warning(f'ERROR on {original_path}! Skipping')
                    logger.warning(traceback.format_exc())

        cleaned_up_path = os.path.join(cleanup_dir, os.path.basename(original_path))
        logger.info(f' Moving "{original_path}" to "{cleaned_up_path}"')
        if not dry_run:
            os.rename(original_path, cleaned_up_path)


def run(cleanup_dir, path, dest, copy, dry_run, interactive, search_re, negative_search_re):
    files = get_files(path, ignore=cleanup_dir)
    moves = defaultdict(list)
    for file in files:
        if not is_video(file, negative_search_re):
            continue

        episode = get_episode(file, search_re, interactive)
        if not episode:
            continue

        original_path = file
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
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactively ask the user when multiple options exist')
    parser.add_argument('--dry-run', '-n', action='store_true', help="Don't do any file system operations")
    parser.add_argument('--verbose', '-v', action='store_true', help="Verbose logging")
    parser.add_argument('path', action='store', help='The path to the root of all the files that need to be renamed')
    parser.add_argument('dest', action='store', help="The path to destination of the files after they've been renamed")
    args = parser.parse_args()

    logging.addLevelName(logging.ERROR, "\033[1;31mERROR")
    logging.addLevelName(logging.WARNING, "\033[1;33mWARN")
    logging.addLevelName(logging.INFO, "\033[1;0mINFO")

    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s [%(funcName)s():%(lineno)d] - %(message)s")
    logging.captureWarnings(True)

    Episode = namedtuple('Episode', 'file_name, series_name, directory_name, season, episode')
    Move = namedtuple('Move', 'episode, original_path')

    if args.dry_run:
        logger.info('Running in dry-run mode. Nothing will actually be moved.')

    try:
        with open(os.path.join(args.cache, 'TVDB_CACHE.pyo'), 'rb') as cache:
            TVDB_CACHE, CHOICES_CACHE = pickle.load(cache)
        logger.info('Loaded TVDB episode cache')
    except:
        logger.info('Failed to load cache.')
        TVDB_CACHE, CHOICES_CACHE = defaultdict(list), dict()

    search_re = re.compile(r"([\w\.\'\-\s\?!\(\)]*)(S(\d+)E(\d+)|(\d+)x(\d+))(.*)", re.IGNORECASE)
    negative_search_re = re.compile(r"(\.sub|\.idx|\.nfo|\.sfv|sample)", re.IGNORECASE)

    tvdb = tvdb_api.Tvdb()
    run(
        cleanup_dir=args.cleanup_dir,
        path=args.path,
        dest=args.dest,
        copy=args.copy,
        dry_run=args.dry_run,
        search_re=search_re,
        negative_search_re=negative_search_re,
        interactive=args.interactive
    )

    try:
        with open(os.path.join(args.cache, 'TVDB_CACHE.pyo'), 'wb') as cache:
            pickle.dump([TVDB_CACHE, CHOICES_CACHE], cache)
    except Exception as e:
        logger.error('Failed to write cache. TVDB episode data will be lost.')
        logger.error(e)
