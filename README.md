# Webcrawler

A simple webcrawler/scraper tool written in Python.

## Installation

### Using `pipenv` (recommended)

It is recommended to create a [Python virtual environment](https://docs.python.org/3/tutorial/venv.html) to manage the required Python version as well as app dependencies regardless of the system environment. [Pipenv](https://pipenv.pypa.io/en/latest/) is an easy way to do so and the module has a `Pipfile` and a `Pipfile.lock` prepared for it, so you can install dependencies and run the app using:

```
# Install dependencies
pipenv install

# Run the project as a module through the created virtual env
pipenv run python -m webcrawler <path/to/config.toml>

# Or activate the virtual env and run it directly
pipenv shell
python -m webcrawler <path/to/config.toml>
```

### Using `requirements.txt`

If you don't want a virtual environment or you have your own already you can just install dependencies regularly using `pip`.

```
# Install dependencies
pip install -r requirements.txt

# Run the project as a module
python -m webcrawler <path/to/config.toml>
```

## Configuration

The tool operates via a config file in [TOML](https://toml.io/en/) format that you need to supply as the first (and only) argument. You'll need to pass the following parameters (you can check `oda_products.toml` as an example file):

### `title`
Title of the crawler.

### `runner.log_level`
Log level threshold to be given to the Python logger. Must correspond to one of the [Python logging levels](https://docs.python.org/3/library/logging.html#logging-levels).

### `runner.log_name`
Name of the logger instance.

### `runner.limit`
The maximum number of pages to be parsed. Note that this refers to _pages_, not parsed items, e.g. if one page yields multiple items that will still only count as one. Setting this to 0 means there's no limit.

### `runner.delay`
Minimum delay between fetching and parsing pages, in milliseconds.

### `urlcollector.classname`
The module path to the class used to collect URL addresses to be parsed. This must point to a child class of `webcrawler.urlcollector.UrlCollector`.
Currently there are 3 different built-in collectors that can be used, each having its own set of arguments that need to be added to this config:

#### `webcrawler.urlcollector.SitemapCollector`
A collector that attempts to retrieve relevant URLs using a website's sitemap. It needs the following arguments:
* `base_url`: The base URL of the website.
* `target_pattern`: A regexp pattern to filter relevant URLs to be parsed.
* `sitemap_path`: Path to the sitemap relative to `base_url`. Defaults to `sitemap.xml`.

#### `webcrawler.urlcollector.RobotsTxtCollector`
An extension of `SitemapCollector`, but instead of directly feeding a sitemap path to it, it attempts to read them from the website's `robots.txt` file. It needs the following arguments:
* `base_url`: The base URL of the website.
* `target_pattern`: A regexp pattern to filter relevant URLs to be parsed.
* `robots_path`: Path to the robots file relative to `base_url`. Defaults to `robots.txt`

#### `webcrawler.urlcollector.CrawlCollector`
If a sitemap isn't available, the collector provides the option to crawl through the site following hyperlinks. It needs the following arguments:
* `base_url`: The base URL of the website.
* `target_pattern`: A regexp pattern to filter relevant URLs to be parsed.
* `crawl_pattern`: A regexp pattern (or an array of patterns) to filter URLs to follow while crawling.
* `start_path`: Path to start the crawl from, relative to `base_url`. Defaults to an empty string.

### `parser.classname`
The module path to the class used to parse the content of a collected page and yield items out of them. This must point to a child class of `webcrawler.parser.Parser`. Any argument needed to create a Parser instance must be provided to this config.

### `output.classname`
The module path to the class used to provide output for the items yielded by the parser. This must point to a child class of `webcrawler.output.Output`. Any argument needed to create an Output instance must be provided to this config.
