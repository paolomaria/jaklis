#!/usr/bin/env python3

import sys
import json
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from lib.natools import fmt, sign, get_privkey


class ListWallets:
    def __init__(
        self, node=False, brut=False, mbr=False, nonMbr=False, larf=False, map=False
    ):
        # Initialize the ListWallets class with optional filters
        self.mbr = mbr  # Filter for members
        self.larf = larf  # Filter for non-empty identities
        self.nonMbr = nonMbr  # Filter for non-members
        self.brut = brut  # Output format flag (brut or JSON)
        self.map = map  # Output format flag (map or list)

        # Define Duniter GVA node
        transport = AIOHTTPTransport(url=node)
        self.client = Client(transport=transport, fetch_schema_from_transport=True)

    def sendDoc(self):
        # Define the GraphQL query to retrieve wallet information
        queryBuild = gql(
            """
            {
                wallets(pagination: { cursor: null, ord: ASC, pageSize: 0 }) {
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                    edges {
                        node {
                            script
                            balance {
                                amount
                                base
                            }
                            idty {
                                isMember
                                username
                            }
                        }
                    }
                }
            }
            """
        )

        try:
            # Execute the GraphQL query
            queryResult = self.client.execute(queryBuild)
        except Exception as e:
            # Handle any exceptions that occur during the query
            sys.stderr.write("Failed to retrieve the list:\n" + str(e) + "\n")
            sys.exit(1)

        jsonBrut = queryResult["wallets"]["edges"]

        walletList = []
        walletMap = {}

        for i, trans in enumerate(jsonBrut):
            dataWork = trans["node"]
            identity = dataWork["idty"]
            is_member = identity and identity["isMember"]

            # Apply filters based on member status and larf flag
            member_filter = self.mbr and not is_member
            non_member_filter = self.nonMbr and is_member
            larf_filter = self.larf and identity
            if member_filter or non_member_filter or larf_filter:
                continue

            wallet_data = {
                "pubkey": dataWork["script"],
                "balance": dataWork["balance"]["amount"] / 100,
                "id": identity,
            }

            if self.map:
                walletMap[dataWork["script"]] = wallet_data
            else:
                walletList.append(wallet_data)

        if self.brut:
            # Generate a list of formatted wallet names using list comprehension
            names = [
                wallet["pubkey"]
                if not (self.mbr or self.nonMbr) or wallet["id"] is None
                else f'{wallet["pubkey"]} {wallet["id"]["username"]}'
                for wallet in walletList
            ]
            return "\n".join(names)
        else:
            # Return JSON data in either map or list format
            return json.dumps(walletMap if self.map else walletList, indent=2)
