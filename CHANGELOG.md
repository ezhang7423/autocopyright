# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and
this project adheres to [Calendar Versioning](https://calver.org/).

## \[1.1.0\] - 2023-02-17

- Added `--exclude/-e` option to allow exclusion of individual files/directories.

- Removed use of `ThreadPoolExecutor` when pool size is less or equal to 1. Now threads
  are used only when pool is bigger than 1.

## \[1.0.0\] - 2023-02-16

- Implemented MVP version of autocopyright.
