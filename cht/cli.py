"""
Handles the command-line interface for this tool
"""

import argparse
from datetime import datetime
import os

import dotenv

from cht import consumer, DATA_PATH, DOTENV_PATH, KEY_VAR, CURR_CONGRESS
from cht.database import Database
from cht.helper import ordinal, valid_congress, congress_from_id
from cht.customtypes import format_str
from cht.transcriptparser import parse_congress


# Setup the CLI parser
def setup_parser() -> argparse.ArgumentParser:

    # Setup base command
    parser = argparse.ArgumentParser(
        prog="cht",
        description="A tool for downloading and parsing transcripts from "
        "Congressional committee hearings. Currently only supports House hearings "
        "from the 105th Congress until the most recent complete Congress (not the current Congress). "
        "Requires an API key for govinfo.gov to download and parse documents. "
        "You can sign up for a key at https://www.govinfo.gov/api-signup."
    )
    parser.add_argument("-k", "--key",
                        help="sets an API key for govinfo.gov")
    parser.set_defaults(func=base_command)
    subparsers = parser.add_subparsers(title="Subcommands")

    # Setup status subcommand
    status_parser = subparsers.add_parser("status",
                                          help="displays the status of the database")
    status_parser.set_defaults(func=status)

    # Setup download subcommand
    download_parser = subparsers.add_parser("download",
                                            help="downloads a document or set of documents")
    download_parser.add_argument("-q", "--quiet", action="store_true",
                                 help="prints no output to the console")
    download_parser.add_argument("-f", "--format", nargs='+', default='txt',
                                 choices=['txt', 'text', 'pdf', 'xml', 'metadata'],
                                 help="the file type to download, defaults to txt")
    download_parser.add_argument("selection", nargs='+',
                                 help="a list of document IDs or Congresses")
    download_parser.set_defaults(func=download)

    # Setup parse subcommand
    parse_parser = subparsers.add_parser("parse",
                                         help="parses transcripts from the specified Congresses")
    parse_parser.add_argument("-q", "--quiet", action="store_true",
                              help="prints no output to the console")
    parse_parser.add_argument("-d", "--download", action="store_true",
                              help="downloads the .txt and metadata files associated with each "
                              "document as they are being parsed")  
    parse_parser.add_argument("congress", nargs='+')
    parse_parser.set_defaults(func=parse)

    # Setup export subcommand
    export_parser = subparsers.add_parser("export",
                                          help="exports a set of parsed documents from the database")
    export_parser.add_argument("-f", "--format", default='csv', choices=['csv', 'json', 'yaml', 'xlsx'],
                               help="the format of the export file (defaults to csv)")
    export_parser.add_argument("-p", "--path", default=f"./output/{datetime.today().strftime("%Y-%m-%d")}.csv",
                               help="the path to save the export to (defaults to ./output/YYYY-MM-DD.csv)")
    export_parser.add_argument("-c", "--congress", nargs='+',
                               help="a specific Congress or list of Congresses to be exported")
    export_parser.add_argument("-q", "--quiet", action="store_true",
                               help="ignores warnings when Congresses are not fully parsed")
    export_parser.set_defaults(func=export)

    return parser


# Save the given API key and setup the database
def key_setup(key: str) -> None:
    if consumer.test_key(key):
        DATA_PATH.mkdir(exist_ok=True)
        DOTENV_PATH.touch(mode=0o600)
        dotenv.set_key(DOTENV_PATH, KEY_VAR, key)

        # Setup database
        with Database() as db:
            if not db.created():
                db.create()
    else:
        raise SystemExit("error: invalid API key")


# Code to execute for the base command
def base_command(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.key is None:
        parser.print_help()
    
    # --key flag
    if args.key is not None:
        key_setup(args.key)


# Code to execute for the status subcommand
def status(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    with Database() as db:
        db.refresh_paths()
        documents = db.get_documents()
        txts = db.get_files('txt')
        pdfs = db.get_files('pdf')
        xmls = db.get_files('xml')

    if len(documents) == 0 and len(txts) == 0 and len(pdfs) == 0 and len(xmls) == 0:
        print("No documents downloaded or parsed")
        return

    print("Parsed:")
    if len(documents) == 0:
        print("No documents parsed")
    else:
        with Database() as db:
            congresses = db.get_documents_congresses()
            for congress in congresses:
                total = len(db.get_documents(congress))
                parsed = len(db.get_documents(congress, complete=True))
                print(f"{ordinal(congress)} Congress: {parsed}/{total} documents")
    print()

    print("Text files:")
    if len(txts) == 0:
        print("No text files downloaded")
    else:
        with Database() as db:
            congresses = db.get_files_congresses('txt')
            for congress in congresses:
                total = len(db.get_files('txt', congress))
                downloaded = len(db.get_files('txt', congress, downloaded=True))
                print(f"{ordinal(congress)} Congress: {downloaded}/{total} documents")
    print()

    print("PDF files:")
    if len(pdfs) == 0:
        print("No PDF files downloaded")
    else:
        with Database() as db:
            congresses = db.get_files_congresses('pdf')
            for congress in congresses:
                total = len(db.get_files('pdf', congress))
                downloaded = len(db.get_files('pdf', congress, downloaded=True))
                print(f"{ordinal(congress)} Congress: {downloaded}/{total} documents")
    print()

    print("Metadata:")
    if len(xmls) == 0:
        print("No metadata files downloaded")
    else:
        with Database() as db:
            congresses = db.get_files_congresses('xml')
            for congress in congresses:
                total = len(db.get_files('xml', congress))
                downloaded = len(db.get_files('xml', congress, downloaded=True))
                print(f"{ordinal(congress)} Congress: {downloaded}/{total} documents")
    print()


# Code to execute for the download subcommand
def download(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:

    # --key flag
    if args.key is not None:
        key_setup(args.key)
    
    dotenv.load_dotenv(DOTENV_PATH)

    # API key required to download
    if KEY_VAR not in os.environ:
        parser.print_usage()
        raise SystemExit("error: an API key must be saved using -k/--key before downloading")
    
    # Download files
    to_download: list[str] = []
    for selection in args.selection:

        # All documents in a Congress
        if selection.isnumeric():
            if valid_congress(int(selection)):
                congress_docs = consumer.get_list(int(selection))
                congress_docs = list(filter(lambda x: congress_from_id(x) == int(selection), congress_docs))
                to_download.extend(congress_docs)
            else:
                raise SystemExit(f"error: downloading from the {ordinal(int(selection))} Congress "
                                 f"is not supported (valid range: 105-{CURR_CONGRESS-1})")
        
        # Specific IDs
        else:
            to_download.append(selection)

    for format in args.format:
        consumer.download_documents(to_download, format, quiet=args.quiet)


# Code to execute for the parse subcommand
def parse(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    
    # --key flag
    if args.key is not None:
        key_setup(args.key)
    
    dotenv.load_dotenv(DOTENV_PATH)

    # API key required to download
    if KEY_VAR not in os.environ:
        parser.print_usage()
        raise SystemExit("error: an API key must be saved using -k/--key before parsing")
    
    # Quiet and 
    
    # Validate congresses
    congresses: list[int] = []
    for congress in args.congress:
        if valid_congress(int(congress)):
            congresses.append(int(congress))
        else:
            raise SystemExit(f"error: parsing from the {ordinal(int(congress))} Congress "
                             f"is not supported (valid range: 105-{CURR_CONGRESS})")
        
    # Parse congresses
    for congress in congresses:
        parse_congress(congress, args.quiet, args.download)


# Code to execute for the export subcommand
def export(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    
    # --key flag
    if args.key is not None:
        key_setup(args.key)
    
    dotenv.load_dotenv(DOTENV_PATH)


def main() -> None:

    # Run parser
    parser = setup_parser()
    args = parser.parse_args()
    args.func(parser, args)
    

if __name__ == "__main__":
    main()