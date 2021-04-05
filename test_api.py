#!/usr/bin/python3

# pylint: disable=invalid-name
# pylint: disable=unused-variable

import sys
import argparse
import time
import json

import requests
import socketio

from web_utils import create_hmac_sig

URL_BASE = "http://localhost:5000/paydb/"
WS_URL = "ws://localhost:5000/"

EXIT_NO_COMMAND = 1

def construct_parser():
    # construct argument parser
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="command")

    ## Websocket

    parser_ws = subparsers.add_parser("websocket", help="Listen to a websocket")
    parser_ws.add_argument("api_key_token", metavar="API_KEY_TOKEN", type=str, help="the API KEY token")
    parser_ws.add_argument("api_key_secret", metavar="API_KEY_SECRET", type=str, help="the API KEY secret")

    ## REST commands

    parser_api_key_create = subparsers.add_parser("api_key_create", help="Create an api key with your username and password")
    parser_api_key_create.add_argument("email", metavar="EMAIL", type=str, help="email")
    parser_api_key_create.add_argument("password", metavar="PASSWORD", type=str, help="password")
    parser_api_key_create.add_argument("device_name", metavar="DEVICE_NAME", type=str, help="the device name for the api key")

    parser_user_info = subparsers.add_parser("user_info", help="Get the user info")
    parser_user_info.add_argument("api_key_token", metavar="API_KEY_TOKEN", type=str, help="the API KEY token")
    parser_user_info.add_argument("api_key_secret", metavar="API_KEY_SECRET", type=str, help="the API KEY secret")

    parser_transaction_create = subparsers.add_parser("transaction_create", help="Create a transaction")
    parser_transaction_create.add_argument("api_key_token", metavar="API_KEY_TOKEN", type=str, help="the API KEY token")
    parser_transaction_create.add_argument("api_key_secret", metavar="API_KEY_SECRET", type=str, help="the API KEY secret")
    parser_transaction_create.add_argument("action", metavar="ACTION", type=str, help="the transaction action")
    parser_transaction_create.add_argument("recipient", metavar="RECIPIENT", type=str, help="the transaction recipient")
    parser_transaction_create.add_argument("amount", metavar="AMOUNT", type=int, help="the transaction amount (integer, cents)")
    parser_transaction_create.add_argument("attachment", metavar="ATTACHMENT", type=str, help="the transaction attachment")

    parser_transaction_info = subparsers.add_parser("transaction_info", help="Get transaction info")
    parser_transaction_info.add_argument("api_key_token", metavar="API_KEY_TOKEN", type=str, help="the API KEY token")
    parser_transaction_info.add_argument("api_key_secret", metavar="API_KEY_SECRET", type=str, help="the API KEY secret")
    parser_transaction_info.add_argument("token", metavar="TOKEN", type=str, help="the unique transaction token")
    return parser

def req(endpoint, params=None, api_key_token=None, api_key_secret=None):
    if api_key_token:
        if not params:
            params = {}
        params["nonce"] = int(time.time())
        params["api_key"] = api_key_token
    url = URL_BASE + endpoint
    if params:
        headers = {"Content-type": "application/json"}
        body = json.dumps(params)
        if api_key_token:
            headers["X-Signature"] = create_hmac_sig(api_key_secret, body)
        print("   POST - " + url)
        r = requests.post(url, headers=headers, data=body)
    else:
        print("   GET - " + url)
        r = requests.get(url)
    return r

def check_request_status(r):
    try:
        r.raise_for_status()
    except Exception as e:
        print("::ERROR::")
        print(str(r.status_code) + " - " + r.url)
        print(r.text)
        raise e

def websocket(args):
    print(":: calling websocket..")
    ns = '/paydb'
    # open websocket
    sio = socketio.Client()
    @sio.event(namespace=ns)
    def connect():
        print("connection established")
        print("authenticating with api key", args.api_key_token)
        # create auth data
        nonce = int(time.time())
        sig = create_hmac_sig(args.api_key_secret, str(nonce))
        auth = {"signature": sig, "api_key": args.api_key_token, "nonce": nonce}
        # emit auth message
        sio.emit("auth", auth, namespace=ns)

    @sio.event(namespace=ns)
    def info(data):
        print("info event received:", data)

    @sio.event(namespace=ns)
    def tx(data):
        print("tx event received:", data)

    @sio.event(namespace=ns)
    def disconnect():
        print("disconnected from server")

    sio.connect(WS_URL, namespaces=[ns])
    sio.wait()

def api_key_create(args):
    print(":: calling api_key_create..")
    r = req("api_key_create", {"email": args.email, "password": args.password, "device_name": args.device_name})
    check_request_status(r)
    print(r.text)

def user_info(args):
    print(":: calling user_info..")
    r = req("user_info", {"email": None}, args.api_key_token, args.api_key_secret)
    check_request_status(r)
    print(r.text)

def transaction_create(args):
    print(":: calling transaction_create..")
    r = req("transaction_create", {"action": args.action, "recipient": args.recipient, "amount": args.amount, "attachment": args.attachment}, args.api_key_token, args.api_key_secret)
    check_request_status(r)
    print(r.text)

def transaction_info(args):
    print(":: calling transaction_info..")
    r = req("transaction_info", {"token": args.token}, args.api_key_token, args.api_key_secret)
    check_request_status(r)
    print(r.text)

def run_parser():
    # parse arguments
    parser = construct_parser()
    args = parser.parse_args()

    # set appropriate function
    function = None
    if args.command == "websocket":
        function = websocket
    elif args.command == "api_key_create":
        function = api_key_create
    elif args.command == "user_info":
        function = user_info
    elif args.command == "transaction_create":
        function = transaction_create
    elif args.command == "transaction_info":
        function = transaction_info
    else:
        parser.print_help()
        sys.exit(EXIT_NO_COMMAND)

    if function:
        function(args)

if __name__ == "__main__":
    run_parser()
