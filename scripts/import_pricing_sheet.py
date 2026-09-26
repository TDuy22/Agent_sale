"""Future Google Sheets pricing import command.

TODO:
1. Authenticate with Google using deployment-appropriate credentials.
2. Map a versioned sheet schema into config/pricing.yaml.
3. Validate prices and material codes before atomically replacing the local snapshot.

The request path must continue reading the local repository snapshot, never Google Sheets.
"""


def main() -> None:
    raise NotImplementedError("Google Sheets import is intentionally not implemented in MVP")


if __name__ == "__main__":
    main()
