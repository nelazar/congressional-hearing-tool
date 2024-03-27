"""
Handles the command-line interface for this tool
"""

import argparse
from datetime import datetime
from pathlib import Path

import dotenv

from cht import consumer
from cht.database import Database
from cht.helper import ordinal


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
    parser.add_argument("-s", "--status", action="store_true",
                        help="display the status of the database")
    parser.add_argument("-k", "--key",
                        help="sets an API key for govinfo.gov")
    parser.set_defaults(func=base_command)
    subparsers = parser.add_subparsers(title="Subcommands")

    # Setup download subcommand
    download_parser = subparsers.add_parser("download",
                                            help="downloads a document or set of documents")
    download_parser.add_argument("-i", "--id", nargs='+',
                                 help="a specific document ID or list of IDs")
    download_parser.add_argument("-c", "--congress", nargs='+',
                                 help="a specific Congress or list of Congresses")
    download_parser.add_argument("-f", "--format", choices=['txt', 'text', 'pdf', 'xml', 'metadata'],
                                 help="the file type to download")
    download_parser.add_argument("-p", "--path", default="./downloads/",
                                 help="the directory to download the files to")
    download_parser.set_defaults(func=download)

    # Setup parse subcommand
    parse_parser = subparsers.add_parser("parse",
                                         help="parses transcripts from the specified Congresses")
    parse_parser.add_argument("-v", "--verbose", action="store_true",
                              help="prints the document ID of each document being parsed")
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


# Code to execute for the base command
def base_command(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.key is None and not args.status:
        parser.print_help()
    
    # --key flag
    if args.key is not None:
        if consumer.test_key(args.key):
            Path("./data/").mkdir(exist_ok=True)
            env_path = Path("./data/.env")
            env_path.touch(mode=0o600)
            dotenv.set_key(env_path, 'GOVINFO_KEY', args.key)
        else:
            raise SystemExit("error: invalid API key")

    # --status flag
    if args.status:
        with Database() as db:
            congresses = db.get_congresses()

        if len(congresses) == 0:
            print("No documents downloaded or parsed")
            return

        print("Parsed:")
        printed = False
        for congress in congresses:
            if congress['parsed'] > 0:
                print(f"{ordinal(congress['congress'])} Congress: "
                      f"{congress['parsed']}/{congress['total']} documents")
                printed = True
        if not printed:
            print("No documents parsed")
        print()

        print("Text files:")
        printed = False
        for congress in congresses:
            if congress['txts'] > 0:
                print(f"{ordinal(congress['congress'])} Congress: "
                      f"{congress['txts']}/{congress['total']} documents")
                printed = True
        if not printed:
            print("No text files downloaded")
        print()

        print("PDF files:")
        printed = False
        for congress in congresses:
            if congress['pdfs'] > 0:
                print(f"{ordinal(congress['congress'])} Congress: "
                      f"{congress['pdfs']}/{congress['total']} documents")
                printed = True
        if not printed:
            print("No PDF files downloaded")
        print()

        print("Metadata:")
        printed = False
        for congress in congresses:
            if congress['xmls'] > 0:
                print(f"{ordinal(congress['congress'])} Congress: "
                      f"{congress['xmls']}/{congress['total']} documents")
                printed = True
        if not printed:
            print("No metadata downloaded")
        print()


# Code to execute for the download subcommand
def download(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    pass


# Code to execute for the parse subcommand
def parse(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    pass


# Code to execute for the export subcommand
def export(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    pass


def main() -> None:

    # Run parser
    parser = setup_parser()
    args = parser.parse_args()
    args.func(parser, args)
    

if __name__ == "__main__":
    main()