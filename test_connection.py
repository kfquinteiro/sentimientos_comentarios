"""Testa a conexão com a API do ExportComments (ping)."""
from exportcomments_client import ExportCommentsClient

if __name__ == "__main__":
    client = ExportCommentsClient()
    print(client.ping())
