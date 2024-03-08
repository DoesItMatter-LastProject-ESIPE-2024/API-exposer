# API Exposer

**API Exposer** is a web server with three simple objectives :

* Expose a REST API for each device of a matter fabric [^1]
* Expose all nodes of a matter fabric
* Expose a swagger for each node with it's REST API

[^1]: Because of the complexity of using CHIP. This project is only compatible with a matter server from the library

## API Exposer - Installation

All librairies can be install with the requirements file `./api_exposer/requirements.txt`

```shell
pip install -r ./api_exposer/requirements.txt
```

## API Exposer - Usage

To run the server, simply run the python main file called `main_api_exposer.py`

```shell
python ./main_api_exposer.py
```

There are some arguments that can be shown by adding the `-h` option.

# PDF Parser

PDF Parser is a script used to scrap information inside the matter cluster specification pdf file.

## PDF Parser - Installation

Because of the dependency `tabula-py` you will need to install java 8 (or above) and add it to your PATH.

After installing java you can be install the requirements file `./api_exposer/requirements.txt`

```shell
pip install -r ./api_exposer/requirements.txt
```

## PDF Parser - Usage

To run the script, simply run the python main file called `main_pdf_parser.py`

```shell
python ./main_pdf_parser.py
```

There are some arguments that can be shown by adding the `-h` option.
