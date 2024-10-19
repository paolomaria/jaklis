#!/usr/bin/env python3

import argparse
import sys
import os
import string
import random
from dotenv import load_dotenv
from duniterpy.key import SigningKey
from pathlib import Path
from lib.gva import GvaApi
from lib.cesium import CesiumPlus

__version__ = "0.1.1"

MY_PATH = Path(__file__).resolve().parent

# Set file paths
dotenv_file = MY_PATH / ".env"
dotenv_template = MY_PATH / ".env.template"

# Check and create dotenv file
if not dotenv_file.is_file():
    dotenv_file.write_text(dotenv_template.read_text())

# Load environment variables
load_dotenv(dotenv_file)

# Set global values (default parameters) regarding environment variables
node = os.getenv("DUNITER") + "/gva" or "https://g1v1.p2p.legal/gva"
pod = os.getenv("ESNODE") or "https://g1.data.e-is.pro"
destPubkey = False

# define parser
parser = argparse.ArgumentParser(
    description="CLI Client for Cesium+ and Ḡchange",
    epilog="current node: '" + node + "', current pod: '" + pod + "'.",
)

# load global arguments
parser.add_argument(
    "-v",
    "--version",
    action="store_true",
    help="Display the current program version",
)
parser.add_argument("-k", "--key", help="Path to the keyfile (PubSec)")
parser.add_argument(
    "-n", "--node", help="Address of the Cesium+, Gchange, or Duniter node to use"
)

# Define commands with arguments
commands = {
    "read": {
        "help": "Read messages",
        "arguments": {
            ("n", "number"): {
                "type": int,
                "default": 3,
                "help": "Display the last NUMBER messages",
            },
            ("j", "json"): {"action": "store_true", "help": "Output in JSON format"},
            ("o", "outbox"): {"action": "store_true", "help": "Read sent messages"},
        },
        "type": "cesium",
    },
    "send": {
        "help": "Send a message",
        "arguments": {
            ("d", "destinataire"): {
                "required": True,
                "help": "Recipient of the message",
            },
            ("t", "titre"): {"help": "Title of the message to send"},
            ("m", "message"): {"help": "Message to send"},
            ("f", "fichier"): {"help": "Send the message from the 'FILE'"},
            ("o", "outbox"): {
                "action": "store_true",
                "help": "Send the message to the outbox",
            },
        },
        "type": "cesium",
    },
    "delete": {
        "help": "Delete a message",
        "arguments": {
            ("i", "id"): {
                "action": "append",
                "nargs": "+",
                "required": True,
                "help": "ID(s) of the message(s) to delete",
            },
            ("o", "outbox"): {
                "action": "store_true",
                "help": "Delete a sent message",
            },
        },
        "type": "cesium",
    },
    "get": {
        "help": "View a Cesium+ profile",
        "arguments": {
            ("p", "profile"): {"help": "Profile name"},
            ("a", "avatar"): {
                "action": "store_true",
                "help": "Also retrieve the avatar in raw base64 format",
            },
        },
        "type": "cesium",
    },
    "page": {
        "help": "View a Cesium+ page",
        "arguments": {
            ("p", "page"): {"help": "Page name"},
            ("a", "avatar"): {
                "action": "store_true",
                "help": "Also retrieve the page's avatar in raw base64 format",
            },
        },
        "type": "cesium",
    },
    "set": {
        "help": "Configure your Cesium+ profile",
        "arguments": {
            ("n", "name"): {"help": "Profile name"},
            ("d", "description"): {"help": "Profile description"},
            ("v", "ville"): {"help": "Profile city"},
            ("a", "adresse"): {"help": "Profile address"},
            ("pos", "position"): {
                "nargs": 2,
                "help": "Geographical coordinates (lat + lon)",
            },
            ("s", "site"): {"help": "Profile website"},
            ("A", "avatar"): {"help": "Path to profile avatar in PNG"},
        },
        "type": "cesium",
    },
    "erase": {
        "help": "Erase your Cesium+ profile",
        "arguments": {},
        "type": "cesium",
    },
    "stars": {
        "help": "View a profile's stars / Rate a profile (option -s RATING)",
        "arguments": {
            ("p", "profile"): {"help": "Target profile"},
            ("n", "number"): {"type": int, "help": "Number of stars"},
        },
        "type": "cesium",
    },
    "unstars": {
        "help": "Remove a star",
        "arguments": {
            ("p", "profile"): {"help": "Profile to unstar"},
        },
        "type": "cesium",
    },
    "getoffer": {
        "help": "Get information about a Ḡchange listing",
        "arguments": {
            ("i", "id"): {"help": "Target listing to retrieve"},
        },
        "type": "cesium",
    },
    "setoffer": {
        "help": "Create a Ḡchange listing",
        "arguments": {
            ("t", "title"): {"help": "Title of the listing to create"},
            ("d", "description"): {"help": "Description of the listing to create"},
            ("c", "category"): {"help": "Category of the listing to create"},
            ("l", "location"): {
                "nargs": 2,
                "help": "Location of the listing to create (lat + lon)",
            },
            ("p", "picture"): {"help": "Image of the listing to create"},
            ("ci", "city"): {"help": "City of the listing to create"},
            ("pr", "price"): {"help": "Price of the listing to create"},
        },
        "type": "cesium",
    },
    "deleteoffer": {
        "help": "Delete a Ḡchange listing",
        "arguments": {
            ("i", "id"): {"help": "Target listing to delete"},
        },
        "type": "cesium",
    },
    "geolocProfiles": {
        "help": "Get JSON of all geolocated accounts",
        "arguments": {},
        "type": "cesium",
    },
    "pay": {
        "help": "Pay in Ḡ1",
        "arguments": {
            ("p", "pubkey"): {"help": "Payment recipient"},
            ("a", "amount"): {"type": float, "help": "Transaction amount"},
            ("c", "comment"): {
                "default": "",
                "help": "Transaction comment",
                "nargs": "*",
            },
            ("m", "mempool"): {
                "action": "store_true",
                "help": "Use mempool sources",
            },
            ("v", "verbose"): {
                "action": "store_true",
                "help": "Display the JSON result of the transaction",
            },
        },
        "type": "gva",
    },
    "history": {
        "help": "View Ḡ1 account transaction history",
        "arguments": {
            ("p", "pubkey"): {"help": "Public key of the target account"},
            ("n", "number"): {
                "type": int,
                "default": 10,
                "help": "Display the last NUMBER transactions",
            },
            ("j", "json"): {
                "action": "store_true",
                "help": "Display the result in JSON format",
            },
            ("nocolors"): {
                "action": "store_true",
                "help": "Display the result in black and white",
            },
        },
        "type": "gva",
    },
    "balance": {
        "help": "View Ḡ1 account balance",
        "arguments": {
            ("p", "pubkey"): {"help": "Public key of the target account"},
            ("m", "mempool"): {
                "action": "store_true",
                "help": "Use mempool sources",
            },
        },
        "type": "gva",
    },
    "id": {
        "help": "View public key/username identity",
        "arguments": {
            ("p", "pubkey"): {"help": "Public key of the target account"},
            ("u", "username"): {"help": "Username of the target account"},
        },
        "type": "gva",
    },
    "idBalance": {
        "help": "View public key/username identity and balance",
        "arguments": {
            ("p", "pubkey"): {"help": "Public key of the target account"},
        },
        "type": "gva",
    },
    "currentUd": {
        "help": "Display the current Universal Dividend amount",
        "arguments": {
            ("p", "pubkey"): {"help": "Public key of the target account"},
        },
        "type": "gva",
    },
    "listWallets": {
        "help": "List all G1 wallets",
        "arguments": {
            ("m", "mbr"): {
                "action": "store_true",
                "help": "Display raw list of member pubkeys",
            },
            ("nm", "non_mbr"): {
                "action": "store_true",
                "help": "Display raw list of nonmember identity pubkeys",
            },
            ("l", "larf"): {
                "action": "store_true",
                "help": "Display raw list of nonmember pubkeys",
            },
            ("b", "brut"): {
                "action": "store_true",
                "help": "Display raw list of all pubkeys",
            },
        },
        "type": "gva",
    },
}

# Process commands and arguments
subparsers = parser.add_subparsers(title="jaklis Commands", dest="cmd")
for cmd, cmd_info in commands.items():
    cmd_parser = subparsers.add_parser(cmd, help=cmd_info["help"])
    for args, kwargs in cmd_info["arguments"].items():
        if isinstance(args, str):
            cmd_parser.add_argument("--" + args, **kwargs)
        else:
            short_arg, long_arg = args
            cmd_parser.add_argument("-" + short_arg, "--" + long_arg, **kwargs)

args = parser.parse_args()
args_dict = vars(args)
cmd = args.cmd
if args.version:
    print(__version__)
    sys.exit(0)

if not cmd:
    parser.print_help()
    sys.exit(0)


def createTmpDunikey():
    # Generate a pseudo-random nonce
    nonce = "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(32)
    )
    keyPath = "/tmp/secret.dunikey-" + nonce

    # Create a dummy key (replace with actual key creation logic)
    key = SigningKey.from_credentials(
        "sgse547yhd54xv6541srdh", "sfdgwdrhpkxdawsbszqpof1sdg65xc", None
    )
    key.save_pubsec_file(keyPath)

    return keyPath


def get_arg_value(args, arg):
    try:
        return getattr(args, arg)
    except AttributeError:
        return False


def get_dunikey(args):
    if args.key:
        return args.key
    dunikey = os.getenv("DUNIKEY")
    if not dunikey:
        keyPath = createTmpDunikey()
        dunikey = keyPath
    if not os.path.isfile(dunikey):
        HOME = os.getenv("HOME")
        dunikey = HOME + dunikey
        if not os.path.isfile(dunikey):
            sys.stderr.write("The keyfile {0} is not found.\n".format(dunikey))
            sys.exit(1)
    return dunikey


pubkey = get_arg_value(args, "pubkey")
profile = get_arg_value(args, "profile")

noNeedDunikey = cmd in (
    "history",
    "balance",
    "page",
    "id",
    "idBalance",
    "listWallets",
    "geolocProfiles",
) and (pubkey or profile)

if noNeedDunikey:
    dunikey = pubkey if pubkey else profile
else:
    dunikey = get_dunikey(args)

keyPath = False if dunikey else createTmpDunikey()


def handle_cesium_commands(args, cmd, cesium):
    # Get args of the command
    cmd_args = (
        list(zip(*list(commands[cmd]["arguments"].keys())))[1]
        if len(commands[cmd]["arguments"].keys()) > 0
        else []
    )
    cmd_args_dict = {arg: args_dict[arg] for arg in cmd_args if arg in args_dict}
    cmd_args_values = list(cmd_args_dict.values())

    # Messaging
    if cmd == "read":
        cesium.read(*cmd_args_values)
    elif cmd == "send":
        if args.fichier:
            with open(args.fichier, "r") as f:
                msgT = f.read()
                titre = msgT.splitlines(True)[0].replace("\n", "")
                msg = "".join(msgT.splitlines(True)[1:])
                if args.titre:
                    titre = args.titre
                    msg = msgT
        elif args.titre and args.message:
            titre = args.titre
            msg = args.message
        else:
            titre = input("Enter the message title: ")
            msg = input("Enter the message content: ")

        cesium.send(titre, msg, args.destinataire, args.outbox)

    elif cmd == "delete":
        cesium.delete(args.id[0], args.outbox)

    # Profiles
    elif cmd == "set":
        cesium.set(**cmd_args_dict)
    elif cmd == "get":
        cesium.get(**cmd_args_dict)
    elif cmd == "page":
        cesium.getPage(**cmd_args_dict)
    elif cmd == "erase":
        cesium.erase()
    elif cmd == "geolocProfiles":
        cesium.geolocProfiles(node)

    # Stars
    elif cmd == "stars":
        if args.number or args.number == 0:
            cesium.like(args.number, args.profile)
        else:
            cesium.readLikes(args.profile)
    elif cmd == "unstars":
        cesium.unLike(args.profile)

    # Offers
    elif cmd == "getoffer":
        cesium.getOffer(args.id)
    elif cmd == "setoffer":
        cesium.setOffer(**cmd_args_dict)
    elif cmd == "deleteoffer":
        cesium.deleteOffer(**cmd_args_dict)
    else:
        raise ValueError(f"Unknown command: {cmd}")


def handle_gva_commands(args, cmd, gva):
    # Get args of the command
    cmd_args = (
        list(zip(*list(commands[cmd]["arguments"].keys())))[1]
        if len(commands[cmd]["arguments"].keys()) > 0
        else []
    )
    cmd_args_dict = {arg: args_dict[arg] for arg in cmd_args if arg in args_dict}
    # cmd_args_values = list(cmd_args_dict.values())

    if cmd == "pay":
        gva.pay(args.amount, args.comment, args.mempool, args.verbose)
    elif cmd == "history":
        gva.history(args.json, args.nocolors, args.number)
    elif cmd == "balance":
        gva.balance(args.mempool)
    elif cmd == "id":
        gva.id(**cmd_args_dict)
    elif cmd == "idBalance":
        gva.idBalance(**cmd_args_dict)
    elif cmd == "currentUd":
        gva.currentUd()
    elif cmd == "listWallets":
        gva.listWallets(args.brut, args.mbr, args.non_mbr, args.larf)
    else:
        raise ValueError(f"Unknown command: {cmd}")


# Construct the CesiumPlus object
if commands[cmd]["type"] == "cesium":
    if args.node:
        pod = args.node

    cesium = CesiumPlus(dunikey, pod, noNeedDunikey)
    handle_cesium_commands(args, cmd, cesium)

# Construct the GvaApi object
elif commands[cmd]["type"] == "gva":
    if args.node:
        node = args.node

    if hasattr(args, "pubkey"):
        destPubkey = args.pubkey

    gva = GvaApi(dunikey, node, destPubkey, noNeedDunikey)
    handle_gva_commands(args, cmd, gva)
else:
    raise ValueError(f"Unknown command: {cmd}")

if keyPath:
    os.remove(keyPath)
