# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and
this project adheres to [Calendar Versioning](https://calver.org/).


## \[1.2.2\] - 2024-10-11

  Exclude .gitignore if directory is git repository.

## \[1.2.1\] - 2024-10-11

  Exclude .git folder and copyright license if present in source directory.


## \[1.2.0\] - 2024-10-11

- Bumped version to work without pyproject.toml file in repo.

## \[1.1.0\] - 2023-02-17

- Added `--exclude/-e` option to allow exclusion of individual files/directories.

- Removed use of `ThreadPoolExecutor` when pool size is less or equal to 1. Now threads
  are used only when pool is bigger than 1.

## \[1.0.0\] - 2023-02-16

- Implemented MVP version of autocopyright.
