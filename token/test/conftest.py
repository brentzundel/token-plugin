import pytest

from ledger.util import F
from plenum.client.wallet import Wallet
from plugin.tokens.src.main import update_node_obj
from plugin.tokens.src.util import register_token_wallet_with_client
from plugin.tokens.src.wallet import TokenWallet
from plenum.test.plugin.helper import getPluginPath
from plugin.tokens.test.helper import send_get_utxo, send_xfer


def build_wallets_from_data(name_seeds):
    wallets = []
    for name, seed in name_seeds:
        w = Wallet(name)
        w.addIdentifier(seed=seed.encode())
        wallets.append(w)
    return wallets


@pytest.fixture(scope="module")
def SF_token_wallet():
    return TokenWallet('SF_MASTER')


@pytest.fixture(scope="module")
def SF_address(SF_token_wallet):
    seed = 'sf000000000000000000000000000000'.encode()
    SF_token_wallet.add_new_address(seed=seed)
    return next(iter(SF_token_wallet.addresses.keys()))


@pytest.fixture(scope="module")
def seller_token_wallet():
    return TokenWallet('SELLER')


@pytest.fixture(scope="module")
def seller_address(seller_token_wallet):
    # Token selling/buying platform's address
    seed = 'se000000000000000000000000000000'.encode()
    seller_token_wallet.add_new_address(seed=seed)
    return next(iter(seller_token_wallet.addresses.keys()))


@pytest.fixture(scope="module")
def trustee_wallets(trustee_data):
    return build_wallets_from_data(trustee_data)


@pytest.fixture(scope="module")
def allPluginsPath(allPluginsPath):
    return allPluginsPath + [getPluginPath('token')]


@pytest.fixture(scope="module")
def do_post_node_creation():
    # Integrate plugin into each node.
    def _post_node_creation(node):
        update_node_obj(node)

    return _post_node_creation


@pytest.fixture(scope="module")
def txnPoolNodeSet(tconf, do_post_node_creation, txnPoolNodeSet):
    return txnPoolNodeSet


@pytest.fixture(scope="module")
def tokens_distributed(public_minting, seller_token_wallet, seller_address,
                       user1_address, user1_token_wallet,
                       user2_address, user2_token_wallet,
                       user3_address, user3_token_wallet, looper, client1,
                       wallet1, client1Connected):
    register_token_wallet_with_client(client1, seller_token_wallet)
    send_get_utxo(looper, seller_address, wallet1, client1)
    total_amount = seller_token_wallet.get_total_address_amount(seller_address)

    inputs = [[seller_token_wallet, seller_address, seq_no] for seq_no, _ in
              next(iter(seller_token_wallet.get_all_address_utxos(seller_address).values()))]
    each_user_share = total_amount // 3
    outputs = [[user1_address, each_user_share],
               [user2_address, each_user_share],
               [user3_address, each_user_share],
               [seller_address, total_amount % 3]]
    req = send_xfer(looper, inputs, outputs, client1)
    for w, a in [(user1_token_wallet, user1_address),
                 (user2_token_wallet, user2_address),
                 (user3_token_wallet, user3_address)]:
        register_token_wallet_with_client(client1, w)
        send_get_utxo(looper, a, wallet1, client1)

    reply, _ = client1.getReply(req.identifier, req.reqId)
    return reply[F.seqNo.name]